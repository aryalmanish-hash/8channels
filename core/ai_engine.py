"""
core/ai_engine.py
Multi-provider AI engine with smart task-based routing.

Providers: Groq, OpenRouter (300+ models), Gemini
Task-based routing picks the best model for each job.
Full verbose log at logs/latest_generation.log.
"""

from __future__ import annotations
import json
import time
import yaml
import requests
from pathlib import Path


# ── Log file (overwritten every run) ──────────────────────────────────────
_LOG_FILE = Path("logs") / "latest_generation.log"
_LOG_INITIALIZED = False


def _init_log():
    """Reset log file at start of new generation."""
    global _LOG_INITIALIZED
    _LOG_FILE.parent.mkdir(exist_ok=True)
    _LOG_FILE.write_text(
        f"[LOG START] {datetime_now()}\n" + "=" * 70 + "\n",
        encoding="utf-8"
    )
    _LOG_INITIALIZED = True


def datetime_now():
    from datetime import datetime as _dt
    return _dt.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str):
    """Append line to log file. Silent to console."""
    global _LOG_INITIALIZED
    if not _LOG_INITIALIZED:
        _init_log()
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime_now()}] {msg}\n")
    except Exception:
        pass

def _strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from AI response (qwen/reasoning models)."""
    if not text:
        return text
    import re as _re
    # Remove <think>...</think> blocks (case-insensitive, multiline)
    text = _re.sub(r"<think>.*?</think>", "", text, flags=_re.DOTALL | _re.IGNORECASE)
    # Remove <thinking>...</thinking> blocks
    text = _re.sub(r"<thinking>.*?</thinking>", "", text, flags=_re.DOTALL | _re.IGNORECASE)
    # Remove "We need to output..." or "Okay, let me..." preambles
    lines = text.strip().splitlines()
    cleaned = []
    started = False
    for line in lines:
        low = line.strip().lower()
        if not started:
            # Skip meta-commentary until first real content line
            if low.startswith(("we need", "okay,", "let me", "here's my", "let's tackle",
                              "sure,", "sure!", "i'll write", "analyzing", "understanding",
                              "the user wants", "based on")):
                continue
            # First real content line
            if line.strip():
                started = True
        if started:
            cleaned.append(line)
    return "\n".join(cleaned).strip()


def reset_log():
    """Call at START of a new video generation. Wipes old log."""
    global _LOG_INITIALIZED
    _LOG_FILE.parent.mkdir(exist_ok=True)
    _LOG_FILE.write_text(
        f"[LOG START] {datetime_now()}\n" + "=" * 70 + "\n",
        encoding="utf-8"
    )
    _LOG_INITIALIZED = True




# ── Load API keys ──────────────────────────────────────────────────────────
def _load_keys():
    p = Path("config/global_settings.yaml")
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {}


# ── Models per task type ──────────────────────────────────────────────────
# Format: list of (provider, model_name)

# STORY (creative writing) — quality > speed
STORY_MODELS = [
    # ── Tier 1: Groq fast + clean ──
    ("groq",       "llama-3.3-70b-versatile"),                      # 1.1s clean best
    ("groq",       "meta-llama/llama-4-scout-17b-16e-instruct"),    # 2.0s clean
    ("groq",       "groq/compound"),                                # 5.2s clean
    ("groq",       "qwen/qwen3.6-27b"),                             # 1.8s has <think>
    # ── Tier 2: Gemini clean ──
    ("gemini",     "gemini-2.5-flash"),                             # 9.7s clean
    # ── Tier 3: OpenRouter big/backup ──
    ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"),       # 22.8s big brain
    ("openrouter", "nvidia/nemotron-3-nano-30b-a3b:free"),          # 8.3s chatty
    ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),       # 47s slow
    ("openrouter", "meta-llama/llama-3.3-70b-instruct:free"),       # rate-limited backup
]

# METADATA (JSON structure) — good at following format
METADATA_MODELS = [
    # ── Tier 1: Groq fast + clean JSON ──
    ("groq",       "llama-3.1-8b-instant"),                         # 0.9s BEST fastest
    ("groq",       "llama-3.3-70b-versatile"),                      # 1.3s clean JSON
    # ── Tier 2: Gemini clean JSON ──
    ("gemini",     "gemini-2.5-flash"),                             # 6.1s clean JSON
    # ── Tier 3: OpenRouter (chatty but works) ──
    ("openrouter", "nvidia/nemotron-3-nano-30b-a3b:free"),          # 4.8s chatty
    ("openrouter", "nvidia/nemotron-3-super-120b-a12b:free"),       # 11s chatty
    # ── Tier 4: Backup ──
    ("groq",       "meta-llama/llama-4-scout-17b-16e-instruct"),    # occasional 503
]

# SHORT tasks (safety, validation) — speed matters
SHORT_MODELS = [
    ("groq",       "llama-3.1-8b-instant"),                         # 0.7s fastest
    ("groq",       "llama-3.3-70b-versatile"),                      # 0.7s
    ("openrouter", "nvidia/nemotron-3-nano-30b-a3b:free"),          # 1.7s
    ("gemini",     "gemini-2.5-flash"),                             # 2.6s
    ("groq",       "meta-llama/llama-4-scout-17b-16e-instruct"),    # 4.0s backup
]

# Legacy lists (kept for backwards compat)
GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
]

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.0-flash",
]


# ── Rate-limit spacing ───────────────────────────────────────────────────
_LAST_CALL_TS = {"groq": 0.0, "openrouter": 0.0, "gemini": 0.0}
_MIN_GAP = {"groq": 1.2, "openrouter": 0.5, "gemini": 2.0}


def _rate_limit(provider: str):
    now = time.time()
    gap = now - _LAST_CALL_TS.get(provider, 0)
    if gap < _MIN_GAP.get(provider, 0):
        time.sleep(_MIN_GAP[provider] - gap)
    _LAST_CALL_TS[provider] = time.time()


# ── Provider callers ──────────────────────────────────────────────────────

def _call_groq(model: str, prompt: str, system: str = "") -> str | None:
    try:
        from groq import Groq
        keys = _load_keys()
        api_key = keys.get("groq_api_key", "")
        if not api_key:
            log(f"  [GROQ] No API key")
            return None

        _rate_limit("groq")
        client = Groq(api_key=api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=1.2,
            top_p=0.95,
        )
        text = response.choices[0].message.content
        text = _strip_think_tags(text or "")
        if text and len(text.strip()) > 0:
            return text.strip()
        return None
    except Exception as e:
        log(f"  [GROQ] {model} error: {e}")
        raise


def _call_openrouter(model: str, prompt: str, system: str = "") -> str | None:
    try:
        keys = _load_keys()
        api_key = keys.get("openrouter_api_key", "")
        if not api_key:
            log(f"  [OR] No API key")
            return None

        _rate_limit("openrouter")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "https://github.com/8channel-content-factory",
                "X-Title":       "8-Channel Content Factory",
            },
            json={
                "model":       model,
                "messages":    messages,
                "temperature": 1.2, "top_p": 0.95,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            log(f"  [OR] {model} HTTP {resp.status_code}: {resp.text[:200]}")
            raise RuntimeError(f"HTTP {resp.status_code}")

        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        text = _strip_think_tags(text or "")
        if text and len(text.strip()) > 0:
            return text.strip()
        return None
    except Exception as e:
        log(f"  [OR] {model} error: {e}")
        raise


def _call_gemini(model: str, prompt: str, system: str = "") -> str | None:
    try:
        from google import genai
        keys = _load_keys()
        api_key = keys.get("gemini_api_key", "")
        if not api_key:
            log(f"  [GEMINI] No API key")
            return None

        _rate_limit("gemini")
        client = genai.Client(api_key=api_key)
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
        )
        text = getattr(response, "text", None)
        text = _strip_think_tags(text or "")
        if text and len(text.strip()) > 0:
            return text.strip()
        return None
    except Exception as e:
        log(f"  [GEMINI] {model} error: {e}")
        raise


PROVIDER_FUNCS = {
    "groq":       _call_groq,
    "openrouter": _call_openrouter,
    "gemini":     _call_gemini,
}


# ── Smart routing ────────────────────────────────────────────────────────
def _model_short_name(provider: str, model: str) -> str:
    """Return a clean short label for progress display."""
    m = model.split("/")[-1].split(":")[0]
    return f"{provider.title()} {m}"


def ask_ai_task(prompt: str, system: str = "", task: str = "short",
                progress_callback=None) -> str | None:
    """
    Route to best AI models for given task type.
    task: "story" | "metadata" | "short"

    progress_callback(provider_label, elapsed_sec, ok_bool) — for CLI live updates.
    """
    if task == "story":
        models = STORY_MODELS
    elif task == "metadata":
        models = METADATA_MODELS
    else:
        models = SHORT_MODELS

    log(f"\n=== ask_ai_task task={task} ===")
    log(f"prompt (first 300): {prompt[:300]}")
    log(f"trying {len(models)} models in order")

    for i, (provider, model) in enumerate(models, 1):
        label = _model_short_name(provider, model)
        log(f"\n  [{i}/{len(models)}] Trying {label}")
        t0 = time.time()
        try:
            result = PROVIDER_FUNCS[provider](model, prompt, system)
            elapsed = time.time() - t0
            if result:
                log(f"  [{i}/{len(models)}] {label} OK in {elapsed:.1f}s ({len(result)} chars)")
                log(f"  response first 300: {result[:300]}")
                if progress_callback:
                    progress_callback(label, elapsed, True)
                return result
            else:
                log(f"  [{i}/{len(models)}] {label} empty in {elapsed:.1f}s")
                if progress_callback:
                    progress_callback(label, elapsed, False)
        except Exception as e:
            elapsed = time.time() - t0
            log(f"  [{i}/{len(models)}] {label} FAIL in {elapsed:.1f}s: {e}")
            if progress_callback:
                progress_callback(label, elapsed, False)
            continue

    log(f"  All {len(models)} models failed for task={task}")
    return None


# ── Backward-compat wrappers ─────────────────────────────────────────────
def ask_ai(prompt: str, system: str = "") -> str | None:
    """Default: use short-task routing."""
    return ask_ai_task(prompt, system, task="short")


def ask_groq(prompt: str, system: str = "", model: str | None = None) -> str | None:
    """Direct Groq call (legacy). Use ask_ai_task for smart routing."""
    for m in GROQ_MODELS if not model else [model]:
        try:
            _rate_limit("groq")
            r = _call_groq(m, prompt, system)
            if r:
                return r
        except Exception:
            continue
    return None


def ask_gemini(prompt: str, system: str = "", model: str | None = None) -> str | None:
    """Direct Gemini call (legacy)."""
    for m in GEMINI_MODELS if not model else [model]:
        try:
            _rate_limit("gemini")
            r = _call_gemini(m, prompt, system)
            if r:
                return r
        except Exception:
            continue
    return None


# ── Higher-level helpers used by other modules ───────────────────────────
def generate_script_with_ai(channel_id: str, title: str, summary: str = "") -> str | None:
    """Generate script for any channel — routed as STORY task."""
    prompt = f"""Write a 60-90 second video script for channel '{channel_id}'.

Title: {title}
Context: {summary}

Rules:
- Natural spoken English
- Strong hook in first sentence
- Clear structure
- End with a call-to-action
"""
    return ask_ai_task(prompt, task="story")

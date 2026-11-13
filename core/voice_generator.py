"""
core/voice_generator.py
Voice generator using edge-tts (primary) and pyttsx3 (fallback).
Natural-sounding voices per channel.
"""

from __future__ import annotations

import asyncio
import json
import wave
from pathlib import Path


# ── Channel Voice Map ──────────────────────────────────────────────────────

CHANNEL_VOICES = {
    "reddit_stories":      {"voice": "en-US-GuyNeural",         "rate": "+15%", "gender": "male"},
    "english_learning":    {"voice": "en-US-JennyNeural",       "rate": "+0%",  "gender": "female"},
    "psychology":          {"voice": "en-US-AriaNeural",        "rate": "-5%",  "gender": "female"},
    "dark_history":        {"voice": "en-GB-RyanNeural",        "rate": "-5%",  "gender": "male"},
    "ai_tools_automation": {"voice": "en-US-AndrewNeural",      "rate": "+5%",  "gender": "male"},
    "quiz":                {"voice": "en-US-EmmaNeural",        "rate": "+5%",  "gender": "female"},
    "facts":               {"voice": "en-US-SteffanNeural",     "rate": "+0%",  "gender": "male"},
    "sports_reviews":      {"voice": "en-GB-ThomasNeural",      "rate": "+5%",  "gender": "male"},
}

DEFAULT_VOICE = {"voice": "en-US-GuyNeural", "rate": "+0%", "gender": "male"}

# Available voice options for manual selection
VOICE_OPTIONS = {
    "guy_us":      {"voice": "en-US-GuyNeural",       "gender": "male",   "accent": "American"},
    "andrew_us":   {"voice": "en-US-AndrewNeural",    "gender": "male",   "accent": "American"},
    "brian_us":    {"voice": "en-US-BrianNeural",     "gender": "male",   "accent": "American"},
    "eric_us":     {"voice": "en-US-EricNeural",      "gender": "male",   "accent": "American"},
    "ryan_gb":     {"voice": "en-GB-RyanNeural",      "gender": "male",   "accent": "British"},
    "thomas_gb":   {"voice": "en-GB-ThomasNeural",    "gender": "male",   "accent": "British"},
    "aria_us":     {"voice": "en-US-AriaNeural",      "gender": "female", "accent": "American"},
    "jenny_us":    {"voice": "en-US-JennyNeural",     "gender": "female", "accent": "American"},
    "emma_us":     {"voice": "en-US-EmmaNeural",      "gender": "female", "accent": "American"},
    "ava_us":      {"voice": "en-US-AvaNeural",       "gender": "female", "accent": "American"},
    "sonia_gb":    {"voice": "en-GB-SoniaNeural",     "gender": "female", "accent": "British"},
}


def get_available_voices() -> list[dict]:
    return [
        {"key": k, "name": v["voice"], "gender": v["gender"], "accent": v["accent"]}
        for k, v in VOICE_OPTIONS.items()
    ]



def sanitize_script_for_voice(script: str) -> str:
    """
    Clean script text so TTS doesn't read markdown/emojis literally.
    Removes: **bold**, *italic*, _under_, emojis, URLs, bullet points, etc.
    """
    import re as _re
    if not script:
        return script

    # Remove markdown emphasis (** and __ and *)
    script = _re.sub(r"\*\*([^\*]+?)\*\*", r"\1", script)   # **bold**
    script = _re.sub(r"__([^_]+?)__", r"\1", script)                 # __bold__
    script = _re.sub(r"\*([^\*\n]+?)\*", r"\1", script)          # *italic*
    script = _re.sub(r"(?<!\w)_([^_\n]+?)_(?!\w)", r"\1", script) # _italic_

    # Remove markdown headers (# ## ###)
    script = _re.sub(r"^\s*#{1,6}\s+", "", script, flags=_re.MULTILINE)

    # Remove bullet points and list markers at line start
    script = _re.sub(r"^[\s]*[\*\-\+•]\s+", "", script, flags=_re.MULTILINE)
    script = _re.sub(r"^\s*\d+[\.\)]\s+", "", script, flags=_re.MULTILINE)

    # Remove URLs
    script = _re.sub(r"https?://\S+", "", script)
    script = _re.sub(r"www\.\S+", "", script)

    # Remove emojis (broad unicode range)
    script = _re.sub(
        "["
        "\U0001F600-\U0001F64F"   # emoticons
        "\U0001F300-\U0001F5FF"   # symbols & pictographs
        "\U0001F680-\U0001F6FF"   # transport & map
        "\U0001F1E0-\U0001F1FF"   # flags
        "\U0001F900-\U0001F9FF"   # supplemental symbols
        "\U0001FA00-\U0001FA6F"   # extended symbols
        "\U0001FA70-\U0001FAFF"
        "\U00002700-\U000027BF"   # dingbats
        "\U000024C2-\U0001F251"
        "]+",
        "", script, flags=_re.UNICODE
    )

    # Remove stray leftover markdown chars (backticks, tildes at word start/end)
    script = _re.sub(r"`([^`]+)`", r"\1", script)
    script = _re.sub(r"~~([^~]+)~~", r"\1", script)

    # Collapse multiple spaces + multiple blank lines
    script = _re.sub(r"[ \t]+", " ", script)
    script = _re.sub(r"\n{3,}", "\n\n", script)

    return script.strip()


def estimate_duration_seconds(script: str) -> float:
    words = [w for w in script.split() if w.strip()]
    duration = max(6.0, len(words) / 150 * 60)
    return min(duration, 180.0)


async def _edge_tts_generate(
    script: str,
    output_path: Path,
    voice: str,
    rate: str = "+0%",
) -> bool:
    """Generate audio using edge-tts async."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(script, voice, rate=rate)
        await communicate.save(str(output_path))
        return output_path.exists() and output_path.stat().st_size > 1000
    except Exception as e:
        print(f"  edge-tts failed ({voice}): {e}")
        return False




# ── Narrator Gender Detection ──────────────────────────────────────────

FEMALE_INDICATORS = [
    # Direct self-identification
    "my husband", "my boyfriend", "my fiance", "my ex-husband", "my ex-boyfriend",
    "as a woman", "as a girl", "as a mother", "as a wife", "as a daughter",
    "as a sister", "as a mom", "as a mum", "as a girlfriend", "as a bride",
    "i am a woman", "i am a girl", "i am a mom", "i am a mum", "i am a wife",
    "i am a mother", "i am a sister", "i am a daughter", "i am a bride",
    "i'm a woman", "i'm a girl", "i'm a mom", "i'm a mum", "i'm a wife",
    "i'm a mother", "i'm a sister", "i'm a daughter", "i'm a bride",
    # Life events female-coded
    "pregnant", "my period", "my dress", "bridesmaid", "maid of honor",
    "morning sickness", "my baby shower", "my wedding dress", "my bra",
    "in labor", "my ob", "my ob-gyn", "menstrual", "breastfeeding",
    # Female pronouns for self
    "as her mother", "her mom", "her mum", "her wife", "her husband",
]

MALE_INDICATORS = [
    # Direct self-identification
    "my wife", "my girlfriend", "my fiancee", "my ex-wife", "my ex-girlfriend",
    "as a man", "as a guy", "as a father", "as a husband", "as a son",
    "as a brother", "as a dad", "as a boyfriend", "as a groom",
    "i am a man", "i am a guy", "i am a dad", "i am a father",
    "i am a husband", "i am a brother", "i am a son", "i am a groom",
    "i'm a man", "i'm a guy", "i'm a dad", "i'm a father",
    "i'm a husband", "i'm a brother", "i'm a son", "i'm a groom",
    # Life events male-coded
    "my beard", "my mustache", "my prostate",
    # Male pronouns for self
    "as his father", "his dad", "his wife", "his husband",
]


def _ai_detect_narrator_gender(script: str) -> str:
    """
    Use AI to detect narrator gender.
    Returns 'male', 'female', or 'unclear'.
    """
    try:
        from core.ai_engine import ask_ai
        prompt = (
            "Read this Reddit story. The narrator uses 'I' or 'me' to refer to themselves. "
            "Determine the narrator\'s gender (NOT other characters in the story).\n\n"
            "STORY:\n"
            f"{script[:1500]}\n\n"
            "Reply with EXACTLY ONE WORD:\n"
            "  MALE   - if the narrator is a man/boy/guy/husband/father/son/brother\n"
            "  FEMALE - if the narrator is a woman/girl/wife/mother/daughter/sister\n"
            "  UNCLEAR - if you truly cannot tell from the text\n\n"
            "Look for direct clues like (28F), (35M), \"my wife\", \"my husband\", "
            "\"as a mother\", or any pronouns used to describe the narrator by others."
        )
        response = ask_ai(prompt)
        if not response:
            return "unclear"
        response = response.strip().upper()
        # Take first word only
        first_word = response.split()[0] if response else ""
        first_word = first_word.strip(".,!?\"\'")
        if "FEMALE" in first_word:
            return "female"
        if "MALE" in first_word:
            return "male"
        return "unclear"
    except Exception as e:
        print(f"  [GENDER] AI detection failed: {e}")
        return "unclear"


def detect_narrator_gender(script: str) -> str:
    """
    Detect narrator gender.
    Priority (most accurate + cheapest first):
      0. Hint file from story_generator (AI-declared Narrator: in prompt) <- BEST
      1. Age+gender tag "I (28F)" or "(35M)" attached to I/me — reliable
      2. Indicator phrases like "my husband", "as a woman" — no API call needed
      3. AI (Groq) — reads whole script contextually — LAST resort (saves quota)
      4. Truly neutral -> alternate 50/50 based on script hash
    Returns 'male', 'female', or 'neutral'.
    """
    import re as _re
    from pathlib import Path as _P

    # ── 0. Check hint file from story_generator (fastest + most reliable) ──
    hint_file = _P.cwd() / "_narrator_hint.tmp"
    if hint_file.exists():
        try:
            hint = hint_file.read_text(encoding="utf-8").strip().lower()
            if hint in ("male", "female"):
                print(f"  [GENDER] From AI story hint: {hint}")
                hint_file.unlink()  # cleanup
                return hint
        except Exception:
            pass

    lower = script.lower()

    # ── 2. Look for AITA-style age+gender pattern (STRONG signal) ──
    narrator_tag = _re.search(
        r"\b(?:i|me)\s*[\(\[]\s*\d{1,2}\s*([mfMF])\s*[\)\]]",
        script,
    )
    if narrator_tag:
        letter = narrator_tag.group(1).lower()
        if letter == "f":
            print(f"  [GENDER] Pattern (I nnF): female")
            return "female"
        if letter == "m":
            print(f"  [GENDER] Pattern (I nnM): male")
            return "male"

    first_tag = _re.search(r"[\(\[]\s*\d{1,2}\s*([mfMF])\s*[\)\]]", script)
    if first_tag:
        letter = first_tag.group(1).lower()
        if letter == "f":
            print(f"  [GENDER] Pattern (nnF): female")
            return "female"
        if letter == "m":
            print(f"  [GENDER] Pattern (nnM): male")
            return "male"

    # ── 3. Indicator words ──
    female_score = sum(1 for indicator in FEMALE_INDICATORS if indicator in lower)
    male_score   = sum(1 for indicator in MALE_INDICATORS   if indicator in lower)

    if female_score > male_score:
        print(f"  [GENDER] Indicators: female ({female_score} vs {male_score})")
        return "female"
    if male_score > female_score:
        print(f"  [GENDER] Indicators: male ({male_score} vs {female_score})")
        return "male"

    # ── 3.5 AI fallback — only when indicators fail (saves API quota) ──
    ai_result = _ai_detect_narrator_gender(script)
    if ai_result in ("male", "female"):
        print(f"  [GENDER] AI detected: {ai_result}")
        return ai_result

    # ── 4. Truly neutral: alternate 50/50 based on script hash ──
    script_hash = sum(ord(c) for c in script[:200])
    result = "female" if script_hash % 2 == 0 else "male"
    print(f"  [GENDER] Hash fallback: {result}")
    return result


GENDER_VOICE_MAP = {
    "reddit_stories": {
        "male": "en-US-GuyNeural",
        "female": "en-US-AriaNeural",
        "neutral": "en-US-GuyNeural",
    },
    "english_learning": {
        "male": "en-US-AndrewNeural",
        "female": "en-US-JennyNeural",
        "neutral": "en-US-JennyNeural",
    },
    "psychology": {
        "male": "en-US-BrianNeural",
        "female": "en-US-AriaNeural",
        "neutral": "en-US-AriaNeural",
    },
    "dark_history": {
        "male": "en-GB-RyanNeural",
        "female": "en-GB-SoniaNeural",
        "neutral": "en-GB-RyanNeural",
    },
    "ai_tools_automation": {
        "male": "en-US-AndrewNeural",
        "female": "en-US-EmmaNeural",
        "neutral": "en-US-AndrewNeural",
    },
    "quiz": {
        "male": "en-US-SteffanNeural",
        "female": "en-US-EmmaNeural",
        "neutral": "en-US-EmmaNeural",
    },
    "facts": {
        "male": "en-US-SteffanNeural",
        "female": "en-US-JennyNeural",
        "neutral": "en-US-SteffanNeural",
    },
    "sports_reviews": {
        "male": "en-GB-ThomasNeural",
        "female": "en-GB-LibbyNeural",
        "neutral": "en-GB-ThomasNeural",
    },
}

# ── Vibe-based voice map (used when AI provides a Voice: hint) ────────────
# 5 vibes × 2 genders = 10 distinct voices
VIBE_VOICE_MAP = {
    ("male",   "warm"):      "en-US-GuyNeural",       # storyteller
    ("male",   "dramatic"):  "en-US-EricNeural",      # deep dramatic
    ("male",   "serious"):   "en-US-BrianNeural",     # mature serious
    ("male",   "energetic"): "en-US-AndrewNeural",    # young casual
    ("male",   "mature"):    "en-GB-RyanNeural",      # British calm

    ("female", "warm"):      "en-US-AriaNeural",      # warm friendly
    ("female", "dramatic"):  "en-US-EmmaNeural",      # bright dramatic
    ("female", "serious"):   "en-US-AvaNeural",       # mature serious
    ("female", "energetic"): "en-US-JennyNeural",     # young energetic
    ("female", "mature"):    "en-GB-SoniaNeural",     # British calm
}


def _read_voice_vibe_hint():
    """Read voice vibe hint from _voice_vibe_hint.tmp if present."""
    from pathlib import Path as _P
    hint_file = _P.cwd() / "_voice_vibe_hint.tmp"
    if hint_file.exists():
        try:
            vibe = hint_file.read_text(encoding="utf-8").strip().lower()
            if vibe in ("warm", "dramatic", "serious", "energetic", "mature"):
                return vibe
        except Exception:
            pass
    return None


def _pick_voice_from_vibe(channel_id: str, gender: str, script: str = "") -> str:
    """
    Pick voice for reddit_stories based on AI vibe hint.
    Falls back to random voice from gender pool for that channel.
    """
    import random

    # Only reddit_stories uses vibe map for now
    if channel_id == "reddit_stories":
        vibe = _read_voice_vibe_hint()
        if vibe:
            voice = VIBE_VOICE_MAP.get((gender, vibe))
            if voice:
                print(f"  [VOICE] Vibe {vibe.upper()} + {gender} -> {voice}")
                # Cleanup vibe hint after use
                try:
                    (Path.cwd() / "_voice_vibe_hint.tmp").unlink()
                except Exception:
                    pass
                return voice
        # Fallback: random from that gender pool
        pool = [v for (g, _), v in VIBE_VOICE_MAP.items() if g == gender]
        if pool:
            chosen = random.choice(pool)
            print(f"  [VOICE] No vibe hint, random {gender} pick: {chosen}")
            return chosen

    return None  # let caller use default channel map




def generate_voice(
    script: str,
    output_path: Path,
    voice_key: str = None,
    channel_id: str = None,
    rate: str = None,
) -> tuple[float, str]:
    """
    Generate voice audio.
    Returns (duration_seconds, mode)
    """
    # Sanitize script — strip markdown/emojis so TTS doesn't read literally
    script = sanitize_script_for_voice(script)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Pick voice config
    if voice_key and voice_key in VOICE_OPTIONS:
        voice_cfg = VOICE_OPTIONS[voice_key]
        voice_name = voice_cfg["voice"]
        voice_rate = rate or "+0%"
    elif channel_id:
        # Detect narrator gender from script
        gender = detect_narrator_gender(script)

        # First: try vibe-based voice pick (reddit_stories, uses AI hint)
        voice_name = _pick_voice_from_vibe(channel_id, gender, script)

        # Second: fall back to per-channel gender map
        if not voice_name:
            gender_map = GENDER_VOICE_MAP.get(channel_id, {})
            voice_name = gender_map.get(gender, "")

        # Third: use channel default
        if not voice_name and channel_id in CHANNEL_VOICES:
            voice_name = CHANNEL_VOICES[channel_id]["voice"]

        # Last resort
        if not voice_name:
            voice_name = DEFAULT_VOICE["voice"]

        ch_cfg = CHANNEL_VOICES.get(channel_id, DEFAULT_VOICE)
        voice_rate = rate or ch_cfg.get("rate", "+0%")
    else:
        voice_name = DEFAULT_VOICE["voice"]
        voice_rate = rate or "+0%"

    # Try edge-tts first
    try:
        # Convert MP3 output to WAV path
        mp3_path = output_path.with_suffix(".mp3")

        success = asyncio.run(
            _edge_tts_generate(script, mp3_path, voice_name, voice_rate)
        )

        if success:
            # Convert MP3 to WAV using ffmpeg
            import subprocess
            import shutil
            ffmpeg = shutil.which("ffmpeg")
            if ffmpeg:
                result = subprocess.run(
                    [ffmpeg, "-y", "-i", str(mp3_path),
                     "-ar", "44100", "-ac", "1", str(output_path)],
                    capture_output=True
                )
                if output_path.exists() and output_path.stat().st_size > 1000:
                    mp3_path.unlink(missing_ok=True)

                    # Get real duration from audio
                    duration = _get_audio_duration(output_path)
                    if duration <= 0:
                        duration = estimate_duration_seconds(script)

                    # Save voice info
                    info = {
                        "voice": voice_name,
                        "rate": voice_rate,
                        "mode": "edge-tts",
                        "duration": duration,
                    }
                    info_path = output_path.parent / "voice_info.json"
                    with open(info_path, "w", encoding="utf-8") as f:
                        json.dump(info, f, indent=2)

                    return duration, f"edge_tts_{voice_name}"
            else:
                # No ffmpeg but mp3 exists — use mp3 directly
                if mp3_path.exists():
                    mp3_path.rename(output_path.with_suffix(".mp3"))
                    duration = estimate_duration_seconds(script)
                    return duration, f"edge_tts_mp3_{voice_name}"

    except Exception as e:
        print(f"  edge-tts error: {e}")

    # Fallback to pyttsx3
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.save_to_file(script, str(output_path))
        engine.runAndWait()
        if output_path.exists() and output_path.stat().st_size > 1000:
            duration = estimate_duration_seconds(script)
            return duration, "pyttsx3_fallback"
    except Exception as e:
        print(f"  pyttsx3 fallback failed: {e}")

    # Silent placeholder
    return _generate_silent(script, output_path), "silent_placeholder"


def _get_audio_duration(audio_path: Path) -> float:
    """Get actual audio duration using wave module."""
    try:
        with wave.open(str(audio_path), "r") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            return frames / float(rate)
    except Exception:
        return 0.0


def _generate_silent(script: str, output_path: Path) -> float:
    duration = estimate_duration_seconds(script)
    sample_rate = 44100
    total_frames = int(duration * sample_rate)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        chunk = sample_rate
        remaining = total_frames
        while remaining > 0:
            frames = min(chunk, remaining)
            wav.writeframes(b"\x00\x00" * frames)
            remaining -= frames
    return duration


def generate_voice_placeholder(script: str, output_path: Path) -> float:
    return _generate_silent(script, output_path)
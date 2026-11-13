"""
core/thumbnail_generator.py
3-tier thumbnail system:
  Primary  : HuggingFace FLUX.1-schnell  (best quality, free tier)
  Fallback : Gemini 2.5 Flash Image      (Nano Banana, free tier)
  Fallback : Pollinations.ai             (no key, unlimited)
  Final    : PIL drawn thumbnail         (always works)

Uses per-channel prompt templates and AI scene distillation.
Auto-crops bottom 80px to remove any logo/watermark.
"""

from __future__ import annotations
import io
import random
import textwrap
import urllib.parse
from pathlib import Path

import requests
import yaml
from core.channel_styles import get_style


# ── Per-channel prompt templates ─────────────────────────────────────────────
CHANNEL_PROMPT_TEMPLATES = {
    "reddit_stories": """
{scene}.

CRITICAL: This must look 100% like a REAL amateur smartphone photo
secretly taken at a real family event. NOT AI. NOT professional. NOT
beautiful. NOT cinematic.

CAMERA: shaky iPhone 12 photo, slightly out of focus, motion blur on
moving hands, JPEG compression artifacts visible, mild lens flare from
ceiling light, auto-exposure struggling with mixed indoor lighting,
uneven white balance, natural noise/grain at ISO 800+, NO color
grading, NO filters, raw camera output.

PEOPLE: completely average-looking real humans, NOT models. Plain
faces, asymmetric features, double chins, receding hairlines, acne
scars, crow\'s feet, eye bags, smudged makeup, frizzy untreated hair.
Real bodies (overweight, skinny, normal, old, young). Wearing cheap
everyday clothes — wrinkled t-shirts, faded hoodies, stretched leggings,
ill-fitting jeans, slippers, mismatched socks. Could be your boring
coworker or your weird uncle.

ENVIRONMENT: messy real rooms. Visible clutter — coffee cups, dishes,
remote controls, magazines, kids toys, laundry pile, cables, cheap
IKEA furniture, slightly stained carpet, family photos on cluttered
walls, dated wallpaper, dim overhead bulb lighting making faces look
slightly orange. NOT staged. NOT styled.

MOMENT: frozen mid-reaction during an emotional confrontation or shock.
Eyes wide. Mouths open mid-sentence. Hands frozen in awkward positions.
Body language unposed and awkward like real surprise.

OBJECT: one important storytelling object visible in foreground —
envelope, phone screen, paperwork, photo, test result, ring, document.

OUTPUT: vertical 9:16 phone photo aspect, no text, no captions, no
watermark, no logo, no border.

STRICTLY AVOID: model-beautiful faces, perfect symmetry, smooth skin,
glamour, cinematic color grading, dramatic studio lighting, professional
composition, fashion poses, fantasy elements, horror, scary faces,
demon eyes, dark moody atmosphere, oversaturated colors, HDR, painted
look, illustration, anime, cartoon, plastic skin, doll faces, Instagram
filter look, perfect framing.
""".strip(),

    # Other channels use a simpler default — can be customized later
    "default": """
{scene}.

Realistic photograph, professional photography, natural lighting,
authentic atmosphere, vertical 9:16, no text, no watermark, no logo.
""".strip(),
}


CHANNEL_HOOKS = {
    "reddit_stories":      ["WAIT FOR IT...", "YOU WON\'T BELIEVE THIS", "STORYTIME", "REDDIT DRAMA"],
    "english_learning":    ["STOP SAYING THIS", "ENGLISH TIP", "GRAMMAR FIX", "SAY THIS INSTEAD"],
    "psychology":          ["YOUR BRAIN DOES THIS", "PSYCHOLOGY FACT", "MIND TRICK"],
    "dark_history":        ["THEY HID THIS", "DARK TRUTH", "HISTORY\'S SECRET"],
    "ai_tools_automation": ["FREE AI TOOL", "AI HACK", "AUTOMATE THIS"],
    "quiz":                ["CAN YOU ANSWER?", "ONLY 5% GET THIS", "QUIZ TIME"],
    "facts":               ["DID YOU KNOW?", "MIND BLOWN", "INSANE FACT"],
    "sports_reviews":      ["WHAT A GOAL", "MATCH BREAKDOWN", "EPIC MOMENT"],
}


# ── Load global settings ─────────────────────────────────────────────────────
def _load_settings() -> dict:
    try:
        path = Path("config/global_settings.yaml")
        if path.exists():
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        pass
    return {}


# ── AI scene description ─────────────────────────────────────────────────────
def _build_scene_prompt(script: str, title: str) -> str:
    """Use AI to extract the dramatic scene description from the story."""
    try:
        from core.ai_engine import ask_ai
        prompt = (
            f"Read this Reddit AITA story. Describe in 25-35 words the SINGLE "
            f"most shocking visual MOMENT — the exact scene where the truth is "
            f"revealed or confrontation happens. Include: WHO is there (ages, "
            f"roles, gender), WHAT object or paper is visible, WHERE it happens "
            f"(specific room/location), and the EMOTIONS on faces.\n\n"
            f"Title: {title}\n\n"
            f"Story: {script[:1500]}\n\n"
            f"Reply with ONLY the scene description. No quotes, no explanation, "
            f"no prefix like \"the scene shows\". Just describe what we see in "
            f"natural English."
        )
        scene = ask_ai(prompt)
        if scene and len(scene) > 15:
            scene = scene.strip().strip('"').strip("'").replace("\n", " ")
            words = scene.split()
            if len(words) > 50:
                scene = " ".join(words[:40])
            print(f"  AI scene: {scene[:140]}...")
            return scene
    except Exception as e:
        print(f"  AI scene failed: {e}")

    # Fallback — generic scene
    return (
        "Family members standing in a living room, one person holding an envelope, "
        "everyone looking shocked, mixed emotions of anger and disbelief on their faces"
    )


def _build_full_prompt(channel_id: str, scene: str) -> str:
    """Build the full prompt using channel template + scene."""
    tmpl = CHANNEL_PROMPT_TEMPLATES.get(channel_id, CHANNEL_PROMPT_TEMPLATES["default"])
    return tmpl.format(scene=scene)


# ── Crop bottom to remove logo/watermark ─────────────────────────────────────
def _crop_bottom_watermark(image_path: Path, crop_px: int = 80) -> bool:
    """Crop bottom N pixels to remove any model logo. Returns True on success."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        w, h = img.size
        if h > crop_px + 100:
            cropped = img.crop((0, 0, w, h - crop_px))
            # Stretch back to original height to keep 9:16
            cropped = cropped.resize((w, h), Image.LANCZOS)
            cropped.save(image_path, "PNG", quality=95)
            return True
    except Exception as e:
        print(f"  Crop failed: {e}")
    return False


# ── Tier 1: HuggingFace FLUX.1-schnell ───────────────────────────────────────
def _huggingface_thumbnail(prompt: str, output_path: Path, token: str) -> bool:
    """Generate via HuggingFace FLUX.1-schnell."""
    if not token:
        return False
    try:
        url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "width":  1024,
                "height": 1792,
                "num_inference_steps": 4,
            },
        }
        print(f"  HuggingFace FLUX.1-schnell: generating...")
        resp = requests.post(url, headers=headers, json=payload, timeout=120)

        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(resp.content)
            if output_path.exists() and output_path.stat().st_size > 10000:
                print(f"  HF FLUX OK: {output_path.stat().st_size // 1024} KB")
                return True
        else:
            print(f"  HF FLUX failed: {resp.status_code} {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"  HF error: {e}")
        return False


# ── Tier 2: Gemini 2.5 Flash Image (Nano Banana) ─────────────────────────────
def _gemini_thumbnail(prompt: str, output_path: Path, api_key: str) -> bool:
    """Generate via Gemini image models. Tries newest first."""
    if not api_key:
        return False
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        # Try models in order — newest first to use fresh quotas
        models_to_try = [
            "gemini-3.1-flash-image",
            "gemini-3-pro-image",
            "gemini-2.5-flash-image",
        ]

        for model_name in models_to_try:
            try:
                print(f"  Gemini {model_name}: generating...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data is not None:
                        data = part.inline_data.data
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_bytes(data)
                        if output_path.exists() and output_path.stat().st_size > 10000:
                            print(f"  Gemini {model_name} OK: {output_path.stat().st_size // 1024} KB")
                            return True
            except Exception as inner_e:
                err = str(inner_e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    print(f"  {model_name}: quota exhausted, trying next...")
                    continue
                else:
                    print(f"  {model_name} error: {err[:200]}")
                    continue
        print(f"  All Gemini models failed")
        return False
    except Exception as e:
        print(f"  Gemini SDK error: {e}")
        return False



def _pollinations_thumbnail(prompt: str, output_path: Path) -> bool:
    """Generate via Pollinations.ai (no key needed)."""
    try:
        encoded = urllib.parse.quote(prompt)
        url     = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1080&height=1920&nologo=true&enhance=true"
        )
        print(f"  Pollinations.ai: generating...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp    = requests.get(url, timeout=90, stream=True, headers=headers)
        if resp.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            if output_path.exists() and output_path.stat().st_size > 10000:
                print(f"  Pollinations OK: {output_path.stat().st_size // 1024} KB")
                return True
        print(f"  Pollinations failed: HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"  Pollinations error: {e}")
        return False


# ── Tier 4: PIL fallback ─────────────────────────────────────────────────────
def _pil_thumbnail(channel_id: str, title: str, output_path: Path) -> bool:
    """Drawn fallback thumbnail."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return False

    style  = get_style(channel_id)
    bg     = style["bg"]
    accent = style["accent"]
    label  = style["short_label"]
    icon   = style["emoji_safe_icon"]
    hook   = random.choice(CHANNEL_HOOKS.get(channel_id, ["WATCH THIS"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img  = Image.new("RGB", (1080, 1920), bg)
    draw = ImageDraw.Draw(img)

    try:
        font_xl    = ImageFont.truetype("arialbd.ttf", 96)
        font_big   = ImageFont.truetype("arialbd.ttf", 72)
        font_mid   = ImageFont.truetype("arialbd.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf",   36)
    except Exception:
        font_xl = font_big = font_mid = font_small = ImageFont.load_default()

    for i in range(20):
        shade = tuple(max(0, c - i * 3) for c in bg)
        draw.rectangle([0, i * 96, 1080, (i + 1) * 96], fill=shade)

    draw.rectangle([0, 0, 1080, 180], fill=accent)
    draw.text((60, 50),  icon,  fill="white", font=font_mid)
    draw.text((140, 55), label, fill="white", font=font_mid)

    bbox   = draw.textbbox((0, 0), hook, font=font_big)
    hook_x = (1080 - (bbox[2] - bbox[0])) // 2
    draw.rectangle([40, 280, 1040, 420], fill=(0, 0, 0))
    draw.text((hook_x, 310), hook, fill=accent, font=font_big)

    wrapped = textwrap.wrap(title.upper(), width=16)[:6]
    y = 500
    for idx, line in enumerate(wrapped):
        font = font_xl if idx == 0 and len(line) <= 14 else font_big
        bbox = draw.textbbox((0, 0), line, font=font)
        x    = (1080 - (bbox[2] - bbox[0])) // 2
        draw.text((x + 4, y + 4), line, fill=(0, 0, 0), font=font)
        draw.text((x, y),         line, fill="white",   font=font)
        y += 100

    draw.rectangle([0, 1720, 1080, 1920], fill=(0, 0, 0))
    draw.rectangle([60, 1760, 1020, 1770], fill=accent)
    draw.text((60, 1790), "WATCH NOW",              fill="white",         font=font_mid)
    draw.text((60, 1850), "Swipe up for full video", fill=(180, 180, 180), font=font_small)

    img.save(output_path, quality=95)
    print(f"  PIL fallback saved")
    return True




def _generate_thumbnail_hook(script: str, title: str) -> dict:
    """
    Use AI to generate a punchy 2-5 word hook for the thumbnail.
    Returns dict: {"hook": "SHE LIED FOR YEARS", "emphasis": "LIED",
                   "vibe": "anger", "position": "bottom"}
    """
    try:
        from core.ai_engine import ask_ai
        prompt = (
            f"Read this Reddit AITA story and create a viral thumbnail hook.\n\n"
            f"Title: {title}\n\n"
            f"Story: {script[:1000]}\n\n"
            f"Reply with EXACTLY this format (no other text):\n"
            f"HOOK: <2 to 5 ALL CAPS words that grab attention>\n"
            f"EMPHASIS: <ONE word from the hook to highlight in different color>\n"
            f"VIBE: <one of: anger, shock, betrayal, drama, sad, exposed>\n\n"
            f"Example:\n"
            f"HOOK: SHE LIED FOR YEARS\n"
            f"EMPHASIS: LIED\n"
            f"VIBE: betrayal"
        )
        resp = ask_ai(prompt)
        if not resp:
            return _default_hook()

        result = {"hook": "", "emphasis": "", "vibe": "drama"}
        for line in resp.splitlines():
            line = line.strip()
            if line.upper().startswith("HOOK:"):
                result["hook"] = line.split(":", 1)[1].strip().upper()
            elif line.upper().startswith("EMPHASIS:"):
                result["emphasis"] = line.split(":", 1)[1].strip().upper()
            elif line.upper().startswith("VIBE:"):
                result["vibe"] = line.split(":", 1)[1].strip().lower()

        if not result["hook"] or len(result["hook"]) > 50:
            return _default_hook()

        # Clean up
        result["hook"]     = result["hook"].strip('"').strip("'").strip(".")
        result["emphasis"] = result["emphasis"].strip('"').strip("'").strip(".")
        # Cap to 5 words
        words = result["hook"].split()
        if len(words) > 5:
            result["hook"] = " ".join(words[:5])

        h = result["hook"]
        e = result["emphasis"]
        v = result["vibe"]
        print(f"  Hook: {h} (emphasis: {e}, vibe: {v})")
        return result
    except Exception as e:
        print(f"  Hook generation failed: {e}")
        return _default_hook()


def _default_hook() -> dict:
    """Fallback hook if AI fails."""
    return {
        "hook":     random.choice(["YOU WONT BELIEVE THIS", "THE TRUTH HURTS", "SHOCKING STORY"]),
        "emphasis": "",
        "vibe":     "drama",
    }


# Vibe color map — emphasis color + main text color
VIBE_COLORS = {
    "anger":    {"main": "#FFFFFF", "emphasis": "#FF2222", "stroke": "#000000"},
    "shock":    {"main": "#FFFFFF", "emphasis": "#FFD700", "stroke": "#000000"},
    "betrayal": {"main": "#FFFFFF", "emphasis": "#FF3366", "stroke": "#000000"},
    "drama":    {"main": "#FFFFFF", "emphasis": "#FFCC00", "stroke": "#000000"},
    "sad":      {"main": "#FFFFFF", "emphasis": "#66CCFF", "stroke": "#000000"},
    "exposed":  {"main": "#FFFFFF", "emphasis": "#FF6600", "stroke": "#000000"},
}


def _overlay_thumbnail_text(image_path: Path, hook_data: dict) -> bool:
    """
    Overlay MrBeast-style text + Reddit branding bar (top-right).
    Auto-shrinks font so text never touches frame edges.
    Safe margins: 8% on each side.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont

        img  = Image.open(image_path).convert("RGB")
        W, H = img.size
        draw = ImageDraw.Draw(img)

        hook     = hook_data.get("hook", "STORY TIME")
        emphasis = hook_data.get("emphasis", "")
        vibe     = hook_data.get("vibe", "drama")
        colors   = VIBE_COLORS.get(vibe, VIBE_COLORS["drama"])

        # ── Reddit branding bar (top-right) ──────────────────────────
        _draw_reddit_branding(img, draw, W, H, channel_name="UpvoteAnthology")

        # ── Main hook text — auto-shrink to fit ──────────────────────
        side_margin   = int(W * 0.08)   # 8% padding each side
        max_text_w    = W - (2 * side_margin)

        # Word wrap — max 2 lines
        words = hook.split()
        if len(words) <= 3:
            lines = [hook]
        else:
            mid = len(words) // 2
            lines = [" ".join(words[:mid]), " ".join(words[mid:])]

        # Find biggest font size where ALL lines fit within max_text_w
        font_size = int(W * 0.13)   # start big ~140px
        font      = None
        font_name = _find_bold_font()

        while font_size > 40:
            try:
                font = ImageFont.truetype(font_name, font_size)
            except Exception:
                font = ImageFont.load_default()
                break

            # Check if every line fits
            fits = True
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_w = bbox[2] - bbox[0]
                # Add stroke width to total
                stroke_w = max(6, int(font_size * 0.08))
                if line_w + (stroke_w * 2) > max_text_w:
                    fits = False
                    break

            if fits:
                break
            font_size -= 6

        if font is None:
            font = ImageFont.load_default()

        stroke_w = max(6, int(font_size * 0.08))
        line_h   = font_size + 12
        total_h  = line_h * len(lines)

        # Position: bottom 25% but with safe padding
        bottom_margin = int(H * 0.06)
        y_start       = H - total_h - bottom_margin

        # Draw each line, word-by-word for emphasis coloring
        for i, line in enumerate(lines):
            line_words = line.split()
            space_w = draw.textlength(" ", font=font)
            word_widths = []
            for w in line_words:
                ww = draw.textlength(w, font=font)
                word_widths.append(ww)
            total_line_w = sum(word_widths) + space_w * (len(line_words) - 1)
            cx = (W - total_line_w) // 2
            y  = y_start + i * line_h

            for wi, word in enumerate(line_words):
                color = colors["main"]
                clean_word = word.upper().strip(".,!?")
                clean_emp  = emphasis.upper().strip(".,!?") if emphasis else ""
                if clean_emp and clean_word == clean_emp:
                    color = colors["emphasis"]

                draw.text(
                    (cx, y),
                    word,
                    font=font,
                    fill=color,
                    stroke_width=stroke_w,
                    stroke_fill=colors["stroke"],
                )
                cx += word_widths[wi] + space_w

        img.save(image_path, "PNG", quality=95)
        print(f"  Text overlay: \"{hook}\" font_size={font_size} vibe={vibe}")
        return True
    except Exception as e:
        print(f"  Text overlay failed: {e}")
        import traceback; traceback.print_exc()
        return False


def _find_bold_font() -> str:
    """Find best available bold font on system."""
    for f in ["impact.ttf", "arialbd.ttf", "Arial Bold.ttf",
              "DejaVuSans-Bold.ttf", "arial.ttf"]:
        try:
            from PIL import ImageFont
            ImageFont.truetype(f, 50)
            return f
        except Exception:
            continue
    return "arial.ttf"


def _draw_reddit_branding(img, draw, W: int, H: int, channel_name: str = "UpvoteAnthology"):
    """
    Top-LEFT branding:
    - Reddit logo (PNG if available, otherwise orange circle with R)
    - Channel name BELOW the logo, white text with stroke, NO background bar
    """
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Sizing
        logo_size = int(W * 0.12)            # ~130px on 1080 — bigger
        margin_l  = int(W * 0.04)            # ~43px from left
        margin_t  = int(H * 0.025)           # ~48px from top

        # Logo position (top-left)
        logo_x = margin_l
        logo_y = margin_t

        # Try to load Reddit logo from assets
        logo_path = Path("assets/icons/upvote_anthology.png")
        logo_img  = None
        if logo_path.exists():
            try:
                logo_img = Image.open(logo_path).convert("RGBA")
                logo_img = logo_img.resize((logo_size, logo_size), Image.LANCZOS)
            except Exception:
                logo_img = None

        if logo_img is not None:
            img.paste(logo_img, (logo_x, logo_y), logo_img)
        else:
            # Fallback: orange circle with white "R"
            draw.ellipse(
                [logo_x, logo_y, logo_x + logo_size, logo_y + logo_size],
                fill=(255, 69, 0, 255)
            )
            r_font_size = int(logo_size * 0.7)
            font_name = _find_bold_font()
            try:
                r_font = ImageFont.truetype(font_name, r_font_size)
            except Exception:
                r_font = ImageFont.load_default()
            r_bbox = draw.textbbox((0, 0), "R", font=r_font)
            r_w    = r_bbox[2] - r_bbox[0]
            r_h    = r_bbox[3] - r_bbox[1]
            draw.text(
                (logo_x + (logo_size - r_w) // 2,
                 logo_y + (logo_size - r_h) // 2 - int(logo_size * 0.1)),
                "R", fill="white", font=r_font
            )

        # Channel name BELOW logo, no background, white with stroke
        font_size = int(W * 0.028)           # ~30px on 1080
        font_name = _find_bold_font()
        try:
            font = ImageFont.truetype(font_name, font_size)
        except Exception:
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), channel_name, font=font)
        text_w    = text_bbox[2] - text_bbox[0]
        text_h    = text_bbox[3] - text_bbox[1]

        # Center text horizontally under the logo
        text_x = logo_x + (logo_size - text_w) // 2
        text_y = logo_y + logo_size + int(logo_size * 0.12)

        stroke_w = max(3, int(font_size * 0.12))
        draw.text(
            (text_x, text_y),
            channel_name,
            font=font,
            fill="white",
            stroke_width=stroke_w,
            stroke_fill="black",
        )

        print(f"  Branding: logo top-left, channel name below ({channel_name})")
        return True
    except Exception as e:
        print(f"  Branding error: {e}")
        return False

def generate_thumbnail(
    channel_id: str,
    title: str,
    output_path: Path,
    script: str = "",
) -> bool:
    """
    3-tier thumbnail generator.
    Tries: HuggingFace -> Gemini -> Pollinations -> PIL
    Auto-crops bottom to remove logos.
    """
    output_path = Path(output_path)
    settings    = _load_settings()
    hf_token    = settings.get("huggingface_token", "")
    gemini_key  = settings.get("gemini_api_key", "")

    # Build the prompt
    scene  = _build_scene_prompt(script, title)
    prompt = _build_full_prompt(channel_id, scene)
    print(f"  Prompt length: {len(prompt)} chars")

    # Generate the AI hook for text overlay
    hook_data = _generate_thumbnail_hook(script, title)

    # Tier 1: Gemini (best quality)
    if gemini_key:
        if _gemini_thumbnail(prompt, output_path, gemini_key):
            _crop_bottom_watermark(output_path, crop_px=80)
            _overlay_thumbnail_text(output_path, hook_data)
            return True

    # Tier 2: HuggingFace FLUX
    if hf_token:
        if _huggingface_thumbnail(prompt, output_path, hf_token):
            _crop_bottom_watermark(output_path, crop_px=80)
            _overlay_thumbnail_text(output_path, hook_data)
            return True

    # Tier 3: Pollinations
    if _pollinations_thumbnail(prompt, output_path):
        _overlay_thumbnail_text(output_path, hook_data)
        return True

    # Tier 4: PIL fallback
    print(f"  All AI tiers failed — using PIL fallback")
    return _pil_thumbnail(channel_id, title, output_path)

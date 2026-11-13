from __future__ import annotations
import re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HIGHLIGHT_WORDS = {
    "betrayed","stolen","caught","secret","lied","cheated",
    "exposed","affair","pregnant","fired","arrested",
    "dead","died","killed","hate","never","always",
    "destroyed","ruined","broke","failed","shocking",
    "disgusting","unbelievable","insane","crazy","angry",
    "furious","devastated","heartbroken","terrified","kicked",
    "blocked","deleted","confronted","revealed","discovered",
    "money","thousand","selfish","wrong","fault","blame",
    "infidelity","cheating","divorce","abuse","victim",
    "lying","breakdown","paycheck","vegas","betrayal",
}

def _clean_word(w):
    return re.sub(r"[^a-zA-Z]", "", w).lower()

def _is_highlight(w):
    return _clean_word(w) in HIGHLIGHT_WORDS

def _load_font(size):
    """Load best available bold font. Montserrat preferred."""
    candidates = [
        r"C:\Users\user\Downloads\8CHANNELS\8_Channel_Content_Factory\assets\fonts\Montserrat-ExtraBold.ttf",
        r"C:\Users\user\Downloads\8CHANNELS\8_Channel_Content_Factory\assets\fonts\Montserrat-Bold.ttf",
        r"C:\Windows\Fonts\Montserrat-ExtraBold.ttf",
        r"C:\Windows\Fonts\Montserrat-Bold.ttf",
        "impact.ttf",
        "ariblk.ttf",
        "arialbd.ttf",
        "verdanab.ttf",
        "trebucbd.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _clean_caption_text(text):
    text = re.sub(r"^Title:\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\bA-I-T-A\b", "AITA", text)
    text = re.sub(r"\bA\s*-\s*I\s*-\s*T\s*-\s*A\b", "AITA", text)
    return text.strip()

def _render_caption_frame(words, canvas_w, canvas_h, font_size=72):
    """
    Render caption words centered in a dark box.
    Equal padding top and bottom inside box.
    Bold font. Highlight emotion words in yellow.
    """
    # Render at 2x for crispness then scale down
    scale  = 2
    W      = canvas_w * scale
    H      = canvas_h * scale
    fs     = font_size * scale
    pad_x  = 36 * scale   # horizontal padding inside box
    pad_y  = 22 * scale   # vertical padding inside box — equal top and bottom
    sw     = 4 * scale    # stroke width

    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(fs)

    text = " ".join(words)
    if not text.strip():
        return np.zeros((canvas_h, canvas_w, 4), dtype="uint8")

    # Measure full text to get height accurately
    bbox = draw.textbbox((0, 0), text, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]
    # ascent and descent for perfect vertical centering
    asc  = -bbox[1]  # ascent (above baseline)
    desc =  bbox[3]  # descent (below baseline)

    # Caption box position — lower third of screen
    box_w  = tw + pad_x * 2
    box_h  = th + pad_y * 2
    box_x  = (W - box_w) // 2
    box_y  = int(H * 0.74) - box_h // 2

    # Draw dark rounded box
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_w, box_y + box_h],
        radius=pad_y,
        fill=(10, 10, 15, 115),
    )

    # Text starts at: box_x + pad_x, box_y + pad_y
    # For perfect centering: use bbox[1] offset to remove ascender gap
    text_x = box_x + pad_x
    text_y = box_y + pad_y - bbox[1]  # subtract bbox[1] to fix top gap

    # Draw each word with stroke then fill
    x = text_x
    for word in words:
        wb   = draw.textbbox((0, 0), word, font=font)
        ww   = wb[2] - wb[0]
        fill = (255, 230, 0, 255) if _is_highlight(word) else (255, 255, 255, 255)
        # Stroke
        for dx in range(-sw, sw + 1):
            for dy in range(-sw, sw + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, text_y + dy), word, font=font, fill=(0, 0, 0, 255))
        # Fill
        draw.text((x, text_y), word, font=font, fill=fill)
        x += ww + fs // 3

    # Scale down 2x -> 1x
    img = img.resize((canvas_w, canvas_h), Image.LANCZOS)
    return np.array(img)

def _parse_srt(srt_path):
    try:
        content = Path(srt_path).read_text(encoding="utf-8")
    except Exception:
        return []
    segments = []
    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        tl = lines[1]
        text = " ".join(lines[2:]).strip()
        m = re.match(
            r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
            tl
        )
        if m and text:
            g = m.groups()
            s = int(g[0])*3600+int(g[1])*60+int(g[2])+int(g[3])/1000
            e = int(g[4])*3600+int(g[5])*60+int(g[6])+int(g[7])/1000
            segments.append({"start": s, "end": e, "text": text})
    return segments

def make_caption_clips(segments, width=1080, height=1920, duration=60.0, font_size=72, max_words=3):
    from moviepy.editor import ImageClip
    clips = []
    for seg in segments:
        start = seg["start"]
        end   = min(seg["end"], duration)
        dur   = max(0.05, end - start)
        raw   = _clean_caption_text(seg["text"])
        words = raw.split()
        if not words:
            continue
        chunks    = [words[i:i+max_words] for i in range(0, len(words), max_words)]
        chunk_dur = dur / len(chunks)
        for ci, chunk in enumerate(chunks):
            cs    = start + ci * chunk_dur
            cd    = max(0.05, min(start + (ci+1)*chunk_dur, duration) - cs)
            frame = _render_caption_frame(chunk, width, height, font_size=font_size)
            rgb   = frame[:,:,:3].astype("uint8")
            alpha = (frame[:,:,3]/255.0).astype("float32")
            if alpha.max() <= 0:
                continue
            bc = ImageClip(rgb, duration=cd).set_start(cs)
            mc = ImageClip(alpha, ismask=True, duration=cd).set_start(cs)
            clips.append(bc.set_mask(mc))
    return clips

def make_script_caption_clips(script, duration, width=1080, height=1920, max_words=3, font_size=72):
    from moviepy.editor import ImageClip
    skip  = ("title:","topic:","quiz:","lesson:","channel:")
    lines = []
    for line in script.splitlines():
        line = line.strip()
        if line and not any(line.lower().startswith(s) for s in skip):
            lines.append(line)
    words  = " ".join(lines).split()
    words  = [w for w in words if w != "-"]
    chunks = [words[i:i+max_words] for i in range(0, len(words), max_words)]
    if not chunks:
        return []
    tpc   = duration / len(chunks)
    clips = []
    for i, chunk in enumerate(chunks):
        start = i * tpc
        dur   = max(0.05, tpc)
        frame = _render_caption_frame(chunk, width, height, font_size=font_size)
        rgb   = frame[:,:,:3].astype("uint8")
        alpha = (frame[:,:,3]/255.0).astype("float32")
        if alpha.max() <= 0:
            continue
        bc = ImageClip(rgb, duration=dur).set_start(start)
        mc = ImageClip(alpha, ismask=True, duration=dur).set_start(start)
        clips.append(bc.set_mask(mc))
    return clips
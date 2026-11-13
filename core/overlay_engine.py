from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR  = Path(__file__).resolve().parents[1]
ICONS_DIR = BASE_DIR / "assets" / "icons"
FONTS_DIR = BASE_DIR / "assets" / "fonts"
WIN_FONTS = Path("C:/Windows/Fonts")

@dataclass
class Overlay:
    name: str
    image: np.ndarray
    start: float
    end: float
    x: int = 0
    y: int = 0
    fade_in: float = 0.0
    fade_out: float = 0.0

def _load_font(size, bold=True):
    """Load best available font. Montserrat ExtraBold preferred."""
    if bold:
        candidates = [
            str(FONTS_DIR / "Montserrat-ExtraBold.ttf"),
            str(FONTS_DIR / "Montserrat-Bold.ttf"),
            str(WIN_FONTS / "Montserrat-ExtraBold.ttf"),
            str(WIN_FONTS / "Montserrat-Bold.ttf"),
            "ariblk.ttf",
            "arialbd.ttf",
            "impact.ttf",
            "verdanab.ttf",
            "trebucbd.ttf",
        ]
    else:
        candidates = [
            str(FONTS_DIR / "Montserrat-Bold.ttf"),
            str(WIN_FONTS / "Montserrat-Bold.ttf"),
            "arialbd.ttf",
            "arial.ttf",
            "verdana.ttf",
        ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _load_icon(name, size=36):
    p = ICONS_DIR / f"{name}.png"
    if not p.exists():
        return None
    try:
        return Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
    except Exception:
        return None

def _wrap_text(text, font, max_width, draw):
    words   = text.split()
    lines   = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        w    = bbox[2] - bbox[0]
        if w <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines

def _draw_avatar(draw, ax, ay, diameter):
    r  = diameter // 2
    cx = ax + r
    cy = ay + r
    draw.ellipse([ax, ay, ax+diameter, ay+diameter], fill=(211,211,211,255))
    head_r  = int(r * 0.38)
    head_cy = ay + int(diameter * 0.35)
    draw.ellipse([cx-head_r, head_cy-head_r, cx+head_r, head_cy+head_r], fill=(255,255,255,255))
    sh_w = int(diameter * 0.72)
    sh_h = int(diameter * 0.45)
    sh_x = cx - sh_w // 2
    sh_y = ay + int(diameter * 0.58)
    draw.ellipse([sh_x, sh_y, sh_x+sh_w, sh_y+sh_h], fill=(255,255,255,255))

class OverlayEngine:
    def __init__(self, width=1080, height=1920):
        self.width    = width
        self.height   = height
        self.overlays = []

    def add_overlay(self, overlay):
        self.overlays.append(overlay)

    def get_clips(self):
        from moviepy.editor import ImageClip
        clips = []
        for ov in self.overlays:
            rgb   = ov.image[:,:,:3].astype("uint8")
            alpha = (ov.image[:,:,3]/255.0).astype("float32")
            if alpha.max() <= 0:
                continue
            dur  = max(0.05, ov.end - ov.start)
            base = ImageClip(rgb, duration=dur)
            mask = ImageClip(alpha, ismask=True, duration=dur)
            clip = (base.set_mask(mask)
                    .set_start(ov.start)
                    .set_position((ov.x, ov.y)))
            if ov.fade_in > 0:
                clip = clip.crossfadein(ov.fade_in)
            if ov.fade_out > 0:
                clip = clip.crossfadeout(ov.fade_out)
            clips.append(clip)
        return clips

    def clear(self):
        self.overlays = []

def create_reddit_ui_overlay(
    subreddit, title, width=1080, height=1920,
    duration=4.0, upvotes="12.4k", comments="847",
    username="throwaway_story", time_ago="6h ago"
):
    """
    Reddit card rendered at 4x scale then downsampled with LANCZOS.
    Gives crisp pixel-perfect text on any device.
    """
    ORANGE = (255, 69,  0, 255)
    WHITE  = (255, 255, 255, 255)
    DARK   = (20,  20,  20, 255)
    DGRAY  = (26,  26,  27, 255)
    MGRAY  = (58,  58,  60, 255)
    GRAY   = (95,  99, 104, 255)

    # 4x render for pixel-perfect crispness
    scale = 4
    W     = width  * scale
    H     = height * scale
    pad   = 60    * scale   # 60px each side - safe from mobile edges
    cw    = W - pad * 2
    # FIX: increased card height to prevent title clipping
    ch    = 540   * scale
    cx    = pad
    cy    = ((height - 540) // 2 - 80) * scale

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Shadow
    sh_img = Image.new("RGBA", (cw + 20*scale, ch + 20*scale), (0,0,0,0))
    shd    = ImageDraw.Draw(sh_img)
    shd.rounded_rectangle(
        [8*scale, 8*scale, cw+12*scale, ch+12*scale],
        radius=20*scale, fill=(0,0,0,80)
    )
    canvas.paste(sh_img, (cx - 10*scale, cy - 4*scale), sh_img)

    # White card
    card = Image.new("RGBA", (cw, ch), (0,0,0,0))
    cd   = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, cw-1, ch-1], radius=20*scale, fill=WHITE)

    # Orange bar — top corners rounded, bottom corners sharp
    bar_h = 56 * scale
    cd.rounded_rectangle([0, 0, cw-1, bar_h], radius=20*scale, fill=ORANGE)
    cd.rectangle([0, bar_h-20*scale, 20*scale, bar_h], fill=ORANGE)
    cd.rectangle([cw-20*scale, bar_h-20*scale, cw-1, bar_h], fill=ORANGE)

    # Subreddit text — solid white, centered
    f_sub  = _load_font(32*scale, bold=True)
    sub_tx = f"r/{subreddit}"
    tmp_d  = ImageDraw.Draw(Image.new("RGBA", (cw, bar_h)))
    sb     = tmp_d.textbbox((0, 0), sub_tx, font=f_sub)
    stw    = sb[2] - sb[0]
    sth    = sb[3] - sb[1]
    stx    = (cw - stw) // 2
    sty    = (bar_h - sth) // 2 - scale
    cd.text((stx, sty), sub_tx, font=f_sub, fill=WHITE)

    # Avatar
    av_size = 54 * scale
    ax = 20 * scale
    ay = bar_h + 14 * scale
    _draw_avatar(cd, ax, ay, av_size)

    # Username
    f_user = _load_font(28*scale, bold=False)
    ux = ax + av_size + 10*scale
    uy = ay + (av_size - 21*scale) // 2
    _user_text = f"u/{username}  •  {time_ago}"
    _ls = 2 * scale
    _cur_x = ux
    for _ch in _user_text:
        cd.text((_cur_x, uy), _ch, font=f_user, fill=MGRAY)
        _bb = cd.textbbox((0, 0), _ch, font=f_user)
        _cur_x += (_bb[2] - _bb[0]) + _ls

    # Title — bold, line-by-line, protected bottom margin
    f_title  = _load_font(40*scale, bold=True)
    title_x  = 20 * scale
    title_y  = ay + av_size + 16*scale
    max_tw   = cw - 40*scale
    tmp_draw = ImageDraw.Draw(Image.new("RGBA", (cw, ch)))
    t_lines  = _wrap_text(title, f_title, max_tw, tmp_draw)

    # FIX: footer locked at ch - 70*scale, title must stop 25*scale above it
    footer_y         = ch - 80 * scale
    max_title_bottom = footer_y - 25 * scale

    for line in t_lines[:4]:
        lb = tmp_draw.textbbox((0, 0), line, font=f_title)
        lh = lb[3] - lb[1]
        if title_y + lh > max_title_bottom:
            break
        cd.text((title_x, title_y), line, font=f_title, fill=DARK)
        title_y += lh + 12*scale

    # Footer separator
    cd.line(
        [(20*scale, footer_y), (cw - 20*scale, footer_y)],
        fill=(210, 210, 210, 255), width=scale
    )

    # FIX: Bottom bar — darker text, share pushed left to avoid corner clip
    by      = footer_y + 10*scale
    isz     = 34 * scale
    f_count = _load_font(26*scale, bold=True)

    # Upvote
    ix  = 20 * scale
    uv  = _load_icon("upvote", isz)
    if uv:
        card.paste(uv, (ix, by), uv)
    else:
        cd.text((ix, by), "▲", font=f_count, fill=ORANGE)
    cd.text((ix + isz + 10*scale, by + 2*scale), upvotes, font=f_count, fill=DGRAY)

    # Comment
    ix2 = ix + isz + 130*scale
    cm  = _load_icon("comment", isz)
    if cm:
        card.paste(cm, (ix2, by), cm)
    else:
        cd.text((ix2, by), "●", font=f_count, fill=GRAY)
    cd.text((ix2 + isz + 10*scale, by + 2*scale), comments, font=f_count, fill=DGRAY)

    # FIX: Share pushed left by 15px to avoid rounded corner clipping
    ix3 = cw - 175*scale   # more space so Share text stays inside card
    sh2 = _load_icon("share", isz)
    if sh2:
        card.paste(sh2, (ix3, by), sh2)
    else:
        cd.text((ix3, by), "↗", font=f_count, fill=GRAY)
    cd.text((ix3 + isz + 10*scale, by + 2*scale), "Share", font=f_count, fill=GRAY)

    # Paste card onto canvas
    canvas.paste(card, (cx, cy), card)

    # Downsample 4x -> 1x with LANCZOS for pixel-perfect result
    canvas = canvas.resize((width, height), Image.LANCZOS)

    arr = np.array(canvas)
    return Overlay(
        name="reddit_ui", image=arr,
        start=0.0, end=duration,
        x=0, y=0,
        fade_in=0.4, fade_out=0.8,
    )


def save_reddit_card_png(
    subreddit, title, output_path,
    width=1080, height=1920,
    duration=4.0, upvotes="12.4k", comments="847",
    username="throwaway_story", time_ago="6h ago"
):
    """
    Save Reddit card as PNG for FFmpeg overlay.
    Returns path to saved PNG.
    This bypasses MoviePy alpha blending for pixel-perfect text.
    """
    ov  = create_reddit_ui_overlay(
        subreddit=subreddit,
        title=title,
        width=width,
        height=height,
        duration=duration,
        upvotes=upvotes,
        comments=comments,
        username=username,
        time_ago=time_ago,
    )
    arr = ov.image
    img = Image.fromarray(arr.astype("uint8"), "RGBA")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path

def create_channel_watermark(channel_name, width=1080, height=1920, duration=60.0):
    """
    Watermark with UpvoteAnthology logo + @channel_name text.
    Bottom-right corner, semi-transparent so it doesnt distract.
    """
    # Watermark strip height
    strip_h = 80
    img     = Image.new("RGBA", (width, strip_h), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(img)

    # ── Try to load logo ─────────────────────────────────────────────
    logo_size  = 44
    logo_img   = None
    logo_path  = Path("assets/icons/upvote_anthology.png")
    if logo_path.exists():
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
            logo_img = logo_img.resize((logo_size, logo_size), Image.LANCZOS)
            # Reduce alpha to 60% for semi-transparent look
            alpha = logo_img.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.60))
            logo_img.putalpha(alpha)
        except Exception:
            logo_img = None

    # ── Text ─────────────────────────────────────────────────────────
    font = _load_font(28, bold=True)
    text = f"@{channel_name}"
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
    except Exception:
        tw = len(text) * 14
        th = 28

    # ── Layout: [logo][gap][text]  right-aligned ─────────────────────
    gap        = 10
    right_pad  = 60
    total_w    = (logo_size + gap if logo_img else 0) + tw
    start_x    = width - total_w - right_pad

    if logo_img:
        logo_y = (strip_h - logo_size) // 2
        img.paste(logo_img, (start_x, logo_y), logo_img)
        text_x = start_x + logo_size + gap
    else:
        text_x = start_x

    text_y = (strip_h - th) // 2 - 2

    # Draw text with light stroke for readability, semi-transparent
    draw.text(
        (text_x, text_y),
        text,
        font=font,
        fill=(255, 255, 255, 180),
        stroke_width=2,
        stroke_fill=(0, 0, 0, 160),
    )

    arr = np.array(img)
    return Overlay(
        name="watermark",
        image=arr,
        start=0.0,
        end=duration,
        x=0,
        y=max(0, height - strip_h - 20),
    )



def create_cta_overlay(
    text="Follow for more stories",
    width=1080, height=1920,
    start=0.0, duration=3.0
):
    bar_h = 110
    img   = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw  = ImageDraw.Draw(img)
    y0    = height - bar_h - 100
    draw.rounded_rectangle([60, y0, width-60, y0+bar_h], radius=16, fill=(255,69,0,230))
    font  = _load_font(44, bold=True)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]
    except Exception:
        tw = len(text) * 24
        th = 44
    tx = (width - tw) // 2
    ty = y0 + (bar_h - th) // 2
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255, 255))
    arr = np.array(img)
    return Overlay(
        name="cta", image=arr,
        start=start, end=start + duration,
        x=0, y=0,
        fade_in=0.3, fade_out=0.5,
    )
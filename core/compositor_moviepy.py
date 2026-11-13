"""PERMANENT BACKUP — Old MoviePy compositor (kept for fallback)
New pipeline is in compositor_ffmpeg.py
"""

from __future__ import annotations
import subprocess
import json
import re
import random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from core.overlay_engine import OverlayEngine
from core.caption_renderer import make_caption_clips, make_script_caption_clips

import time as _ct_time
_CT_START = None
_CT_LAST  = None

def _ct_stamp(label: str) -> None:
    global _CT_START, _CT_LAST
    now = _ct_time.time()
    if _CT_START is None:
        _CT_START = now
        _CT_LAST = now
        print(f"  [COMPT] START | {label}")
        return
    step = now - _CT_LAST
    total = now - _CT_START
    _CT_LAST = now
    print(f"  [COMPT] +{step:6.1f}s  total {total:6.1f}s | {label}")


def _ct_reset() -> None:
    global _CT_START, _CT_LAST
    _CT_START = None
    _CT_LAST = None




def _parse_srt(srt_path):
    try:
        content = Path(srt_path).read_text(encoding="utf-8")
    except Exception:
        return []
    segments = []
    blocks   = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        tl   = lines[1]
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


def _make_vignette_image(width, height):
    """
    Strong vignette — corners and edges are very dark.
    Uses radial gradient from center outward.
    """
    import math
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    cx  = width  / 2.0
    cy  = height / 2.0
    max_dist = math.sqrt(cx**2 + cy**2)

    # Build alpha channel row by row
    for y in range(height):
        for x in range(width):
            dist  = math.sqrt((x - cx)**2 + (y - cy)**2)
            ratio = dist / max_dist         # 0 at center, 1 at corner
            # Strong curve — barely dark at center, very dark at edges
            alpha = int(220 * (ratio ** 1.6))
            alpha = min(220, max(0, alpha))
            arr[y, x, 3] = alpha            # only alpha, RGB stays 0

    return arr


def _make_vignette(width, height):
    """Strong radial vignette — corners dark, center bright."""
    import math
    arr = np.zeros((height, width, 4), dtype=np.uint8)
    cx  = width  / 2.0
    cy  = height / 2.0
    max_dist = math.sqrt(cx ** 2 + cy ** 2)
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            dist  = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            ratio = min(1.0, dist / max_dist)
            alpha = int(200 * (ratio ** 1.8))
            alpha = max(0, min(200, alpha))
            arr[y,   x,   3] = alpha
            if x + 1 < width:
                arr[y,   x+1, 3] = alpha
            if y + 1 < height:
                arr[y+1, x,   3] = alpha
            if x + 1 < width and y + 1 < height:
                arr[y+1, x+1, 3] = alpha
    return arr


def _process_bg_frame(frame, dim=0.35, blur_radius=0.8):
    """
    Apply dimming + slight blur to each background frame.
    dim=0.35 means 35% darker.
    blur_radius=0.8 removes moire artifacts.
    """
    # Slight blur to remove moire patterns
    if blur_radius > 0:
        pil = Image.fromarray(frame.astype("uint8"), "RGB")
        pil = pil.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        frame = np.array(pil)
    # Dimming
    frame = (frame * (1.0 - dim)).clip(0, 255).astype("uint8")
    return frame




def _get_vibe_settings(categories: list) -> dict:
    """
    Return dimming and color settings based on background vibe categories.
    gaming     : lighter dim, higher saturation
    industrial : medium dim, cool tone, higher contrast
    fpv_drone  : warm cinematic, medium dim
    satisfying : soft warm, light dim
    default    : standard settings
    """
    cats = [c.lower() for c in (categories or [])]
    if "gaming" in cats:
        return {"dim": 0.15, "saturation": 1.15, "contrast": 1.0,  "label": "gaming"}
    if "industrial" in cats:
        return {"dim": 0.25, "saturation": 0.90, "contrast": 1.10, "label": "industrial"}
    if "fpv_drone" in cats:
        return {"dim": 0.30, "saturation": 1.05, "contrast": 1.05, "label": "cinematic"}
    if "satisfying" in cats:
        return {"dim": 0.20, "saturation": 1.05, "contrast": 1.0,  "label": "satisfying"}
    return     {"dim": 0.35, "saturation": 1.0,  "contrast": 1.0,  "label": "default"}

def _build_background(clips, duration, width, height, scene_duration=18, dim=0.35):
    """
    Build background from multiple clips with scene cuts.
    Each clip plays for scene_duration seconds then cuts to next.
    Applies dimming + blur to remove moire.
    """
    from moviepy.editor import VideoFileClip, ColorClip, concatenate_videoclips

    if not clips:
        return ColorClip(size=(width, height), color=(15, 15, 15), duration=duration)

    segments      = []
    time_remaining = duration
    clip_idx      = 0
    used_starts   = {}

    while time_remaining > 0.1:
        seg_dur   = min(scene_duration, time_remaining)
        clip_path = clips[clip_idx % len(clips)]
        clip_idx += 1

        try:
            raw = VideoFileClip(str(clip_path), audio=False)

            # Random start point — different each scene
            key = str(clip_path)
            if raw.duration > seg_dur + 2:
                used = used_starts.get(key, [])
                # Try to find unused section
                for _ in range(10):
                    start_at = random.uniform(0, raw.duration - seg_dur - 1)
                    overlap  = any(abs(start_at - u) < seg_dur for u in used)
                    if not overlap:
                        break
                used.append(start_at)
                used_starts[key] = used
            else:
                start_at = 0

            end_at = min(start_at + seg_dur, raw.duration)
            seg    = raw.subclip(start_at, end_at)

            # Resize to fill 1080x1920
            scale = max(height / seg.h, width / seg.w)
            nw    = int(seg.w * scale)
            nh    = int(seg.h * scale)
            seg   = seg.resize((nw, nh))
            x1    = (nw - width)  // 2
            y1    = (nh - height) // 2
            seg   = seg.crop(x1=x1, y1=y1, x2=x1+width, y2=y1+height)

            # Apply dimming + blur per frame
            seg = seg.fl_image(lambda f, _d=dim: _process_bg_frame(f, dim=_d, blur_radius=0.8))

            segments.append(seg)
            time_remaining -= seg_dur
            print(f"    Scene {clip_idx}: {clip_path.name} start={start_at:.1f}s dur={seg_dur:.1f}s")

        except Exception as e:
            print(f"  Clip failed: {e}")
            pad = ColorClip(size=(width, height), color=(15,15,15), duration=seg_dur)
            segments.append(pad)
            time_remaining -= seg_dur

    if not segments:
        return ColorClip(size=(width, height), color=(15,15,15), duration=duration)

    bg = concatenate_videoclips(segments)
    if bg.duration < duration:
        pad = ColorClip(size=(width,height), color=(15,15,15), duration=duration - bg.duration)
        bg  = concatenate_videoclips([bg, pad])
    return bg.subclip(0, duration)



def _apply_card_overlay_ffmpeg(
    video_path: Path,
    card_png: Path,
    output_path: Path,
    card_start: float = 0.0,
    card_end: float = 4.0,
    fade_in: float = 0.4,
    fade_out: float = 0.8,
) -> bool:
    """
    FFmpeg overlay with fade — fast version using -loop 1 input flag.
    Avoids slow loop filter that caused timeouts.
    """
    import shutil as _shutil
    _ffmpeg = _shutil.which("ffmpeg")
    if not _ffmpeg:
        print("  FFmpeg not found")
        return False
    if not Path(str(card_png)).exists():
        print(f"  Card PNG not found: {card_png}")
        return False
    if not Path(str(video_path)).exists():
        print(f"  Video not found: {video_path}")
        return False

    try:
        card_duration  = card_end - card_start
        fade_out_start = max(0, card_duration - fade_out)

        filter_str = (
            f"[1:v]format=rgba,"
            f"fade=t=in:st=0:d={fade_in}:alpha=1,"
            f"fade=t=out:st={fade_out_start}:d={fade_out}:alpha=1[card];"
            f"[0:v][card]overlay=(W-w)/2:(H-h)/2"
            f":enable='between(t,{card_start},{card_end})'[outv]"
        )

        cmd = [
            _ffmpeg, "-y",
            "-i", str(video_path),
            "-loop", "1", "-t", str(card_duration), "-i", str(card_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "medium",
            "-c:a", "aac",
            str(output_path),
        ]

        print(f"  Running FFmpeg overlay (fade in {fade_in}s, fade out {fade_out}s)...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if Path(str(output_path)).exists() and Path(str(output_path)).stat().st_size > 50000:
            size_mb = Path(str(output_path)).stat().st_size / 1024 / 1024
            print(f"  FFmpeg overlay success: {size_mb:.1f} MB")
            return True
        else:
            print(f"  FFmpeg overlay failed")
            print(f"  STDERR: {result.stderr[-400:]}")
            return False

    except Exception as e:
        print(f"  FFmpeg overlay error: {e}")
        return False

    try:
        fade_out_start = max(card_start, card_end - fade_out)
        filter_str = (
            f"[1:v]loop=loop=-1:size=1:start=0,"
            f"setpts=N/FRAME_RATE/TB,"
            f"format=rgba,"
            f"fade=t=in:st={card_start}:d={fade_in}:alpha=1,"
            f"fade=t=out:st={fade_out_start}:d={fade_out}:alpha=1[card];"
            f"[0:v][card]overlay=(W-w)/2:(H-h)/2"
            f":enable='between(t,{card_start},{card_end})'[outv]"
        )
        cmd = [
            _ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(card_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "medium",
            "-c:a", "aac",
            str(output_path),
        ]
        print(f"  Running FFmpeg overlay with fade...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if Path(str(output_path)).exists() and Path(str(output_path)).stat().st_size > 50000:
            return True
        else:
            print(f"  STDERR: {result.stderr[-400:]}")
            return False
    except Exception as e:
        print(f"  Error: {e}")
        return False
    if not Path(str(card_png)).exists():
        print(f"  Card PNG not found: {card_png}")
        return False
    if not Path(str(video_path)).exists():
        print(f"  Video not found: {video_path}")
        return False

    try:
        fade_out_start = max(card_start, card_end - fade_out)

        # Verified working filter from Test 3
        filter_str = (
            f"[1:v]format=rgba,"
            f"fade=in:st={card_start}:d={fade_in}:alpha=1,"
            f"fade=out:st={fade_out_start}:d={fade_out}:alpha=1[card];"
            f"[0:v][card]overlay=(W-w)/2:(H-h)/2"
            f":enable='between(t,{card_start},{card_end})'[outv]"
        )

        cmd = [
            _ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(card_png),
            "-filter_complex", filter_str,
            "-map", "[outv]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "medium",
            "-c:a", "aac",
            str(output_path),
        ]

        print(f"  Running FFmpeg card overlay...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if Path(str(output_path)).exists() and Path(str(output_path)).stat().st_size > 50000:
            size_mb = Path(str(output_path)).stat().st_size / 1024 / 1024
            print(f"  FFmpeg overlay success: {size_mb:.1f} MB")
            return True
        else:
            print(f"  FFmpeg overlay failed")
            print(f"  STDERR: {result.stderr[-400:]}")
            return False

    except Exception as e:
        print(f"  FFmpeg overlay error: {e}")
        return False


    try:
        duration = card_end - card_start

        # FFmpeg overlay with fade in and fade out using alpha filter
        # overlay=(W-w)/2:(H-h)/2 centers the card
        # enable= shows overlay only during card window
        # alpha fade in and out using format+colorchannelmixer
        filter_complex = (
            f"[1:v]"
            f"fade=in:st={card_start}:d={fade_in}:alpha=1,"
            f"fade=out:st={card_end - fade_out}:d={fade_out}:alpha=1"
            f"[card];"
            f"[0:v][card]overlay=(W-w)/2:(H-h)/2:enable='"
            f"between(t,{card_start},{card_end})'"
            f"[outv]"
        )

        cmd = [
            ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(card_png),
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "0:a?",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "medium",
            "-c:a", "aac",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if output_path.exists() and output_path.stat().st_size > 50000:
            return True
        else:
            print(f"  FFmpeg card overlay failed: {result.stderr[-300:]}")
            return False

    except Exception as e:
        print(f"  FFmpeg card overlay error: {e}")
        return False


def compose_video_moviepy(
    channel_id,
    script,
    audio_path,
    output_path,
    duration,
    title="",
    background_path=None,
    background_clips=None,
    use_kinetic_captions=True,
    resolution=(1080, 1920),
    srt_path=None,
    overlays=None,
):
    _ct_reset(); _ct_stamp("compose_video START")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from moviepy.editor import (
            AudioFileClip,
            CompositeVideoClip,
            ImageClip,
        )
        width, height = resolution

        # ── Layer 1: Background with scene cuts + dimming + blur ──────
        if background_clips and len(background_clips) > 0:
            clips_list = background_clips
        elif background_path and Path(str(background_path)).exists():
            clips_list = [Path(str(background_path))]
        else:
            clips_list = []

        print(f"  Building background — {len(clips_list)} clip(s) available")
        _vibe_cats = [str(c) for c in (background_clips or [])]
        _vibe      = _get_vibe_settings(_vibe_cats)
        print(f"  Vibe profile: {_vibe['label']} dim={_vibe['dim']} sat={_vibe['saturation']}")
        bg_clip = _build_background(clips_list, duration, width, height, scene_duration=18, dim=_vibe['dim'])
        print(f"  Background ready")

        # ── Layer 2: Vignette (strong radial darkening) ───────────────
        print(f"  Building vignette...")
        _ct_stamp("about to build vignette")
        vig_arr  = _make_vignette(width, height)
        _ct_stamp("vignette built")
        vig_rgb  = vig_arr[:,:,:3].astype("uint8")
        vig_a    = (vig_arr[:,:,3] / 255.0).astype("float32")
        vig_clip = ImageClip(vig_rgb, duration=duration).set_mask(
            ImageClip(vig_a, ismask=True, duration=duration)
        )
        print(f"  Vignette ready")

        # ── Layer 3: Blur zone behind caption + card areas ────────────
        blur_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        bd       = ImageDraw.Draw(blur_img)
        # Caption zone
        bd.rectangle([0, int(height*0.66), width, int(height*0.84)], fill=(0,0,0,65))
        # Card zone
        bd.rectangle([0, int(height*0.30), width, int(height*0.64)], fill=(0,0,0,40))
        _ct_stamp("about to build blur zone")
        blur_img  = blur_img.filter(ImageFilter.GaussianBlur(radius=14))
        _ct_stamp("blur zone built")
        blur_arr  = np.array(blur_img)
        blur_rgb  = blur_arr[:,:,:3].astype("uint8")
        blur_a    = (blur_arr[:,:,3]/255.0).astype("float32")
        blur_clip = ImageClip(blur_rgb, duration=duration).set_mask(
            ImageClip(blur_a, ismask=True, duration=duration)
        )

        # ── Layer 4: Captions ─────────────────────────────────────────
        caption_clips = []
        if use_kinetic_captions:
            srt_file = srt_path
            if not srt_file or not Path(str(srt_file)).exists():
                srt_file = Path(audio_path).parent / "captions.srt"
            segments = _parse_srt(Path(srt_file)) if srt_file and Path(str(srt_file)).exists() else []
            if segments:
                _ct_stamp("about to build caption clips")
                caption_clips = make_caption_clips(segments, width, height, duration)
                _ct_stamp(f"caption clips built ({len(caption_clips)})")
                print(f"  Synced captions: {len(caption_clips)} clips")
            else:
                caption_clips = make_script_caption_clips(script, duration, width, height)
                print(f"  Script captions: {len(caption_clips)} clips")

        # ── Layer 5: Overlays ─────────────────────────────────────────
        overlay_clips = []
        if overlays:
            engine = OverlayEngine(width=width, height=height)
            for ov in overlays:
                engine.add_overlay(ov)
            overlay_clips = engine.get_clips()
            print(f"  Overlays: {len(overlay_clips)} clips")

        # ── Composite ─────────────────────────────────────────────────
        _ct_stamp("about to composite layers")
        all_layers = [bg_clip, vig_clip, blur_clip] + caption_clips + overlay_clips
        final      = CompositeVideoClip(all_layers, size=(width, height))
        _ct_stamp("composite object created")
        final      = final.set_duration(duration)

        # ── Audio ─────────────────────────────────────────────────────
        if audio_path and Path(str(audio_path)).exists():
            try:
                audio = AudioFileClip(str(audio_path))
                if audio.duration > duration:
                    audio = audio.subclip(0, duration)
                final = final.set_audio(audio)
                print(f"  Audio loaded")
            except Exception as e:
                print(f"  Audio failed: {e}")

        # ── Export — optimized for speed ──────────────────────────────
        print(f"  Rendering (medium quality — crisp text)...")
        _ct_stamp("STARTING write_videofile — this is the big one")
        final.write_videofile(
            str(output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            ffmpeg_params=["-crf", "18"],
            verbose=False,
            logger=None,
            threads=2,
        )

        _ct_stamp("write_videofile DONE")
        success = output_path.exists() and output_path.stat().st_size > 50000
        if success:
            print(f"  Rendered: {output_path.name}")
            (output_path.parent / "render_info.json").write_text(
                json.dumps({"renderer": "compositor_v3", "duration": duration,
                            "clips": len(clips_list), "dim": 0.35}, indent=2),
                encoding="utf-8"
            )
        return success

    except Exception as e:
        print(f"  Compositor error: {e}")
        import traceback; traceback.print_exc()
        Path(output_path).parent.joinpath("compositor_error.txt").write_text(str(e))
        return False
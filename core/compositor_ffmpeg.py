"""
core/compositor_ffmpeg.py

HYBRID compositor: MoviePy builds overlay PNGs, FFmpeg does all video work.

Pipeline (two-pass for reliability):
  Pass 1: Concat BG clips + apply dim/vignette + mix audio -> base.mp4
  Pass 2: Overlay card + watermark PNGs + burn captions via subtitles filter -> final.mp4

Uses FFmpeg subtitles filter for captions (10x faster than 85 PNG overlays).
Uses concat demuxer + filter_complex for backgrounds.
Uses libx264 with preset=veryfast for i3-level CPUs.
"""

from __future__ import annotations
import os
import re
import subprocess
import shutil as _sh
import tempfile
import time
from pathlib import Path


FFMPEG = _sh.which("ffmpeg")


def _srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h*3600 - m*60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _build_word_chunk_srt(source_srt: Path, output_srt: Path, chunk_size: int = 3) -> bool:
    """
    Read source SRT (whole sentences) and rewrite as small chunks of N words
    with proportional timing. This gives the 3-words-at-a-time look.
    """
    try:
        content = source_srt.read_text(encoding="utf-8")
        blocks = re.split(r"\n\s*\n", content.strip())
        new_blocks = []
        chunk_idx = 1

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
            if not m or not text:
                continue

            g = m.groups()
            start = int(g[0])*3600 + int(g[1])*60 + int(g[2]) + int(g[3])/1000
            end   = int(g[4])*3600 + int(g[5])*60 + int(g[6]) + int(g[7])/1000

            # Clean the text
            text = re.sub(r"^Title[,:]?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"A-I-T-A", "AITA", text)
            words = text.split()
            if not words:
                continue

            # Split into chunks of `chunk_size` words
            chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]
            per_chunk_dur = (end - start) / len(chunks)

            for ci, chunk in enumerate(chunks):
                cs = start + ci * per_chunk_dur
                ce = cs + per_chunk_dur
                chunk_text = " ".join(chunk)
                new_blocks.append(
                    f"{chunk_idx}\n"
                    f"{_srt_time(cs)} --> {_srt_time(ce)}\n"
                    f"{chunk_text}\n"
                )
                chunk_idx += 1

        output_srt.write_text("\n".join(new_blocks), encoding="utf-8")
        return True
    except Exception as e:
        print(f"  [FFMPEG] SRT chunking failed: {e}")
        return False


def _make_bg_concat_file(clips: list, workdir: Path) -> Path:
    """Build FFmpeg concat demuxer text file listing background clips in order."""
    concat_file = workdir / "concat_list.txt"
    lines = []
    for clip in clips:
        # Escape backslashes for FFmpeg concat demuxer on Windows
        p = str(Path(clip).resolve()).replace("\\", "/")
        lines.append(f"file '{p}'")
    concat_file.write_text("\n".join(lines), encoding="utf-8")
    return concat_file


def _save_overlays_as_pngs(overlays: list, workdir: Path) -> list:
    """
    Convert Overlay objects (numpy arrays) to PNG files on disk.
    Returns list of dicts: {"path": Path, "x": int, "y": int, "start": float, "end": float}
    """
    from PIL import Image
    saved = []
    for i, ov in enumerate(overlays or []):
        try:
            arr = ov.image
            img = Image.fromarray(arr.astype("uint8"), "RGBA")
            png = workdir / f"overlay_{i}_{ov.name}.png"
            img.save(png, "PNG")
            saved.append({
                "path":  png,
                "x":     ov.x,
                "y":     ov.y,
                "start": ov.start,
                "end":   ov.end,
                "name":  ov.name,
            })
        except Exception as e:
            print(f"  [FFMPEG] Failed to save overlay {i}: {e}")
    return saved


def _run_ffmpeg(cmd: list, timeout: int = 1800, label: str = "ffmpeg") -> bool:
    """Run an FFmpeg command; return True if success."""
    _t = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - _t
        if r.returncode == 0:
            print(f"  [FFMPEG] {label} OK in {elapsed:.1f}s")
            return True
        else:
            print(f"  [FFMPEG] {label} FAILED (rc={r.returncode}) after {elapsed:.1f}s")
            print(f"  STDERR (last 500): {r.stderr[-500:]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  [FFMPEG] {label} TIMEOUT after {timeout}s")
        return False
    except Exception as e:
        print(f"  [FFMPEG] {label} ERROR: {e}")
        return False




def _build_ass_from_srt(srt_path, ass_path, video_w=1080, video_h=1920):
    """
    Convert SRT to ASS with Montserrat Bold + UPPERCASE + colors + bounce.
    Alignment=2 = bottom-center. MarginV = pixels from BOTTOM edge.

    Features:
      - Montserrat Bold font (embedded if available)
      - ALL UPPERCASE text
      - Kick words in RED, emotion words in YELLOW
      - Bounce animation: pop 120% -> 90% -> 100%
      - Thick stroke (Outline=14)
      - MarginV=500 (higher up from bottom)
    """
    import re as _re

    # ── Word categories for coloring ──────────────────────────────────
    KICK_WORDS = {
        # anger, forceful actions
        "STOP", "NO", "NEVER", "DON'T", "SHUT", "OUT", "LEAVE", "GET",
        "SCREAMED", "YELLED", "SHOUTED", "SNAPPED", "SLAMMED", "STORMED",
        "KICKED", "THREW", "SLAPPED", "PUSHED", "HIT", "FIRED", "QUIT",
        "REFUSED", "STOPPED", "ENDED", "BROKE", "SHATTERED", "DESTROYED",
        "RUINED", "CRUSHED", "SMASHED", "TORE", "RIPPED", "BURNED",
        "DUMPED", "DIVORCED", "BLOCKED", "REJECTED", "IGNORED", "DISMISSED",
        "CONFRONTED", "EXPOSED", "CALLED", "WARNED",
    }
    EMOTION_WORDS = {
        # feelings, reactions, drama
        "SHOCKED", "STUNNED", "SHATTERED", "DEVASTATED", "HEARTBROKEN",
        "FURIOUS", "LIVID", "ENRAGED", "PISSED", "ANGRY", "MAD", "UPSET",
        "HURT", "BROKEN", "CRUSHED", "BETRAYED", "BLINDSIDED",
        "AMAZING", "INCREDIBLE", "UNBELIEVABLE", "INSANE", "CRAZY",
        "SHOCKING", "DISGUSTING", "HORRIBLE", "TERRIBLE", "AWFUL",
        "LOVE", "HATE", "MISS", "WANT", "NEED", "FELT", "FEEL",
        "CRIED", "CRYING", "TEARS", "SOBBING", "LAUGHED", "SMILED",
        "CHEATED", "LIED", "STOLEN", "STOLE", "SECRET", "AFFAIR",
        "PREGNANT", "DIVORCE", "WEDDING", "FUNERAL", "DIED", "DEATH",
    }

    def _color_word(word_upper):
        """Return ASS color tag for word if it's in a category."""
        # Strip punctuation for lookup
        clean = _re.sub(r"[^A-Z']", "", word_upper)
        if clean in KICK_WORDS:
            return "{\\c&H0000FF&}"      # RED in ASS BGR format = &H0000FF&
        if clean in EMOTION_WORDS:
            return "{\\c&H00FFFF&}"      # YELLOW
        return None

    def _apply_word_colors(text_line):
        """
        Take an uppercase text line and inject ASS color tags around
        kick/emotion words. Reset color after each colored word.
        """
        words = text_line.split()
        out = []
        for w in words:
            tag = _color_word(w)
            if tag:
                # Colored word then reset to white
                out.append(f"{tag}{w}{{\\c&HFFFFFF&}}")
            else:
                out.append(w)
        return " ".join(out)

    # ── Parse SRT ──────────────────────────────────────────────────────
    content = Path(srt_path).read_text(encoding="utf-8")
    blocks = _re.split(r"\n\s*\n", content.strip())

    events = []
    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        tl = lines[1]
        text_content = " ".join(lines[2:]).strip()
        m = _re.match(
            r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
            tl
        )
        if not m:
            continue
        g = m.groups()
        s_h, s_m, s_s, s_ms = int(g[0]), int(g[1]), int(g[2]), int(g[3])
        e_h, e_m, e_s, e_ms = int(g[4]), int(g[5]), int(g[6]), int(g[7])

        start_ass = f"{s_h}:{s_m:02d}:{s_s:02d}.{s_ms // 10:02d}"
        end_ass   = f"{e_h}:{e_m:02d}:{e_s:02d}.{e_ms // 10:02d}"

        # UPPERCASE the text
        text_clean = text_content.replace("\n", " ").replace("{", "").replace("}", "").upper()
        # Apply word coloring
        text_colored = _apply_word_colors(text_clean)
        # Bounce animation: scale 120% -> 90% -> 100% over 200ms
        # \t(0,88,\fscx90\fscy90) then \t(80,200,\fscx100\fscy100)
        anim = "{\\fscx120\\fscy120\\t(0,100,\\fscx90\\fscy90)\\t(100,200,\\fscx100\\fscy100)}"
        final_text = f"{anim}{text_colored}"
        events.append((start_ass, end_ass, final_text))

    # ── Write ASS file with Montserrat Bold style ────────────────────
    ass_content = f"""[Script Info]
Title: Captions
ScriptType: v4.00+
PlayResX: {video_w}
PlayResY: {video_h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Bold,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,14,0,2,80,80,500,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    for start, end, txt in events:
        ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{txt}\n"

    Path(ass_path).write_text(ass_content, encoding="utf-8")



def compose_video_ffmpeg(
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
    card_png=None,
    card_start=0.0,
    card_end=7.0,
    card_fade_in=0.7,
    card_fade_out=0.8,
):
    """
    Hybrid FFmpeg pipeline.
    Returns True on success, raises exception on failure.
    """
    if not FFMPEG:
        raise RuntimeError("ffmpeg not found in PATH")

    _start = time.time()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = resolution

    # Working directory (temp files here)
    workdir = output_path.parent / "_ffmpeg_temp"
    workdir.mkdir(parents=True, exist_ok=True)

    # ── Prepare background clips list ─────────────────────────────────
    if background_clips and len(background_clips) > 0:
        bg_clips = [str(Path(c).resolve()) for c in background_clips]
    elif background_path and Path(str(background_path)).exists():
        bg_clips = [str(Path(background_path).resolve())]
    else:
        raise RuntimeError("No background clips provided")

    print(f"  [FFMPEG] {len(bg_clips)} background clip(s), target duration {duration:.1f}s")

    # ── PASS 1: Concat backgrounds + scale/crop + dim + audio ─────────
    # Each clip is trimmed to 18s scene, scaled to 1080x1920, dimmed 35%, joined
    base_mp4 = workdir / "base.mp4"

    # Build filter_complex: process each clip then concat
    scene_dur = 18.0
    n_scenes = max(1, int(duration / scene_dur) + 1)

    inputs = []
    filters = []
    for i in range(n_scenes):
        clip = bg_clips[i % len(bg_clips)]
        inputs.extend(["-t", str(scene_dur), "-i", clip])
        # Each clip: scale to fill 1080x1920, crop center, dim 35%
        filters.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,eq=brightness=-0.15[v{i}]"
        )

    # Concat processed clips
    concat_inputs = "".join(f"[v{i}]" for i in range(n_scenes))
    filters.append(f"{concat_inputs}concat=n={n_scenes}:v=1:a=0[bgv]")

    # Trim to exact duration
    filters.append(f"[bgv]trim=duration={duration},setpts=PTS-STARTPTS[bgout]")

    # Audio input
    audio_path = Path(audio_path).resolve()
    inputs.extend(["-i", str(audio_path)])
    audio_idx = n_scenes  # audio is after all video inputs

    filter_str = ";".join(filters)

    pass1_cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[bgout]",
        "-map", f"{audio_idx}:a",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-t", str(duration),
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-threads", "0",
        str(base_mp4),
    ]

    print(f"  [FFMPEG] Pass 1: build base video (bg concat + dim + audio)...")
    if not _run_ffmpeg(pass1_cmd, timeout=900, label="Pass 1"):
        raise RuntimeError("Pass 1 (base video) failed")

    if not base_mp4.exists() or base_mp4.stat().st_size < 50000:
        raise RuntimeError(f"Pass 1 produced empty/small file: {base_mp4}")

    # ── PASS 2: Overlays + captions ───────────────────────────────────
    # Save overlays (card, watermark, cta) as PNGs
    overlay_files = _save_overlays_as_pngs(overlays, workdir)
    print(f"  [FFMPEG] Saved {len(overlay_files)} overlay PNGs")

    # ── Add Reddit card as an extra overlay with fade in/out ──────────
    if card_png and Path(str(card_png)).exists():
        card_entry = {
            "path":  Path(card_png),
            "x":     0,
            "y":     0,
            "start": card_start,
            "end":   card_end,
            "name":  "reddit_card",
            "fade_in":  card_fade_in,
            "fade_out": card_fade_out,
        }
        overlay_files.append(card_entry)
        print(f"  [FFMPEG] Card added to overlays: {Path(card_png).name} @ {card_start}-{card_end}s")

    # Build word-chunk SRT for captions (3 words per chunk)
    chunk_srt = workdir / "chunks.srt"
    srt_ok = False
    print(f"  [FFMPEG] Caption inputs: use_kinetic={use_kinetic_captions}, srt_path={srt_path}")
    if use_kinetic_captions and srt_path and Path(str(srt_path)).exists():
        srt_ok = _build_word_chunk_srt(Path(srt_path), chunk_srt, chunk_size=3)
        if srt_ok and chunk_srt.exists():
            n_lines = len(chunk_srt.read_text(encoding="utf-8").splitlines())
            print(f"  [FFMPEG] Built chunks.srt ({n_lines} lines, {chunk_srt.stat().st_size} bytes)")
        else:
            print(f"  [FFMPEG] SRT chunking failed or output missing")
    else:
        print(f"  [FFMPEG] Skipping captions — SRT path invalid or use_kinetic_captions=False")

    # Assemble Pass 2 command
    pass2_inputs = ["-i", str(base_mp4)]
    for ov in overlay_files:
        # Loop the PNG for its display duration
        dur = max(0.1, ov["end"] - ov["start"])
        pass2_inputs.extend(["-loop", "1", "-t", str(dur), "-i", str(ov["path"])])

    # Build overlay filter chain
    stream = "[0:v]"
    filter_parts = []
    for i, ov in enumerate(overlay_files):
        in_idx = i + 1
        next_stream = f"[ov{i}]"
        # If this overlay has fade in/out (e.g. Reddit card), pre-process input
        fade_in_dur  = ov.get("fade_in", 0)
        fade_out_dur = ov.get("fade_out", 0)
        if fade_in_dur > 0 or fade_out_dur > 0:
            fade_out_start = max(0, (ov["end"] - ov["start"]) - fade_out_dur)
            pre_stream = f"[pre{i}]"
            filter_parts.append(
                f"[{in_idx}:v]format=rgba,"
                f"fade=t=in:st=0:d={fade_in_dur}:alpha=1,"
                f"fade=t=out:st={fade_out_start}:d={fade_out_dur}:alpha=1"
                f"{pre_stream}"
            )
            filter_parts.append(
                f"{stream}{pre_stream}overlay="
                f"{ov['x']}:{ov['y']}:"
                f"enable='between(t,{ov['start']},{ov['end']})'"
                f"{next_stream}"
            )
        else:
            filter_parts.append(
                f"{stream}[{in_idx}:v]overlay="
                f"{ov['x']}:{ov['y']}:"
                f"enable='between(t,{ov['start']},{ov['end']})'"
                f"{next_stream}"
            )
        stream = next_stream

    # Add captions - use ASS file directly for guaranteed positioning
    if srt_ok:
        ass_path = workdir / "cap.ass"
        ass_ok = False
        try:
            _build_ass_from_srt(chunk_srt, ass_path, video_w=1080, video_h=1920)
            ass_ok = ass_path.exists() and ass_path.stat().st_size > 100
            if ass_ok:
                print(f"  [FFMPEG] Built ASS file: {ass_path.name} ({ass_path.stat().st_size} bytes)")
        except Exception as _e:
            print(f"  [FFMPEG] ASS build failed: {_e}")

        if ass_ok:
            ass_str = str(ass_path.resolve())
            ass_escaped = ass_str.replace("\\", "/").replace(":", "\\:")
            # Point libass to our fonts folder so Montserrat is found
            fonts_dir_str = str((Path("assets/fonts")).resolve())
            fonts_dir_esc = fonts_dir_str.replace("\\", "/").replace(":", "\\:")
            filter_parts.append(
                f"{stream}subtitles=filename='{ass_escaped}':fontsdir='{fonts_dir_esc}'[final]"
            )
            final_stream = "[final]"
            print(f"  [FFMPEG] Captions filter ADDED (ASS mode)")
        else:
            # Fallback: SRT + force_style
            srt_esc = str(chunk_srt.resolve()).replace("\\", "/").replace(":", "\\:")
            style = "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Alignment=2,MarginV=220,Bold=1"
            filter_parts.append(
                f"{stream}subtitles='{srt_esc}':force_style='{style}'[final]"
            )
            final_stream = "[final]"
            print(f"  [FFMPEG] Fallback SRT captions")
    else:
        # No captions - use last overlay stream
        if overlay_files:
            filter_parts.append(f"{stream}copy[final]")
            final_stream = "[final]"
        else:
            final_stream = "[0:v]"

    filter_str2 = ";".join(filter_parts) if filter_parts else None

    pass2_cmd = [FFMPEG, "-y", *pass2_inputs]
    if filter_str2:
        pass2_cmd.extend(["-filter_complex", filter_str2, "-map", final_stream])
    else:
        pass2_cmd.extend(["-map", "0:v"])
    pass2_cmd.extend([
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "copy",
        "-r", "30",
        "-pix_fmt", "yuv420p",
        "-threads", "0",
        str(output_path),
    ])

    print(f"  [FFMPEG] Pass 2: overlays + captions...")
    print(f"  [FFMPEG] Pass 2 filter_complex:")
    if filter_str2:
        for part in filter_str2.split(";"):
            print(f"    {part}")
    else:
        print(f"    (no filters)")
    if not _run_ffmpeg(pass2_cmd, timeout=900, label="Pass 2"):
        raise RuntimeError("Pass 2 (overlays + captions) failed")

    if not output_path.exists() or output_path.stat().st_size < 50000:
        raise RuntimeError(f"Pass 2 produced empty/small file: {output_path}")

    elapsed = time.time() - _start
    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  [FFMPEG] SUCCESS: {output_path.name} ({size_mb:.1f} MB) in {elapsed:.1f}s")

    # Keep workdir for debugging (contains chunks.srt, base.mp4, overlays)
    # Can be manually deleted later
    return True
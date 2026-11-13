"""
core/renderer.py
Video renderer with moviepy support and FFmpeg fallback.
Creates vertical 1080x1920 videos for shorts/reels.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import json

from core.channel_styles import get_style


def _escape_drawtext(text: str) -> str:
    return text.replace("\\", "").replace("'", "").replace(":", "-").replace(",", " ")[:72]


def _escape_subtitle_path(path: Path) -> str:
    s = str(path.resolve()).replace("\\", "/")
    s = s.replace(":", "\\:").replace("'", "\\'")
    return s


def render_placeholder_video(
    channel_id: str,
    title: str,
    audio_path: Path,
    captions_path: Path,
    output_path: Path,
    duration: float
) -> bool:
    """
    Render video. Tries moviepy first, then FFmpeg fallback.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try moviepy first
    moviepy_result = _render_with_moviepy(channel_id, title, audio_path, captions_path, output_path, duration)
    if moviepy_result:
        return True
    
    # Fallback to FFmpeg
    return _render_with_ffmpeg(channel_id, title, audio_path, captions_path, output_path, duration)


def _render_with_moviepy(
    channel_id: str,
    title: str,
    audio_path: Path,
    captions_path: Path,
    output_path: Path,
    duration: float
) -> bool:
    """Render using moviepy if available."""
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip
        
        style = get_style(channel_id)
        bg_color = style.get("bg_color", (30, 30, 30))
        text_color = style.get("text_color", "white")
        
        # Create background
        bg = ColorClip(size=(1080, 1920), color=bg_color, duration=duration)
        
        # Create title text
        safe_title = title[:60] if len(title) > 60 else title
        try:
            title_clip = TextClip(
                safe_title,
                fontsize=48,
                color=text_color,
                size=(1000, None),
                method='caption'
            ).set_position(('center', 200)).set_duration(duration)
        except Exception:
            title_clip = None
        
        # Create channel label
        label = style.get("short_label", channel_id)
        try:
            label_clip = TextClip(
                label,
                fontsize=36,
                color="yellow",
            ).set_position(('center', 80)).set_duration(duration)
        except Exception:
            label_clip = None
        
        # Composite
        clips = [bg]
        if title_clip:
            clips.append(title_clip)
        if label_clip:
            clips.append(label_clip)
        
        video = CompositeVideoClip(clips)
        
        # Add audio
        if audio_path.exists():
            try:
                audio = AudioFileClip(str(audio_path))
                video = video.set_audio(audio)
            except Exception:
                pass
        
        # Export
        video.write_videofile(
            str(output_path),
            fps=24,
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        # Save render info
        info = {
            "renderer": "moviepy",
            "channel_id": channel_id,
            "duration": duration,
            "resolution": "1080x1920",
        }
        with open(output_path.parent / "render_info.json", "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)
        
        return output_path.exists() and output_path.stat().st_size > 10000
    
    except ImportError:
        return False
    except Exception as e:
        (output_path.parent / "moviepy_error.txt").write_text(str(e), encoding="utf-8")
        return False


def _render_with_ffmpeg(
    channel_id: str,
    title: str,
    audio_path: Path,
    captions_path: Path,
    output_path: Path,
    duration: float
) -> bool:
    """Render using FFmpeg as fallback."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        (output_path.parent / "render_missing_ffmpeg.txt").write_text(
            "FFmpeg not found. Install FFmpeg to render MP4 files.\n",
            encoding="utf-8",
        )
        return False

    style = get_style(channel_id)
    color = style.get("ffmpeg_color", "0x1e1e1e")
    label = _escape_drawtext(style.get("short_label", channel_id))
    safe_title = _escape_drawtext(title)

    filters = [
        f"drawbox=x=0:y=0:w=1080:h=210:color=black@0.38:t=fill",
        f"drawtext=text='{label}':fontcolor=yellow:fontsize=54:x=(w-text_w)/2:y=70",
        f"drawtext=text='{safe_title}':fontcolor=white:fontsize=54:x=(w-text_w)/2:y=300",
        f"drawbox=x=80:y=1560:w=920:h=130:color=black@0.45:t=fill",
        f"drawtext=text='Manual review required':fontcolor=white:fontsize=34:x=(w-text_w)/2:y=1610",
    ]
    
    if captions_path.exists():
        pass  # Subtitle burning removed — captions handled by compositor
    
    vf = ",".join(filters)

    cmd = [
        ffmpeg,
        "-y",
        "-f", "lavfi",
        "-i", f"color=c={color}:s=1080x1920:d={duration}",
        "-i", str(audio_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(output_path),
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        (output_path.parent / "render_error.txt").write_text(result.stderr, encoding="utf-8")
        return False
    
    # Save render info
    info = {
        "renderer": "ffmpeg",
        "channel_id": channel_id,
        "duration": duration,
        "resolution": "1080x1920",
    }
    with open(output_path.parent / "render_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    
    return True
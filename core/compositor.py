"""
core/compositor.py

Smart chooser: tries new FFmpeg pipeline first, falls back to MoviePy if it fails.
Both implementations must be kept in sync API-wise.
"""

from __future__ import annotations
import time
from datetime import datetime


def compose_video(
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
    card_fade_in=0.4,
    card_fade_out=0.8,
):
    """
    Primary compositor entry point.

    Order:
    1. Try compose_video_ffmpeg (fast hybrid pipeline)
    2. If that raises any exception, print ERROR and fall back to MoviePy
    3. Return True/False from whichever succeeded
    """
    _start = time.time()
    _start_str = datetime.now().strftime("%H:%M:%S")
    print(f"  [COMPOSE] START @ {_start_str}")

    # Try FFmpeg pipeline first
    try:
        from core.compositor_ffmpeg import compose_video_ffmpeg
        result = compose_video_ffmpeg(
            channel_id=channel_id,
            script=script,
            audio_path=audio_path,
            output_path=output_path,
            duration=duration,
            title=title,
            background_path=background_path,
            background_clips=background_clips,
            use_kinetic_captions=use_kinetic_captions,
            resolution=resolution,
            srt_path=srt_path,
            overlays=overlays,
            card_png=card_png,
            card_start=card_start,
            card_end=card_end,
            card_fade_in=card_fade_in,
            card_fade_out=card_fade_out,
        )
        _elapsed = time.time() - _start
        print(f"  [COMPOSE] FFmpeg pipeline DONE in {_elapsed:.1f}s")
        return result
    except NotImplementedError as e:
        print(f"  [COMPOSE] FFmpeg pipeline not ready yet: {e}")
        print(f"  [COMPOSE] Falling back to MoviePy compositor...")
    except Exception as e:
        print(f"  [COMPOSE] ERROR in FFmpeg pipeline: {e}")
        print(f"  [COMPOSE] Falling back to MoviePy compositor...")

    # Fallback: MoviePy compositor
    try:
        from core.compositor_moviepy import compose_video_moviepy
        result = compose_video_moviepy(
            channel_id=channel_id,
            script=script,
            audio_path=audio_path,
            output_path=output_path,
            duration=duration,
            title=title,
            background_path=background_path,
            background_clips=background_clips,
            use_kinetic_captions=use_kinetic_captions,
            resolution=resolution,
            srt_path=srt_path,
            overlays=overlays,
        )
        _elapsed = time.time() - _start
        _mins = int(_elapsed // 60)
        _secs = int(_elapsed % 60)
        print(f"  [COMPOSE] MoviePy compositor DONE in {_mins}m {_secs}s ({_elapsed:.1f}s)")
        return result
    except Exception as e:
        _elapsed = time.time() - _start
        print(f"  [COMPOSE] FATAL: both pipelines failed after {_elapsed:.1f}s")
        print(f"  [COMPOSE] Error: {e}")
        return False


# Re-export _apply_card_overlay_ffmpeg from old compositor for workflow.py compatibility
try:
    from core.compositor_moviepy import _apply_card_overlay_ffmpeg
except ImportError:
    _apply_card_overlay_ffmpeg = None

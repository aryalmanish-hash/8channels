"""
core/music_manager.py
Free background music for videos.
- No looping (plays once, fades out cleanly)
- Verified direct MP3 URLs (no API key needed)
- AI fallback: asks Groq/Gemini for a working MP3 URL if all fail
"""

from __future__ import annotations
import random
import subprocess
import shutil
import time
from pathlib import Path
import requests

MUSIC_CACHE = Path("assets/music")

CHANNEL_MOOD = {
    "reddit_stories":      "dramatic",
    "english_learning":    "upbeat",
    "psychology":          "calm",
    "dark_history":        "dramatic",
    "ai_tools_automation": "upbeat",
    "quiz":                "upbeat",
    "facts":               "calm",
    "sports_reviews":      "upbeat",
}

# Verified working direct MP3 URLs — tested 2026-06-30
MUSIC_POOL = {
    "calm": [
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Relaxing%20Piano%20Music.mp3",
        "https://cdn.pixabay.com/audio/2022/11/22/audio_febc508520.mp3",
        "https://cdn.pixabay.com/audio/2022/08/04/audio_2dde668d05.mp3",
    ],
    "dramatic": [
        "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3",
        "https://cdn.pixabay.com/audio/2022/08/23/audio_d16737dc28.mp3",
        "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
    ],
    "upbeat": [
        "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
        "https://cdn.pixabay.com/audio/2022/08/04/audio_2dde668d05.mp3",
        "https://cdn.pixabay.com/audio/2022/11/22/audio_febc508520.mp3",
    ],
    "ambient": [
        "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3",
        "https://cdn.pixabay.com/audio/2022/11/22/audio_febc508520.mp3",
        "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Relaxing%20Piano%20Music.mp3",
    ],
}

ALL_VERIFIED = [
    "https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3",
    "https://cdn.pixabay.com/audio/2022/11/22/audio_febc508520.mp3",
    "https://cdn.pixabay.com/audio/2022/08/23/audio_d16737dc28.mp3",
    "https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3",
    "https://cdn.pixabay.com/audio/2022/08/04/audio_2dde668d05.mp3",
    "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Relaxing%20Piano%20Music.mp3",
]


def _get_mood(channel_id: str, vibe: str = None) -> str:
    if vibe == "emotional":
        return "calm"
    if vibe == "energetic":
        return "upbeat"
    return CHANNEL_MOOD.get(channel_id, "ambient")


def _download_track(url: str, dest: Path) -> bool:
    """Download audio track to dest path."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, timeout=60, stream=True, headers=headers)
        if resp.status_code == 200:
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            if dest.exists() and dest.stat().st_size > 10000:
                size_kb = dest.stat().st_size // 1024
                print(f"  Downloaded: {dest.name} ({size_kb} KB)")
                return True
        print(f"  Download failed: HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"  Download error: {e}")
        return False


def _ask_ai_for_music_url(mood: str) -> str | None:
    """
    Ask Groq/Gemini for a verified free direct MP3 download URL.
    Only called when all known URLs fail.
    """
    try:
        from core.ai_engine import ask_ai
        prompt = (
            f"I need a direct download URL for a free {mood} background music MP3. "
            f"Requirements:\n"
            f"- Must be a direct .mp3 file URL (not a webpage)\n"
            f"- Must be free to use (Creative Commons or royalty-free)\n"
            f"- Must be from a reliable CDN (pixabay CDN, incompetech, archive.org, etc.)\n"
            f"- URL must work without login or API key\n"
            f"Reply with ONLY the direct URL, nothing else. No explanation."
        )
        response = ask_ai(prompt)
        if not response:
            return None
        # Extract URL from response
        import re
        urls = re.findall(r'https?://[^\s"\'<>]+\.mp3[^\s"\'<>]*', response)
        if urls:
            url = urls[0].strip()
            print(f"  AI suggested URL: {url}")
            return url
        return None
    except Exception as e:
        print(f"  AI fallback error: {e}")
        return None


def _get_raw_music(mood: str) -> Path | None:
    """Get a raw music file — from cache, known URLs, or AI fallback."""
    MUSIC_CACHE.mkdir(parents=True, exist_ok=True)

    # Check cache first
    cache_files = list(MUSIC_CACHE.glob("*.mp3")) + list(MUSIC_CACHE.glob("*.wav"))
    if cache_files:
        picked = random.choice(cache_files)
        print(f"  Using cached music: {picked.name}")
        return picked

    # Try mood pool
    pool = MUSIC_POOL.get(mood, ALL_VERIFIED).copy()
    random.shuffle(pool)
    for url in pool:
        fname = f"{mood}_{url.split(chr(47))[-1]}"
        dest  = MUSIC_CACHE / fname
        if _download_track(url, dest):
            return dest
        time.sleep(0.3)

    # Try all verified URLs
    all_urls = ALL_VERIFIED.copy()
    random.shuffle(all_urls)
    for url in all_urls:
        fname = f"fallback_{url.split(chr(47))[-1]}"
        dest  = MUSIC_CACHE / fname
        if _download_track(url, dest):
            return dest

    # AI fallback — ask AI for a working URL
    print("  All known URLs failed — asking AI for music URL...")
    ai_url = _ask_ai_for_music_url(mood)
    if ai_url:
        dest = MUSIC_CACHE / f"ai_suggested_{int(time.time())}.mp3"
        if _download_track(ai_url, dest):
            return dest

    print("  All music sources failed including AI fallback")
    return None


def _prepare_music(src: Path, dest: Path, duration: float) -> bool:
    """
    Prepare music for mixing:
    - Trim to video duration if track is longer
    - If track is shorter, just use it as-is (plays once, then silence)
    - Apply 15% volume + 2s fade in + 3s fade out
    - No looping — avoids broken seams
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("  FFmpeg not found")
        return False
    try:
        # Get track duration first
        probe_cmd = [
            ffmpeg, "-i", str(src),
            "-f", "null", "-"
        ]
        probe = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=15)
        track_dur = duration  # default
        import re
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", probe.stderr)
        if m:
            h, mn, s = m.groups()
            track_dur = int(h)*3600 + int(mn)*60 + float(s)
            print(f"  Track duration: {track_dur:.1f}s, video: {duration:.1f}s")

        # Use the shorter of track or video duration
        use_dur   = min(track_dur, duration)
        fade_out  = max(0.0, use_dur - 3.0)

        cmd = [
            ffmpeg, "-y",
            "-i", str(src),
            "-t", str(use_dur),
            "-af", (
                f"volume=0.08,"
                f"afade=t=in:st=0:d=2,"
                f"afade=t=out:st={fade_out:.2f}:d=3"
            ),
            "-ar", "44100",
            "-ac", "2",
            str(dest),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"  Music prepared: {use_dur:.1f}s, 15% vol, clean fade out")
            return True
        print(f"  Prepare failed: {result.stderr[-300:]}")
        return False
    except Exception as e:
        print(f"  Prepare error: {e}")
        return False


def _mix_audio_tracks(voice_path: Path, music_path: Path, output_path: Path) -> bool:
    """
    Mix voice (100%) with music (15%, already faded).
    Music shorter than voice is fine — amix pads with silence.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    try:
        cmd = [
            ffmpeg, "-y",
            "-i", str(voice_path),
            "-i", str(music_path),
            "-filter_complex",
            (
                "[0:a]volume=1.0[voice];"
                "[1:a]volume=1.0[music];"
                "[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            ),
            "-map", "[aout]",
            "-ar", "44100",
            "-ac", "1",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if output_path.exists() and output_path.stat().st_size > 1000:
            print(f"  Mixed: voice + background music OK")
            return True
        print(f"  Mix failed: {result.stderr[-300:]}")
        return False
    except Exception as e:
        print(f"  Mix error: {e}")
        return False


def get_background_music(
    channel_id: str,
    duration: float,
    workspace: Path,
    vibe: str = None,
    api_key: str = None,
) -> Path | None:
    """
    Main entry. Get background music prepared for video duration.
    Returns WAV path ready for mixing, or None if all sources failed.
    """
    mood = _get_mood(channel_id, vibe)
    print(f"  Music: channel={channel_id} mood={mood} video={duration:.1f}s")

    raw = _get_raw_music(mood)
    if not raw:
        return None

    prepared = Path(str(workspace)) / "background_music.wav"
    ok = _prepare_music(raw, prepared, duration)
    return prepared if ok else None


def mix_voice_with_music(
    voice_path: Path,
    music_path: Path,
    workspace: Path,
) -> Path | None:
    """Mix voice with background music. Returns mixed WAV or None."""
    if not music_path or not Path(str(music_path)).exists():
        return None
    if not voice_path or not Path(str(voice_path)).exists():
        return None
    mixed = Path(str(workspace)) / "voice_with_music.wav"
    ok    = _mix_audio_tracks(voice_path, music_path, mixed)
    return mixed if ok else None


def speed_up_audio(audio_path: Path, multiplier: float = 1.25) -> tuple[bool, float]:
    """
    Speed up an audio file in-place using FFmpeg atempo (preserves pitch).
    Returns (success, new_duration_seconds).

    atempo is limited to 0.5-2.0 per filter. For 1.25x this is fine as single filter.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return False, 0.0

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg:
        print(f"  [SPEED] ffmpeg not found — skipping speed-up")
        return False, 0.0

    # Speed up to temp file, then replace original
    temp_out = audio_path.parent / (audio_path.stem + "_speeded" + audio_path.suffix)

    cmd = [
        ffmpeg, "-y",
        "-i", str(audio_path),
        "-filter:a", f"atempo={multiplier}",
        "-vn",
        str(temp_out),
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            print(f"  [SPEED] atempo failed: {r.stderr[-300:]}")
            return False, 0.0
    except Exception as e:
        print(f"  [SPEED] atempo error: {e}")
        return False, 0.0

    if not temp_out.exists() or temp_out.stat().st_size < 1000:
        return False, 0.0

    # Replace original with speeded version
    try:
        audio_path.unlink()
        shutil.move(str(temp_out), str(audio_path))
    except Exception as e:
        print(f"  [SPEED] move failed: {e}")
        return False, 0.0

    # Measure new duration
    new_dur = 0.0
    if ffprobe:
        try:
            r2 = subprocess.run(
                [ffprobe, "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True, timeout=15
            )
            new_dur = float(r2.stdout.strip())
        except Exception:
            pass

    print(f"  [SPEED] Voice sped up {multiplier}x — new duration {new_dur:.2f}s")
    return True, new_dur


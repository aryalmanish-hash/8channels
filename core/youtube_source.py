"""
core/youtube_source.py

Downloads CC-licensed background clips from YouTube using yt-dlp.
Then trims a random segment and returns the trimmed file.
Auto-deletes the full source video to save disk space.

Skips junk (tutorials, templates, too-short clips).
"""

from __future__ import annotations
import json
import random
import shutil
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = BASE / "assets" / "youtube_temp"
HISTORY_FILE = BASE / "assets" / "backgrounds" / "_youtube_history.json"
KEEP_HISTORY = 100  # remember last 100 YouTube video IDs to avoid repeats

YTDLP  = shutil.which("yt-dlp")
FFMPEG = shutil.which("ffmpeg")

# Junk keywords in titles — skip these results
JUNK_KEYWORDS = [
    # Tutorials / instructional
    "how to", "tutorial", "template", "guide", "review",
    "explained", "walkthrough", "settings", "setup",
    "how i", "why i", "reaction", "vs.", " vs ", "top 10",
    "compilation of", "best of", "unboxing",
    # Promotional / calls-to-action likely burned into video
    "subscribe", "like and subscribe", "smash the", "hit the bell",
    "check out my", "check out our", "please like", "please subscribe",
    "follow me on", "join my", "link in bio", "link in description",
    # Watermark / channel promo signals
    "channel intro", "outro", "sponsored by",
]

# Category search queries — from research
CATEGORY_QUERIES = {
    "gaming":              ["minecraft parkour vertical no copyright", "subway surfers gameplay vertical no copyright"],
    "gaming_minecraft":    ["minecraft parkour vertical no copyright"],
    "gaming_subway":       ["subway surfers no commentary vertical", "subway surfers gameplay vertical no copyright"],
    "gaming_gta":          ["gta 5 gameplay vertical no copyright"],
    "gaming_racing":       ["asphalt racing vertical no copyright"],
    "gaming_roblox":       ["roblox parkour vertical no copyright"],
    "gameplay":            ["minecraft parkour vertical no copyright", "subway surfers gameplay vertical no copyright"],
    "asmr_crafts":         ["soap cutting asmr vertical no copyright", "kinetic sand cutting vertical no copyright"],
    "asmr_food":           ["food asmr vertical no copyright", "cake decorating vertical no copyright"],
    "asmr_cleaning":       ["power washing satisfying vertical", "cleaning restoration vertical"],
    "satisfying":          ["oddly satisfying vertical no copyright", "satisfying compilation vertical"],
    "satisfying_hydraulic":["hydraulic press crushing vertical", "hydraulic press satisfying vertical"],
    "industrial":          ["cnc machine vertical no copyright", "laser cutting vertical no copyright"],
    "fpv_drone":           ["fpv drone cinematic vertical no copyright", "aerial drone vertical no copyright"],
    "nature_scenic":       ["nature timelapse vertical no copyright", "mountain scenic vertical no copyright"],
    "ocean_waves":         ["ocean waves vertical no copyright"],
    "city_night":          ["city night driving vertical no copyright", "cyberpunk city vertical no copyright"],
    "dark":                ["dark cinematic vertical no copyright"],
}


# ── History tracking (avoid downloading same video twice) ──────────────────

def _load_history():
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_history(hist):
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(json.dumps(hist[-KEEP_HISTORY*3:], indent=2), encoding="utf-8")
    except Exception:
        pass


def _mark_used(video_id):
    hist = _load_history()
    hist.append({"id": video_id, "ts": time.time()})
    _save_history(hist)


def _recently_used_ids():
    hist = _load_history()
    return set(item["id"] for item in hist[-KEEP_HISTORY:])


# ── Search YouTube for CC videos ────────────────────────────────────────────

# Uploaders known to burn subscribe text / watermarks into their vertical videos
NOISY_UPLOADERS = [
    "vertical satisfying video",
    "no copyright videos",  # generic — often heavily branded
]


def _is_junk(title, uploader=""):
    t = (title or "").lower()
    u = (uploader or "").lower()
    for kw in JUNK_KEYWORDS:
        if kw in t:
            return True
    # Also reject if uploader is a known noisy channel
    for noisy in NOISY_UPLOADERS:
        if noisy in u:
            return True
    return False


def _search_youtube_cc(query, max_results=10):
    """
    Search YouTube for CC-licensed videos matching query.
    Returns list of dicts: {id, uploader, duration, title}
    """
    if not YTDLP:
        return []
    try:
        cmd = [
            YTDLP,
            f"ytsearch{max_results}:{query}",
            "--match-filter", "license = 'Creative Commons Attribution license (reuse allowed)'",
            "--flat-playlist",
            "--print", "%(id)s|%(uploader).50s|%(duration)s|%(title).80s",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if r.returncode != 0:
            return []
        results = []
        for line in r.stdout.strip().splitlines():
            parts = line.split("|")
            if len(parts) < 4:
                continue
            vid, uploader, dur, title = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
            try:
                dur_f = float(dur) if dur and dur != "NA" else 0
            except ValueError:
                dur_f = 0
            results.append({
                "id": vid,
                "uploader": uploader,
                "duration": dur_f,
                "title": title,
            })
        return results
    except Exception as e:
        print(f"    [YT] Search error: {e}")
        return []


# ── Download + trim ─────────────────────────────────────────────────────────

def _download_video(video_id, dest_path):
    """Download YouTube video (best mp4 quality) to dest_path."""
    if not YTDLP:
        return False
    url = f"https://youtube.com/watch?v={video_id}"
    try:
        cmd = [
            YTDLP,
            url,
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",   # up to 1080p, best available
            "--merge-output-format", "mp4",
            "-o", str(dest_path),
            "--no-playlist",
            "--quiet",
            "--no-warnings",
            "--no-progress",
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return dest_path.exists() and dest_path.stat().st_size > 50000
    except Exception as e:
        print(f"    [YT] Download error: {e}")
        return False


def _trim_random_segment(src_path, dest_path, segment_duration, source_duration):
    """
    Trim a random `segment_duration` chunk out of the source video.
    Uses -c copy for speed (no re-encoding).
    Returns True on success.
    """
    if not FFMPEG:
        return False

    # Pick a random start point, leaving room for segment_duration
    max_start = max(0, source_duration - segment_duration - 2)
    start = random.uniform(0, max_start) if max_start > 0 else 0

    try:
        cmd = [
            FFMPEG, "-y",
            "-ss", str(start),
            "-i", str(src_path),
            "-t", str(segment_duration),
            "-c", "copy",  # fast, no re-encode
            "-avoid_negative_ts", "make_zero",
            str(dest_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if dest_path.exists() and dest_path.stat().st_size > 20000:
            return True
        # Fallback: re-encode if copy failed
        print(f"    [YT] Copy trim failed, trying re-encode")
        cmd2 = [
            FFMPEG, "-y",
            "-ss", str(start),
            "-i", str(src_path),
            "-t", str(segment_duration),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac",
            str(dest_path),
        ]
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
        return dest_path.exists() and dest_path.stat().st_size > 20000
    except Exception as e:
        print(f"    [YT] Trim error: {e}")
        return False


def download_youtube_clip(category, segment_duration=20, min_source_duration=60):
    """
    Main entry point.
    Search YouTube CC for `category`, pick a good result, download, trim, cleanup.
    Returns Path to the trimmed segment, or None on failure.

    - segment_duration: length of trimmed clip we want (default 20s)
    - min_source_duration: skip sources shorter than this
    """
    if not YTDLP:
        print("    [YT] yt-dlp not available")
        return None

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    queries = CATEGORY_QUERIES.get(category, [category])
    random.shuffle(queries)

    blocked = _recently_used_ids()

    for query in queries:
        print(f"    [YT] Search: {query}")
        results = _search_youtube_cc(query, max_results=10)
        if not results:
            print(f"    [YT] No results")
            continue

        # Filter: not junk, long enough, not recently used
        good = [
            r for r in results
            if r["duration"] >= min_source_duration
            and r["id"] not in blocked
            and not _is_junk(r["title"], r.get("uploader", ""))
        ]
        if not good:
            print(f"    [YT] All results filtered out (junk/too short/used)")
            continue

        random.shuffle(good)
        for candidate in good[:3]:  # try up to 3 candidates per query
            vid = candidate["id"]
            print(f"    [YT] Trying: {candidate['title'][:60]} by {candidate['uploader'][:30]}")

            src_path = DOWNLOAD_DIR / f"{category}_{vid}_src.mp4"
            _t = time.time()
            ok = _download_video(vid, src_path)
            print(f"    [YT] Download: {'OK' if ok else 'FAIL'} in {time.time()-_t:.1f}s")

            if not ok:
                if src_path.exists():
                    src_path.unlink()
                continue

            # Trim random segment
            trimmed = DOWNLOAD_DIR / f"{category}_{vid}_trim.mp4"
            trim_ok = _trim_random_segment(
                src_path, trimmed,
                segment_duration=segment_duration,
                source_duration=candidate["duration"],
            )

            # Delete the source video (save disk space)
            try:
                src_path.unlink()
                print(f"    [YT] Deleted source (freed {int(candidate['duration'])}s of video)")
            except Exception:
                pass

            if trim_ok:
                _mark_used(vid)
                size_kb = trimmed.stat().st_size // 1024
                print(f"    [YT] SUCCESS trimmed segment: {trimmed.name} ({size_kb} KB)")
                return trimmed
            else:
                if trimmed.exists():
                    trimmed.unlink()

    print(f"    [YT] All YouTube attempts failed for '{category}'")
    return None


def cleanup_youtube_temp():
    """Delete any leftover files in the youtube_temp folder."""
    if DOWNLOAD_DIR.exists():
        for f in DOWNLOAD_DIR.iterdir():
            try:
                f.unlink()
            except Exception:
                pass

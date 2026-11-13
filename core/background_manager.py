from __future__ import annotations
import json
import random
import time
import shutil
import subprocess
from pathlib import Path
import requests

BASE     = Path(__file__).resolve().parents[1]
ASSETS   = BASE / "assets" / "backgrounds"
HEADERS  = {"User-Agent": "Mozilla/5.0"}

# ── History tracking (avoid repeating same clip file across videos) ────────
HISTORY_FILE = ASSETS / "_used_clips_history.json"
KEEP_HISTORY = 25

# Random window tracking (avoid same segment of same file)
WINDOW_HISTORY_FILE = ASSETS / "_window_history.json"
WINDOW_GAP = 15  # seconds gap between segments from same file


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


def _mark_used(clip_name):
    hist = _load_history()
    hist.append({"name": clip_name, "ts": time.time()})
    _save_history(hist)


def _recently_used_names(n=KEEP_HISTORY):
    hist = _load_history()
    return set(item["name"] for item in hist[-n:])


def _load_window_history():
    try:
        if WINDOW_HISTORY_FILE.exists():
            return json.loads(WINDOW_HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_window_history(data):
    try:
        WINDOW_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        WINDOW_HISTORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _mark_window_used(clip_name, start_sec, end_sec):
    data = _load_window_history()
    if clip_name not in data:
        data[clip_name] = []
    data[clip_name].append({"start": start_sec, "end": end_sec, "ts": time.time()})
    # Trim to last 20 windows per file
    data[clip_name] = data[clip_name][-20:]
    _save_window_history(data)


def _pick_random_window(clip_name, clip_duration, segment_duration):
    """
    Pick a random start time that doesn't overlap with recently-used windows.
    Ensures WINDOW_GAP seconds between segments from same file.
    Returns (start_sec, end_sec).
    """
    max_start = max(0, clip_duration - segment_duration - 1)
    if max_start <= 0:
        return 0, min(clip_duration, segment_duration)

    used_windows = _load_window_history().get(clip_name, [])

    # Try up to 20 random starts, pick first one that doesnt overlap
    for _ in range(20):
        start = random.uniform(0, max_start)
        end = start + segment_duration
        overlap = False
        for w in used_windows:
            # Consider gap zone around each used window
            w_start = w["start"] - WINDOW_GAP
            w_end   = w["end"] + WINDOW_GAP
            if start < w_end and end > w_start:
                overlap = True
                break
        if not overlap:
            return start, end

    # If all attempts overlap, just pick a random start anyway
    start = random.uniform(0, max_start)
    return start, start + segment_duration


CATEGORY_QUERIES = {
    "gaming": [
        "mobile game vertical", "subway surfers vertical", "temple run mobile",
        "endless runner mobile", "parkour game vertical", "candy crush mobile game",
        "puzzle game mobile vertical", "video game screen vertical",
        "arcade game vertical", "gaming screen recording vertical",
        "mobile racing game vertical", "racing game vertical",
        "car racing gameplay vertical", "asphalt racing mobile",
        "adventure game vertical", "action game mobile vertical", "platform game vertical",
    ],
    "gameplay": [
        "mobile gameplay vertical", "arcade gameplay vertical",
        "racing gameplay vertical", "endless runner gameplay",
        "puzzle gameplay mobile", "action gameplay vertical",
        "adventure gameplay vertical", "platform gameplay vertical",
        "shooter gameplay vertical",
    ],
    "industrial": [
        "laser cutting metal machine sparks", "cnc machine cutting metal",
        "water jet cutting steel vertical", "hydraulic press crushing machine",
        "factory assembly line automated", "metal cutting sparks slow motion",
        "3d printing timelapse vertical", "plasma cutting metal sparks",
        "industrial robot arm factory", "wood cutting machine satisfying",
        "welding sparks slow motion", "manufacturing process vertical",
    ],
    "asmr_crafts": [
        "kinetic sand cutting satisfying asmr", "soap cutting satisfying asmr",
        "power washing dirty carpet satisfying", "satisfying cleaning restoration vertical",
        "epoxy resin art pouring vertical", "pottery making clay satisfying",
        "cake decorating satisfying vertical", "slime satisfying asmr vertical",
        "sand art satisfying vertical", "rug tufting satisfying vertical",
    ],
    "fpv_drone": [
        "fpv drone flying mountains vertical", "drone city night lights vertical",
        "rainy night city driving neon", "fpv drone forest vertical",
        "aerial city skyscraper vertical", "hyperlapse city night vertical",
        "tokyo night drive vertical", "new york city aerial vertical",
        "cyberpunk city neon lights vertical", "mountain drone aerial vertical",
    ],
    "satisfying": [
        "satisfying sand cutting vertical", "kinetic sand satisfying vertical",
        "satisfying soap cutting asmr", "satisfying crushing machine",
        "satisfying compilation vertical", "oddly satisfying vertical",
    ],
    "dark": [
        "abstract dark particles vertical", "dark neon lights abstract",
        "dark cinematic vertical", "black smoke slow motion",
    ],
}

CHANNEL_CATEGORIES = {
    "reddit_stories":      ["gaming", "industrial", "asmr_crafts", "fpv_drone"],
    "english_learning":    ["fpv_drone", "asmr_crafts"],
    "psychology":          ["fpv_drone", "asmr_crafts"],
    "dark_history":        ["industrial", "fpv_drone", "dark"],
    "ai_tools_automation": ["industrial", "gaming"],
    "quiz":                ["gaming", "asmr_crafts"],
    "facts":               ["fpv_drone", "asmr_crafts"],
    "sports_reviews":      ["gaming", "industrial"],
}


def _load_pexels_key():
    import yaml
    p = BASE / "config" / "global_settings.yaml"
    if p.exists():
        with open(p, "r") as f:
            return (yaml.safe_load(f) or {}).get("pexels_api_key", "")
    return ""


def _get_duration(path):
    ff = shutil.which("ffprobe")
    if not ff:
        return 0.0
    try:
        r = subprocess.run(
            [ff, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=10
        )
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _trim_segment(src_path, dest_path, start_sec, duration):
    """Trim a segment from a source clip using ffmpeg. Fast copy first, re-encode if fails."""
    ff = shutil.which("ffmpeg")
    if not ff:
        return False
    try:
        cmd = [
            ff, "-y",
            "-ss", str(start_sec),
            "-i", str(src_path),
            "-t", str(duration),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            str(dest_path),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if dest_path.exists() and dest_path.stat().st_size > 20000:
            return True
        # Fallback re-encode
        cmd2 = [
            ff, "-y",
            "-ss", str(start_sec),
            "-i", str(src_path),
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac",
            str(dest_path),
        ]
        subprocess.run(cmd2, capture_output=True, text=True, timeout=90)
        return dest_path.exists() and dest_path.stat().st_size > 20000
    except Exception:
        return False


def _search_pexels(query, api_key, per_page=15, min_dur=15):
    url = "https://api.pexels.com/videos/search"
    params = {"query": query, "per_page": per_page, "orientation": "portrait"}
    try:
        r = requests.get(url, headers={"Authorization": api_key}, params=params, timeout=15)
        videos = r.json().get("videos", [])
        return [v for v in videos if v.get("duration", 0) >= min_dur]
    except Exception as e:
        print(f"    Pexels error: {e}")
        return []


def _best_file(video):
    files = video.get("video_files", [])
    portrait = [f for f in files if f.get("file_type") == "video/mp4" and f.get("height", 0) >= 720]
    if not portrait:
        portrait = [f for f in files if f.get("file_type") == "video/mp4"]
    if not portrait:
        return None
    portrait.sort(key=lambda x: x.get("height", 0), reverse=True)
    for f in portrait:
        if f.get("height", 0) <= 1080:
            return f
    return portrait[-1]


def download_pexels_fresh(category, min_dur=15, blocked_names=None):
    """Download a fresh Pexels clip (skips names in blocked_names)."""
    api_key = _load_pexels_key()
    if not api_key:
        return None
    blocked_names = blocked_names or set()
    out = ASSETS / category
    out.mkdir(parents=True, exist_ok=True)
    queries = CATEGORY_QUERIES.get(category, [category])
    random.shuffle(queries)

    for query in queries[:6]:
        videos = _search_pexels(query, api_key, per_page=15, min_dur=min_dur)
        if not videos:
            continue
        random.shuffle(videos)
        for video in videos:
            vf = _best_file(video)
            if not vf:
                continue
            url = vf.get("link", "")
            vid = video.get("id", "x")
            dur = int(video.get("duration", 0))
            name = f"{category}_{vid}_{dur}s.mp4"
            if name in blocked_names:
                continue
            dest = out / name
            if dest.exists():
                return dest
            try:
                print(f"    [PEXELS] Downloading: '{query}' ({dur}s)")
                r = requests.get(url, timeout=120, stream=True)
                with open(dest, "wb") as fp:
                    for chunk in r.iter_content(8192):
                        fp.write(chunk)
                if dest.stat().st_size > 100000:
                    return dest
                dest.unlink()
            except Exception as e:
                print(f"    [PEXELS] Download failed: {e}")
                if dest.exists():
                    dest.unlink()
        time.sleep(0.3)
    return None


# Backward-compat wrapper
def download_clip(category, min_dur=15, output_dir=None):
    return download_pexels_fresh(category, min_dur=min_dur, blocked_names=_recently_used_names())


def get_clips_for_video(channel_id, video_duration, scene_duration=18, preferred_categories=None):
    """
    Get multiple background clips with priority:
      1. YouTube CC fresh download (with auto-trim to scene_duration)
      2. Pexels fresh download
      3. Cached clip with RANDOM WINDOW (start time varies each use)
      4. Any cached fallback
    Marks each returned clip name as used so it wont be picked in next N videos.
    Random window: each cached clip is trimmed at a different random start each time.
    """
    if preferred_categories:
        categories = list(preferred_categories)
    else:
        categories = list(CHANNEL_CATEGORIES.get(channel_id, ["gaming", "asmr_crafts"]))
    random.shuffle(categories)

    n_scenes = max(1, int(video_duration / scene_duration) + 1)
    print(f"  Need {n_scenes} scene clips for {video_duration:.0f}s video")

    blocked_recent = _recently_used_names()
    print(f"  Recently used (blocked): {len(blocked_recent)} clip names")

    # Lazy import — YouTube module may not always be present/working
    try:
        from core.youtube_source import download_youtube_clip
        yt_available = True
    except ImportError:
        yt_available = False
        print("  [WARN] YouTube source module not available")

    clips = []
    used_this_video = set()

    for i in range(n_scenes):
        cat = categories[i % len(categories)]
        cat_dir = ASSETS / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        blocked_all = blocked_recent | used_this_video
        found = None

        # ── STEP 1: Try YouTube CC first ───────────────────────────────
        if yt_available:
            print(f"  Scene {i+1}: trying YouTube CC ({cat})...")
            try:
                yt_clip = download_youtube_clip(cat, segment_duration=scene_duration + 2)
                if yt_clip and yt_clip.exists():
                    # Move to a permanent-ish location for compose_video to use
                    dest_name = f"yt_{cat}_{int(time.time())}.mp4"
                    dest_path = cat_dir / dest_name
                    shutil.move(str(yt_clip), str(dest_path))
                    found = dest_path
                    print(f"    Got YouTube: {found.name}")
            except Exception as e:
                print(f"    YouTube error: {e}")

        # ── STEP 2: Try Pexels fresh download ──────────────────────────
        if not found:
            print(f"    YouTube failed - trying Pexels fresh download...")
            try:
                fresh = download_pexels_fresh(cat, min_dur=scene_duration, blocked_names=blocked_all)
                if fresh and fresh.name not in blocked_all:
                    found = fresh
                    print(f"    Got Pexels FRESH: {found.name}")
            except Exception as e:
                print(f"    Pexels error: {e}")

        # ── STEP 3: Cache — use random window from unused cached clip ──
        if not found:
            print(f"    Fresh sources failed - checking cache with RANDOM WINDOW...")
            cache_clips = [c for c in cat_dir.glob("*.mp4") if c.name not in blocked_all]
            for clip in cache_clips:
                dur = _get_duration(clip)
                if dur >= scene_duration + 2:
                    # Pick random window from this clip
                    start, end = _pick_random_window(clip.name, dur, scene_duration)
                    print(f"    Random window from {clip.name}: {start:.1f}s-{end:.1f}s")
                    # Trim to a temp scene file
                    scene_temp = cat_dir / f"_scene_{int(time.time()*1000)}_{clip.stem}.mp4"
                    if _trim_segment(clip, scene_temp, start, scene_duration):
                        _mark_window_used(clip.name, start, end)
                        found = scene_temp
                        print(f"    Trimmed segment: {scene_temp.name}")
                        break

        # ── STEP 4: Cross-category cache fallback ──────────────────────
        if not found:
            for alt_cat in categories:
                if alt_cat == cat:
                    continue
                alt_dir = ASSETS / alt_cat
                if not alt_dir.exists():
                    continue
                alt_clips = [c for c in alt_dir.glob("*.mp4") if c.name not in blocked_all]
                for clip in alt_clips:
                    dur = _get_duration(clip)
                    if dur >= scene_duration + 2:
                        start, end = _pick_random_window(clip.name, dur, scene_duration)
                        scene_temp = alt_dir / f"_scene_{int(time.time()*1000)}_{clip.stem}.mp4"
                        if _trim_segment(clip, scene_temp, start, scene_duration):
                            _mark_window_used(clip.name, start, end)
                            found = scene_temp
                            print(f"    Cross-category ({alt_cat}) window: {clip.name} @ {start:.1f}s")
                            break
                if found:
                    break

        # ── STEP 5: LAST RESORT — reuse any clip whole ─────────────────
        if not found:
            print(f"    All fresh options exhausted - reusing old clip")
            all_cached = list(cat_dir.glob("*.mp4"))
            for clip in all_cached:
                if clip.name in used_this_video or clip.name.startswith("_scene_"):
                    continue
                dur = _get_duration(clip)
                if dur >= scene_duration:
                    found = clip
                    print(f"    Reusing: {found.name}")
                    break

        if found:
            used_this_video.add(found.name)
            _mark_used(found.name)
            clips.append(found)
        else:
            print(f"  WARNING: could not get clip for scene {i+1}")

    return clips


def cleanup_scene_temps():
    """Delete all _scene_*.mp4 temp files created by random windowing."""
    if not ASSETS.exists():
        return
    for cat_dir in ASSETS.iterdir():
        if cat_dir.is_dir():
            for f in cat_dir.glob("_scene_*.mp4"):
                try:
                    f.unlink()
                except Exception:
                    pass


def cleanup_all_youtube():
    """Delete downloaded YouTube clips (yt_ prefix)."""
    if not ASSETS.exists():
        return
    for cat_dir in ASSETS.iterdir():
        if cat_dir.is_dir():
            for f in cat_dir.glob("yt_*.mp4"):
                try:
                    f.unlink()
                except Exception:
                    pass


def get_background_for_channel(channel_id):
    clips = get_clips_for_video(channel_id, video_duration=60)
    return clips[0] if clips else None


def get_background_for_video(channel_id, video_duration=60):
    clips = get_clips_for_video(channel_id, video_duration)
    return clips[0] if clips else None


def list_available_backgrounds():
    result = {}
    if not ASSETS.exists():
        return result
    for cat_dir in ASSETS.iterdir():
        if cat_dir.is_dir():
            clips = []
            for c in cat_dir.glob("*.mp4"):
                if c.name.startswith("_scene_"):
                    continue  # skip temp
                clips.append({"name": c.name, "duration": _get_duration(c)})
            result[cat_dir.name] = clips
    return result

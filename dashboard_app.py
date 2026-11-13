"""dashboard_app.py - Flask dashboard for 8-Channel Content Factory."""

from __future__ import annotations
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for

from core.bootstrap import bootstrap
from core.database import connect
from core.config_loader import load_all_channel_configs
from core.review_manager import approve_video
from core.posting_tracker import set_platform_status
from core.cli_helpers import (
    folder_size, format_size, rclone_available,
    drive_upload_video, drive_upload_thumbnail,
    drive_list_channel, drive_delete_video,
    cleanup_workspace_for_video, cleanup_old_workspaces,
)

app = Flask(__name__,
            template_folder=str(PROJECT_ROOT / "templates"),
            static_folder=str(PROJECT_ROOT / "static"))

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
STATUS_FILE   = DATA_DIR / "posting_status.json"
SCHEDULE_FILE = DATA_DIR / "schedule.json"
HISTORY_FILE  = DATA_DIR / "history.json"
PLATFORMS = ["youtube_shorts", "tiktok", "instagram_reels", "facebook_reels"]

CHANNEL_COLORS = {
    "reddit_stories":      "#FF4500",
    "english_learning":    "#3B82F6",
    "psychology":          "#A855F7",
    "dark_history":        "#7F1D1D",
    "ai_tools_automation": "#06B6D4",
    "quiz":                "#EAB308",
    "facts":               "#10B981",
    "sports_reviews":      "#EF4444",
}


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_stats():
    configs = load_all_channel_configs()
    stats = {}
    with connect() as conn:
        for cid in configs.keys():
            total    = conn.execute("SELECT COUNT(*) FROM videos WHERE channel_id=?", (cid,)).fetchone()[0]
            review   = conn.execute("SELECT COUNT(*) FROM videos WHERE channel_id=? AND status=?", (cid, "needs_review")).fetchone()[0]
            approved = conn.execute("SELECT COUNT(*) FROM videos WHERE channel_id=? AND status=?", (cid, "approved_for_upload")).fetchone()[0]
            posted   = conn.execute("SELECT COUNT(*) FROM videos WHERE channel_id=? AND status=?", (cid, "posted")).fetchone()[0]
            stats[cid] = {
                "name":     configs[cid].get("channel_name", cid),
                "color":    CHANNEL_COLORS.get(cid, "#888"),
                "total":    total,
                "review":   review,
                "approved": approved,
                "posted":   posted,
            }
    return stats


def get_recent_videos(limit=20, status_filter=None):
    with connect() as conn:
        if status_filter:
            rows = conn.execute(
                "SELECT video_id, channel_id, title, status, created_at, final_video_path, thumbnail_path "
                "FROM videos WHERE status=? ORDER BY created_at DESC LIMIT ?",
                (status_filter, limit)).fetchall()
        else:
            rows = conn.execute(
                "SELECT video_id, channel_id, title, status, created_at, final_video_path, thumbnail_path "
                "FROM videos ORDER BY created_at DESC LIMIT ?",
                (limit,)).fetchall()
    videos = []
    for r in rows:
        videos.append({
            "video_id":   r[0],
            "channel_id": r[1],
            "title":      r[2] or "(no title)",
            "status":     r[3],
            "created":    r[4],
            "video_path": r[5] or "",
            "thumb_path": r[6] or "",
            "color":      CHANNEL_COLORS.get(r[1], "#888"),
        })
    return videos


# ───────────────────────────────────────────────────────────────────
# PAGE ROUTES
# ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    stats   = get_stats()
    recent  = get_recent_videos(limit=10)
    totals  = {
        "channels": len(stats),
        "videos":   sum(s["total"] for s in stats.values()),
        "review":   sum(s["review"] for s in stats.values()),
        "posted":   sum(s["posted"] for s in stats.values()),
    }
    return render_template("dashboard.html",
                           page="dashboard",
                           stats=stats,
                           recent=recent,
                           totals=totals)


@app.route("/review")
def review_page():
    pending = get_recent_videos(limit=50, status_filter="needs_review")
    return render_template("review.html",
                           page="review",
                           videos=pending)


@app.route("/channels")
def channels_page():
    configs = load_all_channel_configs()
    channels = []
    for cid, cfg in configs.items():
        channels.append({
            "id":    cid,
            "name":  cfg.get("channel_name", cid),
            "color": CHANNEL_COLORS.get(cid, "#888"),
        })
    return render_template("channels.html",
                           page="channels",
                           channels=channels)


# ───────────────────────────────────────────────────────────────────
# API ROUTES
# ───────────────────────────────────────────────────────────────────
@app.route("/api/approve", methods=["POST"])
def api_approve():
    video_id = request.json.get("video_id", "").strip()
    if not video_id:
        return jsonify({"ok": False, "error": "Missing video_id"}), 400
    try:
        approve_video(video_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/reject", methods=["POST"])
def api_reject():
    video_id = request.json.get("video_id", "").strip()
    if not video_id:
        return jsonify({"ok": False, "error": "Missing video_id"}), 400
    try:
        with connect() as conn:
            conn.execute("UPDATE videos SET status=? WHERE video_id=?", ("rejected", video_id))
            conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/generate", methods=["POST"])
def api_generate():
    channel_id = request.json.get("channel_id", "").strip()
    limit      = int(request.json.get("limit", 1))
    if not channel_id:
        return jsonify({"ok": False, "error": "Missing channel_id"}), 400
    try:
        cmd = ["cmd", "/c", "start", "cmd", "/k",
               sys.executable, "-c",
               f"from core.workflow import create_channel_batch; create_channel_batch(\"{channel_id}\", {limit})"]
        subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))
        return jsonify({"ok": True, "message": f"Launching generator for {channel_id}..."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/open_folder", methods=["POST"])
def api_open_folder():
    video_id   = request.json.get("video_id", "").strip()
    channel_id = request.json.get("channel_id", "").strip()
    if not video_id or not channel_id:
        return jsonify({"ok": False, "error": "Missing params"}), 400
    ws = PROJECT_ROOT / "channels" / channel_id / "workspace"
    if not ws.exists():
        return jsonify({"ok": False, "error": "Channel workspace missing"}), 404
    for f in ws.iterdir():
        if video_id in f.name:
            subprocess.Popen(["explorer", str(f.resolve())])
            return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Folder not found"}), 404


# ───────────────────────────────────────────────────────────────────
# FILE SERVING (videos, thumbnails)
# ───────────────────────────────────────────────────────────────────
@app.route("/file/<path:filepath>")
def serve_file(filepath):
    full = PROJECT_ROOT / filepath
    if not full.exists():
        return f"Not found: {filepath}", 404
    return send_from_directory(PROJECT_ROOT, filepath)



@app.route("/upload")
def upload_page():
    videos = get_recent_videos(limit=50)
    # Only show approved or posted (ready for upload)
    ready = [v for v in videos if v["status"] in ("approved_for_upload", "needs_review", "posted")]
    status_data = load_json(STATUS_FILE, {})
    # Attach platform status to each video
    for v in ready:
        v["platforms"] = status_data.get(v["video_id"], {})
    return render_template("upload.html",
                           page="upload",
                           videos=ready,
                           platforms=PLATFORMS)


@app.route("/history")
def history_page():
    history = load_json(HISTORY_FILE, [])
    # Most recent first
    history = sorted(history, key=lambda h: h.get("time", ""), reverse=True)[:100]
    return render_template("history.html",
                           page="history",
                           history=history)


@app.route("/schedule")
def schedule_page():
    schedule = load_json(SCHEDULE_FILE, [])
    schedule = sorted(schedule, key=lambda s: s.get("when", ""))
    videos = get_recent_videos(limit=30)
    return render_template("schedule.html",
                           page="schedule",
                           schedule=schedule,
                           videos=videos)


@app.route("/cleanup")
def cleanup_page():
    configs = load_all_channel_configs()
    channel_sizes = []
    total_bytes = 0
    for cid in configs.keys():
        ws = PROJECT_ROOT / "channels" / cid / "workspace"
        size = folder_size(ws)
        total_bytes += size
        channel_sizes.append({
            "id":     cid,
            "name":   configs[cid].get("channel_name", cid),
            "color":  CHANNEL_COLORS.get(cid, "#888"),
            "size":   format_size(size),
            "bytes":  size,
        })
    return render_template("cleanup.html",
                           page="cleanup",
                           channels=channel_sizes,
                           total_size=format_size(total_bytes))


@app.route("/guide")
def guide_page():
    return render_template("guide.html", page="guide")


# ───────────────────────────────────────────────────────────────────
# UPLOAD / STATUS / HISTORY API
# ───────────────────────────────────────────────────────────────────
@app.route("/api/mark_posted", methods=["POST"])
def api_mark_posted():
    video_id = request.json.get("video_id", "").strip()
    platform = request.json.get("platform", "").strip()
    posted   = bool(request.json.get("posted", True))
    if not video_id or not platform:
        return jsonify({"ok": False, "error": "Missing params"}), 400
    try:
        # Update JSON file
        data = load_json(STATUS_FILE, {})
        if video_id not in data:
            data[video_id] = {}
        data[video_id][platform] = posted
        save_json(STATUS_FILE, data)

        # Update SQLite too
        try:
            set_platform_status(video_id, platform, "posted" if posted else "pending")
        except Exception:
            pass

        # Add to history if posted
        if posted:
            hist = load_json(HISTORY_FILE, [])
            hist.append({
                "video_id": video_id,
                "platform": platform,
                "time":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            save_json(HISTORY_FILE, hist)

        # Check if all platforms posted -> update video status
        if all(data[video_id].get(p, False) for p in PLATFORMS):
            with connect() as conn:
                conn.execute("UPDATE videos SET status=? WHERE video_id=?", ("posted", video_id))
                conn.commit()

        return jsonify({"ok": True, "data": data[video_id]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/schedule/add", methods=["POST"])
def api_schedule_add():
    video_id = request.json.get("video_id", "").strip()
    when     = request.json.get("when", "").strip()
    note     = request.json.get("note", "").strip()
    if not video_id or not when:
        return jsonify({"ok": False, "error": "Missing fields"}), 400
    schedule = load_json(SCHEDULE_FILE, [])
    schedule.append({
        "video_id": video_id,
        "when":     when,
        "note":     note,
        "added":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_json(SCHEDULE_FILE, schedule)
    return jsonify({"ok": True})


@app.route("/api/schedule/delete", methods=["POST"])
def api_schedule_delete():
    idx = request.json.get("index", -1)
    schedule = load_json(SCHEDULE_FILE, [])
    if 0 <= idx < len(schedule):
        schedule.pop(idx)
        save_json(SCHEDULE_FILE, schedule)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid index"}), 400


# ───────────────────────────────────────────────────────────────────
# CLEANUP API
# ───────────────────────────────────────────────────────────────────
@app.route("/api/cleanup_channel", methods=["POST"])
def api_cleanup_channel():
    channel_id = request.json.get("channel_id", "").strip()
    keep       = int(request.json.get("keep", 3))
    if not channel_id:
        return jsonify({"ok": False, "error": "Missing channel_id"}), 400
    try:
        count, freed = cleanup_old_workspaces(channel_id, keep)
        return jsonify({"ok": True, "deleted": count, "freed": format_size(freed)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ───────────────────────────────────────────────────────────────────
# DRIVE API
# ───────────────────────────────────────────────────────────────────
@app.route("/api/drive_upload", methods=["POST"])
def api_drive_upload():
    video_id = request.json.get("video_id", "").strip()
    if not video_id:
        return jsonify({"ok": False, "error": "Missing video_id"}), 400
    if not rclone_available():
        return jsonify({"ok": False, "error": "rclone not installed"}), 500
    try:
        with connect() as conn:
            row = conn.execute(
                "SELECT channel_id, thumbnail_path FROM videos WHERE video_id=?",
                (video_id,)
            ).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Video not found"}), 404
        cid, thumb = row
        # Upload thumbnail only (small + fast for phone access)
        if thumb and Path(thumb).exists():
            drive_upload_thumbnail(Path(thumb), cid, video_id)
        # Upload workspace folder
        ws = PROJECT_ROOT / "channels" / cid / "workspace"
        folder = None
        for f in ws.iterdir():
            if video_id in f.name:
                folder = f
                break
        if folder:
            drive_upload_video(folder, video_id, cid)
            return jsonify({"ok": True, "message": "Uploaded to Drive"})
        return jsonify({"ok": False, "error": "Workspace folder not found"}), 404
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    bootstrap()
    print()
    print("=" * 60)
    print("  8-CHANNEL CONTENT FACTORY - DASHBOARD")
    print("=" * 60)
    print()
    print("  Desktop : http://localhost:5000")
    print("  Mobile  : http://<your-pc-ip>:5000")
    print()
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)

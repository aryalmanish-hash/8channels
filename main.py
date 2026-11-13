"""main.py — CLI for the 8-Channel Content Factory (WC Klips style)."""

from __future__ import annotations
import sys
from pathlib import Path

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parent
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from core.bootstrap import bootstrap
from core.config_loader import load_all_channel_configs
from core.database import connect
from core.workflow import create_channel_batch
from core.review_manager import approve_video
from core.posting_tracker import set_platform_status
from core.cli_helpers import (
    ok, info, warn, err, header, divider, format_size, folder_size,
    rclone_available, drive_upload_video, drive_upload_thumbnail,
    drive_list_channel, drive_delete_video,
    cleanup_workspace_for_video, cleanup_old_workspaces,
)

PLATFORMS = ["youtube_shorts", "tiktok", "instagram_reels", "facebook_reels"]


def pick_channel():
    configs = load_all_channel_configs()
    channels = list(configs.items())
    print()
    for i, (cid, cfg) in enumerate(channels, 1):
        name = cfg.get("channel_name", cid)
        print(f"  {i}. {name}  ({cid})")
    print("  0. Back")
    choice = input("\nChoose channel: ").strip()
    if choice == "0":
        return None
    if not choice.isdigit() or not (1 <= int(choice) <= len(channels)):
        err("Invalid choice")
        return None
    return channels[int(choice) - 1][0]


def pick_video(status_filter=None):
    with connect() as conn:
        if status_filter:
            rows = conn.execute(
                "SELECT video_id, channel_id, title, status, created_at FROM videos WHERE status=? ORDER BY created_at DESC LIMIT 30",
                (status_filter,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT video_id, channel_id, title, status, created_at FROM videos ORDER BY created_at DESC LIMIT 30").fetchall()
    if not rows:
        warn("No videos found")
        return None
    print()
    for i, r in enumerate(rows, 1):
        title = (r[2] or "(no title)")[:50]
        print(f"  {i:2}. [{r[3]:15}] {r[1]:20} {title}")
    print("   0. Back")
    choice = input("\nChoose video: ").strip()
    if choice == "0":
        return None
    if not choice.isdigit() or not (1 <= int(choice) <= len(rows)):
        err("Invalid choice")
        return None
    return rows[int(choice) - 1][0]


def action_generate_one():
    header("GENERATE ONE VIDEO")
    cid = pick_channel()
    if not cid:
        return

    import time
    from datetime import datetime as _dt

    _start = time.time()
    _start_str = _dt.now().strftime("%H:%M:%S")

    print()
    print("=" * 60)
    print(f"  GENERATING VIDEO - {cid}")
    print("=" * 60)
    print(f"  Start: {_start_str}")
    print()

    try:
        results = create_channel_batch(cid, 1)
        _end = time.time()
        _end_str = _dt.now().strftime("%H:%M:%S")
        _elapsed = _end - _start
        _mins = int(_elapsed // 60)
        _secs = int(_elapsed % 60)

        print()
        print("=" * 60)
        if results:
            for vid, folder in results:
                print(f"  DONE: {vid}")
                # Show final published folder (not workspace)
                _out = Path(f"channels/{cid}/output/{vid}")
                if _out.exists():
                    print(f"  Location: {_out}")
        else:
            warn("No video created")
        print("=" * 60)
        info(f"Start   : {_start_str}")
        info(f"End     : {_end_str}")
        info(f"Elapsed : {_mins} min {_secs} sec")
        print("=" * 60)
    except Exception as e:
        _end = time.time()
        _elapsed = _end - _start
        err(f"Generation failed after {int(_elapsed)}s: {e}")


def action_generate_batch():
    header("GENERATE BATCH (LEAVE PC MODE)")
    info("Will generate videos for selected channels in sequence.")
    info("You can leave your PC.\n")
    configs = load_all_channel_configs()
    channels = list(configs.keys())
    print("Select channels (comma separated, or all):")
    for i, cid in enumerate(channels, 1):
        name = configs[cid].get("channel_name", cid)
        print(f"  {i}. {name} ({cid})")
    sel = input("\nChannels: ").strip().lower()
    if sel == "all":
        selected = channels
    else:
        try:
            nums = [int(x.strip()) for x in sel.split(",") if x.strip().isdigit()]
            selected = [channels[n-1] for n in nums if 1 <= n <= len(channels)]
        except Exception:
            err("Invalid selection")
            return
    if not selected:
        err("No channels selected")
        return
    limit_str = input("Videos per channel [default 1]: ").strip() or "1"
    if not limit_str.isdigit():
        err("Invalid number")
        return
    limit = int(limit_str)
    info(f"\nBatch: {len(selected)} channels x {limit} videos = {len(selected)*limit} total")
    info("Leave PC. Ctrl+C to abort.\n")
    total_done = 0
    for cid in selected:
        header(f"CHANNEL: {cid}")
        try:
            results = create_channel_batch(cid, limit)
            total_done += len(results)
            for vid, folder in results:
                ok(f"Done: {vid}")
        except Exception as e:
            err(f"Channel {cid} failed: {e}")
    print()
    ok(f"BATCH COMPLETE: {total_done} videos created")


def action_review():
    header("REVIEW PENDING VIDEOS")
    video_id = pick_video(status_filter="needs_review")
    if not video_id:
        return
    with connect() as conn:
        row = conn.execute(
            "SELECT channel_id, title, final_video_path, thumbnail_path FROM videos WHERE video_id=?",
            (video_id,)).fetchone()
    if not row:
        err("Video not found")
        return
    channel_id, title, final_path, thumb_path = row
    print()
    info(f"Video    : {video_id}")
    info(f"Channel  : {channel_id}")
    info(f"Title    : {title}")
    info(f"Video    : {final_path}")
    info(f"Thumb    : {thumb_path}")
    print()
    print("  1. Approve")
    print("  2. Reject")
    print("  3. Open folder in explorer")
    print("  0. Back")
    choice = input("\nAction: ").strip()
    if choice == "1":
        approve_video(video_id)
        ok(f"Approved: {video_id}")
    elif choice == "2":
        with connect() as conn:
            conn.execute("UPDATE videos SET status=? WHERE video_id=?", ("rejected", video_id))
            conn.commit()
        warn(f"Rejected: {video_id}")
    elif choice == "3":
        import subprocess
        ws = Path(f"channels/{channel_id}/workspace")
        for f in ws.iterdir():
            if video_id in f.name:
                subprocess.run(["explorer", str(f.resolve())])
                ok("Opened in explorer")
                break


def action_mark_uploaded():
    header("MARK UPLOADED PER PLATFORM")
    video_id = pick_video()
    if not video_id:
        return
    with connect() as conn:
        row = conn.execute("SELECT status, title FROM videos WHERE video_id=?", (video_id,)).fetchone()
    if not row:
        err("Video not found")
        return
    status, title = row
    if status not in ("approved_for_upload", "posted"):
        warn(f"Status is {status} - usually you review/approve first.")
        cont = input("Continue anyway? (y/N): ").strip().lower()
        if cont != "y":
            return
    print(f"\nVideo: {title}")
    print("Platforms:")
    for i, p in enumerate(PLATFORMS, 1):
        print(f"  {i}. {p}")
    print("  0. Back")
    choice = input("\nPlatform: ").strip()
    if choice == "0":
        return
    if not choice.isdigit() or not (1 <= int(choice) <= len(PLATFORMS)):
        err("Invalid")
        return
    platform = PLATFORMS[int(choice) - 1]
    set_platform_status(video_id, platform, "posted")
    ok(f"Marked {platform} as posted for {video_id}")


def action_drive():
    header("GOOGLE DRIVE")
    if not rclone_available():
        err("rclone not installed or not in PATH")
        return
    print("\n  1. Upload video folder to Drive")
    print("  2. Upload thumbnail only (for phone)")
    print("  3. List Drive contents for a channel")
    print("  4. Delete video from Drive")
    print("  0. Back")
    choice = input("\nAction: ").strip()
    if choice == "1":
        video_id = pick_video()
        if not video_id:
            return
        with connect() as conn:
            row = conn.execute("SELECT channel_id FROM videos WHERE video_id=?", (video_id,)).fetchone()
        if not row:
            err("Not found")
            return
        cid = row[0]
        ws_root = Path(f"channels/{cid}/workspace")
        folder = None
        for f in ws_root.iterdir():
            if video_id in f.name:
                folder = f
                break
        if not folder:
            err(f"Workspace folder not found for {video_id}")
            return
        drive_upload_video(folder, video_id, cid)
    elif choice == "2":
        video_id = pick_video()
        if not video_id:
            return
        with connect() as conn:
            row = conn.execute("SELECT channel_id, thumbnail_path FROM videos WHERE video_id=?", (video_id,)).fetchone()
        if not row:
            err("Not found")
            return
        cid, thumb = row
        if not thumb or not Path(thumb).exists():
            err(f"Thumbnail missing: {thumb}")
            return
        drive_upload_thumbnail(Path(thumb), cid, video_id)
    elif choice == "3":
        cid = pick_channel()
        if not cid:
            return
        success, items = drive_list_channel(cid)
        if success:
            ok(f"Drive has {len(items)} videos for {cid}:")
            for it in items:
                print(f"   - {it}")
        else:
            err("Drive list failed")
    elif choice == "4":
        cid = pick_channel()
        if not cid:
            return
        success, items = drive_list_channel(cid)
        if not items:
            warn("No videos on Drive for this channel")
            return
        for i, it in enumerate(items, 1):
            print(f"  {i}. {it}")
        sel = input("\nWhich to delete (0=back): ").strip()
        if not sel.isdigit() or sel == "0":
            return
        idx = int(sel)
        if not (1 <= idx <= len(items)):
            err("Invalid")
            return
        confirm = input(f"Delete {items[idx-1]} from Drive? (y/N): ").strip().lower()
        if confirm == "y":
            drive_delete_video(cid, items[idx-1])


def action_cleanup():
    header("CLEANUP")
    print("\n  1. Clean old workspaces for a channel (keep 3)")
    print("  2. Delete specific video workspace")
    print("  3. Show storage usage per channel")
    print("  0. Back")
    choice = input("\nAction: ").strip()
    if choice == "1":
        cid = pick_channel()
        if not cid:
            return
        keep = input("Keep most recent N [default 3]: ").strip() or "3"
        if not keep.isdigit():
            err("Invalid")
            return
        count, freed = cleanup_old_workspaces(cid, int(keep))
        ok(f"Deleted {count} workspaces, freed {format_size(freed)}")
    elif choice == "2":
        video_id = pick_video()
        if not video_id:
            return
        with connect() as conn:
            row = conn.execute("SELECT channel_id FROM videos WHERE video_id=?", (video_id,)).fetchone()
        if not row:
            err("Not found")
            return
        freed = cleanup_workspace_for_video(row[0], video_id)
        ok(f"Freed {format_size(freed)}")
    elif choice == "3":
        configs = load_all_channel_configs()
        print()
        total = 0
        for cid in configs.keys():
            ws = Path(f"channels/{cid}/workspace")
            size = folder_size(ws)
            total += size
            print(f"  {cid:25} {format_size(size):>12}")
        divider("-", 50)
        print(f"  TOTAL                     {format_size(total):>12}")


def action_stats():
    header("STATS & RECENT ACTIVITY")
    with connect() as conn:
        configs = load_all_channel_configs()
        print()
        print(f"  Channel                   Total Review Approved Posted")
        divider("-", 60)
        for cid in configs.keys():
            total    = conn.execute("SELECT COUNT(*) FROM videos WHERE channel_id=?", (cid,)).fetchone()[0]
            review   = conn.execute("SELECT COUNT(*) FROM videos WHERE channel_id=? AND status=?", (cid, "needs_review")).fetchone()[0]
            approved = conn.execute("SELECT COUNT(*) FROM videos WHERE channel_id=? AND status=?", (cid, "approved_for_upload")).fetchone()[0]
            posted   = conn.execute("SELECT COUNT(*) FROM videos WHERE channel_id=? AND status=?", (cid, "posted")).fetchone()[0]
            print(f"  {cid:25} {total:>6} {review:>6} {approved:>8} {posted:>6}")
        print("\n  Recent activity:")
        rows = conn.execute("SELECT video_id, channel_id, status, created_at FROM videos ORDER BY created_at DESC LIMIT 5").fetchall()
        for r in rows:
            print(f"    {r[3][:19]}  {r[1]:20}  [{r[2]:15}]  {r[0][:40]}")


def main():
    bootstrap()
    while True:
        print()
        header("8-CHANNEL CONTENT FACTORY")
        print("  1. Generate ONE video")
        print("  2. Generate BATCH (leave PC mode)")
        print("  3. Review pending videos")
        print("  4. Mark uploaded per platform")
        print("  5. Google Drive")
        print("  6. Cleanup")
        print("  7. Stats and recent activity")
        print("  0. Exit")
        choice = input("\nChoose: ").strip()
        if   choice == "1": action_generate_one()
        elif choice == "2": action_generate_batch()
        elif choice == "3": action_review()
        elif choice == "4": action_mark_uploaded()
        elif choice == "5": action_drive()
        elif choice == "6": action_cleanup()
        elif choice == "7": action_stats()
        elif choice == "0":
            print("\nGoodbye.\n")
            break
        else:
            err("Invalid choice")


if __name__ == "__main__":
    main()

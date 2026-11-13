"""
core/cli_helpers.py
Helpers for CLI: pretty print, rclone Drive, cleanup, file sizes.
"""

from __future__ import annotations
import shutil
import subprocess
from pathlib import Path


def ok(msg):    print(f"[OK]    {msg}")
def info(msg):  print(f"[INFO]  {msg}")
def warn(msg):  print(f"[WARN]  {msg}")
def err(msg):   print(f"[ERROR] {msg}")


def divider(char="=", width=60):
    print(char * width)


def header(text):
    divider()
    print(f"  {text}")
    divider()


def format_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def folder_size(folder):
    folder = Path(folder)
    if not folder.exists():
        return 0
    return sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())


RCLONE     = shutil.which("rclone")
REMOTE     = "gdrive:"
DRIVE_ROOT = "8ChannelContentFactory"


def rclone_available():
    return RCLONE is not None


def rclone_run(args, timeout=60):
    if not RCLONE:
        return False, "rclone not in PATH"
    try:
        result = subprocess.run([RCLONE] + args, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr or result.stdout
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s"
    except Exception as e:
        return False, str(e)


def drive_upload_video(local_folder, video_id, channel_id):
    if not rclone_available():
        err("rclone not installed")
        return False
    remote_path = f"{REMOTE}{DRIVE_ROOT}/{channel_id}/{video_id}"
    info(f"Uploading {Path(local_folder).name} to {remote_path}...")
    okstat, output = rclone_run(["copy", str(local_folder), remote_path, "--progress"], timeout=1800)
    if okstat:
        ok(f"Uploaded to Drive: {remote_path}")
        return True
    err(f"Upload failed: {output[:300]}")
    return False


def drive_upload_thumbnail(thumb_path, channel_id, video_id):
    if not rclone_available():
        return False
    if not Path(thumb_path).exists():
        return False
    remote_path = f"{REMOTE}{DRIVE_ROOT}/_thumbnails/{channel_id}/{video_id}.png"
    okstat, output = rclone_run(["copyto", str(thumb_path), remote_path], timeout=120)
    if okstat:
        ok(f"Thumbnail uploaded: {video_id}.png")
        return True
    return False


def drive_list_channel(channel_id):
    if not rclone_available():
        return False, []
    remote_path = f"{REMOTE}{DRIVE_ROOT}/{channel_id}"
    okstat, output = rclone_run(["lsf", remote_path, "--dirs-only"], timeout=30)
    if okstat:
        items = [l.strip().rstrip("/") for l in output.splitlines() if l.strip()]
        return True, items
    return False, []


def drive_delete_video(channel_id, video_id):
    if not rclone_available():
        return False
    remote_path = f"{REMOTE}{DRIVE_ROOT}/{channel_id}/{video_id}"
    okstat, output = rclone_run(["purge", remote_path], timeout=60)
    if okstat:
        ok(f"Deleted from Drive: {video_id}")
        return True
    err(f"Drive delete failed: {output[:200]}")
    return False


def cleanup_workspace_for_video(channel_id, video_id):
    workspace = Path(f"channels/{channel_id}/workspace/{video_id}")
    if not workspace.exists():
        return 0
    size = folder_size(workspace)
    shutil.rmtree(workspace, ignore_errors=True)
    return size


def cleanup_old_workspaces(channel_id, keep_recent=3):
    ws_root = Path(f"channels/{channel_id}/workspace")
    if not ws_root.exists():
        return 0, 0
    folders = sorted([f for f in ws_root.iterdir() if f.is_dir()],
                     key=lambda p: p.stat().st_mtime, reverse=True)
    if len(folders) <= keep_recent:
        return 0, 0
    to_delete = folders[keep_recent:]
    total_bytes = 0
    count = 0
    for f in to_delete:
        size = folder_size(f)
        shutil.rmtree(f, ignore_errors=True)
        total_bytes += size
        count += 1
    return count, total_bytes

"""Upload package helper.

Upload package is separate from output.
Output contains only final clips and thumbnails.
Upload package contains metadata/checklist/source notes for manual upload.
"""

from __future__ import annotations

from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def create_upload_checklist(folder: Path, platforms: list[str] | None = None) -> None:
    platforms = platforms or ["youtube_shorts", "tiktok", "instagram_reels", "facebook_reels"]
    lines = [
        "UPLOAD CHECKLIST",
        "",
        "Before upload:",
        "[ ] Watch final video fully",
        "[ ] Check audio",
        "[ ] Check captions",
        "[ ] Check title and hashtags",
        "[ ] Check thumbnail",
        "",
        "Platforms:",
    ]
    for p in platforms:
        lines.append(f"[ ] Upload to {p}")
        lines.append(f"[ ] Mark {p} posted in dashboard")
    lines.append("")
    lines.append("Files to use:")
    lines.append("- channels/<channel>/output/final_clips/<video_id>.mp4")
    lines.append("- channels/<channel>/output/thumbnails/<video_id>.png")
    lines.append("- this upload package metadata.txt")
    (folder / "upload_checklist.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_upload_package(channel_id: str, video_id: str, workspace_folder: Path) -> Path:
    package_dir = PROJECT_ROOT / "channels" / channel_id / "upload_packages" / video_id
    package_dir.mkdir(parents=True, exist_ok=True)
    for name in ["metadata.txt", "metadata.json", "upload_checklist.txt", "source_notes.txt", "render_report.json", "safety_report.json"]:
        src = workspace_folder / name
        if src.exists():
            shutil.copy2(src, package_dir / name)
    (package_dir / "WHERE_ARE_FINAL_FILES.txt").write_text(
        f"Final clip:\nchannels/{channel_id}/output/final_clips/{video_id}.mp4\n\n"
        f"Thumbnail:\nchannels/{channel_id}/output/thumbnails/{video_id}.png\n",
        encoding="utf-8",
    )
    return package_dir

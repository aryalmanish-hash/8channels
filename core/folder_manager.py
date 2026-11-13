"""Folder management utilities.

Structure per channel:

channels/<channel_id>/workspace/<video_id>/   = temp working files (deleted after publish)
channels/<channel_id>/output/<video_id>/      = final: final.mp4, thumbnail.png, captions.txt
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import re
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHANNELS_ROOT = PROJECT_ROOT / "channels"


def slugify(text: str, max_len: int = 50) -> str:
    text = text.strip().lower()
    # Detect if this was an AITA-style title (we'll append aita later, not prefix)
    is_aita = bool(re.match(r"^(aita\s+for\s+|aita\s+)", text))
    # Strip common openers so slug starts with real content words
    text = re.sub(r"^(aita\s+for\s+|aita\s+|the\s+|my\s+)", "", text)
    # Drop common stopwords for shorter names
    text = re.sub(r"\b(the|my|a|an|to|of|for|in|on|at|about|and|but|or|is|are|was|were|be|been)\b", "", text)
    # Convert to underscored slug
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")

    if not text:
        text = "video"

    # Append _aita in the middle (before the timestamp) if this was an AITA title
    # We reserve ~5 chars for "_aita" so trim text a bit more
    if is_aita:
        reserved = 5  # length of "_aita"
        max_text = max_len - reserved
    else:
        max_text = max_len

    if len(text) > max_text:
        # Cut at last full word before max_text (avoid mid-word cuts)
        cut = text[:max_text]
        last_us = cut.rfind("_")
        if last_us > max_text * 0.5:
            cut = cut[:last_us]
        text = cut.strip("_") or "video"

    if is_aita:
        text = f"{text}_aita"

    return text



def get_channel_root(channel_id: str) -> Path:
    return CHANNELS_ROOT / channel_id


def ensure_channel_workspace(channel_id: str) -> Path:
    path = get_channel_root(channel_id) / "workspace"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_channel_output(channel_id: str) -> Path:
    output = get_channel_root(channel_id) / "output"
    output.mkdir(parents=True, exist_ok=True)
    return output


# Kept for backward compat
def ensure_channel_output_dirs(channel_id: str) -> tuple[Path, Path]:
    output = ensure_channel_output(channel_id)
    return output, output


def make_video_name(topic: str) -> str:
    """
    Build clean video folder name: <slug>_<YYYYMMDD>_<HHMM>
    Example: aita_snake_roommate_20260706_1442
    """
    slug = slugify(topic, 40)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{slug}_{stamp}"


def create_video_folder(channel_id: str, topic: str) -> tuple[str, Path]:
    """Create workspace folder. Returns (video_id, workspace_folder)."""
    workspace = ensure_channel_workspace(channel_id)
    ensure_channel_output(channel_id)
    video_id = make_video_name(topic)
    folder = workspace / video_id
    # Handle collision
    if folder.exists():
        i = 2
        while (workspace / f"{video_id}_{i}").exists():
            i += 1
        video_id = f"{video_id}_{i}"
        folder = workspace / video_id
    folder.mkdir(parents=True, exist_ok=False)
    return video_id, folder


def create_standard_output_files(folder: Path, title: str = "") -> None:
    placeholders = {
        "script.txt":           "",
        "metadata.txt":         "",
        "upload_checklist.txt": "Manual upload checklist\n\n[ ] Review video\n[ ] Check title\n[ ] Check hashtags\n[ ] Upload manually\n[ ] Mark posted in dashboard\n",
        "source_notes.txt":     "",
        "render_report.json":   "{}\n",
        "metadata.json":        "{}\n",
    }
    for filename, content in placeholders.items():
        path = folder / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def _unescape(s):
    if not isinstance(s, str):
        return s
    return s.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "").strip()


def build_captions_txt(metadata: dict) -> str:
    """Format metadata into captions.txt for the video output folder."""
    yt = metadata.get("youtube_shorts") or metadata.get("youtube") or {}
    tt = metadata.get("tiktok") or {}
    ig = metadata.get("instagram_reels") or metadata.get("instagram") or {}
    fb = metadata.get("facebook_reels") or metadata.get("facebook") or {}
    hashtags = metadata.get("hashtags", [])

    yt_title       = _unescape(yt.get("title", metadata.get("title", "")))
    yt_desc        = _unescape(yt.get("description", metadata.get("description", "")))
    yt_hashtags    = yt.get("hashtags", hashtags[:5] if hashtags else [])
    tt_caption     = _unescape(tt.get("caption", ""))
    ig_caption     = _unescape(ig.get("caption", ""))
    fb_caption     = _unescape(fb.get("caption", ""))

    def fmt_tags(tags):
        if not tags:
            return ""
        return " ".join(f"#{str(t).lstrip('#')}" for t in tags[:5])

    yt_tags_str = fmt_tags(yt_hashtags)

    lines = []
    lines.append("=" * 60)
    lines.append("YOUTUBE SHORTS")
    lines.append("=" * 60)
    lines.append(f"Title: {yt_title}")
    lines.append(f"Hashtags: {yt_tags_str}")
    lines.append("")
    lines.append("Description:")
    lines.append(yt_desc)
    if yt_tags_str and yt_tags_str not in yt_desc:
        lines.append("")
        lines.append(yt_tags_str)
    lines.append("")
    lines.append("")
    lines.append("=" * 60)
    lines.append("TIKTOK")
    lines.append("=" * 60)
    lines.append("Caption:")
    lines.append(tt_caption)
    lines.append("")
    lines.append("")
    lines.append("=" * 60)
    lines.append("INSTAGRAM REELS")
    lines.append("=" * 60)
    lines.append("Caption:")
    lines.append(ig_caption)
    lines.append("")
    lines.append("")
    lines.append("=" * 60)
    lines.append("FACEBOOK REELS")
    lines.append("=" * 60)
    lines.append("Caption:")
    lines.append(fb_caption)
    lines.append("")
    return "\n".join(lines)


def publish_final_files(
    channel_id: str,
    video_id: str,
    workspace_final: Path,
    workspace_thumb: Path = None,
    metadata: dict = None,
    cleanup_workspace: bool = True,
) -> tuple:
    """
    Publish final files to output/<video_id>/ folder.
    Creates: final.mp4, thumbnail.png (if exists), captions.txt inside that folder.
    Cleans up workspace after.
    """
    output_root = ensure_channel_output(channel_id)
    video_output = output_root / video_id
    video_output.mkdir(parents=True, exist_ok=True)

    final_path = None
    thumb_path = None

    # Copy final video with unique name (matches folder = video_id)
    if workspace_final and Path(str(workspace_final)).exists():
        final_out = video_output / f"{video_id}.mp4"
        shutil.copy2(workspace_final, final_out)
        final_path = final_out
        print(f"  [PUBLISH] {final_out.name}")

    # Copy thumbnail if exists (with unique name)
    if workspace_thumb and Path(str(workspace_thumb)).exists():
        thumb_out = video_output / f"{video_id}_thumbnail.png"
        shutil.copy2(workspace_thumb, thumb_out)
        thumb_path = thumb_out
        print(f"  [PUBLISH] {thumb_out.name}")

    # Write captions.txt with unique name
    if metadata:
        try:
            captions_txt = build_captions_txt(metadata)
            captions_out = video_output / f"{video_id}_captions.txt"
            captions_out.write_text(captions_txt, encoding="utf-8")
            print(f"  [PUBLISH] {captions_out.name}")
        except Exception as e:
            print(f"  [PUBLISH] captions.txt failed: {e}")

    # Note: workspace cleanup is now done by workflow.py at the END
    # (after upload_checklist and all other post-publish steps complete).
    return final_path, thumb_path

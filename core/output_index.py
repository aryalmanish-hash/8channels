"""Generate HTML indexes for final outputs only."""

from __future__ import annotations

from pathlib import Path
from core.config_loader import load_all_channel_configs

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHANNELS_ROOT = PROJECT_ROOT / "channels"


def generate_output_indexes() -> None:
    CHANNELS_ROOT.mkdir(parents=True, exist_ok=True)
    configs = load_all_channel_configs()
    links = []
    for channel_id, cfg in configs.items():
        root = CHANNELS_ROOT / channel_id
        final_dir = root / "output" / "final_clips"
        thumb_dir = root / "output" / "thumbnails"
        workspace = root / "workspace"
    # DISABLED: final_dir.mkdir(parents=True, exist_ok=True)
    # DISABLED: thumb_dir.mkdir(parents=True, exist_ok=True)
        workspace.mkdir(parents=True, exist_ok=True)
        _write_channel_index(root, channel_id, cfg.get("channel_name", channel_id))
        links.append((channel_id, cfg.get("channel_name", channel_id)))
    _write_main_index(links)


def _write_main_index(links: list[tuple[str, str]]) -> None:
    rows = "\n".join(
        f'<li><a href="{channel_id}/output/index.html">{name}</a> <span>{channel_id}</span></li>'
        for channel_id, name in links
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Channel Final Outputs</title>
<style>body{{font-family:Arial;background:#111827;color:#f9fafb;padding:30px}}a{{color:#93c5fd;font-size:20px}}li{{margin:14px 0}}span{{color:#9ca3af;margin-left:10px}}</style></head>
<body><h1>Final Outputs By Channel</h1><p>Output contains only final clips and thumbnails. Work files are in workspace. Metadata/checklists are in upload_packages.</p><ul>{rows}</ul></body></html>"""
    (CHANNELS_ROOT / "OPEN_CHANNEL_OUTPUTS.html").write_text(html, encoding="utf-8")


def _write_channel_index(channel_root: Path, channel_id: str, channel_name: str) -> None:
    final_dir = channel_root / "output" / "final_clips"
    thumb_dir = channel_root / "output" / "thumbnails"
    index_path = channel_root / "output" / "index.html"
    clips = sorted(final_dir.glob("*.mp4"), reverse=True)
    rows = []
    for clip in clips:
        stem = clip.stem
        thumb = thumb_dir / f"{stem}.png"
        bits = [f"<strong>{clip.name}</strong>"]
        if thumb.exists():
            bits.append(f'<br><img src="thumbnails/{thumb.name}" style="width:120px;border-radius:8px;margin-top:8px">')
        bits.append(f'<br><a href="final_clips/{clip.name}">final clip</a>')
        rows.append("<li>" + "".join(bits) + "</li>")
    body = "\n".join(rows) or "<li>No final clips yet.</li>"
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>{channel_name} Final Outputs</title>
<style>body{{font-family:Arial;background:#111827;color:#f9fafb;padding:30px}}a{{color:#93c5fd}}li{{margin:22px 0;padding:14px;background:#1f2937;border-radius:12px;list-style:none}}</style></head>
<body><p><a href="../OPEN_CHANNEL_OUTPUTS.html">Back to all channels</a></p><h1>{channel_name}</h1>
<p>Final clips: channels/{channel_id}/output/final_clips/</p><p>Thumbnails: channels/{channel_id}/output/thumbnails/</p><p>Upload packages: channels/{channel_id}/upload_packages/</p><ul>{body}</ul></body></html>"""
    index_path.write_text(html, encoding="utf-8")
"""
core/source_builder.py
Normalizes scraped data into clean source context for script generation.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


def build_source_context(
    channel_id: str,
    title: str,
    summary: str = "",
    link: str = "",
    source_type: str = "unknown"
) -> dict:
    """
    Build a normalized source context dict.
    This gets saved to workspace and passed to script generator.
    """
    return {
        "channel_id": channel_id,
        "title": title.strip(),
        "summary": summary.strip()[:800] if summary else "",
        "link": link.strip(),
        "source_type": source_type,
        "fetched_at": datetime.now().isoformat(),
    }


def save_source_context(folder: Path, context: dict) -> Path:
    """
    Save source context to workspace folder as JSON.
    """
    path = folder / "source_context.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2)
    return path


def load_source_context(folder: Path) -> dict:
    """
    Load source context from workspace folder.
    """
    path = folder / "source_context.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

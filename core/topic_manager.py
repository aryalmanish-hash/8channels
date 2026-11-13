"""
core/topic_manager.py
Connects scraper to workflow.
Uses real web data for all channels.
"""

from __future__ import annotations

from core.scraper import get_web_topics
from core.config_loader import load_global_config


def get_topic_ideas(channel_id: str, count: int = 5) -> list[tuple[str, str]]:
    """
    Returns list of (video_type, topic_string) tuples.
    Used by workflow.create_channel_batch()
    """
    g_cfg = load_global_config()
    token = g_cfg.get("github_token", None)

    web_data = get_web_topics(channel_id, limit=count, github_token=token)

    formatted = []
    for item in web_data:
        title = item.get("title", "").strip()
        summary = item.get("summary", "").strip()
        if summary:
            topic_str = f"{title} - {summary[:120]}"
        else:
            topic_str = title
        formatted.append(("default", topic_str))

    if not formatted:
        formatted.append(("default", f"General topic for {channel_id}"))

    return formatted

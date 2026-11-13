"""Central channel style profiles.

Shared style definitions used by thumbnails, renderer, dashboard labels, and metadata.
Keeping this central avoids breaking one channel when polishing another.
"""

from __future__ import annotations

STYLES = {
    "reddit_stories": {
        "label": "Fictional Reddit Stories",
        "short_label": "STORYTIME",
        "bg": (24, 24, 27),
        "accent": (245, 158, 11),
        "ffmpeg_color": "0x18181b",
        "emoji_safe_icon": "STORY",
        "tone": "dramatic",
    },
    "english_learning": {
        "label": "English Learning",
        "short_label": "ENGLISH FIX",
        "bg": (6, 78, 59),
        "accent": (16, 185, 129),
        "ffmpeg_color": "0x064e3b",
        "emoji_safe_icon": "ABC",
        "tone": "clean_teacher",
    },
    "psychology": {
        "label": "Psychology / Human Behavior",
        "short_label": "MIND SIGNALS",
        "bg": (30, 27, 75),
        "accent": (168, 85, 247),
        "ffmpeg_color": "0x1e1b4b",
        "emoji_safe_icon": "MIND",
        "tone": "calm_dark",
    },
    "dark_history": {
        "label": "Dark History / Mystery",
        "short_label": "DARK HISTORY",
        "bg": (28, 25, 23),
        "accent": (180, 83, 9),
        "ffmpeg_color": "0x1c1917",
        "emoji_safe_icon": "HIST",
        "tone": "documentary",
    },
    "ai_tools_automation": {
        "label": "AI Tools + Automation",
        "short_label": "AI TOOLS",
        "bg": (8, 47, 73),
        "accent": (14, 165, 233),
        "ffmpeg_color": "0x082f49",
        "emoji_safe_icon": "TOOL",
        "tone": "clear_demo",
    },
    "quiz": {
        "label": "Quiz / Brain Challenge",
        "short_label": "QUICK QUIZ",
        "bg": (15, 23, 42),
        "accent": (59, 130, 246),
        "ffmpeg_color": "0x0f172a",
        "emoji_safe_icon": "QUIZ",
        "tone": "energetic",
    },
    "facts": {
        "label": "Faceless Facts / Did You Know",
        "short_label": "DID YOU KNOW",
        "bg": (30, 58, 138),
        "accent": (34, 197, 94),
        "ffmpeg_color": "0x1e3a8a",
        "emoji_safe_icon": "FACT",
        "tone": "curious",
    },
    "sports_reviews": {
        "label": "Sports Type 3 + Safer Reviews",
        "short_label": "SPORTS REVIEW",
        "bg": (69, 10, 10),
        "accent": (239, 68, 68),
        "ffmpeg_color": "0x450a0a",
        "emoji_safe_icon": "SPORT",
        "tone": "analytical",
    },
}


def get_style(channel_id: str) -> dict:
    return STYLES.get(channel_id, {
        "label": channel_id,
        "short_label": channel_id.upper(),
        "bg": (17, 24, 39),
        "accent": (37, 99, 235),
        "ffmpeg_color": "0x111827",
        "emoji_safe_icon": "VID",
        "tone": "generic",
    })

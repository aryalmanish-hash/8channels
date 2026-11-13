"""Posting status helpers."""

from __future__ import annotations

from core.database import connect
from core.status_manager import mark_posted_if_all_platforms

PLATFORMS = [
    "youtube_shorts",
    "tiktok",
    "instagram_reels",
    "facebook_reels",
    "youtube_longform",
    "x_twitter",
    "linkedin",
]


def initialize_posting_rows(video_id: str) -> None:
    with connect() as conn:
        for platform in PLATFORMS:
            conn.execute(
                """
                INSERT OR IGNORE INTO posting_status (video_id, platform, status)
                VALUES (?, ?, 'not_posted')
                """,
                (video_id, platform),
            )
        conn.commit()


def set_platform_status(video_id: str, platform: str, status: str) -> None:
    if platform not in PLATFORMS:
        raise ValueError(f"Unknown platform: {platform}")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO posting_status (video_id, platform, status, posted_at)
            VALUES (?, ?, ?, CASE WHEN ?='posted' THEN CURRENT_TIMESTAMP ELSE NULL END)
            ON CONFLICT(video_id, platform) DO UPDATE SET
                status=excluded.status,
                posted_at=CASE WHEN excluded.status='posted' THEN CURRENT_TIMESTAMP ELSE posting_status.posted_at END
            """,
            (video_id, platform, status, status),
        )
        conn.commit()
    mark_posted_if_all_platforms(video_id)


def get_posting_summary(video_id: str) -> dict[str, str]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT platform, status FROM posting_status WHERE video_id=?",
            (video_id,),
        ).fetchall()
    return {row["platform"]: row["status"] for row in rows}

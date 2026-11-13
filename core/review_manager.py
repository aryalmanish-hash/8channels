"""Manual review helpers."""

from __future__ import annotations

from core.database import connect
from core.config_loader import load_channel_config


def initialize_review_checks(video_id: str, channel_id: str) -> None:
    cfg = load_channel_config(channel_id)
    checks = cfg.get("manual_review", {}).get("checks", [])
    with connect() as conn:
        for check in checks:
            conn.execute(
                """
                INSERT INTO review_checks (video_id, check_name, status)
                VALUES (?, ?, 'pending')
                """,
                (video_id, check),
            )
        conn.commit()


def approve_video(video_id: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE videos SET status='approved_for_upload', updated_at=CURRENT_TIMESTAMP WHERE video_id=?",
            (video_id,),
        )
        conn.execute(
            "UPDATE review_checks SET status='passed', checked_at=CURRENT_TIMESTAMP WHERE video_id=?",
            (video_id,),
        )
        conn.commit()


def mark_needs_edit(video_id: str, notes: str = "") -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE videos SET status='needs_edit', updated_at=CURRENT_TIMESTAMP WHERE video_id=?",
            (video_id,),
        )
        if notes:
            conn.execute(
                "INSERT INTO logs (level, module, message) VALUES ('INFO', 'review', ?)",
                (f"{video_id}: {notes}",),
            )
        conn.commit()

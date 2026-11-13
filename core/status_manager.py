"""Common video status helpers."""

from __future__ import annotations

from core.database import connect

VALID_STATUSES = {
    "draft", "script_generated", "rendered", "needs_review", "approved_for_upload",
    "posted", "archived", "rejected", "needs_edit", "failed"
}


def set_video_status(video_id: str, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    with connect() as conn:
        conn.execute(
            "UPDATE videos SET status=?, updated_at=CURRENT_TIMESTAMP WHERE video_id=?",
            (status, video_id),
        )
        conn.commit()


def archive_video(video_id: str) -> None:
    set_video_status(video_id, "archived")


def reject_video(video_id: str) -> None:
    set_video_status(video_id, "rejected")


def mark_posted_if_all_platforms(video_id: str) -> None:
    with connect() as conn:
        rows = conn.execute(
            "SELECT status FROM posting_status WHERE video_id=? AND platform IN ('youtube_shorts','tiktok','instagram_reels','facebook_reels')",
            (video_id,),
        ).fetchall()
        if rows and all(row["status"] == "posted" for row in rows):
            conn.execute(
                "UPDATE videos SET status='posted', updated_at=CURRENT_TIMESTAMP WHERE video_id=?",
                (video_id,),
            )
            conn.commit()

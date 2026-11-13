"""
core/workflow.py
MVP workflow helpers with source context support.
"""

from __future__ import annotations
import random

import json
from pathlib import Path

from core.database import connect, log
from core.ai_engine import reset_log as reset_ai_log
from core.folder_manager import create_video_folder, create_standard_output_files, publish_final_files
from core.script_generator import generate_script
from core.metadata_generator import generate_metadata
from core.config_loader import load_channel_config
from core.voice_generator import generate_voice
from core.caption_generator import generate_srt
from core.renderer import render_placeholder_video
from core.thumbnail_generator import generate_thumbnail
from core.review_manager import initialize_review_checks
from core.posting_tracker import initialize_posting_rows
from core.output_index import generate_output_indexes
from core.upload_package import create_upload_checklist, create_upload_package
from core.safety_checker import check_script
from core.source_builder import build_source_context, save_source_context
from core.ai_validator import validate_and_improve
from core.compositor import compose_video
from core.overlay_engine import (
    create_reddit_ui_overlay,
    create_channel_watermark,
    create_cta_overlay,
    save_reddit_card_png,
)
from core.background_manager import get_background_for_channel
from core.music_manager import get_background_music, mix_voice_with_music, speed_up_audio


# ── Step timer helper for clean CLI display ────────────────────────────
import time as _step_time
_STEP_TIMER = {"start": 0.0, "current": ""}

def _step(n: int, total: int, label: str):
    """Start a step. Prints [N/TOTAL] label..."""
    _STEP_TIMER["start"] = _step_time.time()
    _STEP_TIMER["current"] = label
    print(f"[{n}/{total}] {label}...", end=" ", flush=True)

def _step_done(status: str = "OK"):
    """Finish current step and print elapsed."""
    elapsed = _step_time.time() - _STEP_TIMER["start"]
    print(f"{status}  ({elapsed:.1f}s)")

def _substep(msg: str):
    """Print a sub-step line indented."""
    print(f"      {msg}")




def create_script_draft(
    channel_id: str,
    video_type: str,
    topic: str,
    source_context: dict = None
) -> tuple[str, Path]:
    """Create script draft with source context support."""
    cfg = load_channel_config(channel_id)
    if video_type not in cfg.get("video_types", []):
        video_type = cfg.get("video_types", ["default"])[0]

    video_id, folder = create_video_folder(channel_id, topic)
    create_standard_output_files(folder, topic)

    # Build source context if not provided
    if source_context is None:
        source_context = build_source_context(
            channel_id=channel_id,
            title=topic,
            summary="",
            link="",
            source_type="manual"
        )

    # Save source context
    save_source_context(folder, source_context)

    # Generate script with source context
    script = generate_script(channel_id, video_type, topic, source_context)
    metadata = generate_metadata(channel_id, topic, script)

    script = validate_and_improve(script, channel_id, workspace=folder)
    (folder / "script.txt").write_text(script, encoding="utf-8")
    safety_report = check_script(channel_id, script)
    (folder / "safety_report.json").write_text(json.dumps(safety_report, indent=2), encoding="utf-8")
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (folder / "metadata.txt").write_text(_metadata_text(metadata), encoding="utf-8")

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO videos (video_id, channel_id, video_type, title, status, output_folder)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (video_id, channel_id, video_type, metadata["title"], "script_generated", str(folder)),
        )
        conn.execute(
            """
            INSERT INTO scripts (video_id, script_text, version, status)
            VALUES (?, ?, ?, ?)
            """,
            (video_id, script, 1, "script_generated"),
        )
        conn.execute(
            """
            INSERT INTO metadata (video_id, youtube_title, youtube_description, youtube_tags,
                                  tiktok_caption, instagram_caption, facebook_caption)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                video_id,
                metadata["youtube_shorts"]["title"],
                metadata["youtube_shorts"]["description"],
                ",".join(metadata["hashtags"]),
                metadata["tiktok"]["caption"],
                metadata["instagram_reels"]["caption"],
                metadata["facebook_reels"]["caption"],
            ),
        )
        conn.commit()

    initialize_posting_rows(video_id)
    generate_output_indexes()
    log("INFO", "workflow", f"Created script draft {video_id}")
    return video_id, folder


def _metadata_text(metadata: dict) -> str:
    hashtags = " ".join(f"#{h}" for h in metadata.get("hashtags", []))
    return f"""TITLE:
{metadata.get('title', '')}

DESCRIPTION:
{metadata.get('description', '')}

HASHTAGS:
{hashtags}

TIKTOK CAPTION:
{metadata.get('tiktok', {}).get('caption', '')}

INSTAGRAM CAPTION:
{metadata.get('instagram_reels', {}).get('caption', '')}

FACEBOOK CAPTION:
{metadata.get('facebook_reels', {}).get('caption', '')}
""".strip() + "\n"


def create_full_mvp_video(
    channel_id: str,
    video_type: str,
    topic: str,
    source_context: dict = None
) -> tuple[str, Path]:
    """Create MVP draft with script, metadata, voice, captions, and MP4."""
    # Reset AI log at start of every new video generation
    reset_ai_log()
    video_id, folder = create_script_draft(channel_id, video_type, topic, source_context)
    script = (folder / "script.txt").read_text(encoding="utf-8")

    voice_path = folder / "voice.wav"
    duration, voice_mode = generate_voice(script, voice_path, channel_id=channel_id)

    # ── Speed up voice 1.25x (video will match this new duration) ──
    # Music will be mixed AFTER, so music stays at 1x
    _speed_ok, _new_dur = speed_up_audio(voice_path, multiplier=1.25)
    if _speed_ok and _new_dur > 0:
        duration = _new_dur
        print(f"  Voice sped up 1.25x — new video duration: {duration:.2f}s")

    captions_path = folder / "captions.srt"
    generate_srt(script, duration, captions_path, audio_path=voice_path)

    # ── Background Music (Pixabay free) ──────────────────────────────
    _vibe_for_music = "emotional" if "_em_score" in dir() else None
    music_path = get_background_music(
        channel_id=channel_id,
        duration=duration,
        workspace=folder,
        vibe=_vibe_for_music,
    )
    audio_for_video = voice_path
    if music_path:
        mixed = mix_voice_with_music(voice_path, music_path, folder)
        if mixed:
            audio_for_video = mixed
            print(f"  Using mixed audio: voice + music")
        else:
            print(f"  Music mix failed — using voice only")
    else:
        print(f"  No music — using voice only")

    thumbnail_path = folder / "thumbnail.png"
    # Thumbnail generation DISABLED per user request (saves ~15s per video)
    thumbnail_created = False
    # Uncomment to re-enable:
    # thumbnail_created = generate_thumbnail(channel_id, topic, thumbnail_path, script=script)

    final_path = folder / "final.mp4"
    # Detect story vibe and pick matching background categories
    from core.background_manager import get_clips_for_video
    _script_lower = script.lower()
    _high_energy  = ["fired","exploded","screamed","confronted","furious",
                      "revenge","exposed","fight","shocking","betrayed",
                      "cheated","caught","destroyed","drama","unbelievable"]
    _emotional    = ["cried","tears","grief","loss","died","cancer","funeral",
                      "heartbroken","devastated","alone","abandoned","surgery",
                      "hospital","elderly","passed away","depression"]
    _he_score = sum(1 for w in _high_energy if w in _script_lower)
    _em_score = sum(1 for w in _emotional  if w in _script_lower)
    if _em_score > _he_score:
        _vibe_categories = ["fpv_drone", "satisfying", "asmr_crafts"]
    elif _he_score >= 2:
        _vibe_categories = ["gaming", "industrial", "gameplay"]
    else:
        _vibe_categories = ["gaming", "satisfying", "industrial", "fpv_drone"]
    print(f"  Story vibe: he={_he_score} em={_em_score} cats={_vibe_categories}")
    background_clips = get_clips_for_video(
        channel_id,
        video_duration=duration,
        scene_duration=18,
        preferred_categories=_vibe_categories,
    )
    background_clip  = background_clips[0] if background_clips else None

    # Build overlays
    overlays = []

    # Reddit UI card — saved as PNG for FFmpeg overlay (pixel-perfect text)
    card_png_path = None
    if channel_id == "reddit_stories":
        import re as _re
        # Story generator strips Title: line and prepends spoken title as first sentence
        # First sentence is the AI-generated title (e.g. "Am I the asshole for taking a parking spot")
        # Try Title: regex first for legacy compatibility, then first sentence
        title_match = _re.search(r"Title:\s*(.+?)(?:\n|$)", script)
        if title_match:
            raw_title = title_match.group(1).strip()
        else:
            # Extract first sentence from spoken script
            first_sentence_match = _re.match(r"^(.*?[?.!])(?:\s|$)", script.strip())
            if first_sentence_match:
                raw_title = first_sentence_match.group(1).strip()
                # Convert spoken "Am I the asshole" back to "AITA" for card display
                raw_title = _re.sub(r"^Am I the asshole", "AITA", raw_title, flags=_re.IGNORECASE)
                raw_title = _re.sub(r"^Would I be the asshole", "WIBTA", raw_title, flags=_re.IGNORECASE)
            else:
                raw_title = topic
        # Cut at first ? or . to avoid spilling into story body
        cut_match  = _re.search(r"^(.*?[?.!])\s", raw_title + " ")
        card_title = cut_match.group(1).strip() if cut_match else raw_title
        # Sanity limit — max 200 chars for the card
        if len(card_title) > 200:
            card_title = card_title[:200].rsplit(" ", 1)[0] + "..."
        print(f"  Card title extracted: {card_title[:80]}")
        subreddit   = "AmITheAsshole"
        _uv_num     = random.randint(1, 49)
        _uv_dec     = random.randint(0, 9)
        _upvotes    = f"{_uv_num}.{_uv_dec}k"
        _comments   = str(random.randint(150, 2400))

        # ── Random username pool (mix of throwaway + regular Reddit-style) ──
        _USERNAME_POOL = [
            # Throwaway style (typical for AITA)
            "throwaway_2847", "throwaway_wife32", "throwaway_famdrama",
            "throwaway_workthing", "throwaway_broke", "throwaway_88x",
            "throwaway_mom45", "throwaway_hurt", "throwaway_confused",
            "throwaway_livid", "throwaway_bride22", "throwaway_ex_wife",
            "throwaway_stressed", "throwaway_lostit", "throwaway_venting",
            # Regular reddit-style usernames
            "SaltyPear_88", "TiredMom_2024", "CautiousMarigold",
            "OverwhelmedDad", "AnxiousSister", "SilentBrother92",
            "FumingNeighbor", "SleeplessBride", "BrokenTrust44",
            "MoodyOwl_2211", "QuietStormX", "PragmaticPenguin",
            "HonestHedgehog", "WeaponizedKindness", "ReluctantHero3",
            "NotYourVillain", "AverageJoe_88", "PatientPanda",
            "TangyOrange_12", "GlacialMoose_99", "SkepticalSquirrel",
            "GentleGiant_44", "BitterBluebell", "MildlyUpset",
            "CoolCoconut77", "SwiftSalmon_1", "MindfulMagpie",
            "HauntedHiker", "PolitePhoenix", "GrumpyGardener22",
        ]
        _random_username = random.choice(_USERNAME_POOL)

        # ── Random time-ago pool (realistic Reddit post ages) ──
        _TIME_POOL = [
            "1h ago", "2h ago", "3h ago", "4h ago", "5h ago",
            "6h ago", "7h ago", "8h ago", "10h ago", "12h ago",
            "14h ago", "16h ago", "18h ago", "22h ago",
            "1d ago", "2d ago", "3d ago",
        ]
        _random_time = random.choice(_TIME_POOL)

        card_png_path = folder / "reddit_card.png"
        save_reddit_card_png(
            subreddit=subreddit,
            title=card_title,
            output_path=card_png_path,
            width=1080,
            height=1920,
            upvotes=_upvotes,
            comments=_comments,
            username=_random_username,
            time_ago=_random_time,
        )
        print(f"  Reddit card PNG saved: {card_png_path.name}")

    # Watermark — always shown
    cfg = load_channel_config(channel_id)
    # Per-channel watermark display name (channel_name in yaml, or fallback map)
    _watermark_names = {
        "reddit_stories":      "UpvoteAnthology",
        "english_learning":    "EnglishDaily",
        "psychology":          "MindDecoded",
        "dark_history":        "DarkChronicles",
        "ai_tools_automation": "AItoolsHub",
        "quiz":                "QuickQuizz",
        "facts":               "FactBurst",
        "sports_reviews":      "SportsPulse",
    }
    channel_name = _watermark_names.get(channel_id, cfg.get("channel_name", channel_id).replace(" ", ""))
    print(f"  Watermark: @{channel_name}")
    watermark = create_channel_watermark(
        channel_name=channel_name,
        width=1080,
        height=1920,
        duration=duration,
    )
    overlays.append(watermark)

    # CTA — shown last 3 seconds
    if duration > 10:
        cta = create_cta_overlay(
            text="Follow for more stories",
            width=1080,
            height=1920,
            start=max(0, duration - 4.0),
            duration=3.5,
        )
        overlays.append(cta)

    # Try compositor first (background + kinetic captions + overlays)
    rendered = compose_video(
        channel_id=channel_id,
        script=script,
        audio_path=audio_for_video,
        output_path=final_path,
        duration=duration,
        title=topic,
        background_path=background_clip,
        background_clips=background_clips,
        use_kinetic_captions=True,
        srt_path=captions_path,
        overlays=overlays,
        card_png=card_png_path,
        card_start=0.0,
        card_end=7.0,
        card_fade_in=0.4,
        card_fade_out=0.8,
    )

    # NOTE: Card overlay is now baked into compose_video_ffmpeg Pass 2.
    # No separate 2nd FFmpeg pass needed — saves ~2 min per video.

    # Fallback to placeholder renderer
    if not rendered:
        rendered = render_placeholder_video(
            channel_id, topic, voice_path, captions_path, final_path, duration
        )
    status = "needs_review" if rendered else "needs_edit"

    # Load metadata from saved JSON for captions.txt
    _metadata_for_publish = None
    _meta_json = folder / "metadata.json"
    if _meta_json.exists():
        try:
            _metadata_for_publish = json.loads(_meta_json.read_text(encoding="utf-8"))
            print(f"  [PUBLISH] loaded metadata.json ({len(_metadata_for_publish)} keys)")
        except Exception as _e:
            print(f"  [PUBLISH] could not load metadata.json: {_e}")
    else:
        print(f"  [PUBLISH] metadata.json missing at {_meta_json}")

    published_final, published_thumb = publish_final_files(
        channel_id, video_id, final_path, thumbnail_path,
        metadata=_metadata_for_publish
    )

    # ── Dark History: mark Wikipedia topic used so it wont be picked again ──
    if channel_id == "dark_history" and published_final:
        try:
            from pathlib import Path as _P
            _wiki_src_file = _P("_dark_history_wiki_source.tmp")
            if _wiki_src_file.exists():
                _wiki_src = _wiki_src_file.read_text(encoding="utf-8").strip()
                if _wiki_src:
                    from core.story_generator_dark_history import mark_topic_used
                    mark_topic_used(_wiki_src)
                _wiki_src_file.unlink()
        except Exception as _e:
            print(f"  [DARK_HISTORY] mark_topic_used error: {_e}")

    create_upload_checklist(folder)
    upload_package = create_upload_package(channel_id, video_id, folder)

    report = {
        "video_id": video_id,
        "workspace_folder": str(folder),
        "voice_path": str(voice_path),
        "captions_path": str(captions_path),
        "workspace_final_video_path": str(final_path) if rendered else "",
        "workspace_thumbnail_path": str(thumbnail_path) if thumbnail_created else "",
        "published_final_video_path": str(published_final) if published_final else "",
        "published_thumbnail_path": str(published_thumb) if published_thumb else "",
        "duration": duration,
        "voice_mode": voice_mode,
        "rendered": rendered,
        "thumbnail_created": thumbnail_created,
        "upload_package": str(upload_package),
        "status": status,
    }
    (folder / "render_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    with connect() as conn:
        conn.execute(
            """
            UPDATE videos
            SET status=?, final_video_path=?, thumbnail_path=?, duration=?, updated_at=CURRENT_TIMESTAMP
            WHERE video_id=?
            """,
            (status, str(published_final) if published_final else "", str(published_thumb) if published_thumb else "", duration, video_id),
        )
        conn.commit()

    initialize_review_checks(video_id, channel_id)
    initialize_posting_rows(video_id)
    generate_output_indexes()
    log("INFO", "workflow", f"Created full MVP video {video_id} status={status}")

    # ─── Full cleanup at end of video generation ───────────────
    # Keeps ONLY the final files in output/<video_id>/
    # Deletes: workspace, downloaded YouTube clips, scene temp files, ffmpeg temp
    try:
        import shutil as _sh_c
        from core.folder_manager import ensure_channel_workspace

        # 1. Delete workspace folder for this video
        _ws = ensure_channel_workspace(channel_id) / video_id
        if _ws.exists():
            _sh_c.rmtree(_ws, ignore_errors=True)
            print(f"  [CLEANUP] workspace deleted: {video_id}")

        # 2. Delete YouTube-downloaded clips (yt_*.mp4)
        from core.background_manager import cleanup_all_youtube, cleanup_scene_temps
        cleanup_all_youtube()
        print(f"  [CLEANUP] YouTube downloads deleted")

        # 3. Delete scene temp trims (_scene_*.mp4)
        cleanup_scene_temps()
        print(f"  [CLEANUP] scene temp files deleted")

        # 4. Delete youtube_temp folder (source videos before trimming)
        try:
            from core.youtube_source import cleanup_youtube_temp
            cleanup_youtube_temp()
            print(f"  [CLEANUP] youtube_temp folder cleaned")
        except ImportError:
            pass

        # 5. Delete any leftover _ffmpeg_temp folders in output
        output_root = Path(f"channels/{channel_id}/output")
        if output_root.exists():
            for f in output_root.rglob("_ffmpeg_temp"):
                if f.is_dir():
                    _sh_c.rmtree(f, ignore_errors=True)
                    print(f"  [CLEANUP] ffmpeg_temp removed: {f}")

    except Exception as _e_cleanup:
        print(f"  [CLEANUP] partial failure: {_e_cleanup}")

    return video_id, folder


def create_channel_batch(channel_id: str, limit: int = 3) -> list[tuple[str, Path]]:
    """Create a batch for any channel using live web topics."""
    from core.topic_manager import get_topic_ideas
    from core.scraper import get_web_topics
    from core.config_loader import load_global_config

    g_cfg = load_global_config()
    token = g_cfg.get("github_token", None)

    # Get raw web data
    web_data = get_web_topics(channel_id, limit=limit, github_token=token)

    results: list[tuple[str, Path]] = []

    for item in web_data[:limit]:
        source_context = build_source_context(
            channel_id=channel_id,
            title=item.get("title", ""),
            summary=item.get("summary", ""),
            link=item.get("link", ""),
            source_type=item.get("source", "unknown")
        )
        topic = item.get("title", f"Topic for {channel_id}")
        results.append(create_full_mvp_video(channel_id, "default", topic, source_context))

    return results


def create_phase1_batch(channel_id: str, limit: int = 3) -> list[tuple[str, Path]]:
    """Backward-compatible alias."""
    return create_channel_batch(channel_id, limit)
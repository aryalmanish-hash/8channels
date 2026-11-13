"""
core/metadata_generator.py
AI-powered metadata generation.
Creates unique titles, descriptions, captions and hashtags per platform.
Falls back to template if AI unavailable.
"""

from __future__ import annotations

import json
import random
import re


# ── Hashtag Pools (fallback) ───────────────────────────────────────────────

HASHTAG_POOLS = {
    "reddit_stories": ["redditstory", "storytime", "aita", "revenge", "drama", "karma", "betrayal", "viral", "reddit", "confession"],
    "english_learning": ["learnenglish", "englishgrammar", "speakenglish", "englishtips", "vocabulary", "ielts", "englishlesson", "grammarfix"],
    "psychology": ["psychology", "humanbehavior", "mindset", "mentalhealth", "selfdevelopment", "emotionalintelligence", "darkpsychology"],
    "dark_history": ["darkhistory", "history", "mystery", "documentary", "truecrime", "ancienthistory", "warhistory", "forgotten"],
    "ai_tools_automation": ["aitools", "automation", "productivity", "artificialintelligence", "tech", "chatgpt", "freeaitools", "nocode"],
    "quiz": ["quiz", "brainteaser", "trivia", "challenge", "iqtest", "generalknowledge", "testyourself"],
    "facts": ["facts", "didyouknow", "science", "amazingfacts", "mindblown", "spacefacts", "naturefacts"],
    "sports_reviews": ["football", "worldcup", "sports", "sportsanalysis", "matchreview", "fifa", "worldcup2026", "tactics"],
}


def _pick_fallback_hashtags(channel_id: str, count: int = 5) -> list[str]:
    pool = HASHTAG_POOLS.get(channel_id, ["shorts", "viral"])
    return random.sample(pool, min(count, len(pool)))


def _try_ai_metadata(channel_id: str, topic: str, script: str) -> dict | None:
    """
    Use AI to generate complete metadata for all platforms.
    """
    try:
        from core.ai_engine import ask_ai, ask_ai_task

        prompt = f"""
You are a social media metadata expert for the {channel_id} channel.

Based on this video script:
{script[:800]}

Topic: {topic}

Generate metadata for this video. Return ONLY valid JSON with this exact structure:

{{
    "youtube_title": "catchy title under 70 chars",
    "youtube_description": "engaging 2-3 sentence description",
    "youtube_hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
    "tiktok_caption": "short catchy caption with 5 hashtags at end",
    "instagram_caption": "engaging caption with save-worthy CTA and 5 hashtags at end",
    "facebook_caption": "shareable caption with share CTA and 5 hashtags at end"
}}

===========================================
HASHTAG STRUCTURE (EACH PLATFORM MUST FOLLOW EXACTLY)
===========================================
Every caption must have EXACTLY 5 hashtags, structured like this:

  Hashtag 1: PLATFORM tag (algorithm boost)
    - TikTok    -> #fyp
    - Instagram -> #reels
    - Facebook  -> #reels
    - YouTube   -> #shorts

  Hashtag 2: #reddit (always)

  Hashtags 3, 4, 5: SPECIFIC to THIS story
    - Extract key nouns/emotions from the story
    - Use CamelCase for multi-word tags (like #SisterDrama not #sisterdrama)
    - Examples from stories:
        * story about wedding fight -> #WeddingDrama #BridezillaMoment #FamilyFeud
        * story about roommate stealing food -> #RoommateDrama #FoodTheft #PettyRevenge
        * story about affair reveal at Thanksgiving -> #ThanksgivingDrama #AffairExposed #FamilyBetrayal
        * story about coworker sabotage -> #WorkDrama #ToxicCoworker #OfficePolitics

STRICTLY AVOID these generic tags: #life #trending #viral #foryou #explore #drama #aita
(those are boring and not story-specific)

The "hashtags" JSON field at root level should be an array of 5 SHARED story-specific tags (used across all platforms).
The per-platform captions each end with their own 5 hashtags matching the above structure.

Rules:
- Each platform gets DIFFERENT caption style
- Each platform gets DIFFERENT 5 hashtags
- Hashtags MUST be extracted from the actual story content — use specific characters (names, relationships), specific events (wedding, thanksgiving, funeral), specific objects (venmo, tesla, journal), and specific emotions (betrayal, revenge, shocking)
- Mix 5 hashtags: 2 broad viral tags (#reddit #storytime #aita) + 3 SPECIFIC to this story
- Example: story about roommate eating food → #roommatedrama #foodtheft #passiveaggressive
- Example: story about wedding fight → #weddingdrama #familyfeud #bridezilla
- DO NOT use generic tags like #life #trending #foryou - be specific
- YouTube title must be under 70 characters
- TikTok caption: short punchy, MUST mention 1-2 story specifics (like the character name or the shocking act), end with 5 hashtags
- Instagram caption: 2-3 lines with story hook, encourages saves, end with 5 hashtags
- Facebook caption: longer 3-4 lines, storytelling tone, encourages shares, end with 5 hashtags
- YouTube title: catchy hook mentioning key story event, under 70 chars, may include ONE hashtag
- YouTube description: 2-3 sentences describing story tease, ends with 5 hashtags
- No markdown in the JSON values
- Return ONLY the JSON object, nothing else
"""

        system = "You output only valid JSON. No explanation. No markdown."
        response = ask_ai_task(prompt, system, task='metadata')

        if not response:
            return None

        # Clean response
        response = response.strip()
        if response.startswith("```"):
            response = re.sub(r"^```\w*\n?", "", response)
            response = re.sub(r"\n?```$", "", response)
            response = response.strip()

        data = json.loads(response)

        # Validate required fields exist
        required = ["youtube_title", "youtube_description", "youtube_hashtags",
                    "tiktok_caption", "instagram_caption", "facebook_caption"]
        for field in required:
            if field not in data:
                return None

        return data

    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"  AI metadata failed: {e}")
        return None


def _extract_hook(script: str) -> str:
    lines = script.strip().split("\n")
    for line in lines:
        clean = line.strip()
        skip_prefixes = ("title:", "topic:", "quiz:", "lesson:", "channel:")
        if clean and not any(clean.lower().startswith(p) for p in skip_prefixes):
            return clean[:150]
    return ""




def _cap_hashtags(tags, max_count=5):
    """Ensure hashtag list is max N items, deduplicated."""
    if not tags:
        return []
    seen = set()
    result = []
    for t in tags:
        if not t:
            continue
        clean = str(t).strip().lstrip("#").strip()
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(clean)
        if len(result) >= max_count:
            break
    return result


def _extract_hashtags_from_caption(caption):
    """Pull #hashtags out of a caption string."""
    import re as _re
    return _re.findall(r"#(\w+)", caption or "")


def _enforce_metadata_structure(meta):
    """
    Post-process AI metadata:
    - Cap all hashtag lists to max 5
    - Populate youtube_shorts.hashtags from description if empty
    """
    if not isinstance(meta, dict):
        return meta

    # Root hashtags
    if "hashtags" in meta:
        meta["hashtags"] = _cap_hashtags(meta["hashtags"], 5)

    # YouTube Shorts
    yt = meta.get("youtube_shorts")
    if isinstance(yt, dict):
        yt_hash = yt.get("hashtags", [])
        if not yt_hash:
            # Try extracting from description
            desc = yt.get("description", "")
            yt_hash = _extract_hashtags_from_caption(desc)
            if not yt_hash:
                # Fall back to root hashtags
                yt_hash = meta.get("hashtags", [])
        # Normalize all tags to have # prefix
        yt_hash = [t if t.startswith("#") else f"#{t}" for t in yt_hash]
        # Remove any existing #shorts or #reddit (we re-add them in order)
        others = [t for t in yt_hash
                  if t.lstrip("#").lower() not in ("shorts", "reddit")]
        # Always: #shorts first, #reddit second, then story-specific up to 3
        yt_hash = ["#shorts", "#reddit"] + others[:3]
        yt["hashtags"] = yt_hash

    # For each platform caption, ensure it has at most 5 hashtags at the end
    for key in ("tiktok", "instagram_reels", "facebook_reels", "instagram", "facebook", "youtube"):
        plat = meta.get(key)
        if isinstance(plat, dict) and "caption" in plat:
            cap = plat["caption"]
            tags_in_cap = _extract_hashtags_from_caption(cap)
            if len(tags_in_cap) > 5:
                # Keep only first 5
                keep = tags_in_cap[:5]
                # Rebuild: strip trailing hashtags then re-add only the top 5
                import re as _re
                cap_text = _re.sub(r"(#\w+\s*)+$", "", cap).strip()
                new_cap = cap_text + "\n\n" + " ".join(f"#{t}" for t in keep)
                plat["caption"] = new_cap
    return meta



def generate_metadata(channel_id: str, topic: str, script: str) -> dict:
    """
    Generate unique metadata for each platform.
    AI-first with template fallback.
    """
    # Try AI first
    ai_meta = _try_ai_metadata(channel_id, topic, script)

    if ai_meta:
        _yt_raw_title = ai_meta.get("youtube_title", topic)
        yt_title = (_yt_raw_title[:100] if len(_yt_raw_title) <= 100
                    else _yt_raw_title[:100].rsplit(" ", 1)[0].rstrip(".,!?"))
        yt_desc = ai_meta.get("youtube_description", "")
        yt_hashtags = ai_meta.get("youtube_hashtags", _pick_fallback_hashtags(channel_id))
        tt_caption = ai_meta.get("tiktok_caption", "")
        ig_caption = ai_meta.get("instagram_caption", "")
        fb_caption = ai_meta.get("facebook_caption", "")
    else:
        # Fallback to template
        hook = _extract_hook(script)
        _yt_raw_title = f"{topic}"
        yt_title = (_yt_raw_title[:100] if len(_yt_raw_title) <= 100
                    else _yt_raw_title[:100].rsplit(" ", 1)[0].rstrip(".,!?"))
        yt_hashtags = _pick_fallback_hashtags(channel_id, 5)
        yt_tags = " ".join(f"#{h}" for h in yt_hashtags)

        yt_desc = f"{hook}\n\n{yt_tags}\n\nLike and subscribe for more."

        tt_hashtags = _pick_fallback_hashtags(channel_id, 5)
        tt_tags = " ".join(f"#{h}" for h in tt_hashtags)
        tt_caption = f"{hook}\n\n{tt_tags}"

        ig_hashtags = _pick_fallback_hashtags(channel_id, 5)
        ig_tags = " ".join(f"#{h}" for h in ig_hashtags)
        ig_caption = f"{hook}\n\nSave this for later.\n\n{ig_tags}"

        fb_hashtags = _pick_fallback_hashtags(channel_id, 5)
        fb_tags = " ".join(f"#{h}" for h in fb_hashtags)
        fb_caption = f"{hook}\n\nShare this with someone who needs to see it.\n\n{fb_tags}"

    # ── Force correct youtube_shorts hashtag structure ──────────────────
    # #shorts first, #reddit second, then 3 story-specific tags
    _yt_raw = yt_hashtags if isinstance(yt_hashtags, list) else []
    # Normalize to # prefix
    _yt_raw = [t if t.startswith("#") else f"#{t}" for t in _yt_raw]
    # Strip #shorts and #reddit — we re-add in correct positions
    _yt_others = [t for t in _yt_raw
                  if t.lstrip("#").lower() not in ("shorts", "reddit")]
    # Build final: #shorts, #reddit, up to 3 story tags = exactly 5
    _yt_final = ["#shorts", "#reddit"] + _yt_others[:3]

    return {
        "title": yt_title if ai_meta else topic[:80],
        "description": yt_desc,
        "hashtags": _yt_final,
        "youtube_shorts": {
            "title": yt_title if ai_meta else topic[:80],
            "description": yt_desc,
            "hashtags": _yt_final,
        },
        "tiktok": {
            "caption": tt_caption,
        },
        "instagram_reels": {
            "caption": ig_caption,
        },
        "facebook_reels": {
            "caption": fb_caption,
        },
    }

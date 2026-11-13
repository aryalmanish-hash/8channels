"""
core/story_generator_dark_history.py

ISOLATED story generator for the dark_history channel.
Reuses shared history tracker + AI engine from reddit_stories module.
Own category pool, name pool, prompt, and banned clichés.

Flow:
  1. Wikipedia seed fetched (from scraper.fetch_wikipedia_random)
  2. AI writes 320-360 word documentary narrative
  3. Narrator gender + voice vibe hints written to temp files
  4. Title saved to history (data/story_history/dark_history_recent_titles.json)
"""

from __future__ import annotations
import re
import random
import time
from pathlib import Path

from core.ai_engine import ask_ai_task
from core.story_generator import get_recent_titles, add_to_history


# ── Dark History Category Pool (40+ specific topics) ─────────────────────
_CATEGORY_POOL = [
    # Mysteries (10)
    "unsolved disappearance",
    "unexplained mass death",
    "vanishing without a trace",
    "cursed object with real history",
    "ghost ship or abandoned vessel",
    "phantom village never found again",
    "unexplained radio transmission",
    "unidentified body found decades later",
    "mysterious death of a public figure",
    "phenomenon witnessed by many but never explained",
    # Wars & conflict (10)
    "forgotten battle of a major war",
    "war crime that was covered up",
    "spy operation that went wrong",
    "secret weapon development",
    "prisoner of war escape story",
    "civilian tragedy during wartime",
    "friendly fire disaster hidden from public",
    "resistance fighter betrayed by their own",
    "child soldiers of a forgotten conflict",
    "chemical or biological weapon test",
    # Criminals & killers (8 — non-graphic)
    "serial killer never caught",
    "criminal who escaped justice",
    "false accusation that ruined lives",
    "cult leader downfall",
    "organized crime empire collapse",
    "kidnapping that shocked a nation",
    "art or antique thief never identified",
    "pirate captain lost fortune",
    # Cursed places (7)
    "abandoned town with dark history",
    "haunted castle real events",
    "cursed film or book real deaths",
    "location where multiple tragedies happened",
    "buildings with disturbing pasts",
    "hospital or asylum with dark legacy",
    "hotel where guests kept dying",
    # Assassinations & royal murders (6)
    "assassination that changed history",
    "attempted assassination that failed",
    "conspiracy behind a famous death",
    "leader killed by their own people",
    "royal family scandal or murder",
    "poisoning of a monarch or noble",
    # Ancient dark rituals (7)
    "human sacrifice civilization",
    "ancient torture practices",
    "religious persecution mass event",
    "witch hunt real history",
    "slavery uprising or rebellion",
    "gladiator combat forgotten truth",
    "ancient burial practices with dark meaning",
    # Modern dark events (10)
    "cult mass tragedy",
    "government coverup exposed later",
    "medical experiment on unwilling subjects",
    "industrial disaster with hidden truth",
    "environmental disaster covered up",
    "corporate scandal that killed people",
    "hostage crisis with dark ending",
    "terrorist plot never fully explained",
    "airline disaster with unresolved cause",
    "school or institution abuse scandal exposed",
    # Weird history (7)
    "medieval strange law or punishment",
    "ancient plague or disease outbreak",
    "explorer who disappeared",
    "lost civilization theory with evidence",
    "prison escape that shocked the world",
    "shipwreck with strange survivor accounts",
    "expedition where the whole team died",
]


# ── Historical/Period-Appropriate Name Pool ──────────────────────────────
_NAME_POOL = [
    # Historical male
    "Heinrich", "Vladimir", "Konstantin", "Alessandro", "Nikolai",
    "Sergei", "Wilhelm", "Ferdinand", "Otto", "Karl",
    "Dmitri", "Rudolf", "Franz", "Anselm", "Boris",
    "Ivan", "Gustav", "Klaus", "Reinhardt", "Emil",
    # Historical female
    "Anastasia", "Elizabetta", "Margarethe", "Ingrid", "Katarina",
    "Sofia", "Wilhelmina", "Lenora", "Olga", "Tatiana",
    "Beatrix", "Isolde", "Adelheid", "Hilda", "Marguerite",
    # Modern historical
    "Marcus", "Julian", "Anton", "Viktor", "Erik",
    "Helena", "Vera", "Nora", "Astrid", "Freda",
]


# ── Story Angles (dark history specific) ─────────────────────────────────
_ANGLE_POOL = [
    "an event covered up for decades until recent evidence emerged",
    "witnesses who saw something but were silenced",
    "documents declassified after 50 years revealing the truth",
    "a small detail everyone missed at the time",
    "the official story was a lie",
    "one person who tried to warn everyone was ignored",
    "the true death toll was much higher than reported",
    "the perpetrators were never brought to justice",
    "evidence was destroyed to protect someone powerful",
    "survivors told a completely different story",
    "the location itself became cursed after these events",
    "modern technology revealed what really happened",
    "a diary or letter discovered years later exposed the truth",
    "the government knew and did nothing",
    "the event was blamed on the wrong people",
]


# ── BANNED clichés — overused topics ──────────────────────────────────────
_BANNED_TOPICS = [
    "Titanic sinking",
    "Adolf Hitler biography",
    "Pearl Harbor",
    "September 11",
    "JFK assassination alone",
    "Jack the Ripper",
    "Bermuda Triangle",
    "Amelia Earhart",
]


def _extract_narrator_gender(text: str) -> str:
    """Parse 'Narrator: MALE' or 'Narrator: FEMALE' from AI output."""
    m = re.search(r"Narrator:\s*(MALE|FEMALE)", text, re.IGNORECASE)
    return m.group(1).lower() if m else random.choice(["male", "female"])


def _extract_voice_vibe(text: str) -> str:
    """Parse 'Voice: DRAMATIC' etc. Valid: warm/dramatic/serious/energetic/mature."""
    m = re.search(r"Voice:\s*(WARM|DRAMATIC|SERIOUS|ENERGETIC|MATURE)", text, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    # Dark history default: serious or dramatic (never energetic)
    return random.choice(["serious", "dramatic", "mature"])


def _extract_title(text: str) -> str:
    """Parse 'Title: <text>' line from AI output. Auto-truncate to 90 chars."""
    m = re.search(r"Title:\s*(.+?)(?:\n|$)", text)
    if not m:
        return ""
    title = m.group(1).strip()
    if len(title) > 90:
        title = title[:90].rsplit(" ", 1)[0].rstrip(".,!?")
    return title


def _clean_script(text: str) -> str:
    """Remove Narrator:, Voice:, Title: lines from spoken script."""
    lines = text.splitlines()
    story_lines = []
    for ln in lines:
        low = ln.strip().lower()
        if low.startswith(("narrator:", "voice:", "title:")):
            continue
        story_lines.append(ln)
    script = "\n".join(story_lines).strip()
    # Strip markdown
    script = re.sub(r"\*+", "", script)
    script = re.sub(r"_{2,}", "", script)
    return script.strip()


def _write_hints(narrator: str, vibe: str) -> None:
    """Write narrator + vibe hints for voice_generator to pick up."""
    try:
        Path("_narrator_hint.tmp").write_text(narrator, encoding="utf-8")
        Path("_voice_vibe_hint.tmp").write_text(vibe, encoding="utf-8")
        print(f"  [DARK_HISTORY] Wrote narrator hint: {narrator}")
        print(f"  [DARK_HISTORY] Wrote voice vibe hint: {vibe}")
    except Exception:
        pass


def generate_dark_history_story(topic_seed: str = "") -> tuple[str, str]:
    """
    Main entry point. Returns (title, clean_script).

    topic_seed = optional Wikipedia summary to inspire the story.
    If empty, AI picks its own topic from the category pool.
    """
    # Random pools for variety
    rng_category = random.choice(_CATEGORY_POOL)
    rng_names    = ", ".join(random.sample(_NAME_POOL, 5))
    rng_angle    = random.choice(_ANGLE_POOL)

    # Load recent titles to avoid repeats
    recent = get_recent_titles("dark_history")
    recent_titles = [item.get("title", "") if isinstance(item, dict) else str(item)
                     for item in recent if item]

    do_not_repeat = ""
    if recent_titles:
        recent_block = "\n".join(f"  - {t}" for t in recent_titles[-20:])
        do_not_repeat = f"""

- CRITICAL: DO NOT WRITE ABOUT THESE RECENT STORIES:
{recent_block}

Your new story MUST be about a COMPLETELY DIFFERENT historical event.
"""

    banned_block = "\n".join(f"  - {t}" for t in _BANNED_TOPICS)

    prompt = f"""You are writing a documentary-style dark history story for a 90-second YouTube short.

Topic seed (may be blank): {topic_seed}

Story category to write about: {rng_category}
Narrative angle: {rng_angle}
Names you may use (if the story needs characters): {rng_names}

- STRICTLY 320-360 words. Count carefully. Under 320 is REJECTED.
- Use REAL historical facts where possible, but write in an ENGAGING narrative style.
- Documentary tone: serious, mysterious, ominous — NOT sensational or comedic.
- Include specific dates, places, and names when possible (real ones preferred).
- Hook the viewer in the first 3 seconds with a shocking or intriguing opening.
- End with a haunting question or unresolved detail that makes people think.
- NO markdown formatting (no **, *, _, #) — voice will read them literally.

- AVOID these overused topics (do NOT write about them):
{banned_block}
{do_not_repeat}

===========================================
OUTPUT FORMAT (MUST FOLLOW EXACTLY)
===========================================

LINE 1: Narrator: <MALE or FEMALE>
LINE 2: Voice: <WARM, DRAMATIC, SERIOUS, or MATURE>
LINE 3: Title: <short punchy title under 90 characters, no "AITA" prefix>
LINE 4+: The 320-360 word documentary story.

Now write the story."""

    system_msg = (
        "You are a professional documentary scriptwriter specializing in dark history. "
        "You write engaging, factual, mysterious narratives for short-form video."
    )

    # Try AI
    print(f"  [DARK_HISTORY] Category: {rng_category}")
    print(f"  [DARK_HISTORY] Angle: {rng_angle}")

    for attempt in range(5):
        try:
            response = ask_ai_task(prompt, system_msg, task="story")
            if response and len(response.strip()) > 250:
                narrator = _extract_narrator_gender(response)
                vibe     = _extract_voice_vibe(response)
                title    = _extract_title(response)
                script   = _clean_script(response)

                if not title:
                    title = f"The Untold Story of {rng_category.title()}"

                # Prepend title to spoken script (viewer sees + hears it)
                spoken_title = title.rstrip("?.!")
                script = spoken_title + ". " + script

                if len(script.split()) < 280:
                    print(f"  [DARK_HISTORY] Attempt {attempt+1}: script too short ({len(script.split())} words), retry")
                    time.sleep(1)
                    continue

                _write_hints(narrator, vibe)
                add_to_history("dark_history", title)
                print(f"  [DARK_HISTORY] Added to history: {title[:70]}")
                return title, script
            else:
                print(f"  [DARK_HISTORY] Attempt {attempt+1}: AI returned empty/short response")

        except Exception as e:
            print(f"  [DARK_HISTORY] Attempt {attempt+1} error: {e}")
            time.sleep(1)

    # Fallback if AI totally fails
    print(f"  [DARK_HISTORY] All AI attempts failed — using template fallback")
    fallback_title  = f"The Forgotten Truth About {rng_category.title()}"
    fallback_script = (
        f"{fallback_title}. History books left this part out. "
        f"There was an event, {rng_category}, that most people never learned about. "
        f"The details were hidden for years. Documents were destroyed. Witnesses were silenced. "
        f"But the truth eventually came out. What happened next changed how we understand this era. "
        f"The lesson is clear: dark events echo through time until someone speaks. "
        f"What other stories are still hidden in our history?"
    )
    _write_hints(random.choice(["male", "female"]), random.choice(["serious", "dramatic"]))
    add_to_history("dark_history", fallback_title)
    return fallback_title, fallback_script


# ── Public entry for topic seed fetching (uses existing scraper) ─────────
def get_dark_history_topic() -> str:
    """
    Fetch a Wikipedia summary as inspiration for the story.
    Returns a string of context or empty string on failure.
    """
    try:
        from core.scraper import fetch_wikipedia_random
        data = fetch_wikipedia_random("dark_history")
        if data and data.get("summary"):
            return data["summary"][:500]
    except Exception as e:
        print(f"  [DARK_HISTORY] Wikipedia seed fetch failed: {e}")
    return ""

# ═══════════════════════════════════════════════════════════════════════════
#  TOPIC BANK MODE — uses real Wikipedia events + 5 story angles
# ═══════════════════════════════════════════════════════════════════════════

# 5 angles per real event → each topic becomes 5 unique videos
_STORY_ANGLES = [
    {
        "name": "cover_up",
        "hint": "Focus on what was HIDDEN and WHY. What did the powerful people cover up? What evidence was destroyed?",
    },
    {
        "name": "human_cost",
        "hint": "Focus on the VICTIMS and SURVIVORS. Their names, their families, what they lost. The personal tragedy.",
    },
    {
        "name": "warning_ignored",
        "hint": "Focus on the WARNINGS that came before. Who predicted this? Who tried to stop it? Why were they silenced?",
    },
    {
        "name": "hidden_truth",
        "hint": "Focus on the TRUTH REVEALED YEARS LATER. What documents were declassified? What secrets came out?",
    },
    {
        "name": "political",
        "hint": "Focus on POWER PLAYS. Who benefited from this event? Which government or group used it for their own gain?",
    },
]


def generate_from_topic_bank() -> tuple[str, str, str]:
    """
    Generate a story using a REAL Wikipedia event from the topic bank
    + one of 5 story angles for variety.

    Returns: (title, clean_script, source_wiki_title)
             source_wiki_title = the Wikipedia page name used, so caller
             can mark it used via mark_topic_used()

    If bank is empty or all topics used, returns ("", "", "").
    Caller should fallback to generate_dark_history_story().
    """
    try:
        from core.wiki_harvester_dark_history import get_next_topic
    except Exception as e:
        print(f"  [DARK_HISTORY] wiki_harvester import failed: {e}")
        return ("", "", "")

    topic = get_next_topic()
    if not topic:
        print(f"  [DARK_HISTORY] Topic bank empty or all used — will fallback")
        return ("", "", "")

    wiki_title   = topic.get("title", "")
    wiki_summary = topic.get("summary", "")
    wiki_url     = topic.get("url", "")
    wiki_cat     = topic.get("category", "historical event")

    # Pick a story angle
    angle = random.choice(_STORY_ANGLES)

    # Check recent titles to avoid similar-angle repeats
    recent = get_recent_titles("dark_history")
    recent_titles = [item.get("title", "") if isinstance(item, dict) else str(item)
                     for item in recent if item]

    do_not_repeat = ""
    if recent_titles:
        recent_block = "\n".join(f"  - {t}" for t in recent_titles[-15:])
        do_not_repeat = f"""

- Recent titles used (avoid similar wording):
{recent_block}
"""

    prompt = f"""You are writing a documentary-style dark history story for a 90-second YouTube short.

REAL HISTORICAL EVENT (use these facts):
Title: {wiki_title}
Category: {wiki_cat}
Wikipedia summary: {wiki_summary}
Source URL: {wiki_url}

STORY ANGLE for this video: {angle["name"]}
Angle instruction: {angle["hint"]}

- Use the REAL facts from the summary above. Do NOT invent fake events.
- You MAY add narrative color (dialogue, atmosphere, emotional detail) but the CORE FACTS must match.
- STRICTLY 320-360 words. Count carefully. Under 320 is REJECTED.
- Documentary tone: serious, mysterious, ominous — NOT sensational or comedic.
- Hook the viewer in the first 3 seconds with a shocking fact or intriguing detail.
- End with a haunting question or unresolved detail.
- NO markdown formatting (no **, *, _, #) — voice reads them literally.
{do_not_repeat}

===========================================
OUTPUT FORMAT (MUST FOLLOW EXACTLY)
===========================================

LINE 1: Narrator: <MALE or FEMALE>
LINE 2: Voice: <WARM, DRAMATIC, SERIOUS, or MATURE>
LINE 3: Title: <short punchy title under 90 characters, reflects the {angle["name"]} angle>
LINE 4+: The 320-360 word documentary story from the {angle["name"]} perspective.

Now write the story."""

    system_msg = (
        "You are a professional documentary scriptwriter specializing in dark history. "
        "You use REAL historical facts and write engaging, factual, mysterious narratives."
    )

    print(f"  [DARK_HISTORY] Topic bank event: {wiki_title[:60]}")
    print(f"  [DARK_HISTORY] Angle: {angle['name']}")

    for attempt in range(5):
        try:
            response = ask_ai_task(prompt, system_msg, task="story")
            if response and len(response.strip()) > 250:
                narrator = _extract_narrator_gender(response)
                vibe     = _extract_voice_vibe(response)
                title    = _extract_title(response)
                script   = _clean_script(response)

                if not title:
                    title = f"{wiki_title} - The {angle['name'].replace('_',' ').title()}"

                # Prepend title to spoken script
                spoken_title = title.rstrip("?.!")
                script = spoken_title + ". " + script

                if len(script.split()) < 280:
                    print(f"  [DARK_HISTORY] Attempt {attempt+1}: too short ({len(script.split())} words)")
                    time.sleep(1)
                    continue

                _write_hints(narrator, vibe)
                add_to_history("dark_history", title)
                print(f"  [DARK_HISTORY] Added to history: {title[:70]}")
                # Return wiki_title so caller can mark_topic_used() after success
                return title, script, wiki_title
            else:
                print(f"  [DARK_HISTORY] Attempt {attempt+1}: AI returned empty response")

        except Exception as e:
            print(f"  [DARK_HISTORY] Attempt {attempt+1} error: {e}")
            time.sleep(1)

    print(f"  [DARK_HISTORY] Topic bank generation failed")
    return ("", "", "")


def mark_topic_used(wiki_title: str) -> None:
    """
    Mark a Wikipedia topic as used in the bank.
    Call this ONLY after successful video generation.
    """
    if not wiki_title:
        return
    try:
        from core.wiki_harvester_dark_history import mark_used
        mark_used(wiki_title)
        print(f"  [DARK_HISTORY] Marked topic used: {wiki_title[:60]}")
    except Exception as e:
        print(f"  [DARK_HISTORY] Could not mark used: {e}")


def generate_dark_history_story_smart() -> tuple[str, str, str]:
    """
    Smart entry point:
    1. Try topic bank (real Wikipedia events + 5 angles) first
    2. Fall back to pure AI (category pool) if bank empty/failed
    Returns: (title, clean_script, wiki_source_title or "")
    """
    # Try topic bank
    title, script, wiki_source = generate_from_topic_bank()
    if title and script:
        return title, script, wiki_source

    # Fallback to old function (pure AI, no real facts)
    print(f"  [DARK_HISTORY] Falling back to pure AI generation")
    title, script = generate_dark_history_story()
    return title, script, ""


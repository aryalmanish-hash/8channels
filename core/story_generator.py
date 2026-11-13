"""
core/story_generator.py
AI-first story generator for reddit_stories.
Uses real AI when available, fallback generator if needed.
"""

from __future__ import annotations
from pathlib import Path

import random
import re
import json
from datetime import datetime


# ── Persistent story history tracker (last N titles per channel) ──────────
_HISTORY_DIR = Path("data") / "story_history"
_HISTORY_MAX = 20  # remember last 20 titles per channel

def _history_file(channel_id: str) -> Path:
    _HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return _HISTORY_DIR / f"{channel_id}_recent_titles.json"

def get_recent_titles(channel_id: str = "reddit_stories") -> list:
    """Load last N titles for a channel."""
    try:
        f = _history_file(channel_id)
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            return data.get("titles", [])[-_HISTORY_MAX:]
    except Exception:
        pass
    return []

def add_to_history(channel_id: str, title: str) -> None:
    """Append a title to channel history, keep last N only."""
    try:
        f = _history_file(channel_id)
        history = get_recent_titles(channel_id)
        history.append({
            "title": title,
            "ts": datetime.now().isoformat(),
        })
        # Keep last N * 2 in file (some buffer), read last N when used
        history = history[-_HISTORY_MAX * 2:]
        f.write_text(json.dumps({"titles": history}, indent=2), encoding="utf-8")
    except Exception:
        pass




CONFLICTS = [
    {"action": "refusing to lend money", "past": "refused to lend them money"},
    {"action": "refusing to babysit", "past": "said no to babysitting"},
    {"action": "exposing a lie", "past": "exposed their lie in front of everyone"},
    {"action": "calling out bad behavior", "past": "called out their toxic behavior"},
    {"action": "setting a boundary", "past": "set a hard boundary"},
    {"action": "saying no to a favor", "past": "refused to do them a favor"},
    {"action": "kicking someone out", "past": "kicked them out of my house"},
    {"action": "cutting off contact", "past": "blocked them on everything"},
    {"action": "refusing to apologize", "past": "refused to say sorry"},
    {"action": "telling the truth", "past": "told the truth even though nobody wanted to hear it"},
    {"action": "choosing myself first", "past": "put myself first for once"},
    {"action": "walking away", "past": "walked away without looking back"},
    {"action": "refusing to pay", "past": "refused to pay their share"},
    {"action": "confronting a liar", "past": "confronted them about their lies"},
    {"action": "refusing to attend a wedding", "past": "said I am not coming to the wedding"},
]

CHARACTERS = [
    {"name": "my sister", "pronoun": "she", "possessive": "her"},
    {"name": "my brother", "pronoun": "he", "possessive": "his"},
    {"name": "my mother", "pronoun": "she", "possessive": "her"},
    {"name": "my father", "pronoun": "he", "possessive": "his"},
    {"name": "my best friend", "pronoun": "they", "possessive": "their"},
    {"name": "my roommate", "pronoun": "they", "possessive": "their"},
    {"name": "my coworker", "pronoun": "they", "possessive": "their"},
    {"name": "my boss", "pronoun": "they", "possessive": "their"},
    {"name": "my ex", "pronoun": "they", "possessive": "their"},
    {"name": "my mother-in-law", "pronoun": "she", "possessive": "her"},
    {"name": "my father-in-law", "pronoun": "he", "possessive": "his"},
    {"name": "my neighbor", "pronoun": "they", "possessive": "their"},
    {"name": "my partner", "pronoun": "they", "possessive": "their"},
    {"name": "my cousin", "pronoun": "they", "possessive": "their"},
    {"name": "my husband", "pronoun": "he", "possessive": "his"},
    {"name": "my wife", "pronoun": "she", "possessive": "her"},
]

SETTINGS = [
    "at a family dinner",
    "during the holidays",
    "at a wedding",
    "at a birthday party",
    "during a road trip",
    "at Thanksgiving dinner",
    "at a barbecue",
    "at a funeral",
    "during Christmas",
    "at a graduation party",
    "during a family vacation",
    "at a restaurant",
    "at work",
    "while house sitting",
    "during a phone call",
    "at a family reunion",
]

BUILDUPS = [
    "I tried to be patient. I really did.",
    "I kept my mouth shut for as long as I could.",
    "I had been dealing with this for months.",
    "At first I thought it was a one-time thing.",
    "I ignored it the first few times.",
    "I gave them chance after chance.",
    "I tried to talk about it calmly but they shut me down.",
    "I had been biting my tongue for way too long.",
]

ESCALATIONS = [
    "But then things went too far.",
    "And then they crossed the line.",
    "What happened next was the final straw.",
    "But that night everything changed.",
    "Then they did something I could not ignore.",
    "Then it all blew up.",
]

EMOTIONS = [
    "I couldn't believe what I was hearing.",
    "My jaw literally dropped.",
    "I was left completely speechless.",
    "The audacity was unreal.",
    "I felt like the ground was pulled from under me.",
    "I was shaking with frustration.",
]

AFTERMATHS = [
    "Now everyone is calling me selfish.",
    "My family thinks I went too far.",
    "People are taking sides and it is getting ugly.",
    "I am being called heartless.",
    "Everyone says I ruined everything.",
    "Now they are giving me the silent treatment.",
    "I am being blamed for the whole situation.",
    "People are saying I overreacted.",
]

JUSTIFICATIONS = [
    "But here is the thing. I had my reasons.",
    "What nobody understands is I had been dealing with this for years.",
    "People only see the ending. They do not see what I went through.",
    "I know it looked bad from the outside. But they have no idea what led to this.",
]

ENDINGS = [
    "Part of me feels guilty but another part knows I did the right thing.",
    "I keep replaying it in my head.",
    "I need unbiased opinions from people who do not know us.",
    "Was I wrong for standing my ground?",
    "Everyone in my life has an opinion. Now I want yours.",
]


def _object_pronoun(pronoun: str) -> str:
    if pronoun == "he":
        return "him"
    if pronoun == "she":
        return "her"
    return "them"


def generate_story_elements() -> dict:
    return {
        "conflict": random.choice(CONFLICTS),
        "character": random.choice(CHARACTERS),
        "setting": random.choice(SETTINGS),
        "buildup": random.choice(BUILDUPS),
        "escalation": random.choice(ESCALATIONS),
        "emotion": random.choice(EMOTIONS),
        "aftermath": random.choice(AFTERMATHS),
        "justification": random.choice(JUSTIFICATIONS),
        "ending": random.choice(ENDINGS),
    }


def generate_title(elements: dict) -> str:
    char = elements["character"]["name"]
    action = elements["conflict"]["action"]
    setting = elements["setting"]
    templates = [
        f"AITA for {action} to {char}?",
        f"AITA for {action} {setting}?",
        f"AITA for {action} after what {char} did?",
        f"AITA for {action} to {char} {setting}?",
        f"I ended up {action}. AITA?",
    ]
    return random.choice(templates)


def _clean_ai_title(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^[\-\*\d\.\)\s]+", "", raw)
    return raw.strip()


def _try_ai_story(topic: str | None = None) -> tuple[str, str] | None:
    """
    Generate story via AI.
    Returns (title, clean_script) where clean_script has NO Narrator: or Title: lines.
    Also writes narrator gender to _narrator_hint.tmp for voice generator.
    """
    try:
        from core.ai_engine import ask_ai, ask_ai_task

        if topic and len(topic.strip()) > 10:
            topic_line = f"Topic seed: {topic.strip()}"
        else:
            topic_line = "Create an original fictional Reddit AITA topic."

        # ── Random seeds injected per call for variety ──
        import random as _r
        _CATEGORY_POOL = [
    # --- Relationships ---
    "living together conflict",
    "long distance relationship falling apart",
    "breaking up and dividing shared stuff",
    "jealousy between best friends",
    "friend group taking sides",
    "unrequited feelings exposed",
    "reconnecting with old ex",
    "partner spending too much time with coworker",
    "online friendship becoming real-life problem",
    "age gap relationship drama",
    # --- Family ---
    "sibling rivalry over inheritance",
    "parent controlling adult child decisions",
    "in-laws showing up unannounced",
    "family money dispute after death",
    "stepfamily conflict over favourites",
    "adult child refusing to care for parent",
    "grandparent ignoring boundaries with grandkids",
    "family secret revealed at wrong moment",
    "sibling using family tragedy for attention",
    "cousin drama at family reunion",
    # --- Work and Career ---
    "unfair boss giving credit to wrong person",
    "colleague sabotaging job application",
    "refusing overtime with no pay",
    "coworker crossing personal boundaries",
    "whistleblowing on company wrongdoing",
    "work friendship turning toxic",
    "client disrespecting service worker",
    "remote work schedule conflict with family",
    "promotion going to less qualified person",
    "side hustle causing workplace conflict",
    # --- School and College ---
    "group project where one person does nothing",
    "professor grading unfairly",
    "college roommate nightmare",
    "cheating accusation that is false",
    "school bully grown up and wants forgiveness",
    "scholarship stolen by family member",
    "dropping out against parents wishes",
    "campus housing conflict",
    # --- Everyday Public Life ---
    "restaurant complaint going wrong",
    "gym equipment hog confrontation",
    "grocery store checkout argument",
    "public transport seat conflict",
    "neighbour noise complaint",
    "parking space dispute",
    "hotel check-in nightmare",
    "coffee shop table squatter",
    "queue jumping confrontation",
    "library or shared space conflict",
    # --- Pets and Animals ---
    "neighbour complaining about my dog",
    "partner giving away my pet without asking",
    "stray animal causing dispute",
    "pet damaging neighbour property",
    "allergy clash between roommates over pet",
    "inheriting someone elses difficult pet",
    # --- Money and Finance ---
    "splitting bills unfairly in shared house",
    "friend refusing to pay back loan",
    "inheritance dispute between siblings",
    "partner hiding secret debt",
    "family expecting free labour or services",
    "being asked to pay for others at restaurant",
    "crowdfunding drama gone wrong",
    # --- Social Media and Technology ---
    "posting something online that causes drama",
    "being exposed in a group chat",
    "someone sharing private photos without consent",
    "gaming addiction causing relationship problems",
    "streaming or content creation conflict with partner",
    "phone privacy violated by partner or parent",
    "fake account discovered",
    # --- Health and Personal ---
    "medical decision family disagrees with",
    "diet or food restriction ignored by host",
    "mental health boundary repeatedly crossed",
    "sleep schedule conflict with partner",
    "disability accommodation refused",
    "someone sharing my private health info",
    # --- Hobbies and Interests ---
    "art or creative work stolen or copied",
    "sports team internal drama",
    "cooking at home causes conflict",
    "book or hobby club falling out",
    "concert or event ticket dispute",
    "collecting hobby mocked by partner",
    # --- Travel and Events ---
    "holiday ruined by someone else decision",
    "travel companion being difficult",
    "event invitation drama",
    "cancelling plans at last minute",
    "gift giving that backfires badly",
    "birthday or celebration ignored",
]
        _NAME_POOL = [
    # Female names
    "Priya", "Zoe", "Fatima", "Ingrid", "Cleo",
    "Nadia", "Petra", "Yuki", "Amara", "Sienna",
    "Lena", "Roxanne", "Camille", "Tasha", "Bridget",
    "Noelle", "Imogen", "Lyra", "Celeste", "Dara",
    "Suki", "Miriam", "Valentina", "Odette", "Fiona",
    "Harriet", "Wren", "Scarlett", "Noor", "Tamsin",
    "Blythe", "Freya", "Isolde", "Zahra", "Vivienne",
    # Male names
    "Cormac", "Devon", "Jasper", "Hunter", "Roman",
    "Cyrus", "Fletcher", "Alistair", "Dashiell", "Rowan",
    "Beckett", "Stellan", "Leif", "Idris", "Callum",
    "Dorian", "Piers", "Emrys", "Theron", "Bastian",
    "Raffael", "Soren", "Zane", "Matteo", "Kieran",
    "Brennan", "Caspian", "Enzo", "Florian", "Gideon",
    "Hawk", "Ignacio", "Jovan", "Knox", "Leandro",
    # Gender neutral names
    "Avery", "Riley", "Quinn", "Sage", "River",
    "Blair", "Casey", "Drew", "Ellis", "Finley",
    "Gray", "Harlow", "Indigo", "Jules", "Kendall",
    "Lane", "Morgan", "Nova", "Oakley", "Phoenix",
]
        _ANGLE_POOL = [
    "I did something to protect myself but it hurt someone else",
    "I enforced a boundary and they called me selfish",
    "I told the truth and everyone turned on me",
    "I refused to help and now everyone blames me",
    "I did something out of frustration and it escalated",
    "I made a decision about my own life and they took it personally",
    "I said no for the first time ever and they exploded",
    "I exposed someone and they claim I betrayed them",
    "I chose myself over someone else and now feel guilty",
    "I reacted to years of being treated badly and snapped",
    "I kept a secret to protect someone but it backfired",
    "I gave honest feedback nobody wanted to hear",
    "I set a financial boundary and they called me greedy",
    "I stopped covering for someone and they got caught",
    "I changed a plan last minute for good reason but ruined it for others",
    "I cut someone off after one final thing too many",
    "I treated two people differently and one found out",
    "I asked for something reasonable and they made it dramatic",
    "I did what I was told to do and somehow it is still my fault",
    "I helped someone and they used it against me later",
]
        _rng_category = _r.choice(_CATEGORY_POOL)
        _rng_names    = ", ".join(_r.sample(_NAME_POOL, 6))
        _rng_angle    = _r.choice(_ANGLE_POOL)

        # ── Load recent story titles to avoid repeating ──
        _recent = get_recent_titles("reddit_stories")
        _recent_titles = [item.get("title", "") if isinstance(item, dict) else str(item)
                          for item in _recent if item]
        if _recent_titles:
            _recent_block = "\n".join(f"  - {t}" for t in _recent_titles[-20:])
            _do_not_repeat = f"""

- CRITICAL: DO NOT WRITE ABOUT SIMILAR THEMES TO THESE RECENT STORIES:
{_recent_block}

Your new story MUST be about a COMPLETELY DIFFERENT scenario, characters, and setting.
Do not reuse the same conflict type, character relationship, or location as any story above.
"""
        else:
            _do_not_repeat = ""

        prompt = f"""
You are writing a VIRAL Reddit AITA story that will be turned into a 90-second short video.

{topic_line}

{_do_not_repeat}
===========================================
OUTPUT FORMAT (MUST FOLLOW EXACTLY)
===========================================
LINE 1: Narrator: MALE   (or)   Narrator: FEMALE
   -- Pick based on the narrator you write.
LINE 2: Voice: WARM   (or)   DRAMATIC / SERIOUS / ENERGETIC / MATURE
   -- Pick voice tone that best matches the story\'s emotional vibe:
        WARM       = family/friendship/heartfelt stories
        DRAMATIC   = shocking betrayal, revelation, revenge
        SERIOUS    = accusations, injustice, principle-based conflicts
        ENERGETIC  = wild wedding drama, chaos, comedy-tinged rage
        MATURE     = long-term relationship, grief, life-changing choices
LINE 3: Title: <title starting with "AITA for..." ending with "?" — MUST be under 90 characters total>
LINE 4: (blank)
LINE 5+: The story in this order:

  PART 1 - HOOK (first 2 sentences):
    Drop the reader into the middle of tension. Something shocking or bold.

  PART 2 - SETUP (2-3 sentences):
    Brief context - who these people are, the relationship, why it matters.
    Use REAL NAMES for characters (Sarah, Mike, Emma, David, etc).
    You can mention ages naturally in flowing sentences like
    "I'm 28" or "my sister Emma is 24" — but NEVER use "(28F)" or "(35M)" brackets format.

  PART 3 - CONFLICT ESCALATION (3-4 sentences):
    Build what happened. Include ONE piece of specific dialogue in quotes.
    Show the antagonist's toxic behavior clearly.

  PART 4 - THE MOMENT (2-3 sentences):
    The exact moment things blew up. What the narrator did or said.

  PART 5 - AFTERMATH (2 sentences):
    Family/friends reactions. Someone is calling narrator names now.

  PART 6 - CLIFFHANGER QUESTION (last line):
    Ask a specific "AITA?" question that makes viewers want to comment.

===========================================
QUALITY RULES
===========================================
- Length: STRICTLY 320 to 360 words. Count words carefully. Anything under 320 is REJECTED and thrown away. Do not write shorter under any circumstance.
- Include AT LEAST ONE line of dialogue in double quotes
- Use REAL NAMES not brackets: "Sarah told me she was pregnant" NOT "my sister (24F) told me"
- Include specific details: "we dated 4 years", "we lived on Oakwood Street"
- Casual conversational Reddit tone
- Narrator is MOSTLY reasonable but has ONE questionable action

===========================================
STRICTLY AVOID
===========================================
- NO age+gender brackets like (28F), (35M), [24 F]  -- use names + natural age mentions instead

- AVOID these OVERUSED cliché plots (do NOT write about them):
  * ANY wedding drama (venue, dress, planning, invitations, cake) - BANNED
  * Sister's fiancé cheating - BANNED
  * Kicking mother-in-law out - BANNED
  * Mom/Dad favoritism - BANNED
  * Airplane seat swap - BANNED
  * Reclining chair on flight - BANNED
  * Coworker taking credit for project - BANNED
  * Roommate eating food/using clothes - BANNED
  Pick a COMPLETELY DIFFERENT, FRESH conflict from your assigned category.

- BE BOLD AND CREATIVE. Push into unusual territory:
  * Weird everyday moments no one talks about
  * Modern tech-era drama (app reviews, Uber driver, delivery mistake, smart doorbell)
  * Cultural or generational clashes
  * Ethical dilemmas with no clear answer
  * Small stakes but intense emotions (parking spot war, gym etiquette, elevator awkwardness)

- Your CATEGORY for this story is: {_rng_category}
  Write a story fitting THIS category. Do NOT pick a different one.

- Your NAME POOL for characters is: {_rng_names}
  Use ONLY names from this list. Do NOT reuse popular names like Emma, Rachel, Alex, David, Mike, Sarah.

- Your CONFLICT ANGLE is: {_rng_angle}
  Center the story around this angle.
- NO markdown formatting like **, *, _, or # symbols. NO bullet points. NO bold. NO italic. Plain text only - voice engine reads asterisks literally
- No "Update:" sections
- No cheesy morals or lessons
- Do NOT resolve the situation - leave it unresolved
"""
        system = "You are a top-tier Reddit AITA story writer. Your stories go viral because they feel 100% real, use specific realistic details, include natural dialogue, and end with genuinely debatable AITA questions. You never write cheesy morals or resolve the conflict."

        response = ask_ai_task(prompt, system, task='story')
        if not response or len(response) < 120:
            return None

        # ── PARSE the AI response ──
        raw_lines = [x.rstrip() for x in response.splitlines()]

        # ── Skip any AI preamble BEFORE the actual story format starts ──
        # AI often writes "Sure! Here's a story..." then the real content.
        # We look for the FIRST line starting with "narrator:" or "title:"
        # and drop everything before it.
        first_content_idx = 0
        for _idx, _l in enumerate(raw_lines):
            _low = _l.strip().lower().lstrip("*_ ").rstrip("*_ ")
            if _low.startswith(("narrator:", "title:", "voice:")):
                first_content_idx = _idx
                break
        raw_lines = raw_lines[first_content_idx:]

        narrator_gender = None
        voice_vibe = None
        title = None
        story_lines = []

        VALID_VIBES = {"WARM", "DRAMATIC", "SERIOUS", "ENERGETIC", "MATURE"}

        for ln in raw_lines:
            stripped = ln.strip()
            # Strip markdown bold/italic markers so **Narrator:** becomes Narrator:
            stripped_clean = stripped.replace("**", "").replace("__", "").strip()
            stripped_clean = stripped_clean.lstrip("*_ ").rstrip("*_ ").strip()
            low = stripped_clean.lower()

            if not stripped:
                # Keep blank lines only inside the story body
                if title is not None:
                    story_lines.append("")
                continue

            if low.startswith("narrator:"):
                val = stripped_clean.split(":", 1)[1].strip().upper()
                if "FEMALE" in val:
                    narrator_gender = "female"
                elif "MALE" in val:
                    narrator_gender = "male"
                continue

            if low.startswith("voice:"):
                val = stripped_clean.split(":", 1)[1].strip().upper()
                # Extract first known vibe word (handles extra text)
                for vibe in VALID_VIBES:
                    if vibe in val:
                        voice_vibe = vibe.lower()
                        break
                continue

            if low.startswith("title:") and title is None:
                title = stripped_clean.split(":", 1)[1].strip()
                # Safety: truncate at 90 chars on word boundary
                if len(title) > 90:
                    title = title[:90].rsplit(" ", 1)[0].rstrip(".,!?")
                continue

            # Everything else is story content
            story_lines.append(stripped)

        # If AI didn't provide a Title:, use topic as fallback
        if not title:
            title = topic.strip() if topic else "AITA story"

        # Build clean script — NO Narrator: line, NO Title: line
        clean_script = chr(10).join(l for l in story_lines if l).strip()

        if len(clean_script) < 100:
            return None

        # ── Prepend spoken version of title so voice + captions include it ──
        # Replace "AITA" -> "Am I the asshole" so TTS reads naturally
        if title:
            spoken_title = title
            # Case-insensitive replacements
            spoken_title = re.sub(r"\bAITA\b", "Am I the asshole", spoken_title)
            spoken_title = re.sub(r"\bWIBTA\b", "Would I be the asshole", spoken_title)
            spoken_title = re.sub(r"\bA-I-T-A\b", "Am I the asshole", spoken_title)
            # Add title as opening line with period so voice pauses naturally
            clean_script = spoken_title.rstrip("?.!") + ". " + clean_script

        # Save gender + voice vibe hint files for voice_generator.
        # If new response has no data, KEEP the previous hints (don't delete).
        try:
            hint_file = Path.cwd() / "_narrator_hint.tmp"
            vibe_file = Path.cwd() / "_voice_vibe_hint.tmp"

            if narrator_gender:
                hint_file.write_text(narrator_gender, encoding="utf-8")
                print(f"  [STORY] Wrote narrator hint: {narrator_gender}")

            if voice_vibe:
                vibe_file.write_text(voice_vibe, encoding="utf-8")
                print(f"  [STORY] Wrote voice vibe hint: {voice_vibe}")
        except Exception:
            pass

        # Save title to history so next generation avoids repeating
        if title:
            add_to_history("reddit_stories", title)
            print(f"  [STORY] Added to history: {title[:60]}")

        return title, clean_script

    except Exception as e:
        print(f"  AI story generation failed: {e}")
        return None


def generate_reddit_story(topic: str = None) -> tuple[str, str]:
    """
    AI-first reddit story generation.
    Falls back to combinatorial template if AI fails.
    """
    ai_result = _try_ai_story(topic)
    if ai_result:
        return ai_result

    elements = generate_story_elements()
    char = elements["character"]
    conflict = elements["conflict"]
    setting = elements["setting"]
    obj = _object_pronoun(char["pronoun"])

    if topic and len(topic) > 15:
        title = topic
    else:
        title = generate_title(elements)

    script = f"""Title: {title}

So this happened {setting} and I still can not believe how it played out.

Let me give you the full context so you can judge for yourself.

It all started when {char["name"]} asked me for something I was not comfortable with.

{elements["buildup"]}

{elements["escalation"]}

{elements["emotion"]}

So I {conflict["past"]}.

Right there. {setting.capitalize()}. In front of everyone.

{elements["aftermath"]}

{char["name"]} said I humiliated {obj}. That I had no right to do what I did.

But {char["pronoun"]} conveniently forgot what {char["pronoun"]} did to me.

{elements["justification"]}

{elements["ending"]}

So Reddit. I need your honest verdict.

Am I the one in the wrong here?

Drop your answer in the comments. NTA or YTA. Let me know.
""".strip()

    return title, script


def _try_ai_topics(count: int = 5) -> list[dict] | None:
    try:
        from core.ai_engine import ask_ai, ask_ai_task

        prompt = f"""
Generate {count} fictional Reddit AITA story titles.

Rules:
- One title per line
- No numbering
- No bullets
- Make them dramatic, varied, and believable
- Start each with AITA or a very Reddit-style framing
"""

        system = "You generate viral Reddit-style topic ideas."
        response = ask_ai_task(prompt, system, task='story')
        if not response:
            return None

        lines = [_clean_ai_title(x) for x in response.splitlines() if x.strip()]
        lines = [x for x in lines if len(x) > 10][:count]
        if not lines:
            return None

        results = []
        for line in lines:
            results.append({
                "title": line,
                "summary": "AI-generated Reddit story topic.",
                "link": "",
                "source": "ai_generated",
            })
        return results
    except Exception as e:
        print(f"  AI topic generation failed: {e}")
        return None


def get_story_topics(count: int = 5) -> list[dict]:
    """
    AI-first topic generation for reddit_stories.
    """
    ai_topics = _try_ai_topics(count)
    if ai_topics:
        return ai_topics

    topics = []
    for _ in range(count):
        elements = generate_story_elements()
        title = generate_title(elements)
        char = elements["character"]
        summary = f"Drama involving {char['name']} {elements['setting']}. {elements['emotion']}"
        topics.append({
            "title": title,
            "summary": summary,
            "link": "",
            "source": "ai_generated",
        })
    return topics
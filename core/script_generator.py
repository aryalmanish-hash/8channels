"""
core/script_generator.py
Generates scripts using AI engine (Groq/Gemini).
Falls back to template if AI unavailable.
"""

from __future__ import annotations

from core.config_loader import load_channel_config




def _enforce_word_limit(script: str, min_words: int = 220, max_words: int = 270) -> str:
    """
    Enforce word count target of 135-160 words for 50-70 second videos.
    - If too long  : trim at sentence boundary near max_words
    - If too short : return as-is
    """
    words = script.split()
    count = len(words)
    print(f"  Script word count: {count} (target {min_words}-{max_words})")

    if count <= max_words:
        return script

    # Trim to max_words
    trimmed = " ".join(words[:max_words])
    # Find last sentence-ending punctuation in last 30% of text
    for punct in [".", "!", "?"]:
        last = trimmed.rfind(punct)
        if last > len(trimmed) * 0.7:
            trimmed = trimmed[:last + 1]
            break

    new_count = len(trimmed.split())
    print(f"  Script trimmed: {count} -> {new_count} words")
    return trimmed

def generate_script(channel_id: str, video_type: str, topic: str, source_context: dict = None) -> str:
    """
    Generate script using AI first, then template fallback.
    """
    cfg = load_channel_config(channel_id)
    allowed = cfg.get("video_types", [])
    if video_type not in allowed and allowed:
        video_type = allowed[0]

    ctx = source_context or {}
    title = ctx.get("title", topic)
    summary = ctx.get("summary", "")

    # ── reddit_stories has its OWN specific AI prompt with Narrator/Voice/Title format ──
    # Skip the generic script AI and go straight to _reddit_story
    if channel_id == "reddit_stories":
        try:
            return _reddit_story(title, summary)
        except Exception as e:
            print(f"  reddit_story failed: {e}")
            # If reddit-specific fails, fall through to generic

    # ── dark_history has its OWN topic-bank + 5-angle story generator ──
    # Uses REAL Wikipedia events, not made-up content
    if channel_id == "dark_history":
        try:
            from core.story_generator_dark_history import generate_dark_history_story_smart
            dh_title, dh_script, dh_wiki = generate_dark_history_story_smart()
            if dh_title and dh_script:
                # Save wiki source to temp file so workflow can mark it used after publish
                if dh_wiki:
                    try:
                        from pathlib import Path as _P
                        _P("_dark_history_wiki_source.tmp").write_text(dh_wiki, encoding="utf-8")
                    except Exception:
                        pass
                return dh_script
        except Exception as e:
            print(f"  dark_history smart generator failed: {e}")
            # Fall through to generic AI + template

    # ── All other channels: try generic AI first ──
    try:
        from core.ai_engine import generate_script_with_ai
        ai_script = generate_script_with_ai(channel_id, title, summary)
        if ai_script and len(ai_script) > 100:
            return _enforce_word_limit(ai_script, min_words=220, max_words=270)
    except Exception as e:
        print(f"  AI script generation failed: {e}")

    # Fallback to templates
    if channel_id == "reddit_stories":
        return _reddit_story(title, summary)
    if channel_id == "english_learning":
        return _english_script(title, summary)
    if channel_id == "psychology":
        return _psychology_script(title, summary)
    if channel_id == "dark_history":
        return _dark_history_script(title, summary)
    if channel_id == "ai_tools_automation":
        return _ai_tools_script(title, summary, ctx.get("source_type", ""))
    if channel_id == "quiz":
        return _quiz_script(title, summary)
    if channel_id == "facts":
        return _facts_script(title, summary)
    if channel_id == "sports_reviews":
        return _sports_script(title, summary)
    return _generic_script(channel_id, title, summary)


def _reddit_story(title: str, summary: str) -> str:
    from core.story_generator import generate_reddit_story
    _, script = generate_reddit_story(title)
    return script


def _english_script(title: str, summary: str) -> str:
    lesson_content = summary if summary else "understanding this common grammar pattern"
    return f"""Lesson: {title}

Most English learners get this wrong every single day.

Today we are looking at: {title}

{lesson_content}

Here is the mistake most people make.

They follow grammar rules from their own language instead of English rules.

Focus on what sounds natural to a native speaker.

Quick tip: if it sounds awkward when you say it out loud, it is probably wrong.

Follow for one English lesson every day.
""".strip()


def _psychology_script(title: str, summary: str) -> str:
    insight = summary if summary else "the way our brain processes this situation"
    return f"""Topic: {title}

Psychologists discovered something most people never think about.

{insight}

When people face this situation, the brain does something automatic.

It tries to protect you by either avoiding the problem or reacting too strongly.

Most people do not even realize this is happening.

Here is what self-aware people do differently.

They pause. Notice the reaction. Then choose how to respond.

That small gap is where real emotional intelligence lives.

Save this if it made you think.
""".strip()


def _dark_history_script(title: str, summary: str) -> str:
    historical_context = summary if summary else "events that history books often leave out"
    return f"""Topic: {title}

History books left this part out.

{historical_context}

It started with something most people at the time thought was normal.

Nobody questioned it. And that is exactly how it continued.

By the time people understood what was happening, it was too late to stop it.

What makes this important today is the warning it contains.

Things can go very wrong when nobody pays attention.

Always verify historical claims with reliable academic sources.
""".strip()


def _ai_tools_script(title: str, summary: str, source_type: str) -> str:
    tool_info = summary if summary else "a powerful automation capability"
    source_note = "Found on GitHub" if source_type == "github" else "Trending in AI"
    return f"""Topic: {title}

{source_note} and most people have no idea this exists.

{tool_info}

Here is why this matters for your workflow.

Step one: understand what problem it solves.

Step two: test it on one small task first.

Step three: if it works, integrate it into your daily workflow.

The best tools solve one real problem quickly.

Try this and tell me in the comments how much time it saved you.
""".strip()


def _quiz_script(title: str, summary: str) -> str:
    quiz_context = summary if summary else "general knowledge most people think they know"
    return f"""Quiz: {title}

Think you know the answer? Let us find out.

Based on: {quiz_context}

Here is your question.

Option A is the first possible answer.

Option B is the second possible answer.

Option C is the third possible answer.

Five seconds. Think carefully.

5... 4... 3... 2... 1...

The correct answer is revealed now.

The most common mistake is choosing the obvious answer.

When you look at the facts the correct answer becomes clear.

Comment your answer before watching the reveal.

Follow for daily quiz challenges.
""".strip()


def _facts_script(title: str, summary: str) -> str:
    fact_content = summary if summary else "something that sounds impossible but is completely real"
    return f"""Topic: {title}

This fact sounds completely made up. But it is real.

{fact_content}

The science behind it is straightforward once you understand the basics.

But because it sounds so strange most people never look into it.

The thing you thought you knew is only part of the story.

The full picture is much more interesting.

Once you know this you will notice it everywhere.

Follow for more mind-blowing facts every day.
""".strip()


def _sports_script(title: str, summary: str) -> str:
    match_context = summary if summary else "a moment that changed the entire game"
    return f"""Topic: {title}

This moment changed everything.

{match_context}

Here is what most people missed when they watched it live.

On the surface it looked simple. But the tactics were calculated.

First: the setup. The real decision was made before the moment happened.

Second: the execution. This is what everyone saw.

Third: the aftermath. This is what it changed going forward.

Context matters in sports analysis.

The moment is just the surface. The thinking behind it is the real story.

Follow for breakdowns like this every week.
""".strip()


def _generic_script(channel_id: str, title: str, summary: str) -> str:
    content = summary if summary else "interesting content for this topic"
    return f"""Channel: {channel_id}
Topic: {title}

{content}
""".strip()

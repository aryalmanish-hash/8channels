"""
core/safety_checker.py
AI-enhanced content safety checker.
Basic keyword check + optional AI review.
"""

from __future__ import annotations

import json
from datetime import datetime


RISK_KEYWORDS = [
    "kill", "murder", "suicide", "bomb", "terrorist",
    "hate", "racist", "explicit", "nsfw", "illegal",
    "slur", "extremist", "graphic violence",
]

SENSITIVE_TOPICS = [
    "self-harm", "eating disorder", "child abuse",
    "sexual assault", "domestic violence",
]


def check_script(channel_id: str, script: str) -> dict:
    """
    Check script for safety issues.
    Uses keyword check + optional AI review.
    """
    flags = []
    lower = script.lower()

    # Keyword check
    for word in RISK_KEYWORDS:
        if word in lower:
            flags.append(f"Risk keyword: '{word}'")

    for topic in SENSITIVE_TOPICS:
        if topic in lower:
            flags.append(f"Sensitive topic: '{topic}'")

    # AI safety check if available
    ai_flags = _ai_safety_check(script, channel_id)
    if ai_flags:
        flags.extend(ai_flags)

    report = {
        "channel_id": channel_id,
        "checked_at": datetime.now().isoformat(),
        "flags": flags,
        "flag_count": len(flags),
        "passed": len(flags) == 0,
        "manual_review_required": len(flags) > 0,
    }

    return report


def _ai_safety_check(script: str, channel_id: str) -> list[str]:
    """
    Optional AI-based safety review.
    Returns list of concerns or empty list.
    """
    try:
        from core.ai_engine import ask_ai

        prompt = f"""
Review this video script for content safety.

Script:
{script[:600]}

Channel type: {channel_id}

Check for:
1. Hate speech or discrimination
2. Misinformation or dangerous claims
3. Content inappropriate for general audience
4. Legal risks

If the script is safe, respond with exactly: SAFE
If there are concerns, list each one on a new line starting with CONCERN:
"""
        system = "You are a content safety reviewer. Be thorough but reasonable."
        response = ask_ai(prompt, system)

        if not response:
            return []

        if "SAFE" in response.strip().upper() and "CONCERN" not in response.upper():
            return []

        concerns = []
        for line in response.splitlines():
            line = line.strip()
            if line.upper().startswith("CONCERN:"):
                concern = line.split(":", 1)[1].strip()
                if concern:
                    concerns.append(f"AI flagged: {concern}")

        return concerns

    except Exception:
        return []

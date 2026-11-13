"""
core/ai_validator.py
Validates AI-generated scripts. Checks quality and can request rewrites.
"""

from __future__ import annotations

import json
from pathlib import Path


def validate_script(script: str, channel_id: str) -> dict:
    """
    Basic validation checks on a script.
    Returns a report dict.
    """
    issues = []
    score = 100

    words = script.split()
    word_count = len(words)

    # Length check
    if word_count < 80:
        issues.append("Script too short (under 80 words)")
        score -= 30
    elif word_count > 400:
        issues.append("Script too long (over 400 words)")
        score -= 15

    # Check for empty or placeholder content
    lower = script.lower()
    if "placeholder" in lower:
        issues.append("Contains placeholder text")
        score -= 25

    # Check first line is a hook
    lines = [l.strip() for l in script.strip().splitlines() if l.strip()]
    if lines:
        first = lines[0].lower()
        if first.startswith("channel:") or first.startswith("video type:"):
            issues.append("First line is metadata, not a hook")
            score -= 20

    # Check has ending / CTA
    if lines:
        last_3 = " ".join(lines[-3:]).lower()
        cta_words = ["comment", "follow", "subscribe", "let me know", "drop", "share", "save", "verdict"]
        has_cta = any(w in last_3 for w in cta_words)
        if not has_cta:
            issues.append("No call-to-action at end")
            score -= 10

    # Grammar red flags
    grammar_issues = [
        ("humiliated they", "Bad pronoun usage"),
        ("humiliated he", "Bad pronoun usage"),
        ("humiliated she", "Bad pronoun usage"),
        ("i am agree", "Grammar error"),
        ("more better", "Grammar error"),
        ("most best", "Grammar error"),
    ]
    for pattern, msg in grammar_issues:
        if pattern in lower:
            issues.append(msg)
            score -= 15

    score = max(0, min(100, score))

    return {
        "score": score,
        "word_count": word_count,
        "issues": issues,
        "passed": score >= 60,
        "needs_rewrite": score < 50,
    }


def try_ai_rewrite(script: str, channel_id: str, issues: list) -> str | None:
    """
    Ask AI to fix issues in a script.
    Returns improved script or None.
    """
    try:
        from core.ai_engine import ask_ai

        issues_text = "\n".join(f"- {i}" for i in issues)

        prompt = f"""
Here is a video script that has quality issues:

{script}

Issues found:
{issues_text}

Please rewrite this script fixing all the issues above.
Keep the same topic and style.
Make it 170 to 240 words.
Keep it natural and engaging.
No markdown. No bullets. No hashtags.
Return only the final improved script.
"""
        system = f"You are a script editor for the {channel_id} channel. Fix quality issues while keeping the voice natural."

        result = ask_ai(prompt, system)
        if result and len(result) > 100:
            return result.strip()
        return None
    except Exception as e:
        print(f"  AI rewrite failed: {e}")
        return None


def validate_and_improve(script: str, channel_id: str, workspace: Path = None) -> str:
    """
    Main function. Validates script, tries AI rewrite if needed.
    Saves validation report to workspace.
    Returns best available script.
    """
    report = validate_script(script, channel_id)

    if report["needs_rewrite"]:
        improved = try_ai_rewrite(script, channel_id, report["issues"])
        if improved:
            # Re-validate the improved version
            new_report = validate_script(improved, channel_id)
            if new_report["score"] > report["score"]:
                report["rewrite_attempted"] = True
                report["rewrite_success"] = True
                report["original_score"] = report["score"]
                report["improved_score"] = new_report["score"]
                script = improved
            else:
                report["rewrite_attempted"] = True
                report["rewrite_success"] = False
        else:
            report["rewrite_attempted"] = True
            report["rewrite_success"] = False

    if workspace:
        report_path = workspace / "script_quality_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    return script

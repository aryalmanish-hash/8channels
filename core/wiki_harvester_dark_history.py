"""
core/wiki_harvester_dark_history.py

Harvests real dark history events from Wikipedia categories via API.
Uses ONLY verified working category names.
Ultra-polite: 4s delay, aggressive 429 backoff, crash-safe saves.
"""

from __future__ import annotations
import json
import time
import random
import requests
from pathlib import Path


# --- All 34 VERIFIED working categories (live-tested) ---
SEED_CATEGORIES = [
    # === Original 12 verified ===
    ("Serial_killers",                       "serial killer case"),
    ("American_serial_killers",              "serial killer case"),
    ("Assassinated_people",                  "assassination"),
    ("Deaths_by_poisoning",                  "poisoning death"),
    ("People_executed_by_hanging",           "execution case"),
    ("Massacres",                            "massacre"),
    ("Genocides",                            "genocide"),
    ("Terrorist_incidents_in_the_2000s",     "terrorist attack"),
    ("Man-made_disasters",                   "man-made disaster"),
    ("Aviation_accidents_and_incidents",     "aviation accident"),
    ("Maritime_incidents",                   "maritime disaster"),
    ("Terrorist_incidents",                  "terrorist attack"),
    # === 22 newly verified ===
    ("Unsolved_murders",                     "unsolved murder"),
    ("Filicides",                            "filicide case"),
    ("Familicides",                          "familicide case"),
    ("Deaths_from_asphyxiation",             "asphyxiation death"),
    ("Shipwrecks",                           "shipwreck"),
    ("Radiation_accidents_and_incidents",    "radiation accident"),
    ("Explosions",                           "explosion disaster"),
    ("Chemical_disasters",                   "chemical disaster"),
    ("British_serial_killers",               "serial killer case"),
    ("German_serial_killers",                "serial killer case"),
    ("Russian_serial_killers",               "serial killer case"),
    ("Female_serial_killers",                "serial killer case"),
    ("Human_sacrifice",                      "human sacrifice"),
    ("Witch_trials",                         "witch trial"),
    ("Religious_persecution",                "religious persecution"),
    ("Political_repression",                 "political repression"),
    ("State_terrorism",                      "state terrorism"),
    ("Secret_police",                        "secret police operation"),
    ("Missing_people",                       "missing person"),
    ("Kidnapping",                           "kidnapping case"),
    ("Hostage_taking",                       "hostage crisis"),
    ("Ghost_towns",                          "abandoned town"),
]

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS  = {"User-Agent": "8ChannelContentFactory/1.0 dark_history_harvester"}
DELAY    = 4.0
LONG_WAIT_ON_REPEATED_429 = 300.0

DATA_DIR    = Path("data")
TOPICS_FILE = DATA_DIR / "dark_history_topics.json"


def _api_get(params: dict, consecutive_429s: list) -> dict:
    """API wrapper with 429 backoff."""
    for attempt in range(3):
        try:
            r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=20)
            if r.status_code == 429:
                consecutive_429s[0] += 1
                wait_time = 90.0 if consecutive_429s[0] < 3 else LONG_WAIT_ON_REPEATED_429
                print(f"    [429] streak={consecutive_429s[0]}, waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
                continue
            if r.status_code != 200:
                return {}
            consecutive_429s[0] = 0
            return r.json()
        except Exception as e:
            if attempt < 2:
                time.sleep(10)
                continue
            print(f"    Error: {e}")
            return {}
    return {}


def _fetch_category_members(category_name: str, max_items: int,
                             consecutive_429s: list) -> list:
    """Get page titles from a Wikipedia category."""
    titles = []
    cmcontinue = None
    while len(titles) < max_items:
        params = {
            "action":  "query",
            "list":    "categorymembers",
            "cmtitle": f"Category:{category_name}",
            "cmtype":  "page",
            "cmlimit": "50",
            "format":  "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        data = _api_get(params, consecutive_429s)
        if not data:
            break

        members = data.get("query", {}).get("categorymembers", [])
        for m in members:
            title = m.get("title", "")
            if title and not any(title.startswith(p) for p in
                ["List of", "File:", "Template:", "Portal:"]):
                titles.append(title)

        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
        time.sleep(DELAY)

    return titles[:max_items]


def _fetch_summary(title: str, consecutive_429s: list) -> str:
    """Fetch clean intro summary."""
    params = {
        "action":      "query",
        "prop":        "extracts",
        "exintro":     "true",
        "explaintext": "true",
        "titles":      title,
        "format":      "json",
    }
    data = _api_get(params, consecutive_429s)
    if not data:
        return ""
    pages = data.get("query", {}).get("pages", {})
    for _pid, page in pages.items():
        extract = page.get("extract", "").strip()
        if extract:
            return extract[:800]
    return ""


def harvest_all(max_per_category: int = 100, verbose: bool = True) -> int:
    """Main harvest."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = {}
    if TOPICS_FILE.exists():
        try:
            existing_data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
            for t in existing_data.get("topics", []):
                existing[t["title"]] = t
            if verbose:
                print(f"  Loaded {len(existing)} existing topics")
        except Exception:
            pass

    all_topics = dict(existing)
    total_new  = 0
    consecutive_429s = [0]

    for cat_name, cat_label in SEED_CATEGORIES:
        if verbose:
            print(f"\n  Category: {cat_name}")

        members = _fetch_category_members(cat_name, max_per_category, consecutive_429s)
        if verbose:
            print(f"    Found {len(members)} pages")
        if not members:
            continue

        for title in members:
            if title in all_topics:
                continue

            summary = _fetch_summary(title, consecutive_429s)
            time.sleep(DELAY)

            if len(summary) < 200:
                continue

            all_topics[title] = {
                "title":    title,
                "summary":  summary,
                "url":      f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "category": cat_label,
                "used":     False,
            }
            total_new += 1

            if verbose and total_new % 10 == 0:
                print(f"    +{total_new} new (bank: {len(all_topics)})")
                _save_topics(all_topics)

    _save_topics(all_topics)

    if verbose:
        print(f"\n  New added   : {total_new}")
        print(f"  Total bank  : {len(all_topics)}")
        print(f"  Saved to    : {TOPICS_FILE}")

    return len(all_topics)


def _save_topics(all_topics: dict) -> None:
    out = {
        "harvested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total":        len(all_topics),
        "topics":       list(all_topics.values()),
    }
    TOPICS_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


def get_next_topic():
    """Pick a random unused topic."""
    if not TOPICS_FILE.exists():
        return None
    try:
        data   = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
        topics = data.get("topics", [])
        unused = [t for t in topics if not t.get("used", False)]
        if not unused:
            return None
        return random.choice(unused)
    except Exception:
        return None


def mark_used(title: str) -> None:
    """Mark topic as used."""
    if not TOPICS_FILE.exists():
        return
    try:
        data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
        for t in data.get("topics", []):
            if t.get("title") == title:
                t["used"] = True
                break
        TOPICS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def get_stats() -> dict:
    """Return bank stats."""
    if not TOPICS_FILE.exists():
        return {"total": 0, "used": 0, "unused": 0, "by_category": {}}
    try:
        data   = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
        topics = data.get("topics", [])
        by_cat = {}
        used   = 0
        for t in topics:
            cat = t.get("category", "unknown")
            by_cat[cat] = by_cat.get(cat, 0) + 1
            if t.get("used"):
                used += 1
        return {
            "total":       len(topics),
            "used":        used,
            "unused":      len(topics) - used,
            "by_category": by_cat,
        }
    except Exception:
        return {"total": 0, "used": 0, "unused": 0, "by_category": {}}

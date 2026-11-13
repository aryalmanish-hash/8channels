"""
core/scraper.py
Main data engine with content filtering.
Fetches real topics from GitHub, RSS, Wikipedia.
Filters out off-topic content per channel.
"""

from __future__ import annotations

import random
import re
import time

import feedparser
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}

DELAY = 0.5


# ── Content Filters Per Channel ────────────────────────────────────────────

REQUIRED_KEYWORDS = {
    "ai_tools_automation": ["ai", "tool", "automation", "gpt", "llm", "bot", "workflow", "productivity", "code", "api", "machine learning", "neural", "assistant", "generate", "automate"],
    "sports_reviews": ["football", "soccer", "world cup", "fifa", "goal", "match", "team", "player", "stadium", "league", "cup", "champion"],
    "psychology": ["psychology", "brain", "mind", "behavior", "mental", "cognitive", "emotion", "therapy", "anxiety", "habit", "motivation", "personality"],
    "dark_history": ["history", "war", "ancient", "death", "plague", "empire", "battle", "massacre", "crime", "disaster", "medieval", "torture"],
    "english_learning": ["english", "grammar", "vocabulary", "speak", "pronunciation", "ielts", "toefl", "language", "fluent", "word"],
    "facts": ["fact", "science", "discover", "research", "study", "found", "amazing", "incredible", "surprising", "world"],
    "quiz": ["quiz", "question", "answer", "test", "trivia", "knowledge", "iq", "brain", "challenge"],
}

BLOCKED_KEYWORDS = {
    "ai_tools_automation": ["prime day", "sale", "discount", "price", "buy", "shop", "amazon", "deal", "offer", "ads"],
    "sports_reviews": ["transfer", "rumor", "gossip", "wife", "girlfriend", "scandal"],
}


def _passes_filter(channel_id: str, title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    
    blocked = BLOCKED_KEYWORDS.get(channel_id, [])
    for word in blocked:
        if word in text:
            return False
    
    required = REQUIRED_KEYWORDS.get(channel_id, [])
    if not required:
        return True
    
    for word in required:
        if word in text:
            return True
    
    return False


# ── Google News RSS ────────────────────────────────────────────────────────

def google_news_rss(query: str) -> str:
    q = query.replace(" ", "+")
    return f"https://news.google.com/rss/search?q={q}&hl=en&gl=US&ceid=US:en"


# ── GitHub API ─────────────────────────────────────────────────────────────

GITHUB_QUERIES = [
    "topic:ai topic:automation",
    "topic:ai-tools",
    "topic:machine-learning tool",
    "topic:chatgpt",
    "topic:llm",
    "topic:productivity automation",
    "topic:no-code",
    "topic:ai-agent",
    "topic:generative-ai",
    "topic:workflow-automation",
    "ai writing tool",
    "ai image generator",
    "ai video tool",
    "ai coding assistant",
    "free ai tool",
]

GITHUB_SORTS = ["stars", "updated", "help-wanted-issues"]


def get_github_ai_trends(token: str, limit: int = 5) -> list[dict]:
    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    query = random.choice(GITHUB_QUERIES)
    sort = random.choice(GITHUB_SORTS)
    params = {
        "q": query,
        "sort": sort,
        "order": "desc",
        "per_page": limit * 4,
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        items = resp.json().get("items", [])
        random.shuffle(items)
        results = []
        for i in items:
            desc = i.get("description", "") or ""
            title = i["name"]
            if not _passes_filter("ai_tools_automation", title, desc):
                continue
            stars = i.get("stargazers_count", 0)
            language = i.get("language", "") or ""
            results.append({
                "title": title,
                "summary": f"{desc} | Stars: {stars} | Language: {language}",
                "link": i["html_url"],
                "source": "github",
            })
            if len(results) >= limit:
                break
        return results
    except Exception as e:
        print(f"  GitHub Error: {e}")
        return []


# ── RSS Sources Per Channel ────────────────────────────────────────────────

RSS_SOURCES = {
    "english_learning": [
        "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english.rss",
        "https://learningenglish.voanews.com/api/zmorgeqiqt",
        google_news_rss("english learning tips"),
        google_news_rss("english grammar mistakes"),
        google_news_rss("IELTS vocabulary"),
        google_news_rss("learn english fluently"),
    ],
    "psychology": [
        "https://www.sciencedaily.com/rss/mind_brain.xml",
        google_news_rss("psychology human behavior"),
        google_news_rss("psychology mindset"),
        google_news_rss("neuroscience brain"),
        google_news_rss("emotional intelligence"),
    ],
    "dark_history": [
        "https://www.historynet.com/feed",
        google_news_rss("dark history mysteries"),
        google_news_rss("ancient history secrets"),
        google_news_rss("war crimes history"),
        google_news_rss("historical disasters"),
    ],
    "ai_tools_automation": [
        google_news_rss("new AI tools"),
        google_news_rss("ChatGPT features"),
        google_news_rss("AI automation workflow"),
        google_news_rss("AI productivity tools"),
        google_news_rss("free AI apps"),
    ],
    "quiz": [
        google_news_rss("trivia quiz questions"),
        google_news_rss("general knowledge quiz"),
        google_news_rss("science quiz"),
    ],
    "facts": [
        "https://www.sciencedaily.com/rss/top.xml",
        google_news_rss("amazing science facts"),
        google_news_rss("mind blowing facts"),
        google_news_rss("surprising facts"),
    ],
    "sports_reviews": [
        "http://feeds.bbci.co.uk/sport/football/rss.xml",
        google_news_rss("FIFA World Cup 2026"),
        google_news_rss("World Cup football match"),
        google_news_rss("football goals highlights"),
    ],
}

WIKI_HINTS = {
    "quiz": ["science", "geography", "world history", "biology", "astronomy", "mathematics"],
    "facts": ["space exploration", "deep ocean", "human biology", "animal behavior", "scientific discoveries"],
    "dark_history": ["world war", "ancient torture", "black plague", "roman empire", "genocide history"],
    "psychology": ["cognitive bias", "psychological manipulation", "social psychology", "Milgram experiment"],
}


# ── RSS Fetcher With Filter ────────────────────────────────────────────────

def fetch_rss_topics(channel_id: str, limit: int = 10) -> list[dict]:
    sources = RSS_SOURCES.get(channel_id, [])
    random.shuffle(sources)
    results = []
    for url in sources:
        if len(results) >= limit:
            break
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                summary = _clean_html(summary)
                
                if not _passes_filter(channel_id, title, summary):
                    continue
                
                link = entry.get("link", "")
                if title and len(title) > 10:
                    results.append({
                        "title": title,
                        "summary": summary[:600] if summary else "",
                        "link": link,
                        "source": "rss",
                    })
            time.sleep(DELAY)
        except Exception:
            continue

    random.shuffle(results)
    return results[:limit]


# ── Wikipedia Scraper ──────────────────────────────────────────────────────

def fetch_wikipedia_summary(topic: str) -> dict:
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": topic,
        "format": "json",
        "srlimit": 3,
    }
    try:
        resp = requests.get(search_url, params=params, headers=HEADERS, timeout=10)
        data = resp.json()
        results = data.get("query", {}).get("search", [])
        if not results:
            return {}
        page_title = random.choice(results[:3])["title"]
        time.sleep(DELAY)
        return fetch_wikipedia_page(page_title)
    except Exception:
        return {}


def fetch_wikipedia_page(page_title: str) -> dict:
    url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        content_div = soup.find("div", {"class": "mw-parser-output"})
        if not content_div:
            return {}
        paragraphs = content_div.find_all("p", recursive=False)
        text_parts = []
        for p in paragraphs[:6]:
            text = _clean_wiki_text(p.get_text())
            if len(text) > 60:
                text_parts.append(text)
        full_text = " ".join(text_parts)
        return {
            "title": page_title,
            "summary": full_text[:1200],
            "url": url,
            "source": "wikipedia",
        }
    except Exception:
        return {}


def fetch_wikipedia_random(channel_id: str) -> dict:
    hints = WIKI_HINTS.get(channel_id, [""])
    hint = random.choice(hints)
    if hint:
        return fetch_wikipedia_summary(hint)
    return {}


# ── Main Topic Fetcher ─────────────────────────────────────────────────────

def get_web_topics(channel_id: str, limit: int = 5, github_token: str = None) -> list[dict]:
    if channel_id == "reddit_stories":
        from core.story_generator import get_story_topics
        return get_story_topics(limit)

    if channel_id == "ai_tools_automation" and github_token:
        github_results = get_github_ai_trends(github_token, limit=max(3, limit))
        if len(github_results) >= limit:
            return github_results[:limit]
        rss_results = fetch_rss_topics(channel_id, limit=limit - len(github_results))
        combined = github_results + rss_results
        random.shuffle(combined)
        return combined[:limit]

    wiki_channels = ["quiz", "facts", "dark_history", "psychology"]
    if channel_id in wiki_channels:
        results = []
        wiki_count = max(1, limit // 2)
        for _ in range(wiki_count):
            data = fetch_wikipedia_random(channel_id)
            if data and data.get("title"):
                results.append({
                    "title": data["title"],
                    "summary": data.get("summary", ""),
                    "link": data.get("url", ""),
                    "source": "wikipedia",
                })
            time.sleep(DELAY)
        rss_results = fetch_rss_topics(channel_id, limit - len(results))
        results.extend(rss_results)
        random.shuffle(results)
        return results[:limit]

    return fetch_rss_topics(channel_id, limit)


# ── Helpers ────────────────────────────────────────────────────────────────

def _clean_html(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ").strip()


def _clean_wiki_text(text: str) -> str:
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

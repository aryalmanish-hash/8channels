# 01 — Live Handover / Paste To Another AI

**Last updated: 2026-06-30 02:00**

Paste this entire file to another AI to continue the project.
This document is the single source of truth. Updated after every session.

---

## SECTION 1 — PROJECT IDENTITY

Project Name : 8_Channel_Content_Factory
Full Path    : C:\\Users\\user\\Downloads\\8CHANNELS\\8_Channel_Content_Factory
Purpose      : Semi-automated faceless content factory for 8 YouTube/TikTok channels
Status       : Phase 1 active — Reddit Stories channel being polished

CRITICAL: The user also has a separate project called WC Klips.
DO NOT touch WC Klips under any circumstance.

---

## SECTION 2 — USER RULES (FOLLOW EXACTLY)

1. User is NOT highly technical — keep explanations simple
2. ALWAYS give cd command and python command on separate lines
3. ALWAYS put exactly 4 lines of = (80 chars) at very end of every apply_fixes.py output
4. ALL code changes go through apply_fixes.py ONLY
5. Do small targeted patches — never rewrite full files for small bugs
6. Always create backup at start of every apply_fixes.py run
7. Keep only last 10 backups (auto-rotate) — folders only, skip zip files
8. Test after every change
9. NO hardcoded content — use AI/web for everything
10. User prefers free tools and APIs
11. Generate → review → post → delete workflow (storage limited)
12. Manual review before any upload
13. Do NOT create docs outside DOCUMENTATION/ folder
14. Do NOT create duplicate handover files
15. Always give ONE clean code block — never split code across multiple messages
16. Backup only the files being changed in that patch
17. If something fails, fix it immediately — no back and forth loops

---

## SECTION 3 — HOW THIS PROJECT WORKS

Every single code change goes through apply_fixes.py.

Flow:
  AI writes apply_fixes.py
  User saves it (replaces old apply_fixes.py)
  User runs: python apply_fixes.py
  Script creates backup automatically
  Script applies targeted patch
  Script tests the change
  User pastes output back to AI
  AI reads output and continues

This is the ONLY working method. Do not deviate from it.

---

## SECTION 4 — API KEYS

Stored in: config/global_settings.yaml

groq_api_key   : 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
GEMINI_API_KEY: YOUR_GCP_GEMINI_API_KEY
pexels_api_key : JT1GlkAaxxiG69tbNNtAkF5tPZAaTD3jIcbKRjMdMb5ARsWkClFTWZ7R
github_token   : YOUR_GITHUB_PAT

Rotate these keys when the system is stable.

Working AI models (verified 2026-06-27):
Groq   : llama-3.1-8b-instant (primary)
         llama-3.3-70b-versatile (secondary)
         gemma2-9b-it (tertiary)
Gemini : gemini-2.5-flash (primary)
         gemini-2.0-flash (secondary)
         gemini-1.5-flash (tertiary)

---

## SECTION 5 — INSTALLED PACKAGES (ALL VERIFIED WORKING)

flask, pyyaml, pillow, pyttsx3, requests, beautifulsoup4, feedparser
groq, google-genai, moviepy, opencv-python, numpy
faster-whisper, edge-tts, yt-dlp, soundfile, librosa
ffmpeg (system binary — must be in PATH)

---

## SECTION 6 — THE 8 CHANNELS

ID                    Content Type                   Voice
reddit_stories        AI AITA drama stories          en-US-GuyNeural     +15%
english_learning      Grammar, vocab, IELTS          en-US-JennyNeural   +0%
psychology            Behavior, mindset              en-US-AriaNeural    -5%
dark_history          Mysteries, wars, dark events   en-GB-RyanNeural    -5%
ai_tools_automation   AI tools from GitHub/RSS       en-US-AndrewNeural  +5%
quiz                  Trivia from Wikipedia/RSS      en-US-EmmaNeural    +5%
facts                 Science facts Wikipedia/RSS    en-US-SteffanNeural +0%
sports_reviews        Football, World Cup 2026       en-GB-ThomasNeural  +5%

Voice system auto-detects narrator gender from script and picks matching voice.

---

## SECTION 7 — FULL FOLDER STRUCTURE

8_Channel_Content_Factory/
├── apply_fixes.py              ALL patches go through this file
├── main.py                     CLI interface
├── dashboard_app.py            Flask web dashboard
├── CHECK_SETUP.py
├── TEST_SYSTEM.py
├── requirements.pip
├── START_SYSTEM.bat
├── START_DASHBOARD.bat
├── INSTALL_REQUIREMENTS.bat
├── RUN_TESTS.bat
├── BACKUPS/                    auto backups, last 10 kept (folders only)
├── DOCUMENTATION/
│   ├── 00_GOALS_AND_REQUIREMENTS.md
│   ├── 01_LIVE_HANDOVER_PASTE_TO_AI.md  THIS FILE
│   ├── 02_LOCAL_SETUP_GUIDE.md
│   ├── 03_HOW_TO_USE_CURRENT_SYSTEM.md
│   ├── 04_TECHNICAL_REFERENCE.md
│   ├── 05_WHAT_IS_DONE_AND_NOT_DONE.md
│   ├── 06_CONTINUE_FROM_HERE.md
│   └── 07_COMMON_SYSTEM_COMPLETED.md
├── config/
│   ├── global_settings.yaml
│   └── channels/
│       └── (8 yaml files, one per channel)
├── core/
│   ├── ai_engine.py            Groq + Gemini fallback FIXED 2026-06-27
│   ├── ai_validator.py         script quality validator
│   ├── backup_manager.py
│   ├── background_manager.py   Pexels video downloader
│   ├── bootstrap.py
│   ├── caption_generator.py    faster-whisper SRT
│   ├── caption_renderer.py     kinetic captions PIL
│   ├── channel_styles.py
│   ├── compositor.py           moviepy assembler + vibe color profiles
│   ├── config_loader.py
│   ├── database.py             SQLite
│   ├── folder_manager.py
│   ├── metadata_generator.py   AI per-platform metadata
│   ├── music_manager.py        FREE background music (NEW 2026-06-30)
│   ├── output_index.py
│   ├── overlay_engine.py       Reddit UI watermark CTA
│   ├── posting_tracker.py
│   ├── renderer.py             FFmpeg fallback
│   ├── review_manager.py
│   ├── safety_checker.py
│   ├── scraper.py              RSS Wikipedia GitHub
│   ├── script_generator.py     135-160 word limit enforced
│   ├── source_builder.py
│   ├── status_manager.py
│   ├── story_generator.py      AI AITA story
│   ├── system_checks.py
│   ├── thumbnail_generator.py  Pollinations.ai + PIL fallback (NEW 2026-06-30)
│   ├── topic_manager.py
│   ├── upload_package.py
│   ├── voice_generator.py      edge-tts + pyttsx3
│   └── workflow.py             full pipeline
├── channels/
│   ├── OPEN_CHANNEL_OUTPUTS.html
│   └── each channel has:
│       ├── assets/
│       ├── prompts/            prompts.yaml EMPTY for all channels
│       ├── templates/
│       ├── output/
│       │   ├── final_clips/    ONLY final MP4s
│       │   └── thumbnails/     ONLY thumbnail PNGs
│       ├── workspace/
│       │   └── video_id/       all working files
│       └── upload_packages/
│           └── video_id/
├── assets/
│   ├── backgrounds/
│   │   ├── dark/               1 clip
│   │   ├── gameplay/           2 clips
│   │   └── satisfying/         1 clip
│   ├── music/                  cached MP3s (NEW 2026-06-30)
│   └── icons/
│       upvote.png, downvote.png, comment.png, share.png,
│       award.png, fire.png, heart.png, laugh.png, shock.png, cry.png
└── database/
    └── content_factory.sqlite  all tables present

---

## SECTION 8 — DATABASE TABLES

channels, topics, videos, scripts, metadata,
posting_status, review_checks, assets_used, logs

---

## SECTION 9 — WHAT IS FULLY WORKING

✅ Web scraping (RSS, Wikipedia, GitHub API)
✅ Content filtering per channel
✅ AI script generation (Groq + Gemini fallback)
✅ AI script validation + auto-rewrite if score < 50
✅ Script word limit enforced (135-160 words = 50-70 sec video)
✅ AI metadata per platform
✅ AI safety checker
✅ edge-tts natural voice
✅ Male/female narrator auto-detection
✅ faster-whisper SRT generation (synced from real audio)
✅ Pexels background video download
✅ Background categories per channel
✅ Vibe color profiles (gaming/industrial/fpv_drone/satisfying)
✅ moviepy compositor (background + captions + audio)
✅ Transparent caption overlay with Pillow alpha masks
✅ Emotion word highlighting (yellow text)
✅ Reddit AITA story generation
✅ Overlay engine (Reddit UI card, watermark, CTA)
✅ Background music (ccMixter + Pixabay CDN, no loop, fade in/out)
✅ Music mixed with voice at 15% volume
✅ AI fallback for music URL if all sources fail
✅ Thumbnail — Pollinations.ai AI image + PIL fallback
✅ Backup rotation (last 10 folders only)
✅ All 8 channel configs registered
✅ SQLite database all tables working
✅ Output/workspace separation
✅ Upload package creation
✅ Per-platform posting tracker
✅ Review queue manager
✅ Flask dashboard (basic)
✅ CLI interface (basic)
✅ ask_ai() FIXED 2026-06-27

---

## SECTION 10 — WHAT IS PARTIALLY WORKING

⚠️ Reddit UI overlay
   Current : white card, orange bar, PNG icons, fade in/out via FFmpeg
   Target  : fully polished — MOSTLY DONE

⚠️ Background videos — only 4 clips total, need 5+ per category
⚠️ Dashboard — basic Flask only

---

## SECTION 11 — WHAT IS NOT BUILT YET

❌ Part system for multi-part stories
❌ Channel prompts files — all 8 prompts.yaml are EMPTY
❌ Generate to post to delete cleanup automation
❌ Full CLI workflow
❌ Full dashboard workflow

---

## SECTION 12 — PIPELINE FLOW

create_channel_batch(channel_id, limit)
  get_web_topics()              scraper.py RSS/Wikipedia/GitHub
  build_source_context()        source_builder.py
  create_full_mvp_video()
    generate_script()           script_generator.py + ai_engine.py
    _enforce_word_limit()       135-160 words enforced
    generate_metadata()         metadata_generator.py + ai_engine.py
    validate_and_improve()      ai_validator.py
    check_script()              safety_checker.py
    generate_voice()            voice_generator.py edge-tts
    generate_srt()              caption_generator.py faster-whisper
    get_background_music()      music_manager.py (ccMixter/Pixabay CDN)
    mix_voice_with_music()      music_manager.py FFmpeg amix
    generate_thumbnail()        thumbnail_generator.py Pollinations.ai
    get_background()            background_manager.py Pexels
    _get_vibe_settings()        compositor.py vibe color profiles
    compose_video()             compositor.py moviepy + PIL
    _apply_card_overlay_ffmpeg() Reddit card PNG overlay
    publish_final_files()       copies to output/final_clips/
    create_upload_package()     upload_package.py
    initialize_review()         review_manager.py

---

## SECTION 13 — MUSIC SYSTEM (NEW 2026-06-30)

File: core/music_manager.py

Sources (in order):
1. Cache — assets/music/ folder (reuses downloaded tracks)
2. Mood pool — verified working direct MP3 URLs per mood
3. AI fallback — asks Groq/Gemini for a working MP3 URL

Verified working URLs (tested 2026-06-30):
  https://cdn.pixabay.com/audio/2022/08/02/audio_884fe92c21.mp3
  https://cdn.pixabay.com/audio/2022/11/22/audio_febc508520.mp3
  https://cdn.pixabay.com/audio/2022/08/23/audio_d16737dc28.mp3
  https://cdn.pixabay.com/audio/2022/05/27/audio_1808fbf07a.mp3
  https://cdn.pixabay.com/audio/2022/08/04/audio_2dde668d05.mp3
  https://incompetech.com/music/royalty-free/mp3-royaltyfree/Relaxing%20Piano%20Music.mp3

Key behaviours:
- NO looping — plays once, fades out cleanly (no broken seams)
- 15% volume so voice is always dominant
- 2s fade in, 3s fade out
- Mixed with voice using FFmpeg amix

Channel mood map:
  reddit_stories      -> dramatic
  english_learning    -> upbeat
  psychology          -> calm
  dark_history        -> dramatic
  ai_tools_automation -> upbeat
  quiz                -> upbeat
  facts               -> calm
  sports_reviews      -> upbeat

---

## SECTION 14 — THUMBNAIL SYSTEM (UPGRADED 2026-06-30)

File: core/thumbnail_generator.py

Primary  : Pollinations.ai free AI image generation
           URL: https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&enhance=true
           No API key needed
           Extracts emotional keywords from script
           Prompt: "{style} {keywords} cinematic photorealistic 9:16, no text"
Fallback : PIL drawn thumbnail (gradient + hook text + title)

---

## SECTION 15 — VIBE COLOR PROFILES (NEW 2026-06-30)

File: core/compositor.py — _get_vibe_settings()

gaming     : dim=0.15, saturation=1.15  (lighter, more vivid)
industrial : dim=0.25, saturation=0.90  (darker, cool tone)
fpv_drone  : dim=0.30, saturation=1.05  (cinematic warm)
satisfying : dim=0.20, saturation=1.05  (soft warm)
default    : dim=0.35, saturation=1.0   (standard)

---

## SECTION 16 — PRIORITY ROADMAP

PHASE 1 — Finish Reddit Stories (CURRENT)
  DONE : Background music (Pixabay CDN + ccMixter + AI fallback)
  DONE : AI thumbnail (Pollinations.ai)
  DONE : Story length control (135-160 words = 50-70 sec)
  DONE : Vibe color profiles
  NEXT : Full end-to-end test (all features together)
  Then : Part system for long stories
  Then : Full CLI and dashboard for reddit_stories

PHASE 2 — Roll out to other 7 channels
  Order: dark_history, facts, psychology, quiz,
         english_learning, ai_tools_automation, sports_reviews

PHASE 3 — Polish
  5+ background clips per category
  Better thumbnails
  Cleanup automation
  Performance on low-end PC

---

## SECTION 17 — TEST COMMANDS

cd C:\\Users\\user\\Downloads\\8CHANNELS\\8_Channel_Content_Factory

Test AI:
python -c "from core.ai_engine import ask_ai; r=ask_ai('Say hello'); print(r[:100] if r else 'FAILED')"

Test music:
python -c "from core.music_manager import get_background_music; from pathlib import Path; r=get_background_music('reddit_stories', 60, Path('.'))); print(r)"

Test thumbnail:
python -c "from core.thumbnail_generator import generate_thumbnail; from pathlib import Path; r=generate_thumbnail('reddit_stories', 'Test Story', Path('test_thumb.png'), script='dramatic betrayal shocking'); print(r)"

Test full reddit video (2-5 min):
python -c "from core.workflow import create_channel_batch; r=create_channel_batch('reddit_stories', 1); print('DONE:', r[0][0])"

Run dashboard:
python dashboard_app.py

---

## SECTION 18 — KNOWN BUGS AND FIXES

BUG    : ask_ai() returning None despite APIs working
DATE   : 2026-06-27
CAUSE  : GROQ_MODELS had openai/gpt-oss-20b causing silent failure
FIX    : Removed bad model, improved null checks
FILE   : core/ai_engine.py
STATUS : FIXED

BUG    : _enforce_word_limit call existed but function body missing
DATE   : 2026-06-30
CAUSE  : Patch inserted call before inserting function definition
FIX    : Inserted function definition before generate_script()
FILE   : core/script_generator.py
STATUS : FIXED

BUG    : Backup rotation crashed on zip files in BACKUPS folder
DATE   : 2026-06-30
CAUSE  : shutil.rmtree called on zip file
FIX    : Filter to folders only: [b for b in BACKUP_DIR.iterdir() if b.is_dir()]
STATUS : FIXED

---

## SECTION 19 — HOW TO CONTINUE WITH ANOTHER AI

1. Paste this entire file to the new AI
2. Tell the new AI what you want to do next
3. New AI writes apply_fixes.py as ONE complete code block
4. Save it replacing the old apply_fixes.py
5. Run: python apply_fixes.py
6. Paste output back to AI
7. Continue

Rules the new AI must follow:
- Read Section 2 carefully
- Always one clean code block only
- Never touch WC Klips
- Never create docs outside DOCUMENTATION/
- Always backup before changes — only files being changed
- Always test after changes
- Always end output with 4 lines of = (80 chars wide)
- Update handover doc after every verified successful step

---

## SESSION LOG

2026-06-27 : Core pipeline built and verified
2026-06-29 : Reddit card finalized, full pipeline verified end-to-end
2026-06-30 : Background music added (Pixabay CDN + AI fallback)
             AI thumbnail via Pollinations.ai added
             Script word limit 135-160 words added
             Vibe color profiles added (gaming/industrial/fpv_drone/satisfying)
             Handover document updated

---

End of handover document.

---

## SESSION UPDATE 2026-06-30 — Thumbnail System Finalized

### Background Music (NEW — `core/music_manager.py`)
- Free direct MP3 URLs from Pixabay CDN + Incompetech (no API key)
- AI fallback: asks Groq/Gemini for working URL if all fail
- NO looping (clean fade out, no broken seams)
- 15% volume mixed under voice via FFmpeg amix
- 2s fade in, 3s fade out

### Script Word Limit (NEW — `core/script_generator.py`)
- Enforces 135-160 words = 50-70 second video target
- Trims at sentence boundary (`.`, `!`, `?`)
- Function: `_enforce_word_limit()` called after AI script generation

### Vibe Color Profiles (NEW — `core/compositor.py`)
- `_get_vibe_settings()` returns dim + saturation per background category
- gaming     -> dim=0.15, sat=1.15
- industrial -> dim=0.25, sat=0.90
- fpv_drone  -> dim=0.30, sat=1.05
- satisfying -> dim=0.20, sat=1.05
- default    -> dim=0.35, sat=1.0

### Thumbnail System (REBUILT — `core/thumbnail_generator.py`)

**Image generation — 3-tier with realism focus:**
1. **Gemini** (primary) — best for realistic candid photos
   - Tries: `gemini-3.1-flash-image`, `gemini-3-pro-image`, `gemini-2.5-flash-image`
   - Auto-skips to next on quota exhaustion (429)
2. **HuggingFace FLUX.1-schnell** (fallback)
   - Endpoint: `router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell`
   - Token saved as `huggingface_token` in `global_settings.yaml`
3. **Pollinations.ai** (last resort, unlimited)
4. **PIL drawn** (final fallback)

**Hyper-realistic prompt (reddit_stories):**
- Forces "amateur smartphone photo" look
- Explicit anti-AI keywords: no plastic skin, no model faces, no cinematic
- Real-world cues: cluttered rooms, average people, ambient indoor lighting

**Text overlay (MrBeast-style):**
- AI generates 2-5 word hook + 1 emphasis word + vibe
- Auto-shrinks font when text too wide (max 90% of frame width)
- Heavy stroke + drop shadow for readability
- Vibe color map: anger=red, shock=yellow, betrayal=pink, drama=gold

**Branding bar (top-LEFT):**
- Real Reddit logo from `assets/icons/reddit_logo.png` (downloaded from redditstatic.com)
- Channel name below logo (white text, stroke, no background bar)
- Logo size: 12% of width

### Title Card Extraction Fix
- `workflow.py` now extracts only the actual title line
- Cuts at first `?`, `.`, or `!`
- Prevents story body spilling into card

### Cleanup System (one-off, run as needed)
- Clears old `workspace/`, `output/`, `upload_packages/`
- Clears cached `assets/backgrounds/` and `assets/music/`
- Forces fresh downloads on next video generation

---

## REMAINING FOR REDDIT CHANNEL

| # | Task | Status |
|---|------|--------|
| 1 | CLI workflow                                      | NEXT  |
| 2 | Dashboard workflow                                | After |
| 3 | Full end-to-end test (audio + video + everything) | After |
| 4 | Part system for long stories                      | After |

---

---

## SESSION UPDATE 2026-06-30 — CLI Rebuilt + Drive Integration

### CLI Rewrite (main.py)
WC Klips-style menu replacing the old foundation CLI.

Main menu:
  1. Generate ONE video
  2. Generate BATCH (leave PC mode)
  3. Review pending videos
  4. Mark uploaded per platform
  5. Google Drive
  6. Cleanup
  7. Stats and recent activity
  0. Exit

Features:
- Numbered menus, 0 to go back
- Status log format: [OK] / [INFO] / [WARN] / [ERROR]
- Batch mode for leaving PC
- Soft warning when marking uploaded without review
- Platforms: youtube_shorts, tiktok, instagram_reels, facebook_reels

### New Module (core/cli_helpers.py)
Shared helpers for CLI and (next) dashboard:
- Logging: ok/info/warn/err/header/divider
- File sizes: format_size, folder_size
- rclone helpers: drive_upload_video, drive_upload_thumbnail,
  drive_list_channel, drive_delete_video
- Cleanup: cleanup_workspace_for_video, cleanup_old_workspaces

### Google Drive Integration (rclone)
- rclone v1.74.3 verified installed
- Remote: gdrive: (configured)
- Drive root folder: 8ChannelContentFactory/
- Full videos: 8ChannelContentFactory/<channel_id>/<video_id>/
- Thumbnails only: 8ChannelContentFactory/_thumbnails/<channel_id>/<video_id>.png
  (for quick mobile upload to TikTok/Instagram)

### Decisions Locked With User
- Database: Hybrid (SQLite + JSON status files)
- Review: Soft warning, not hard block
- Templates: Split base + per-tab (next step)
- Build order: CLI done, dashboard next
- Mobile: dashboard will be responsive
- Drive: rclone handles all sync (not Google Drive API)

---

## REMAINING FOR REDDIT CHANNEL
- CLI workflow: DONE
- Dashboard rebuild (responsive + split templates): NEXT
- Full end-to-end test: After
- Part system for long stories: Last

---

---

## SESSION UPDATE 2026-06-30 (later) - Dashboard Patch 1

### Dashboard rewritten: dashboard_app.py
Pure Flask, single file, mobile-responsive, dark theme.
Runs on 0.0.0.0:5000 so phone can access via PC IP.

### New folder structure
- templates/  - Jinja templates split per page
- static/     - CSS + JS
- data/       - JSON files (posting_status, schedule, history)

### Templates created (Patch 1)
- base.html       - shared layout, topbar, tabs, toast
- dashboard.html  - stats overview + per-channel + recent activity
- review.html     - review queue with approve/reject/open folder/watch
- channels.html   - PLACEHOLDER (Patch 2)
- upload.html     - PLACEHOLDER (Patch 2)
- history.html    - PLACEHOLDER (Patch 2)
- schedule.html   - PLACEHOLDER (Patch 2)
- cleanup.html    - PLACEHOLDER (Patch 2)
- guide.html      - PLACEHOLDER (Patch 2)

### Static files
- style.css - Dark theme matching WC Klips palette, mobile breakpoints
- app.js    - toast() helper, busyButton() helper

### API routes implemented
- POST /api/approve     - approve a video
- POST /api/reject      - reject a video
- POST /api/generate    - launch generator in new CMD
- POST /api/open_folder - open workspace in Windows Explorer

### Channel color coding
Each channel has its own accent color matching theme:
  reddit_stories      #FF4500 (Reddit orange)
  english_learning    #3B82F6 (blue)
  psychology          #A855F7 (purple)
  dark_history        #7F1D1D (dark red)
  ai_tools_automation #06B6D4 (cyan)
  quiz                #EAB308 (yellow)
  facts               #10B981 (green)
  sports_reviews      #EF4444 (red)

### How to run dashboard
  python dashboard_app.py
  Desktop: http://localhost:5000
  Phone:   http://<your-pc-ip>:5000  (same WiFi)

### REMAINING FOR REDDIT CHANNEL
- Dashboard Patch 2 (channels, upload, history, schedule, cleanup, guide tabs): NEXT
- Full end-to-end test: After
- Part system: Last

---

---

## SESSION UPDATE 2026-06-30 (final) - Dashboard Patch 2 COMPLETE

### All 8 dashboard tabs now functional
  Dashboard - stats + recent activity + per-channel cards
  Channels  - generate per-channel with batch size selector
  Review    - approve/reject/open folder/watch
  Upload    - per-platform tracker + Drive upload
  History   - chronological post log
  Schedule  - server-side reminders (JSON persistent)
  Cleanup   - per-channel storage + cleanup keep-N
  Guide     - upload instructions for each platform

### New API endpoints (10 total now)
  POST /api/approve
  POST /api/reject
  POST /api/generate
  POST /api/open_folder
  POST /api/mark_posted
  POST /api/schedule/add
  POST /api/schedule/delete
  POST /api/cleanup_channel
  POST /api/drive_upload
  GET  /file/<path:filepath>

### Persistent JSON data files
  data/posting_status.json - per-video per-platform flags
  data/schedule.json       - server-side reminders
  data/history.json        - post action log

### Mobile responsive
  Dashboard works on phone via http://<pc-ip>:5000
  CSS breakpoint at 700px stacks layouts vertically
  Platform buttons stack as full-width on small screens

### REMAINING FOR REDDIT CHANNEL
  Full end-to-end test (verify everything works together): NEXT
  Part system for long stories: After test

---

---

## SESSION UPDATE 2026-07-06 — Full pipeline overhaul

### Video generation now ~5-9 min (was 30 min)
Full FFmpeg pipeline replaces slow MoviePy compositing.

### New file: core/compositor_ffmpeg.py
Hybrid pipeline:
  Pass 1: concat BG clips + dim + audio -> base.mp4
  Pass 2: overlay card + watermark PNGs + burn captions (ASS file) -> final.mp4
MoviePy compositor kept as backup at core/compositor_moviepy.py.
Smart chooser at core/compositor.py picks FFmpeg first, MoviePy fallback.

### New file: core/youtube_source.py
Downloads Creative Commons YouTube clips (1080p max).
Uses yt-dlp with CC license filter.
Random 20s segment trimmed, then source deleted (zero storage).

### Random window trimming for cached clips
Same cached clip -> different 18s window each use (15s gap enforced).
5/5 unique windows verified.

### AI narrator + voice vibe detection
Story generator writes:
  _narrator_hint.tmp   = male/female
  _voice_vibe_hint.tmp = warm/dramatic/serious/energetic/mature
Voice generator reads hints -> 10 different voices per story vibe.
5 vibes x 2 genders = 10 voices (Guy/Aria/Eric/Emma/Brian/Ava/Andrew/Jenny/Ryan/Sonia).

### Story quality prompts upgraded
- STRICTLY 240-280 words (was 180-240)
- Uses REAL NAMES (Sarah, Mike) not (28F)/(35M) brackets
- 6-part narrative structure enforced
- Line 1 = Narrator, Line 2 = Voice, Line 3 = Title, Line 4+ = story
- Parser strips Narrator/Voice/Title lines from spoken script

### Hashtag structure per platform (EXACTLY 5 tags)
  Platform tag (YouTube=#shorts, TikTok=#fyp, IG=#reels, FB=#reels)
  + #reddit
  + 3 story-specific CamelCase tags
  e.g. #fyp #reddit #ThanksgivingDrama #AffairExposed #FamilyBetrayal
Enforced via _cap_hashtags and _enforce_metadata_structure in metadata_generator.py.

### AI engine hardening
- Groq: 3 models (llama-3.1-8b-instant, llama-3.3-70b-versatile, openai/gpt-oss-20b)
- Gemini: 5 models, dead ones last (gemini-2.5-flash first)
- 1.2s spacing between Groq calls to prevent rate limit
- Better per-model error messages (quota vs dead vs error)

### Cleanup automation after every video
Auto-deletes at end of create_full_mvp_video():
  - workspace folder for that video
  - all YouTube-downloaded clips (yt_*.mp4)
  - scene temp trims (_scene_*.mp4)
  - youtube_temp/ folder
  - any _ffmpeg_temp folders in output
Only kept: output/<video_id>/{video_id}.mp4 + {video_id}_captions.txt

### Folder + file naming
Format: <slug>_aita_<YYYYMMDD>_<HHMM>
Files inside: {folder}.mp4, {folder}_captions.txt, {folder}_thumbnail.png (if enabled)
Old junk folders (final_clips/, thumbnails/) disabled in output_index.py.

### Watermark
Now uses UpvoteAnthology logo + @UpvoteAnthology text (semi-transparent, bottom-right).
Assets/icons/upvote_anthology.png used (transparent background auto-removed on import).

### Captions (video)
Rendered as ASS file (not SRT+force_style) for guaranteed bottom-center placement.
3-words-per-chunk word-flow style, MarginV=220 from bottom, size 72 bold.
core/compositor_ffmpeg.py -> _build_ass_from_srt() builds the ASS file.

### captions.txt per video
Written to output/<video_id>/<video_id>_captions.txt
Contains: YouTube Shorts (title+desc+hashtags) / TikTok / Instagram Reels / Facebook Reels sections.

### Thumbnail
Currently disabled in workflow.py (thumbnail_created = False).
When re-enabled, saves to {folder}/{video_id}_thumbnail.png next to the .mp4.

### CURRENT STATUS — 39/39 checks passing in dry run
Real video generation verified: ~5-9 min per video, all features working.
Voice varies by story vibe. Captions visible. Fresh backgrounds every video.

### REMAINING for reddit_stories channel
  - Re-enable thumbnail generation when needed
  - Part system for very long stories (currently stories cap at 280 words)
  - Dashboard polish (backend all working)

### File map (new/changed)
  NEW      core/compositor_ffmpeg.py
  NEW      core/compositor_moviepy.py (backup of old compose)
  NEW      core/youtube_source.py
  MODIFIED core/compositor.py (chooser)
  MODIFIED core/story_generator.py (Narrator+Voice prompt, hint files)
  MODIFIED core/voice_generator.py (vibe map, 10 voices)
  MODIFIED core/metadata_generator.py (5-hashtag structure, story-specific)
  MODIFIED core/background_manager.py (YouTube-first + random windows)
  MODIFIED core/folder_manager.py (aita in middle, unique filenames)
  MODIFIED core/workflow.py (cleanup at end, metadata to publish)
  MODIFIED core/ai_engine.py (5 Gemini models, Groq spacing)
  MODIFIED core/output_index.py (disabled junk folder creation)
  MODIFIED core/overlay_engine.py (UpvoteAnthology watermark, larger card padding)

---


---

## SESSION UPDATE 2026-07-07 — AI Engine Hardened + OpenRouter Added

### Problems Fixed This Session

BUG: main.py got syntax error from injected progress block
FIX: Restored from backup BEFORE_RESTORE_20260706_114522
STATUS: FIXED — main.py clean at 13273 bytes

BUG: ask_ai() returning None despite Groq working fine
CAUSE: len(text.strip()) > 10 check rejected short valid responses like "OK"
FIX: Changed to len(text.strip()) > 0 in all 3 provider callers (groq, openrouter, gemini)
FILE: core/ai_engine.py
STATUS: FIXED

BUG: OpenRouter model slugs were wrong (404 errors)
CAUSE: Model IDs changed on OpenRouter since last session
FIX: Fetched live free model list from OpenRouter API, tested each one
STATUS: FIXED — correct slugs now in ai_engine.py

BUG: OpenRouter nemotron-120B taking 52 seconds per call
CAUSE: Giant model was first in list, slow to respond
FIX: Reordered — Groq first (1-2s), OR medium models next, giants last
FIX: Reduced OpenRouter timeout from 90s to 30s
STATUS: FIXED — story generation back to 1.7s when Groq available

### OpenRouter Integration (COMPLETE)

OpenRouter key: sk-or-v1-cdf22d9a... (saved in config/global_settings.yaml)

Verified free models on this account (2026-07-07):
  nvidia/nemotron-3-super-120b-a12b:free  — confirmed working (slow, 50s)
  tencent/hy3:free                        — confirmed working (fast)
  meta-llama/llama-3.3-70b-instruct:free  — rate limited but exists
  google/gemma-4-31b-it:free              — rate limited but exists
  nousresearch/hermes-3-llama-3.1-405b:free — rate limited but exists

### Smart Task Routing (COMPLETE)

ask_ai_task(prompt, system, task="story"|"metadata"|"short")

STORY_MODELS order (tried in sequence):
  1. groq       llama-3.3-70b-versatile       (fast, 1-2s)
  2. groq       llama-3.1-8b-instant          (fast, 0.8s)
  3. openrouter meta-llama/llama-3.3-70b      (medium, backup)
  4. openrouter google/gemma-4-31b-it         (medium, backup)
  5. openrouter tencent/hy3:free              (medium, backup)
  6. gemini     gemini-2.5-flash              (backup)
  7. openrouter nvidia/nemotron-120b          (slow last resort)
  8. openrouter nousresearch/hermes-405b      (slow last resort)

METADATA_MODELS order:
  1. groq       llama-3.1-8b-instant
  2. groq       llama-3.3-70b-versatile
  3. openrouter meta-llama/llama-3.3-70b
  4. openrouter google/gemma-4-31b-it
  5. gemini     gemini-2.5-flash
  6. openrouter nvidia/nemotron-120b
  7. openrouter nousresearch/hermes-405b

SHORT_MODELS order:
  1. groq       llama-3.1-8b-instant
  2. groq       llama-3.3-70b-versatile
  3. openrouter tencent/hy3:free
  4. openrouter meta-llama/llama-3.3-70b
  5. gemini     gemini-2.5-flash

story_generator.py  — uses ask_ai_task(task="story")
metadata_generator.py — uses ask_ai_task(task="metadata")
All other modules  — use ask_ai() which routes as SHORT task

### API Keys (all confirmed working 2026-07-07)
  groq_api_key        : gsk_J0y9v6vt1UV...  WORKING
  gemini_api_key      : AQ.Ab8RN6JIeUm4...  WORKING
  openrouter_api_key  : sk-or-v1-cdf22d9a... WORKING
  pexels_api_key      : JT1GlkAaxxiG69t...   (not tested today)
  github_token        : ghp_JDhGxZd9L9y4...  (not tested today)

### Current State After This Session
  core/ai_engine.py       UPDATED — smart routing, OpenRouter, fixed length check
  core/story_generator.py UPDATED — uses task=story routing
  core/metadata_generator.py UPDATED — uses task=metadata routing
  main.py                 RESTORED — clean, syntax OK

### REMAINING TASKS (priority order)

REDDIT STORIES CHANNEL (leave for later — mostly done):
  - Re-enable thumbnail generation
  - Part system for long stories
  - Dashboard polish

NEXT PRIORITY — Other 7 channels:
  Order: dark_history -> facts -> psychology -> quiz
         -> english_learning -> ai_tools_automation -> sports_reviews

  Each channel needs:
  1. Fill prompts.yaml (currently all EMPTY)
  2. Channel-specific script prompts
  3. End-to-end test for that channel

PHASE 3 — Polish (last):
  - 5+ background clips per category
  - Better thumbnails
  - Cleanup automation
  - Performance on low-end PC

---

## SESSION UPDATE 2026-07-07 (evening) — Full Pipeline Hardened

### AI Engine: OpenRouter + Smart Task Routing
Added OpenRouter (300+ free models) + task-based routing:
  STORY_MODELS      : 9 models (Groq first, OpenRouter big brains, Gemini last)
  METADATA_MODELS   : 6 models (fast Groq for JSON, then bigger models)
  SHORT_MODELS      : 5 models (Groq-first for speed)
Best confirmed working models (2026-07-07):
  Groq   : meta-llama/llama-4-scout-17b-16e-instruct  (2.2s, clean output)
  Groq   : groq/compound  (3.4s clean)
  Groq   : llama-3.3-70b-versatile  (1-2s)
  Groq   : qwen/qwen3.6-27b  (1.1s, may have <think>)
  OR     : nvidia/nemotron-3-super-120b-a12b  (3-6s big brain)
  OR     : nvidia/nemotron-3-nano-30b  (2.5s)
  OR     : nvidia/nemotron-3-ultra-550b  (13s, 550B monster)
  Gemini : gemini-2.5-flash  (last resort)

### AI Engine: Content Sanitizers
  _strip_think_tags()  : removes <think>...</think>, <thinking>, meta-preambles
  sanitize_script_for_voice()  : strips **, *, __, _, emojis, URLs, bullets
  Story parser  : skips ALL preamble before first Narrator:/Voice:/Title: line
  Also strips **Narrator:** style markdown wrapping

### AI Engine: Persistent Log File
  logs/latest_generation.log — reset at start of every video (not per call)
  Contains: prompts, responses, timings, model tried, success/fail
  reset_ai_log() called in workflow.py before every generation

### AI Engine: Rate-Limit Handling
  Groq       : 1.2s spacing between calls (avoids 429)
  OpenRouter : 0.5s spacing
  Gemini     : 2.0s spacing
  All 3 providers auto-retry through fallback list on failure/rate limit

### Voice: Vibe-Matched Selection (10 voices)
Story generator writes 2 hint files:
  _narrator_hint.tmp   = male/female
  _voice_vibe_hint.tmp = warm/dramatic/serious/energetic/mature
Voice generator reads hints -> maps to VIBE_VOICE_MAP:
  10 voice combinations (5 vibes x 2 genders)
  Reddit-only currently; other channels use gender map fallback
Hint file is preserved when new AI call omits it (won't be deleted)

### Reddit Card: Random Username + Time
Every card now uses random values from pools:
  Username pool  : 44 realistic names
                   Mix of throwaway_* style + regular usernames
                   (e.g. throwaway_2847, SaltyPear_88, TiredMom_2024)
  Time pool      : 17 realistic ages
                   (1h ago, 2h ago, 5h ago, 1d ago, 3d ago, etc)
  Upvotes/Comments : Already random (X.Xk / 3-4 digit)
Result: every video's card looks like a different real Reddit post.

### Story Prompt Rules (STRICT)
  Length         : STRICTLY 240-280 words
  Names          : REAL NAMES only (Sarah, Mike, Emma) — no (28F)/(35M) brackets
  Format         : Line 1 = Narrator, Line 2 = Voice, Line 3 = Title, Line 4+ = story
  Markdown       : NO markdown formatting like **, *, _, # — voice reads asterisks literally
  Structure      : 6-part narrative (Hook, Setup, Conflict, Moment, Aftermath, Question)

### Metadata: 5 Hashtag Structure
Every platform gets EXACTLY 5 hashtags:
  #1 Platform tag: TikTok=#fyp, IG=#reels, FB=#reels, YT=#shorts
  #2 #reddit (always)
  #3, #4, #5 Story-specific CamelCase (#ThanksgivingDrama, #AffairExposed)
  Enforced via _cap_hashtags() and _enforce_metadata_structure() in metadata_generator.py

### YouTube CC Source
  Uses yt-dlp with --match-filter for Creative Commons license
  Downloads 1080p quality max
  Random 20s segment trimmed from source, source deleted immediately
  Filters junk keywords: subscribe/tutorial/promo/how-to/etc (~30 keywords)
  Blacklists noisy uploaders (Vertical Satisfying Video, etc)
  Skip results < 60s duration
  History tracking prevents re-download of same video

### Backgrounds: Random Window from Cache
When falling back to cached clip:
  Different 18s window each use (start time randomized)
  15s minimum gap between reused windows from same file
  Same clip = 6+ unique 18s segments possible

### Compositor: FFmpeg Pipeline (Fast)
  Pass 1: concat BG + dim + audio -> base.mp4
  Pass 2: overlay watermark + card + burn ASS captions -> final.mp4
  Total: 3-6 min per video (was 30 min with MoviePy)
  MoviePy backup at compositor_moviepy.py (auto-fallback if FFmpeg fails)

### Card Overlay (Baked Into Pass 2)
  Reddit card PNG passed as card_png=... param to compose_video_ffmpeg
  Fade in 0.4s, hold, fade out 0.8s (total 4s)
  No more slow 2nd FFmpeg pass

### Captions (Bottom-Center, ASS Format)
  SRT chunked to 3-word groups via _build_word_chunk_srt()
  Converted to ASS file via _build_ass_from_srt()
  PlayResX=1080, PlayResY=1920, Alignment=2 (bottom-center), MarginV=220
  Font size 72 bold with black outline
  Guaranteed bottom placement (SRT+force_style unreliable across FFmpeg versions)

### Cleanup at End of Every Video
Auto-deleted after publish (only final MP4 + captions.txt kept):
  workspace/<video_id>/ folder
  YouTube downloads (yt_*.mp4)
  Scene temp trims (_scene_*.mp4)
  youtube_temp/ folder
  Any _ffmpeg_temp folders in output

### Folder + File Naming
  Video folder : <slug>_aita_<YYYYMMDD>_<HHMM>
                 (aita in MIDDLE, date at END for uniqueness across posts)
  Video file   : {video_id}.mp4
  Captions file: {video_id}_captions.txt
  Thumbnail    : {video_id}_thumbnail.png (currently disabled)

### CLI Timing Display
  Start: HH:MM:SS at top
  End: HH:MM:SS + Elapsed X min Y sec at bottom
  Video folder location shown after success

### DRY RUN VERIFICATION (32/32 PASS this session)
Every real step tested (script AI, voice, whisper, metadata, card,
watermark, folder naming, YouTube search, random window, compositors,
ASS builder, music module, workflow structure) — all clean.

### CURRENT STATUS
  Reddit Stories channel  : COMPLETE (locked)
  8-channel infrastructure: fully reusable for other 7 channels
  Next up                 : dark_history channel (waiting on user decisions)

### REMAINING PHASE 1 ITEMS (Reddit)
  Thumbnail generation (currently disabled per user)
  Part system for very long stories
  Dashboard polish (backend works, UI needs work)

### PHASE 2 — Dark History Channel (WAITING ON USER)
Questions pending:
  Q1: Channel name (DarkChronicles / HistoryUncovered / TheDarkPast / etc)
  Q2: Logo (skip / auto-generate / user provides)
  Q3: Story source (Wikipedia / RSS / AI / hybrid)
  Q4: Backgrounds mix (YouTube history footage + Pexels dark/moody)

---

---

## SESSION UPDATE 2026-07-07 (late evening) — AI Fallback Verified + Reddit Bug Fixed

### CRITICAL BUG FIXED: reddit_stories was using generic AI prompt
Before: workflow -> generate_script -> generate_script_with_ai (generic 'write me a script')
        which returned '[Intro music plays] Host: ...' preamble junk.
After:  generate_script now routes reddit_stories to _reddit_story() FIRST
        which uses the specific Narrator/Voice/Title format.
File:   core/script_generator.py — reordered channel routing

### Title now spoken + shown in captions
  Story parser prepends spoken title to clean_script.
  Replaces AITA -> 'Am I the asshole' and WIBTA -> 'Would I be the asshole'
  Voice reads: 'Am I the asshole for [title]. [story]'
  Card still shows raw 'AITA for...' visually (branding).

### AI FALLBACK — verified with real test on ALL 20 models (2026-07-07)

STORY_MODELS (final order after real test):
  1. Groq llama-3.3-70b-versatile          — 1.1s clean [BEST]
  2. Groq llama-4-scout-17b-16e-instruct   — 2.0s clean
  3. Groq groq/compound                     — 5.2s clean
  4. Groq qwen/qwen3.6-27b                  — 1.8s has <think> (stripped)
  5. Gemini gemini-2.5-flash                — 9.7s clean
  6. OpenRouter nemotron-3-ultra-550B       — 22.8s big brain
  7. OpenRouter nemotron-3-nano-30B         — 8.3s chatty preamble
  8. OpenRouter nemotron-3-super-120B       — 47s SLOW
  9. OpenRouter llama-3.3-70b-instruct      — rate-limited
  Result: 8/9 models working. Fallback depth 8 levels.

METADATA_MODELS (final order):
  1. Groq llama-3.1-8b-instant              — 0.9s clean JSON [BEST]
  2. Groq llama-3.3-70b-versatile           — 1.3s clean JSON
  3. Gemini gemini-2.5-flash                 — 6.1s clean JSON
  4. OpenRouter nemotron-3-nano-30B          — 4.8s chatty
  5. OpenRouter nemotron-3-super-120B        — 11s chatty
  6. Groq llama-4-scout                      — occasional 503
  Result: 5/6 working. Fallback depth 5 levels.

SHORT_MODELS (all 5 confirmed working):
  1. Groq llama-3.1-8b-instant              — 0.7s [BEST]
  2. Groq llama-3.3-70b-versatile           — 0.7s
  3. OpenRouter nemotron-3-nano-30B          — 1.7s
  4. Gemini gemini-2.5-flash                 — 2.6s
  5. Groq llama-4-scout                      — 4.0s

### Reddit card: random username + time each video
  44 realistic usernames (mix of throwaway_* + regular)
  17 realistic time strings (1h ago -> 3d ago)
  Upvotes + comments already random
  Every video's card looks like a different real post.

### Log file behavior
  logs/latest_generation.log wiped at start of every video generation
  reset_ai_log() called from workflow.py:create_full_mvp_video()
  Contains: prompts, responses, timings, which model succeeded

### CURRENT STATUS
  Reddit Stories channel  : COMPLETE + all bugs fixed
  AI fallback verified    : 18/20 models working across 3 task types
  Ready to test real video: python main.py -> 1 -> 7
  Waiting on user answers for Dark History channel Q1-Q4

---

---

## SESSION UPDATE 2026-07-07 (night) — Reddit Story Variety Hardened

### CRITICAL BUG FIXED: workflow used generic AI, not reddit-specific
  Before: workflow -> generate_script -> generate_script_with_ai (generic)
          Returned '[Intro music plays] Host: ...' preamble junk
  After:  workflow -> generate_script -> _reddit_story (uses Narrator/Voice/Title)
  File:   core/script_generator.py — reordered so reddit_stories checks first

### Title now spoken + shown in captions (Reddit)
  Story parser prepends spoken title to clean_script
  Replaces AITA -> 'Am I the asshole' (front only, kept as AITA at cliffhanger)
  Voice reads: 'Am I the asshole for [title]. [story]...AITA?'
  Card still shows raw 'AITA for...' visually (branding)

### Reddit card: random username + time each video
  44 realistic usernames (throwaway_* + regular Reddit-style)
  17 realistic time strings (1h ago -> 3d ago)
  Upvotes + comments already random

### AI variety maximized (3-step iteration this session)

  STEP 1: Raised temperature 0.7 -> 1.0
          Result: still repeating 'coworker Nadia' pattern (AI stuck on first example)

  STEP 2: Added random category+name+angle pools injected per call
          Result: 5/5 unique first lines, but wedding cliches still frequent

  STEP 3: Higher temp 1.2 + top_p 0.95 + BANNED wedding/coworker plots
          Also added 'be bold, unusual, modern-tech, cultural' creative hints

### Final story generation variety features (all active)
  - temperature=1.2, top_p=0.95 for all providers
  - Random category from 18 pools each call
  - Random 6 names from 44-name pool each call
  - Random conflict angle from 10-angle pool each call
  - BANNED: wedding/fiance cheating/MIL/airplane/coworker cliches
  - Encouraged: modern tech drama, small-stakes conflicts, cultural clashes

### AI FALLBACK VERIFIED (2026-07-07 test)

  STORY_MODELS (9 total, 8 working, 8 fallback levels):
    1. Groq llama-3.3-70b-versatile           1.1s clean [BEST]
    2. Groq llama-4-scout-17b                  2.0s clean
    3. Groq groq/compound                      5.2s clean
    4. Groq qwen3.6-27b                        1.8s has <think> (stripped)
    5. Gemini gemini-2.5-flash                 9.7s clean
    6. OpenRouter nemotron-3-ultra-550B        22.8s big
    7. OpenRouter nemotron-3-nano-30B          8.3s chatty
    8. OpenRouter nemotron-3-super-120B        47s slow
    9. OpenRouter llama-3.3-70b (rate-limited backup)

  METADATA_MODELS (6, 5 working):
    1. Groq llama-3.1-8b-instant               0.9s [BEST JSON]
    2. Groq llama-3.3-70b-versatile            1.3s
    3. Gemini gemini-2.5-flash                 6.1s
    4-6. OpenRouter nemotron models + Llama-4 backup

  SHORT_MODELS (5, all working):
    1. Groq llama-3.1-8b-instant               0.7s
    2. Groq llama-3.3-70b-versatile            0.7s
    3-5. OpenRouter nemotron + Gemini + Llama-4

### CURRENT STATUS
  Reddit Stories channel  : COMPLETE + all reported bugs fixed
  Script variety          : Maximum settings applied
  AI fallback verified    : 18/20 models across 3 task types
  Log file working        : logs/latest_generation.log (wiped per video)
  Ready for real video    : python main.py -> 1 -> 7
  Dark History channel    : Waiting on user answers to Q1-Q4

---


---

## SESSION UPDATE 2026-07-09 — Reddit Card Fixes + Story Variety Maxed

### Bugs Fixed This Session

BUG    : Reddit card showed for only 4 seconds
CAUSE  : workflow.py L347 hardcoded card_end=4.0 (overrode compositor default)
FIX    : Changed card_end=4.0 -> card_end=7.0 in workflow.py compose_video call
FILE   : core/workflow.py
STATUS : FIXED

BUG    : Reddit card title did not match the actual AI-generated story
CAUSE  : L239 regex looked for "Title:" line, but story_generator strips that line
         before returning script. Fallback then used topic seed instead of AI title.
FIX    : Extract card title from spoken script's first sentence.
         Convert "Am I the asshole" -> "AITA" for card display.
         Convert "Would I be the asshole" -> "WIBTA" for card display.
FILE   : core/workflow.py L237-246
STATUS : FIXED

BUG    : youtube_shorts hashtags missing #shorts and #reddit
CAUSE  : generate_metadata() never called _enforce_metadata_structure()
         The AI-provided hashtags went directly into return dict without validation
FIX    : Force #shorts as first tag + #reddit as second tag in return block
         (L264-282 of metadata_generator.py)
FILE   : core/metadata_generator.py
STATUS : FIXED

BUG    : YouTube title capped at 80 chars (too short for good hooks)
CAUSE  : Hardcoded [:80] slice at L237 and L246 of metadata_generator.py
FIX    : Increased to 100 chars with word-boundary truncation
         (uses rsplit(" ", 1)[0] to avoid mid-word cuts)
FILE   : core/metadata_generator.py
STATUS : FIXED

### New Features This Session

FEATURE : Persistent story history tracker
FILE    : core/story_generator.py + data/story_history/*.json
DETAILS : - Saves last 20 titles per channel to JSON
          - Injected into every AI story prompt as "DO NOT REPEAT" list
          - Guarantees theme variety across 20+ videos
          - Verified 8/8 unique stories in test

FEATURE : Massive story variety pools
FILE    : core/story_generator.py (inside _try_ai_story)
DETAILS : - 60+ story categories (was 18)
            (relationships, family, work, school, everyday, pets,
             money, social media, health, hobbies, travel/events)
          - 70 name pool (was 44)
            (mix of female, male, gender-neutral names)
          - 20 conflict angles (was 10)
          - Combinations: 60 x 20 x C(70,6) = millions of unique stories
          - 10,000+ unique stories confirmed possible

FEATURE : Card title 90-char safety limit
FILE    : core/story_generator.py
DETAILS : - Prompt tells AI: "MUST be under 90 characters total"
          - Parser auto-truncates any title > 90 chars at word boundary
          - Prevents card title from being cut off

FEATURE : Caption styling upgraded
FILE    : core/compositor_ffmpeg.py
DETAILS : - Font size: 80 -> 88 (10% bigger)
          - Stroke: 10 -> 14 (thicker outline for readability)
          - MarginV: 500 (raised captions higher from bottom UI)
          - Montserrat Bold applied via fontsdir hint

FEATURE : Expanded colored word lists
FILE    : core/compositor_ffmpeg.py
DETAILS : - KICK_WORDS expanded to ~60 words (anger, commands, endings)
          - EMOTION_WORDS expanded to ~90 words (shock, sadness, anger,
            positive, embarrassment, fear, betrayal, life events)
          - Rendered RED (kick) and YELLOW (emotion) in captions

### Dry Run Verification — 98/98 PASSED
All modules verified after fixes:
  Story generator     : imports + story generation + all pools present
  Script generator    : correct routing to reddit_story
  Metadata generator  : 5 hashtags, #shorts first, #reddit second, 100 char title
  Safety checker      : runs OK
  Voice generator     : 10 vibe/gender combos present
  Caption generator   : imports OK
  Compositor FFmpeg   : ASS builder verified (font 88, stroke 14, bounce, colors)
  Compositor chooser  : card_end=7.0 default set
  Background manager  : imports OK
  Music manager       : cache folder present
  Thumbnail generator : imports OK + Montserrat available
  Overlay engine      : create_reddit_ui_overlay + save_reddit_card_png OK
  Folder manager      : create_video_folder + publish_final_files OK
  Database            : all 9 tables present
  Workflow            : both entry points callable
  History tracker     : file exists, entries valid

### Real Video Test — PASSED (user confirmed)
Story: parking spot conflict
Card duration: 7 seconds (was 4)
Card title matches story: YES
Font 88 + Stroke 14 + colored words: applied
Music + voice + captions + overlays: all working
Render time: ~10-11 min per video

### File Map (changed this session)
  MODIFIED core/story_generator.py    (60 cats, 70 names, 20 angles, 90-char limit, history tracker)
  MODIFIED core/metadata_generator.py (#shorts/#reddit forced, 100-char title cap)
  MODIFIED core/compositor_ffmpeg.py  (font 88, stroke 14, expanded colored words)
  MODIFIED core/compositor.py         (card_end=7.0 default)
  MODIFIED core/workflow.py           (card_end=7.0, title extraction from first sentence)
  NEW      assets/fonts/Montserrat-Bold.ttf (444 KB)
  NEW      data/story_history/reddit_stories_recent_titles.json

### Current Status
  Reddit Stories channel  : COMPLETE — all bugs fixed, real video verified
  System infrastructure   : ready to scale to other 7 channels
  Next channel            : dark_history (waiting on user Q1-Q4)

### PHASE 2 — Dark History Channel (STARTING NEXT)
Questions pending user answers:
  Q1: Channel name (DarkChronicles / HistoryUncovered / TheDarkPast / other)
  Q2: Logo (skip / auto-generate / user provides)
  Q3: Story source (Wikipedia / RSS / AI / hybrid)
  Q4: Background style (YouTube CC history footage + Pexels dark/moody)


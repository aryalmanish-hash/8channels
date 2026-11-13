# 04 — Technical Reference

## Project Structure

```text
8_Channel_Content_Factory/
  DOCUMENTATION/
  config/
  core/
  channels/
  assets/
  output/
  database/
  logs/
  templates/
  main.py
  dashboard_app.py
```

## Core Files

```text
core/config_loader.py       loads YAML configs
core/database.py            SQLite schema/helpers
core/folder_manager.py      creates channel/video folders
core/bootstrap.py           initializes DB and registers channels
core/script_generator.py    Phase 1 script templates
core/metadata_generator.py  metadata
core/voice_generator.py     silent WAV placeholder
core/caption_generator.py   SRT captions
core/renderer.py            basic FFmpeg MP4 placeholder
core/thumbnail_generator.py PNG thumbnail covers
core/posting_tracker.py     posting status helpers
core/review_manager.py      approval/needs-edit helpers
core/workflow.py            MVP workflows
```

## Phase 1 Channels Complete At MVP Level

```text
reddit_stories
quiz
english_learning
```

## Database

SQLite file:

```text
database/content_factory.sqlite
```

Main tables:

- channels
- topics
- videos
- scripts
- metadata
- posting_status
- review_checks
- assets_used
- logs

## Test

```bash
cd 8_Channel_Content_Factory
python -m py_compile core/*.py main.py dashboard_app.py
python core/bootstrap.py
```

## Documentation Rule

Only docs folder:

```text
DOCUMENTATION/
```

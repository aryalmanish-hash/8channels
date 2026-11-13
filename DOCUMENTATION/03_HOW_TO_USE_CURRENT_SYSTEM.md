# 03 — How To Use Current System

All 8 channels now have basic MVP generation.

## Run

```bash
cd 8_Channel_Content_Factory
python core/bootstrap.py
python main.py
```

## Dashboard

```bash
python dashboard_app.py
```

Open:

```text
http://localhost:5000
```

Dashboard can:

- create channel batch for any of the 8 channels
- create full MVP video for any channel
- approve video
- mark needs edit
- mark posted
- show per-channel sections

## Folder Rule

Final upload files only:

```text
channels/<channel_id>/output/final_clips/
channels/<channel_id>/output/thumbnails/
```

Working files:

```text
channels/<channel_id>/workspace/<video_id>/
```

Upload package:

```text
channels/<channel_id>/upload_packages/<video_id>/
```

## Current Quality Level

This is functional MVP for all channels.

Still basic:

- templates are simple
- TTS depends on local pyttsx3
- MP4 requires FFmpeg
- facts/stats/history still need manual checking

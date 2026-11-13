# 02 — Local Setup Guide

## Install Python Packages

From inside project folder:

```bash
cd 8_Channel_Content_Factory
pip install -r requirements.pip
```

## Install FFmpeg

FFmpeg is required to create final MP4 files.

Check:

```bash
ffmpeg -version
```

If missing, install FFmpeg and add it to PATH.

## Check Setup

```bash
python CHECK_SETUP.py
```

## Start Dashboard

Windows:

```text
Double-click START_DASHBOARD.bat
```

Or terminal:

```bash
python dashboard_app.py
```

Open:

```text
http://localhost:5000
```

## Start CLI

Windows:

```text
Double-click START_SYSTEM.bat
```

Or terminal:

```bash
python main.py
```

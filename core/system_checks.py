"""Shared system health checks."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PACKAGES = {
    "flask": "flask",
    "yaml": "pyyaml",
    "PIL": "pillow",
    "pyttsx3": "pyttsx3",
}


def check_system() -> dict:
    packages = []
    for import_name, install_name in REQUIRED_PACKAGES.items():
        ok = importlib.util.find_spec(import_name) is not None
        packages.append({"import": import_name, "package": install_name, "ok": ok})
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    return {
        "python": sys.version,
        "project_root": str(PROJECT_ROOT),
        "packages": packages,
        "ffmpeg": {"ok": ffmpeg_ok, "path": shutil.which("ffmpeg") or ""},
        "ready_for_mp4_render": ffmpeg_ok,
        "ready_for_dashboard": all(p["ok"] for p in packages if p["import"] in {"flask", "yaml"}),
        "ready_for_tts": any(p["import"] == "pyttsx3" and p["ok"] for p in packages),
    }


def write_health_report(path: Path | None = None) -> Path:
    import json
    path = path or PROJECT_ROOT / "system_health.json"
    path.write_text(json.dumps(check_system(), indent=2), encoding="utf-8")
    return path

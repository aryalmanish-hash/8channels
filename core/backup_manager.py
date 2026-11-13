"""Project backup/export helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_ROOT = PROJECT_ROOT / "backups"

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", "backups"}


def create_project_backup(include_outputs: bool = False) -> Path:
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = BACKUP_ROOT / f"content_factory_backup_{stamp}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in PROJECT_ROOT.rglob("*"):
            rel = path.relative_to(PROJECT_ROOT)
            parts = set(rel.parts)
            if parts & EXCLUDE_DIRS:
                continue
            if not include_outputs and ("workspace" in parts or "output" in parts or "upload_packages" in parts):
                continue
            if path.is_file():
                zf.write(path, rel)
    return zip_path


def create_handover_bundle() -> Path:
    """Create a zip containing code/config/docs but not generated outputs."""
    return create_project_backup(include_outputs=False)

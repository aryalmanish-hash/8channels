"""Bootstrap script to initialize database and register channels."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from core.config_loader import load_all_channel_configs, PROJECT_ROOT
from core.database import init_db, upsert_channel, log
from core.output_index import generate_output_indexes


def bootstrap() -> None:
    init_db()
    configs = load_all_channel_configs()
    for channel_id, cfg in configs.items():
        config_path = Path("config") / "channels" / f"{channel_id}.yaml"
        upsert_channel(
            channel_id=channel_id,
            name=cfg.get("channel_name", channel_id),
            config_path=str(config_path),
            status=cfg.get("status", "active"),
        )
    generate_output_indexes()
    log("INFO", "bootstrap", f"Initialized project at {PROJECT_ROOT}")


if __name__ == "__main__":
    bootstrap()
    print("Bootstrap complete. Database initialized and channels registered.")

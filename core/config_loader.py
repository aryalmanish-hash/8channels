"""Configuration loader for the 8-Channel Content Factory.

This module loads the global config and each channel config.
It must stay generic. Do not hardcode channel-specific behavior here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
CHANNEL_CONFIG_DIR = CONFIG_DIR / "channels"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a dictionary: {path}")
    return data


def load_global_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "global_settings.yaml")


def load_channel_config(channel_id: str) -> dict[str, Any]:
    path = CHANNEL_CONFIG_DIR / f"{channel_id}.yaml"
    data = load_yaml(path)
    if data.get("channel_id") != channel_id:
        raise ValueError(
            f"Channel config mismatch. Expected {channel_id}, got {data.get('channel_id')}"
        )
    return data


def list_channel_ids() -> list[str]:
    if not CHANNEL_CONFIG_DIR.exists():
        return []
    return sorted(p.stem for p in CHANNEL_CONFIG_DIR.glob("*.yaml"))


def load_all_channel_configs() -> dict[str, dict[str, Any]]:
    return {channel_id: load_channel_config(channel_id) for channel_id in list_channel_ids()}

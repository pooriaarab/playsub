"""User-tunable settings for Playsub."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "playsub" / "config.json"

# Defaults
MUTE_ADS = True
AUTO_START_WITH_SPOTIFY = True
SHOW_NEXT_LINE = True
WINDOW_OPACITY = 0.92


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {
            "mute_ads": MUTE_ADS,
            "auto_start_with_spotify": AUTO_START_WITH_SPOTIFY,
            "show_next_line": SHOW_NEXT_LINE,
            "window_opacity": WINDOW_OPACITY,
        }

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}

    return {
        "mute_ads": bool(data.get("mute_ads", MUTE_ADS)),
        "auto_start_with_spotify": bool(
            data.get("auto_start_with_spotify", AUTO_START_WITH_SPOTIFY)
        ),
        "show_next_line": bool(data.get("show_next_line", SHOW_NEXT_LINE)),
        "window_opacity": float(data.get("window_opacity", WINDOW_OPACITY)),
    }

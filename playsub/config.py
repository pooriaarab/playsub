"""User-tunable settings and visual theme for Playsub."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "playsub"
CONFIG_PATH = CONFIG_DIR / "config.json"
EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "config.example.json"

DEFAULT_CONFIG: dict = {
    "mute_ads": True,
    "ad_mute_mode": "both",
    "auto_start_with_spotify": True,
    "show_next_line": True,
    "karaoke_mode": True,
    "menu_bar_icon": True,
    "window_opacity": 0.78,
    "theme": {
        "preset": "minimal",
        "font_family": "Helvetica Neue",
        "lyric_size": 22,
        "status_size": 11,
        "next_size": 12,
        "background": "#000000",
        "lyric_color": "#f2f2f2",
        "karaoke_highlight_color": "#ffffff",
        "status_color": "#7a7a7a",
        "next_color": "#5a5a5a",
        "accent_color": "#888888",
        "ad_color": "#b35a5a",
        "progress_color": "#444444",
        "show_badge": False,
        "show_progress": False,
        "show_status": False,
        "show_shadow": False,
        "show_border": False,
    },
}

THEME_PRESETS: dict[str, dict] = {
    "minimal": {
        "font_family": "Helvetica Neue",
        "lyric_size": 22,
        "status_size": 11,
        "next_size": 12,
        "background": "#000000",
        "lyric_color": "#f2f2f2",
        "status_color": "#7a7a7a",
        "next_color": "#5a5a5a",
        "accent_color": "#888888",
        "ad_color": "#b35a5a",
        "progress_color": "#444444",
        "show_badge": False,
        "show_progress": False,
        "show_status": False,
        "show_shadow": False,
        "show_border": False,
        "karaoke_highlight_color": "#ffffff",
    },
    "cinema": {
        "font_family": "Helvetica Neue",
        "lyric_size": 26,
        "status_size": 11,
        "next_size": 12,
        "background": "#000000",
        "lyric_color": "#ffffff",
        "status_color": "#666666",
        "next_color": "#444444",
        "accent_color": "#666666",
        "ad_color": "#aa6666",
        "progress_color": "#333333",
        "show_badge": False,
        "show_progress": False,
        "show_status": False,
        "show_shadow": False,
        "show_border": False,
        "karaoke_highlight_color": "#ffffff",
    },
    "classic": {
        "font_family": "Arial",
        "lyric_size": 27,
        "status_size": 12,
        "next_size": 14,
        "background": "#101014",
        "lyric_color": "#ffe066",
        "status_color": "#8b8b96",
        "next_color": "#8b8b96",
        "accent_color": "#1db954",
        "ad_color": "#ff4d4d",
        "progress_color": "#1db954",
        "show_badge": True,
        "show_progress": True,
        "show_status": True,
        "show_shadow": True,
        "show_border": True,
        "karaoke_highlight_color": "#ffffff",
    },
}


def _merge_theme(raw_theme: dict) -> dict:
    preset_name = str(raw_theme.get("preset", "minimal")).lower()
    base = deepcopy(THEME_PRESETS.get(preset_name, THEME_PRESETS["minimal"]))

    if preset_name == "custom":
        base = deepcopy(THEME_PRESETS["minimal"])

    for key, value in raw_theme.items():
        if key == "preset":
            continue
        base[key] = value

    base["preset"] = preset_name if preset_name in THEME_PRESETS else "custom"
    return base


def load_config() -> dict:
    data: dict = {}
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}

    theme = _merge_theme(data.get("theme", {}))

    return {
        "mute_ads": bool(data.get("mute_ads", DEFAULT_CONFIG["mute_ads"])),
        "ad_mute_mode": str(data.get("ad_mute_mode", DEFAULT_CONFIG["ad_mute_mode"])),
        "auto_start_with_spotify": bool(
            data.get("auto_start_with_spotify", DEFAULT_CONFIG["auto_start_with_spotify"])
        ),
        "show_next_line": bool(data.get("show_next_line", DEFAULT_CONFIG["show_next_line"])),
        "karaoke_mode": bool(data.get("karaoke_mode", DEFAULT_CONFIG["karaoke_mode"])),
        "menu_bar_icon": bool(data.get("menu_bar_icon", DEFAULT_CONFIG["menu_bar_icon"])),
        "window_opacity": float(data.get("window_opacity", DEFAULT_CONFIG["window_opacity"])),
        "theme": theme,
    }


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "mute_ads": config.get("mute_ads", True),
        "ad_mute_mode": config.get("ad_mute_mode", "both"),
        "auto_start_with_spotify": config.get("auto_start_with_spotify", True),
        "show_next_line": config.get("show_next_line", True),
        "karaoke_mode": config.get("karaoke_mode", True),
        "menu_bar_icon": config.get("menu_bar_icon", True),
        "window_opacity": config.get("window_opacity", 0.78),
        "theme": config.get("theme", DEFAULT_CONFIG["theme"]),
    }
    CONFIG_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_example_config() -> None:
    if not CONFIG_PATH.exists() and EXAMPLE_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")

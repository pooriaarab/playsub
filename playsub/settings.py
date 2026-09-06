"""Simple settings window for fonts, colors, and layout."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from playsub.config import THEME_PRESETS, load_config, save_config


class SettingsWindow:
    def __init__(self, parent: tk.Tk, on_save) -> None:
        self.parent = parent
        self.on_save = on_save
        self.config = load_config()
        self.theme = dict(self.config["theme"])

        self.window = tk.Toplevel(parent)
        self.window.title("Playsub Settings")
        self.window.geometry("420x620")
        self.window.transient(parent)
        self.window.grab_set()

        frame = ttk.Frame(self.window, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Theme preset").pack(anchor="w")
        self.preset_var = tk.StringVar(value=self.theme.get("preset", "minimal"))
        preset_box = ttk.Combobox(
            frame,
            textvariable=self.preset_var,
            values=sorted(THEME_PRESETS.keys()) + ["custom"],
            state="readonly",
        )
        preset_box.pack(fill="x", pady=(0, 12))
        preset_box.bind("<<ComboboxSelected>>", self._apply_preset)

        self.opacity_var = tk.DoubleVar(value=self.config["window_opacity"])
        ttk.Label(frame, text="Window transparency").pack(anchor="w")
        ttk.Scale(frame, from_=0.4, to=1.0, variable=self.opacity_var, orient="horizontal").pack(
            fill="x", pady=(0, 12)
        )

        self.offset_var = tk.IntVar(value=int(self.config.get("karaoke_offset_ms", 0)))
        ttk.Label(frame, text="Karaoke timing offset (ms)").pack(anchor="w")
        ttk.Label(
            frame,
            text="Negative = highlight earlier. Positive = later. Try -150 to +150.",
            wraplength=360,
        ).pack(anchor="w")
        ttk.Scale(frame, from_=-500, to=500, variable=self.offset_var, orient="horizontal").pack(
            fill="x", pady=(0, 12)
        )

        self._add_entry(frame, "Font family", "font_family")
        self._add_spin(frame, "Lyric font size", "lyric_size", 12, 48)
        self._add_spin(frame, "Status font size", "status_size", 8, 24)
        self._add_spin(frame, "Next line font size", "next_size", 8, 24)

        ttk.Label(frame, text="Colors (hex like #ffffff)").pack(anchor="w", pady=(8, 4))
        for label, key in [
            ("Background", "background"),
            ("Lyric text", "lyric_color"),
            ("Karaoke highlight", "karaoke_highlight_color"),
            ("Song title", "status_color"),
            ("Next line", "next_color"),
            ("Accent", "accent_color"),
            ("Ad color", "ad_color"),
        ]:
            self._add_entry(frame, label, key)


        toggles = ttk.Frame(frame)
        toggles.pack(fill="x", pady=(8, 12))
        self.bool_vars: dict[str, tk.BooleanVar] = {}
        for label, key in [
            ("Karaoke word highlight", "karaoke_mode"),
            ("Menu bar icon", "menu_bar_icon"),
            ("Show song title", "show_status"),
            ("Show next line area", "show_next_line"),
            ("Show player badge", "show_badge"),
            ("Show progress bar", "show_progress"),
            ("Text shadow", "show_shadow"),
            ("Border", "show_border"),
        ]:
            if key == "show_next_line":
                default = bool(self.config.get("show_next_line", True))
            elif key == "karaoke_mode":
                default = bool(self.config.get("karaoke_mode", True))
            elif key == "menu_bar_icon":
                default = bool(self.config.get("menu_bar_icon", True))
            else:
                default = bool(self.theme.get(key, False))
            var = tk.BooleanVar(value=default)
            self.bool_vars[key] = var
            ttk.Checkbutton(toggles, text=label, variable=var).pack(anchor="w")

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Save", command=self._save).pack(side="right")
        ttk.Button(buttons, text="Cancel", command=self.window.destroy).pack(side="right", padx=(0, 8))

        ttk.Label(
            frame,
            text=f"Config file: ~/.config/playsub/config.json",
            wraplength=360,
        ).pack(anchor="w", pady=(12, 0))

    def _apply_preset(self, _event=None) -> None:
        preset = self.preset_var.get()
        if preset not in THEME_PRESETS:
            return

        self.theme.update(THEME_PRESETS[preset])
        self.theme["preset"] = preset

        for key in [
            "font_family",
            "background",
            "lyric_color",
            "karaoke_highlight_color",
            "status_color",
            "next_color",
            "accent_color",
            "ad_color",
        ]:
            var = getattr(self, f"{key}_var", None)
            if var is not None:
                var.set(str(self.theme.get(key, "")))

        for key in ["lyric_size", "status_size", "next_size"]:
            var = getattr(self, f"{key}_var", None)
            if var is not None:
                var.set(int(self.theme.get(key, 12)))

        for key in [
            "show_status",
            "show_badge",
            "show_progress",
            "show_shadow",
            "show_border",
        ]:
            if key in self.bool_vars:
                self.bool_vars[key].set(bool(self.theme.get(key, False)))

    def _add_entry(self, parent: ttk.Frame, label: str, key: str) -> None:
        ttk.Label(parent, text=label).pack(anchor="w")
        var = tk.StringVar(value=str(self.theme.get(key, "")))
        setattr(self, f"{key}_var", var)
        ttk.Entry(parent, textvariable=var).pack(fill="x", pady=(0, 8))

    def _add_spin(self, parent: ttk.Frame, label: str, key: str, min_v: int, max_v: int) -> None:
        ttk.Label(parent, text=label).pack(anchor="w")
        var = tk.IntVar(value=int(self.theme.get(key, 12)))
        setattr(self, f"{key}_var", var)
        ttk.Spinbox(parent, from_=min_v, to=max_v, textvariable=var, width=8).pack(
            anchor="w", pady=(0, 8)
        )

    def _save(self) -> None:
        updated = load_config()
        updated["window_opacity"] = float(self.opacity_var.get())
        updated["karaoke_offset_ms"] = int(self.offset_var.get())
        updated["show_next_line"] = bool(self.bool_vars["show_next_line"].get())
        updated["karaoke_mode"] = bool(self.bool_vars["karaoke_mode"].get())
        updated["menu_bar_icon"] = bool(self.bool_vars["menu_bar_icon"].get())

        theme = dict(updated["theme"])
        theme["preset"] = self.preset_var.get()
        for key in [
            "font_family",
            "background",
            "lyric_color",
            "karaoke_highlight_color",
            "status_color",
            "next_color",
            "accent_color",
            "ad_color",
        ]:
            var = getattr(self, f"{key}_var", None)
            if var is not None:
                theme[key] = var.get().strip()

        for key in ["lyric_size", "status_size", "next_size"]:
            var = getattr(self, f"{key}_var", None)
            if var is not None:
                theme[key] = int(var.get())

        for key in [
            "show_status",
            "show_badge",
            "show_progress",
            "show_shadow",
            "show_border",
        ]:
            theme[key] = bool(self.bool_vars[key].get())

        updated["theme"] = theme
        save_config(updated)
        self.on_save(updated)
        self.window.destroy()


def open_settings(parent: tk.Tk, on_save) -> None:
    SettingsWindow(parent, on_save)

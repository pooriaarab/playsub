"""Subtle, customizable always-on-top subtitle overlay."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from playsub.lyrics.sync import KaraokeWord
from playsub.settings import open_settings


class PlaysubOverlay:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.theme = dict(config["theme"])
        self._visible = True

        self.root = tk.Tk()
        self.root.title("Playsub")
        self.root.configure(bg=self.theme["background"])
        self.root.attributes("-topmost", True)
        self._apply_opacity()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.width = min(880, screen_width - 48)
        self.height = self._calc_height()
        x = (screen_width - self.width) // 2
        y = screen_height - self.height - 150
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.theme["background"],
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self._state = {
            "badge": "",
            "status": "",
            "line": "Lyrics will appear here",
            "karaoke_words": [],
            "next": "⌘, settings · Esc quit · drag to move",
            "progress": 0.0,
            "mode": "idle",
        }

        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.root.bind("<Escape>", lambda _event: self.quit())
        self.root.bind("<Command-comma>", lambda _event: self.open_settings())
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self._draw()
        self.root.update_idletasks()
        self.raise_to_front()

    def _calc_height(self) -> int:
        base = int(self.theme["lyric_size"]) + 70
        if self.theme.get("show_status"):
            base += int(self.theme["status_size"]) + 10
        if self.config.get("show_next_line", True):
            base += int(self.theme["next_size"]) + 8
        if self.theme.get("show_progress"):
            base += 14
        return max(110, min(base, 220))

    def _apply_opacity(self) -> None:
        try:
            self.root.attributes("-alpha", float(self.config.get("window_opacity", 0.78)))
        except tk.TclError:
            pass

    def _make_font(self, size_key: str, bold: bool = False) -> tkfont.Font:
        family = str(self.theme.get("font_family", "Helvetica Neue"))
        size = int(self.theme.get(size_key, 12))
        weight = "bold" if bold else "normal"
        return tkfont.Font(family=family, size=size, weight=weight)

    def apply_config(self, config: dict) -> None:
        self.config = config
        self.theme = dict(config["theme"])
        self.height = self._calc_height()
        self.root.configure(bg=self.theme["background"])
        self.canvas.configure(bg=self.theme["background"])
        self._apply_opacity()
        self._draw()

    def open_settings(self) -> None:
        open_settings(self.root, self.apply_config)

    def hide(self) -> None:
        self._visible = False
        self.root.withdraw()

    def set_visible(self) -> None:
        self._visible = True
        self.root.deiconify()
        self.raise_to_front()
        self._draw()

    def raise_to_front(self) -> None:
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
        except tk.TclError:
            pass

    def _line_color(self) -> str:
        if self._state["mode"] == "ad":
            return str(self.theme.get("ad_color", "#b35a5a"))
        return str(self.theme.get("lyric_color", "#f2f2f2"))

    def _karaoke_color(self, state: str) -> str:
        if state == "active":
            return str(self.theme.get("karaoke_highlight_color", "#ffffff"))
        if state == "past":
            return str(self.theme.get("lyric_color", "#f2f2f2"))
        return str(self.theme.get("next_color", "#5a5a5a"))

    def _draw_karaoke_line(self, center_y: float, words: list[KaraokeWord]) -> None:
        if not words:
            return

        font = self._make_font("lyric_size", bold=True)
        gap = font.measure(" ")
        parts = [(word.text, self._karaoke_color(word.state)) for word in words]
        total_width = sum(font.measure(text) for text, _color in parts)
        total_width += gap * max(0, len(parts) - 1)

        x = (self.width - total_width) / 2
        for text, color in parts:
            if self.theme.get("show_shadow"):
                self.canvas.create_text(
                    x + 1,
                    center_y + 1,
                    text=text,
                    anchor="w",
                    fill="#000000",
                    font=font,
                )
            self.canvas.create_text(x, center_y, text=text, anchor="w", fill=color, font=font)
            x += font.measure(text) + gap

    def _draw(self) -> None:
        w, h = self.width, self.height
        bg = str(self.theme.get("background", "#000000"))
        self.canvas.delete("all")
        self.canvas.configure(height=h)

        if self.theme.get("show_border"):
            self.canvas.create_rectangle(0, 0, w, h, fill=bg, outline="#2a2a33", width=1)
        else:
            self.canvas.create_rectangle(0, 0, w, h, fill=bg, outline=bg)

        y = 18

        if self.theme.get("show_badge") and self._state["badge"]:
            badge_w = 88
            accent = str(
                self.theme.get("ad_color" if self._state["mode"] == "ad" else "accent_color", "#888888")
            )
            self.canvas.create_rectangle(18, y - 10, 18 + badge_w, y + 12, fill=accent, outline="")
            self.canvas.create_text(
                18 + badge_w / 2,
                y + 1,
                text=self._state["badge"],
                fill=bg,
                font=self._make_font("status_size", bold=True),
            )

        if self.theme.get("show_status") and self._state["status"]:
            self.canvas.create_text(
                w / 2,
                y,
                text=self._state["status"],
                fill=str(self.theme.get("status_color", "#7a7a7a")),
                font=self._make_font("status_size"),
            )
            y += int(self.theme["status_size"]) + 18

        lyric_y = y + int(self.theme["lyric_size"]) // 2 + 6
        karaoke_words = self._state.get("karaoke_words") or []
        line_font = self._make_font("lyric_size", bold=True)
        line_color = self._line_color()

        if karaoke_words and self.config.get("karaoke_mode", True):
            self._draw_karaoke_line(lyric_y, karaoke_words)
        else:
            line_text = self._state["line"]
            if self.theme.get("show_shadow"):
                self.canvas.create_text(
                    w / 2 + 1,
                    lyric_y + 1,
                    text=line_text,
                    fill="#000000",
                    font=line_font,
                    width=w - 56,
                    justify="center",
                )
            self.canvas.create_text(
                w / 2,
                lyric_y,
                text=line_text,
                fill=line_color,
                font=line_font,
                width=w - 56,
                justify="center",
            )

        y = lyric_y + int(self.theme["lyric_size"]) // 2 + 14

        if self.config.get("show_next_line", True) and self._state["next"]:
            self.canvas.create_text(
                w / 2,
                y,
                text=self._state["next"],
                fill=str(self.theme.get("next_color", "#5a5a5a")),
                font=self._make_font("next_size"),
                width=w - 56,
                justify="center",
            )

        if self.theme.get("show_progress"):
            bar_left, bar_right = 24, w - 24
            bar_y = h - 16
            track = str(self.theme.get("progress_color", "#444444"))
            self.canvas.create_line(bar_left, bar_y, bar_right, bar_y, fill=track, width=2)
            progress_x = bar_left + (bar_right - bar_left) * self._state["progress"]
            if progress_x > bar_left:
                accent = str(self.theme.get("accent_color", "#888888"))
                self.canvas.create_line(bar_left, bar_y, progress_x, bar_y, fill=accent, width=2)

    def _start_drag(self, event: tk.Event) -> None:
        self._drag_offset_x = event.x
        self._drag_offset_y = event.y

    def _on_drag(self, event: tk.Event) -> None:
        x = self.root.winfo_x() + event.x - self._drag_offset_x
        y = self.root.winfo_y() + event.y - self._drag_offset_y
        self.root.geometry(f"+{x}+{y}")

    def show_idle(self, message: str) -> None:
        self._state.update(
            {
                "badge": "",
                "status": "",
                "line": message,
                "karaoke_words": [],
                "next": "⌘, settings · Esc quit · drag to move",
                "progress": 0.0,
                "mode": "idle",
            }
        )
        self._draw()

    def show_loading(self, track: str) -> None:
        self._state.update(
            {
                "badge": "SPOTIFY",
                "status": f"Loading · {track}" if self.theme.get("show_status") else "",
                "line": "Fetching lyrics…",
                "karaoke_words": [],
                "next": "",
                "progress": 0.0,
                "mode": "loading",
            }
        )
        self._draw()

    def show_ad(self, muted: bool) -> None:
        detail = "Muted" if muted else "Ad playing"
        self._state.update(
            {
                "badge": "AD",
                "status": "Advertisement" if self.theme.get("show_status") else "",
                "line": "…",
                "karaoke_words": [],
                "next": detail,
                "progress": 0.0,
                "mode": "ad",
            }
        )
        self._draw()

    def show_track(
        self,
        track: str,
        artist: str,
        line: str,
        next_line: str,
        progress: float,
        synced: bool,
        paused: bool = False,
        karaoke_words: list[KaraokeWord] | None = None,
    ) -> None:
        status = ""
        if self.theme.get("show_status"):
            sync_label = "synced" if synced else "estimated"
            prefix = "Paused · " if paused else ""
            status = f"{prefix}{track} — {artist} · {sync_label}"

        self._state.update(
            {
                "badge": "SPOTIFY",
                "status": status,
                "line": line or "…",
                "karaoke_words": karaoke_words or [],
                "next": next_line or "⌘, settings · Esc quit · drag to move",
                "progress": progress,
                "mode": "paused" if paused else "playing",
            }
        )
        self._draw()

    def run(self) -> None:
        self.root.mainloop()

    def quit(self) -> None:
        self.root.quit()
        self.root.destroy()

    def after(self, delay_ms: int, callback) -> None:
        self.root.after(delay_ms, callback)

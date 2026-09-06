"""Polished always-on-top subtitle overlay."""

from __future__ import annotations

import subprocess
import tkinter as tk


class PlaysubOverlay:
    BG = "#101014"
    PANEL = "#18181f"
    ACCENT = "#1db954"
    AD_ACCENT = "#ff4d4d"
    TEXT = "#ffffff"
    LYRIC = "#ffe066"
    MUTED = "#8b8b96"
    BORDER = "#2a2a33"

    def __init__(self, opacity: float = 0.92) -> None:
        self.root = tk.Tk()
        self.root.title("Playsub")
        self.root.configure(bg=self.BG)
        self.root.attributes("-topmost", True)
        try:
            self.root.attributes("-alpha", opacity)
        except tk.TclError:
            pass

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.width = min(940, screen_width - 48)
        self.height = 188
        x = (screen_width - self.width) // 2
        y = screen_height - self.height - 150
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.BG,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self._state = {
            "badge": "SPOTIFY",
            "status": "Starting…",
            "line": "Lyrics will appear here",
            "next": "Esc quit · drag to move",
            "progress": 0.0,
            "mode": "idle",
        }

        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.root.bind("<Escape>", lambda _event: self.quit())
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

        self._draw()
        self.root.update_idletasks()
        self.raise_to_front()
        self._notify_started()

    def _notify_started(self) -> None:
        subprocess.run(
            [
                "osascript",
                "-e",
                'display notification "Synced lyrics + ad mute ready." with title "Playsub"',
            ],
            check=False,
        )

    def raise_to_front(self) -> None:
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
        except tk.TclError:
            pass

    def _accent_color(self) -> str:
        return self.AD_ACCENT if self._state["mode"] == "ad" else self.ACCENT

    def _draw(self) -> None:
        w, h = self.width, self.height
        accent = self._accent_color()
        self.canvas.delete("all")

        self.canvas.create_rectangle(0, 0, w, h, fill=self.BG, outline=self.BORDER, width=1)
        self.canvas.create_rectangle(8, 8, w - 8, h - 8, fill=self.PANEL, outline="", width=0)
        self.canvas.create_rectangle(8, 8, w - 8, 12, fill=accent, outline="")

        self.canvas.create_rectangle(20, 22, 108, 44, fill=accent, outline="")
        self.canvas.create_text(
            64,
            33,
            text=self._state["badge"],
            fill="#08110b" if self._state["mode"] != "ad" else "#1a0505",
            font=("Arial", 11, "bold"),
        )

        self.canvas.create_text(
            w / 2,
            34,
            text=self._state["status"],
            fill=self.MUTED,
            font=("Arial", 12),
        )

        line_color = self.AD_ACCENT if self._state["mode"] == "ad" else self.LYRIC
        self.canvas.create_text(
            w / 2 + 1,
            97 + 1,
            text=self._state["line"],
            fill="#000000",
            font=("Arial", 27, "bold"),
            width=w - 70,
            justify="center",
        )
        self.canvas.create_text(
            w / 2,
            97,
            text=self._state["line"],
            fill=line_color,
            font=("Arial", 27, "bold"),
            width=w - 70,
            justify="center",
        )

        self.canvas.create_text(
            w / 2,
            142,
            text=self._state["next"],
            fill=self.MUTED,
            font=("Arial", 14),
            width=w - 80,
            justify="center",
        )

        bar_left, bar_right = 24, w - 24
        bar_y = h - 22
        self.canvas.create_line(bar_left, bar_y, bar_right, bar_y, fill="#2d2d36", width=4)
        progress_x = bar_left + (bar_right - bar_left) * self._state["progress"]
        if progress_x > bar_left:
            self.canvas.create_line(bar_left, bar_y, progress_x, bar_y, fill=accent, width=4)

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
                "badge": "PLAYSUB",
                "status": "Waiting for music",
                "line": message,
                "next": "Esc quit · drag to move",
                "progress": 0.0,
                "mode": "idle",
            }
        )
        self._draw()

    def show_loading(self, track: str) -> None:
        self._state.update(
            {
                "badge": "SPOTIFY",
                "status": f"Loading · {track}",
                "line": "Fetching synced lyrics…",
                "next": "",
                "progress": 0.15,
                "mode": "loading",
            }
        )
        self._draw()

    def show_ad(self, muted: bool) -> None:
        detail = "Spotify volume muted" if muted else "Ad playing"
        self._state.update(
            {
                "badge": "AD",
                "status": "Advertisement",
                "line": "Enjoying the silence ✨",
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
    ) -> None:
        sync_label = "synced" if synced else "estimated"
        prefix = "Paused · " if paused else ""
        self._state.update(
            {
                "badge": "SPOTIFY",
                "status": f"{prefix}{track} — {artist} · {sync_label}",
                "line": line or "…",
                "next": next_line or "Esc quit · drag to move",
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

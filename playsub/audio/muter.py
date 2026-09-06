"""Mute Spotify during ads and restore volume afterward."""

from __future__ import annotations

import subprocess


class SpotifyAdMuter:
    """Drop Spotify's in-app volume during ads, then put it back."""

    def __init__(self) -> None:
        self._saved_volume: int | None = None
        self._muted_for_ad = False

    def update(self, is_ad: bool, is_playing: bool) -> bool:
        """Return True when an ad is currently muted."""
        if is_ad and is_playing:
            if not self._muted_for_ad:
                self._mute()
            return True

        if self._muted_for_ad:
            self._unmute()
        return False

    def _mute(self) -> None:
        current = self._get_volume()
        if current is None:
            return
        if current > 0:
            self._saved_volume = current
        self._set_volume(0)
        self._muted_for_ad = True

    def _unmute(self) -> None:
        restore = self._saved_volume if self._saved_volume is not None else 50
        self._set_volume(restore)
        self._saved_volume = None
        self._muted_for_ad = False

    @staticmethod
    def _run_applescript(script: str) -> str | None:
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                check=False,
                timeout=3,
            )
        except (subprocess.SubprocessError, OSError):
            return None

        if result.returncode != 0:
            return None
        return (result.stdout or "").strip()

    def _get_volume(self) -> int | None:
        output = self._run_applescript('tell application "Spotify" to return sound volume')
        if output is None:
            return None
        try:
            return max(0, min(100, int(float(output))))
        except ValueError:
            return None

    def _set_volume(self, volume: int) -> None:
        volume = max(0, min(100, volume))
        self._run_applescript(f'tell application "Spotify" to set sound volume to {volume}')

"""Detect and silence Spotify advertisements on macOS."""

from __future__ import annotations

import subprocess


class SpotifyAdMuter:
    """Mute Spotify ads using in-app volume and optional system volume."""

    def __init__(self, mode: str = "both") -> None:
        self.mode = mode if mode in {"spotify", "system", "both"} else "both"
        self._saved_spotify_volume: int | None = None
        self._saved_system_volume: int | None = None
        self._saved_system_muted: bool | None = None
        self._muted_for_ad = False

    def update(self, is_ad: bool, is_playing: bool) -> bool:
        if is_ad and is_playing:
            if not self._muted_for_ad:
                self._mute()
            return True

        if self._muted_for_ad:
            self._unmute()
        return False

    def _mute(self) -> None:
        if self.mode in {"spotify", "both"}:
            current = self._get_spotify_volume()
            if current is not None and current > 0:
                self._saved_spotify_volume = current
            elif self._saved_spotify_volume is None:
                self._saved_spotify_volume = 80
            self._set_spotify_volume(0)

        if self.mode in {"system", "both"}:
            system = self._get_system_volume()
            if system is not None:
                self._saved_system_volume = system["volume"]
                self._saved_system_muted = system["muted"]
            self._set_system_muted(True)

        self._muted_for_ad = True

    def _unmute(self) -> None:
        if self.mode in {"spotify", "both"}:
            restore = self._saved_spotify_volume if self._saved_spotify_volume is not None else 80
            self._set_spotify_volume(restore)
            self._saved_spotify_volume = None

        if self.mode in {"system", "both"}:
            if self._saved_system_muted is False and self._saved_system_volume is not None:
                self._set_system_volume(self._saved_system_volume, muted=False)
            elif self._saved_system_muted is True:
                self._set_system_muted(True)
            else:
                self._set_system_muted(False)
            self._saved_system_volume = None
            self._saved_system_muted = None

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

    def _get_spotify_volume(self) -> int | None:
        output = self._run_applescript('tell application "Spotify" to return sound volume')
        if output is None:
            return None
        try:
            return max(0, min(100, int(float(output))))
        except ValueError:
            return None

    def _set_spotify_volume(self, volume: int) -> None:
        volume = max(0, min(100, volume))
        self._run_applescript(f'tell application "Spotify" to set sound volume to {volume}')

    def _get_system_volume(self) -> dict | None:
        script = """
        set s to get volume settings
        set vol to output volume of s
        set muted to output muted of s
        return (vol as string) & "|||" & (muted as string)
        """
        output = self._run_applescript(script)
        if output is None:
            return None
        parts = output.split("|||")
        if len(parts) != 2:
            return None
        try:
            return {
                "volume": max(0, min(100, int(float(parts[0])))),
                "muted": parts[1].strip().lower() == "true",
            }
        except ValueError:
            return None

    def _set_system_volume(self, volume: int, muted: bool = False) -> None:
        volume = max(0, min(100, volume))
        muted_text = "true" if muted else "false"
        self._run_applescript(
            f"set volume output volume {volume} output muted {muted_text}"
        )

    def _set_system_muted(self, muted: bool) -> None:
        muted_text = "true" if muted else "false"
        self._run_applescript(f"set volume output muted {muted_text}")

"""Read playback state from the Spotify desktop app on macOS."""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from playsub.models import PlaybackState

ORIGIN_HEADER = "https://open.spotify.com"
SPOTIFY_PORTS = (4381, 4380, 4378, 4379)
AD_TRACK_NAMES = {"advertisement", "ad", "spotify ad", "spotify"}


@dataclass
class _SmoothPosition:
    position_sec: float = 0.0
    is_playing: bool = False
    updated_at: float = 0.0


class SpotifyPlayer:
    player_name = "spotify"

    def __init__(self) -> None:
        self._smooth = _SmoothPosition()
        self._tokens: tuple[str, str] | None = None
        self._active_port: int | None = None

    def get_playback(self, now: float) -> PlaybackState | None:
        state = self._get_from_local_api()
        if state is None:
            state = self._get_from_applescript()

        if state is None:
            self._smooth.is_playing = False
            return None

        self._smooth.position_sec = state.position_sec
        self._smooth.is_playing = state.is_playing
        self._smooth.updated_at = now
        return state

    def get_smooth_position(self, now: float) -> float:
        if not self._smooth.is_playing:
            return self._smooth.position_sec
        elapsed = max(0.0, now - self._smooth.updated_at)
        return self._smooth.position_sec + elapsed

    @staticmethod
    def is_running() -> bool:
        try:
            result = subprocess.run(
                ["pgrep", "-x", "Spotify"],
                capture_output=True,
                check=False,
            )
        except OSError:
            return False
        return result.returncode == 0

    def _get_from_local_api(self) -> PlaybackState | None:
        for port in SPOTIFY_PORTS:
            status = self._fetch_status(port)
            if status is None:
                continue
            self._active_port = port
            return self._parse_status_json(status)
        return None

    def _fetch_status(self, port: int) -> dict | None:
        tokens = self._get_tokens(port)
        if tokens is None:
            return None

        oauth_token, csrf_token = tokens
        query = urllib.parse.urlencode(
            {
                "oauth": oauth_token,
                "csrf": csrf_token,
                "returnafter": "1",
                "returnon": "play,pause,track",
            }
        )
        url = f"http://127.0.0.1:{port}/remote/status.json?{query}"

        try:
            request = urllib.request.Request(url, headers={"Origin": ORIGIN_HEADER})
            with urllib.request.urlopen(request, timeout=2) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None

    def _get_tokens(self, port: int) -> tuple[str, str] | None:
        if self._active_port == port and self._tokens is not None:
            return self._tokens

        csrf_token = self._fetch_json(f"http://127.0.0.1:{port}/simplecsrf/token.json")
        oauth_token = self._fetch_json("https://open.spotify.com/token")
        if not csrf_token or not oauth_token:
            return None

        csrf = csrf_token.get("token")
        oauth = oauth_token.get("t")
        if not csrf or not oauth:
            return None

        self._tokens = (oauth, csrf)
        return self._tokens

    def _fetch_json(self, url: str) -> dict | None:
        try:
            request = urllib.request.Request(url, headers={"Origin": ORIGIN_HEADER})
            with urllib.request.urlopen(request, timeout=2) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def _looks_like_ad(
        track_name: str,
        artist_name: str,
        spotify_url: str = "",
        popularity: int | None = None,
        duration_sec: float = 0.0,
        is_ad_flag: bool = False,
    ) -> bool:
        if is_ad_flag:
            return True

        url_lower = spotify_url.lower()
        if ":ad:" in url_lower or url_lower.startswith("spotify:ad"):
            return True

        if track_name.strip().lower() in AD_TRACK_NAMES:
            return True
        if "advertisement" in track_name.lower():
            return True
        if artist_name.strip().lower() in AD_TRACK_NAMES:
            return True

        # Short tracks named "Spotify" with zero popularity are usually ads.
        if (
            popularity == 0
            and 0 < duration_sec <= 31
            and track_name.strip().lower() in {"spotify", "advertisement"}
        ):
            return True

        return False

    def _parse_status_json(self, status: dict) -> PlaybackState | None:
        track = status.get("track") or {}
        if not track:
            return None

        artists = track.get("artists") or []
        artist_name = artists[0]["name"] if artists else "Unknown Artist"
        track_name = track.get("name") or "Unknown Track"
        is_ad = self._looks_like_ad(
            track_name,
            artist_name,
            is_ad_flag=bool(track.get("advertisement")),
        )

        if is_ad:
            track_name = "Advertisement"
            artist_name = "Spotify"

        album = track.get("album") or {}
        album_name = album.get("name") or album.get("uri") or ""
        duration_ms = track.get("duration") or status.get("duration") or 0
        position_ms = status.get("position") or 0

        return PlaybackState(
            track=track_name,
            artist=artist_name,
            album=album_name if isinstance(album_name, str) else "",
            position_sec=max(0.0, float(position_ms) / 1000.0),
            duration_sec=max(0.0, float(duration_ms) / 1000.0),
            is_playing=bool(status.get("playing")),
            is_ad=is_ad,
            player=self.player_name,
        )

    @staticmethod
    def _get_from_applescript() -> PlaybackState | None:
        script = """
        tell application "System Events"
            set spotifyRunning to (name of processes) contains "Spotify"
        end tell
        if spotifyRunning is false then
            return "NOT_RUNNING"
        end if

        tell application "Spotify"
            try
                set trackUrl to spotify url of current track
                set trackName to name of current track
                set artistName to artist of current track
                set albumName to album of current track
                set trackPop to popularity of current track
                set pos to player position
                set dur to (duration of current track) / 1000
                set stateText to player state as string
                return trackUrl & "|||" & trackName & "|||" & artistName & "|||" & albumName & "|||" & pos & "|||" & dur & "|||" & stateText & "|||" & trackPop
            on error errMsg number errNum
                return "ERROR:" & errNum & ":" & errMsg
            end try
        end tell
        """

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

        output = (result.stdout or "").strip()
        if not output or output == "NOT_RUNNING" or output.startswith("ERROR:"):
            return None

        parts = output.split("|||")
        if len(parts) != 8:
            return None

        track_url, track_name, artist_name, album_name, pos_text, dur_text, state_text, pop_text = parts
        try:
            position_sec = float(pos_text)
            duration_sec = float(dur_text)
            popularity = int(pop_text)
        except ValueError:
            return None

        is_ad = SpotifyPlayer._looks_like_ad(
            track_name,
            artist_name,
            spotify_url=track_url,
            popularity=popularity,
            duration_sec=duration_sec,
        )
        if is_ad:
            track_name = "Advertisement"
            artist_name = "Spotify"

        return PlaybackState(
            track=track_name,
            artist=artist_name,
            album=album_name,
            position_sec=max(0.0, position_sec),
            duration_sec=max(0.0, duration_sec),
            is_playing=state_text.lower() == "playing",
            is_ad=is_ad,
            player="spotify",
        )

"""Main Playsub loop: lyrics overlay, ad mute, player polling."""

from __future__ import annotations

import threading
import time

from playsub.audio.muter import SpotifyAdMuter
from playsub.config import load_config
from playsub.lyrics.lrclib import LRCLibClient
from playsub.lyrics.sync import line_at_position, line_progress, next_line_preview
from playsub.models import PlaybackState, TrackLyrics
from playsub.overlay import PlaysubOverlay
from playsub.players.spotify import SpotifyPlayer

POLL_MS = 400
PLAYER_REFRESH_SEC = 1.0


def track_key(state: PlaybackState) -> str:
    duration = int(round(state.duration_sec))
    return f"{state.player}::{state.artist}::{state.track}::{state.album}::{duration}".lower()


class PlaysubApp:
    def __init__(self) -> None:
        self.config = load_config()
        self.overlay = PlaysubOverlay(opacity=self.config["window_opacity"])
        self.player = SpotifyPlayer()
        self.lrclib = LRCLibClient()
        self.ad_muter = SpotifyAdMuter()

        self.current_key = ""
        self.current_lyrics: TrackLyrics | None = None
        self.last_playback: PlaybackState | None = None
        self.last_player_poll = 0.0
        self.loading = False
        self.fetching_key = ""

    def start(self) -> None:
        self.overlay.show_idle("Open Spotify and play a song")
        self.overlay.after(POLL_MS, self.tick)
        self.overlay.run()

    def tick(self) -> None:
        now = time.monotonic()

        if now - self.last_player_poll >= PLAYER_REFRESH_SEC:
            playback = self.player.get_playback(now)
            self.last_player_poll = now
            if playback is not None:
                self.last_playback = playback
                self._handle_playback_change(playback)

        playback = self.last_playback
        if playback is None:
            self.overlay.show_idle("Open Spotify and play a song")
        elif playback.is_ad:
            muted = False
            if self.config["mute_ads"]:
                muted = self.ad_muter.update(is_ad=True, is_playing=playback.is_playing)
            self.overlay.show_ad(muted=muted)
        else:
            self.ad_muter.update(is_ad=False, is_playing=playback.is_playing)
            if not playback.is_playing:
                self._render_track(playback.position_sec, paused=True)
            else:
                position = self.player.get_smooth_position(now)
                self._render_track(position, paused=False)

        self.overlay.after(POLL_MS, self.tick)

    def _handle_playback_change(self, playback: PlaybackState) -> None:
        if playback.is_ad:
            self.current_key = ""
            self.current_lyrics = None
            self.loading = False
            self.fetching_key = ""
            return

        key = track_key(playback)
        if key == self.current_key or key == self.fetching_key:
            return

        self.current_key = key
        self.current_lyrics = None
        self.loading = True
        self.fetching_key = key
        self.overlay.show_loading(playback.track)

        thread = threading.Thread(
            target=self._fetch_lyrics_in_background,
            args=(playback, key),
            daemon=True,
        )
        thread.start()

    def _fetch_lyrics_in_background(self, playback: PlaybackState, key: str) -> None:
        lyrics = self.lrclib.fetch_lyrics(
            track=playback.track,
            artist=playback.artist,
            album=playback.album,
            duration_sec=playback.duration_sec,
        )

        def apply_result() -> None:
            if key != self.current_key:
                return

            self.loading = False
            self.fetching_key = ""
            self.current_lyrics = lyrics

            if lyrics is None and self.last_playback is not None:
                self.overlay.show_track(
                    track=self.last_playback.track,
                    artist=self.last_playback.artist,
                    line="No lyrics found for this song",
                    next_line="Try another track",
                    progress=0.0,
                    synced=False,
                )
            elif self.last_playback is not None:
                self._render_track(self.last_playback.position_sec, paused=not self.last_playback.is_playing)

        self.overlay.after(0, apply_result)

    def _render_track(self, position_sec: float, paused: bool) -> None:
        if self.loading or self.last_playback is None:
            return

        if self.current_lyrics is None:
            self.overlay.show_track(
                track=self.last_playback.track,
                artist=self.last_playback.artist,
                line="No lyrics yet",
                next_line="",
                progress=0.0,
                synced=False,
                paused=paused,
            )
            return

        current = line_at_position(self.current_lyrics, position_sec)
        upcoming = (
            next_line_preview(self.current_lyrics, position_sec)
            if self.config["show_next_line"]
            else ""
        )
        progress = line_progress(self.current_lyrics, position_sec)

        self.overlay.show_track(
            track=self.last_playback.track,
            artist=self.last_playback.artist,
            line=current,
            next_line=upcoming,
            progress=progress,
            synced=self.current_lyrics.is_synced,
            paused=paused,
        )

"""Fetch lyrics from the free LRCLIB API."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

from playsub.models import LyricLine, TrackLyrics

LRCLIB_GET_URL = "https://lrclib.net/api/get"
LRC_LINE_PATTERN = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")


class LRCLibClient:
    def fetch_lyrics(
        self,
        track: str,
        artist: str,
        album: str = "",
        duration_sec: float = 0.0,
    ) -> TrackLyrics | None:
        params = urllib.parse.urlencode(
            {
                "track_name": track,
                "artist_name": artist,
                "album_name": album,
                "duration": int(round(duration_sec)),
            }
        )
        url = f"{LRCLIB_GET_URL}?{params}"

        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "playsub/1.0"},
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                payload = response.read().decode("utf-8")
            data = json.loads(payload)
        except Exception:
            return None

        synced = (data.get("syncedLyrics") or "").strip()
        plain = (data.get("plainLyrics") or "").strip()

        if synced:
            lines = self._parse_synced_lyrics(synced)
            if lines:
                return TrackLyrics(
                    track=track,
                    artist=artist,
                    lines=lines,
                    plain_text=plain,
                    is_synced=True,
                )

        if plain:
            lines = self._estimate_lines_from_plain(plain, duration_sec)
            return TrackLyrics(
                track=track,
                artist=artist,
                lines=lines,
                plain_text=plain,
                is_synced=False,
            )

        return None

    @staticmethod
    def _parse_synced_lyrics(synced_text: str) -> list[LyricLine]:
        lines: list[LyricLine] = []
        for raw_line in synced_text.splitlines():
            match = LRC_LINE_PATTERN.match(raw_line.strip())
            if not match:
                continue
            minutes = int(match.group(1))
            seconds = float(match.group(2))
            text = match.group(3).strip()
            if not text or text == "♪":
                continue
            lines.append(LyricLine(start_sec=(minutes * 60) + seconds, text=text))
        lines.sort(key=lambda line: line.start_sec)
        return lines

    @staticmethod
    def _estimate_lines_from_plain(plain_text: str, duration_sec: float) -> list[LyricLine]:
        raw_lines = [line.strip() for line in plain_text.splitlines() if line.strip()]
        if not raw_lines:
            return []
        total_duration = duration_sec if duration_sec > 0 else max(len(raw_lines) * 4, 180)
        step = total_duration / len(raw_lines)
        return [
            LyricLine(start_sec=index * step, text=text)
            for index, text in enumerate(raw_lines)
        ]

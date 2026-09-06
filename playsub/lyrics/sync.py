from __future__ import annotations

from playsub.models import LyricLine, TrackLyrics


def line_at_position(lyrics: TrackLyrics, position_sec: float) -> str:
    if not lyrics.lines:
        return ""
    current = lyrics.lines[0].text
    for line in lyrics.lines:
        if position_sec + 0.05 >= line.start_sec:
            current = line.text
        else:
            break
    return current


def next_line_preview(lyrics: TrackLyrics, position_sec: float) -> str:
    for line in lyrics.lines:
        if line.start_sec > position_sec + 0.05:
            return line.text
    return ""


def line_progress(lyrics: TrackLyrics, position_sec: float) -> float:
    """Return 0-1 progress through the current lyric line."""
    if not lyrics.lines:
        return 0.0

    current_index = 0
    for index, line in enumerate(lyrics.lines):
        if position_sec + 0.05 >= line.start_sec:
            current_index = index
        else:
            break

    start = lyrics.lines[current_index].start_sec
    if current_index + 1 < len(lyrics.lines):
        end = lyrics.lines[current_index + 1].start_sec
    else:
        end = start + 4.0

    if end <= start:
        return 0.0

    return max(0.0, min(1.0, (position_sec - start) / (end - start)))

from __future__ import annotations

from dataclasses import dataclass

from playsub.models import LyricLine, TrackLyrics

WordState = str  # "past" | "active" | "future"


@dataclass(frozen=True)
class KaraokeWord:
    text: str
    state: WordState


def current_line_index(lyrics: TrackLyrics, position_sec: float) -> int:
    if not lyrics.lines:
        return 0

    current_index = 0
    for index, line in enumerate(lyrics.lines):
        if position_sec + 0.05 >= line.start_sec:
            current_index = index
        else:
            break
    return current_index


def line_end_sec(lyrics: TrackLyrics, line_index: int) -> float:
    lines = lyrics.lines
    if not lines:
        return 0.0

    start = lines[line_index].start_sec
    if line_index + 1 < len(lines):
        return lines[line_index + 1].start_sec
    return start + 4.0


def line_at_position(lyrics: TrackLyrics, position_sec: float) -> str:
    if not lyrics.lines:
        return ""
    return lyrics.lines[current_line_index(lyrics, position_sec)].text


def next_line_preview(lyrics: TrackLyrics, position_sec: float) -> str:
    index = current_line_index(lyrics, position_sec)
    if index + 1 < len(lyrics.lines):
        return lyrics.lines[index + 1].text
    for line in lyrics.lines:
        if line.start_sec > position_sec + 0.05:
            return line.text
    return ""


def line_progress(lyrics: TrackLyrics, position_sec: float) -> float:
    if not lyrics.lines:
        return 0.0

    index = current_line_index(lyrics, position_sec)
    start = lyrics.lines[index].start_sec
    end = line_end_sec(lyrics, index)
    if end <= start:
        return 0.0
    return max(0.0, min(1.0, (position_sec - start) / (end - start)))


def karaoke_words_at_position(lyrics: TrackLyrics, position_sec: float) -> list[KaraokeWord]:
    """Split the current line into words and mark which one is being sung."""
    if not lyrics.lines:
        return []

    index = current_line_index(lyrics, position_sec)
    line = lyrics.lines[index]
    words = line.text.split()
    if not words:
        return []

    start = line.start_sec
    end = line_end_sec(lyrics, index)
    duration = max(end - start, len(words) * 0.25)
    step = duration / len(words)

    result: list[KaraokeWord] = []
    for word_index, word in enumerate(words):
        word_start = start + (word_index * step)
        word_end = word_start + step
        if position_sec >= word_end:
            state: WordState = "past"
        elif position_sec >= word_start:
            state = "active"
        else:
            state = "future"
        result.append(KaraokeWord(text=word, state=state))

    return result

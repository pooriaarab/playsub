from __future__ import annotations

import re
from dataclasses import dataclass

from playsub.models import LyricLine, TrackLyrics

# Enhanced LRC embeds per-word timestamps like: <00:12.34>hello
ENHANCED_WORD_TAG = re.compile(r"<(\d+):(\d+(?:\.\d+)?)>")

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
    text = lyrics.lines[current_line_index(lyrics, position_sec)].text
    return _strip_word_tags(text)


def next_line_preview(lyrics: TrackLyrics, position_sec: float) -> str:
    index = current_line_index(lyrics, position_sec)
    if index + 1 < len(lyrics.lines):
        return _strip_word_tags(lyrics.lines[index + 1].text)
    for line in lyrics.lines:
        if line.start_sec > position_sec + 0.05:
            return _strip_word_tags(line.text)
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


def _tag_to_seconds(minutes: str, seconds: str) -> float:
    return (int(minutes) * 60) + float(seconds)


def _strip_word_tags(text: str) -> str:
    cleaned = ENHANCED_WORD_TAG.sub("", text)
    return " ".join(cleaned.split())


def _count_syllables(word: str) -> int:
    cleaned = word.lower().strip(".,!?\"'`")
    if not cleaned:
        return 1
    if len(cleaned) <= 3:
        return 1

    count = 0
    prev_vowel = False
    for char in cleaned:
        is_vowel = char in "aeiouy"
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    if cleaned.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _parse_enhanced_word_timings(line: LyricLine, line_end: float) -> list[tuple[str, float, float]]:
    matches = list(ENHANCED_WORD_TAG.finditer(line.text))
    if not matches:
        return []

    timed: list[tuple[str, float, float]] = []
    for index, match in enumerate(matches):
        word_start = _tag_to_seconds(match.group(1), match.group(2))
        content_start = match.end()
        content_end = matches[index + 1].start() if index + 1 < len(matches) else len(line.text)
        word = _strip_word_tags(line.text[content_start:content_end])
        if not word:
            continue
        if index + 1 < len(matches):
            next_match = matches[index + 1]
            word_end = _tag_to_seconds(next_match.group(1), next_match.group(2))
        else:
            word_end = line_end
        timed.append((word, word_start, max(word_end, word_start + 0.05)))
    return timed


def _estimate_word_timings(line: LyricLine, line_end: float) -> list[tuple[str, float, float]]:
    words = [_strip_word_tags(word) for word in line.text.split()]
    words = [word for word in words if word]
    if not words:
        return []

    start = line.start_sec
    gap = max(line_end - start, 0.1)
    syllables = [_count_syllables(word) for word in words]
    total_syllables = sum(syllables)

    # Singing usually finishes before the next lyric line starts.
    estimated_vocal = total_syllables * 0.30
    duration = min(gap * 0.72, max(estimated_vocal, len(words) * 0.10))
    duration = max(duration, len(words) * 0.08)

    cursor = start
    timings: list[tuple[str, float, float]] = []
    for word, syllable_count in zip(words, syllables):
        word_duration = duration * (syllable_count / total_syllables)
        timings.append((word, cursor, cursor + word_duration))
        cursor += word_duration
    return timings


def _word_timings(line: LyricLine, line_end: float) -> tuple[tuple[str, float, float], ...]:
    if line.word_timings:
        return line.word_timings

    enhanced = _parse_enhanced_word_timings(line, line_end)
    if enhanced:
        return tuple(enhanced)

    return tuple(_estimate_word_timings(line, line_end))


def prepare_track_lyrics(lyrics: TrackLyrics) -> TrackLyrics:
    """Bake per-line karaoke timings once when lyrics are loaded."""
    if not lyrics.is_synced or not lyrics.lines:
        return lyrics
    if all(line.word_timings for line in lyrics.lines):
        return lyrics

    prepared: list[LyricLine] = []
    for index, line in enumerate(lyrics.lines):
        if line.word_timings:
            prepared.append(line)
            continue
        end = line_end_sec(lyrics, index)
        prepared.append(
            LyricLine(
                start_sec=line.start_sec,
                text=line.text,
                word_timings=_word_timings(line, end),
            )
        )

    return TrackLyrics(
        track=lyrics.track,
        artist=lyrics.artist,
        lines=prepared,
        plain_text=lyrics.plain_text,
        is_synced=lyrics.is_synced,
        has_word_sync=lyrics.has_word_sync,
    )


def karaoke_words_at_position(
    lyrics: TrackLyrics,
    position_sec: float,
    offset_sec: float = 0.0,
) -> list[KaraokeWord]:
    """Highlight the word being sung right now."""
    if not lyrics.lines:
        return []

    position_sec += offset_sec
    index = current_line_index(lyrics, position_sec)
    line = lyrics.lines[index]
    end = line_end_sec(lyrics, index)
    timings = _word_timings(line, end)
    if not timings:
        return []

    active_index: int | None = None
    for word_index, (_word, word_start, word_end) in enumerate(timings):
        if word_start <= position_sec < word_end:
            active_index = word_index
            break

    if active_index is None:
        if position_sec < timings[0][1]:
            active_index = 0
        elif position_sec >= timings[-1][2]:
            active_index = None
        else:
            for word_index, (_word, word_start, _word_end) in enumerate(timings):
                if position_sec >= word_start:
                    active_index = word_index

    result: list[KaraokeWord] = []
    for word_index, (word, _word_start, word_end) in enumerate(timings):
        if active_index is None:
            state: WordState = "past"
        elif word_index < active_index:
            state = "past"
        elif word_index == active_index:
            state = "active"
        else:
            state = "future"
        result.append(KaraokeWord(text=word, state=state))

    return result

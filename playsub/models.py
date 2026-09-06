from dataclasses import dataclass


@dataclass(frozen=True)
class PlaybackState:
    """What a music player is playing right now."""

    track: str
    artist: str
    album: str
    position_sec: float
    duration_sec: float
    is_playing: bool
    is_ad: bool = False
    player: str = "spotify"


@dataclass(frozen=True)
class LyricLine:
    start_sec: float
    text: str
    # Optional real word timings: (word, start_sec, end_sec)
    word_timings: tuple[tuple[str, float, float], ...] = ()


@dataclass(frozen=True)
class TrackLyrics:
    track: str
    artist: str
    lines: list[LyricLine]
    plain_text: str
    is_synced: bool
    has_word_sync: bool = False

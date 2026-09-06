# Playsub

**Playsub** = play + subtitles. A tiny Mac menu-bar-adjacent overlay that shows synced lyrics for whatever you're listening to, mutes Spotify ads, and launches automatically with your player.

Works with **Spotify** today. Built so **Apple Music**, **YouTube Music**, and others can plug in later.

## Features

- Synced lyric subtitles (via free [LRCLIB](https://lrclib.net/) API)
- Always-on-top floating bar with progress indicator
- **Ad muter** — drops Spotify's in-app volume to 0 during ads, restores after
- **Auto-start** — optional watcher launches Playsub when Spotify opens
- Player-agnostic architecture (`playsub/players/`)

## Quick start

```bash
git clone https://github.com/pooriaarab/playsub.git
cd playsub
./run.sh
```

Or double-click **`Start Playsub.command`**.

Requires **Python 3.14 + tkinter** on macOS:

```bash
brew install python-tk@3.14
```

## Auto-start with Spotify

```bash
chmod +x scripts/install-autostart.sh
./scripts/install-autostart.sh
```

This installs a background watcher. When Spotify opens, Playsub starts. When Spotify quits, Playsub stops.

## Customize look and feel

Press **⌘,** (Command + comma) while Playsub is focused to open settings.

Or edit `~/.config/playsub/config.json` directly.

### Theme presets

| Preset | Vibe |
|--------|------|
| `minimal` | Soft white lyrics, no badge, no green/yellow (default) |
| `cinema` | Just lyrics, very clean |
| `classic` | Old colorful Spotify-style look |
| `custom` | Your own colors and sizes |

### Example config

```json
{
  "window_opacity": 0.78,
  "show_next_line": true,
  "theme": {
    "preset": "minimal",
    "font_family": "Helvetica Neue",
    "lyric_size": 22,
    "lyric_color": "#f2f2f2",
    "background": "#000000",
    "show_badge": false,
    "show_progress": false,
    "show_status": true
  }
}
```

Copy `config.example.json` from the repo as a starting point.

## Config

Optional file: `~/.config/playsub/config.json`

```json
{
  "mute_ads": true,
  "auto_start_with_spotify": true,
  "show_next_line": true,
  "window_opacity": 0.92
}
```

## Controls

| Action | Result |
|--------|--------|
| **Esc** | Quit |
| **Drag** | Move the overlay |

## macOS permissions

Allow **Automation** access so Playsub can read Spotify and control its volume:

**System Settings → Privacy & Security → Automation**

## What else could this do?

Ideas on the roadmap:

- **Apple Music / Music.app** player adapter
- **Karaoke mode** — highlight each word as it's sung
- **Translation** under each line
- **Mini player** with album art
- **Last.fm / Discord** "now playing" status
- **Lyrics search hotkey** when a song has no match
- **Menu bar icon** instead of a floating bar
- **Windows / Linux** support

## Project layout

```
playsub/
  playsub/
    app.py          # main loop
    overlay.py      # subtitle UI
    players/        # spotify today, more later
    lyrics/         # LRCLIB + sync helpers
    audio/          # ad muter
  scripts/          # watcher + autostart installer
  main.py
  run.sh
```

## License

MIT — personal use tool. LRCLIB lyrics are community-sourced, not officially licensed.

#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_NAME="com.pooriaarab.playsub.watcher.plist"
PLIST_SRC="$INSTALL_DIR/launchd/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"
PYTHON_BIN="/opt/homebrew/bin/python3.14"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="/usr/bin/python3"
fi

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$HOME/.config/playsub"

sed "s|__INSTALL_DIR__|$INSTALL_DIR|g; s|__PYTHON_BIN__|$PYTHON_BIN|g; s|__HOME__|$HOME|g" "$PLIST_SRC" > "$PLIST_DST"

launchctl bootout "gui/$(id -u)/$PLIST_NAME" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/$PLIST_NAME"
launchctl kickstart -k "gui/$(id -u)/$PLIST_NAME"

echo "Auto-start installed."
echo "Playsub will launch when Spotify opens."

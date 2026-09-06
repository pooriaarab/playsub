#!/usr/bin/env python3
"""Launch Playsub when Spotify opens; stop when Spotify quits."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

INSTALL_DIR = Path(__file__).resolve().parents[1]
RUN_SCRIPT = INSTALL_DIR / "run.sh"
LOG_PATH = Path.home() / ".config" / "playsub" / "watcher.log"


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def spotify_running() -> bool:
    return subprocess.run(["pgrep", "-x", "Spotify"], capture_output=True).returncode == 0


def playsub_running() -> bool:
    marker = str(INSTALL_DIR / "main.py")
    return subprocess.run(["pgrep", "-f", marker], capture_output=True).returncode == 0


def launch_playsub() -> None:
    env = os.environ.copy()
    env["PLAYSUB_INSTALL_DIR"] = str(INSTALL_DIR)
    subprocess.Popen(
        ["/bin/bash", str(RUN_SCRIPT)],
        cwd=str(INSTALL_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    log("Launched Playsub")


def stop_playsub() -> None:
    marker = str(INSTALL_DIR / "main.py")
    subprocess.run(["pkill", "-f", marker], check=False)
    log("Stopped Playsub")


def main() -> int:
    log("Watcher started")
    playsub_was_running = False

    while True:
        spotify_up = spotify_running()
        playsub_up = playsub_running()

        if spotify_up and not playsub_up:
            launch_playsub()
            playsub_was_running = True
        elif not spotify_up and playsub_up and playsub_was_running:
            stop_playsub()
            playsub_was_running = False
        elif playsub_up:
            playsub_was_running = True

        time.sleep(4)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)

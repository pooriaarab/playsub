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
MAIN_SCRIPT = INSTALL_DIR / "main.py"
LOG_PATH = Path.home() / ".config" / "playsub" / "watcher.log"
LOCK_PATH = Path.home() / ".config" / "playsub" / "playsub.pid"


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def spotify_running() -> bool:
    return subprocess.run(["pgrep", "-x", "Spotify"], capture_output=True).returncode == 0


def _running_pids() -> list[int]:
    marker = str(MAIN_SCRIPT)
    result = subprocess.run(["pgrep", "-f", marker], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.append(int(line))
        except ValueError:
            continue
    return pids


def playsub_running() -> bool:
    return len(_running_pids()) > 0


def cleanup_extra_instances() -> None:
    pids = _running_pids()
    if len(pids) <= 1:
        if pids:
            LOCK_PATH.write_text(str(pids[0]), encoding="utf-8")
        return

    keep = pids[-1]
    for pid in pids[:-1]:
        subprocess.run(["kill", str(pid)], check=False)
    LOCK_PATH.write_text(str(keep), encoding="utf-8")
    log(f"Cleaned duplicate Playsub instances, kept pid {keep}")


def launch_playsub() -> None:
    if playsub_running():
        cleanup_extra_instances()
        return

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
    time.sleep(2)
    cleanup_extra_instances()
    log("Launched Playsub")


def stop_playsub() -> None:
    marker = str(MAIN_SCRIPT)
    subprocess.run(["pkill", "-f", marker], check=False)
    if LOCK_PATH.exists():
        LOCK_PATH.unlink(missing_ok=True)
    log("Stopped Playsub")


def main() -> int:
    log("Watcher started")

    while True:
        spotify_up = spotify_running()
        playsub_up = playsub_running()

        if spotify_up:
            cleanup_extra_instances()
            if not playsub_running():
                launch_playsub()
        elif playsub_up:
            stop_playsub()

        time.sleep(5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(0)

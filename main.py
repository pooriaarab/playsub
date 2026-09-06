#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import sys
from pathlib import Path

LOCK_PATH = Path.home() / ".config" / "playsub" / "playsub.lock"


def _acquire_single_instance_lock() -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK_PATH.open("w", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(0)
    handle.write(str(Path(__file__).resolve()))
    handle.flush()


from playsub.app import PlaysubApp


def main() -> None:
    _acquire_single_instance_lock()
    PlaysubApp().start()


if __name__ == "__main__":
    main()

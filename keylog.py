"""Session file and key normalization logic, independent of the GUI."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def normalize_key(key: object) -> dict[str, str]:
    """Represent a pynput Key or KeyCode without parsing its display string."""
    char = getattr(key, "char", None)
    if isinstance(char, str):
        return {"kind": "character", "value": char}

    name = getattr(key, "name", None)
    if isinstance(name, str):
        return {"kind": "special", "value": name}

    vk = getattr(key, "vk", None)
    if isinstance(vk, int):
        return {"kind": "virtual_key", "value": str(vk)}

    return {"kind": "unknown", "value": type(key).__name__}


def new_session_path(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return directory / f"session-{stamp}-{uuid.uuid4().hex[:8]}.jsonl"


class SessionWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        # Exclusive creation prevents accidental overwrite. On POSIX, mode 0600
        # gives the owner read/write access only.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        self.file: TextIO = os.fdopen(fd, "w", encoding="utf-8", newline="\n")
        self.closed = False
        try:
            self._write({"time": utc_now(), "event": "start"})
        except OSError:
            self.file.close()
            raise

    def _write(self, record: dict[str, object]) -> None:
        self.file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.file.flush()

    def write_key(self, timestamp: str, key: dict[str, str]) -> None:
        if self.closed:
            raise ValueError("Session is closed")
        self._write({"time": timestamp, "event": "key", **key})

    def close(self, reason: str) -> None:
        if self.closed:
            return
        try:
            self._write({"time": utc_now(), "event": "stop", "reason": reason})
        finally:
            self.closed = True
            self.file.close()

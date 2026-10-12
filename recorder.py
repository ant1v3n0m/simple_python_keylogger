"""Bounded, testable lifecycle for an opt-in keyboard recording session."""

from __future__ import annotations

import math
import queue
import time
from pathlib import Path
from typing import Callable

from keylog import SessionWriter, new_session_path, normalize_key, utc_now


class Recorder:
    def __init__(
        self,
        listener_factory: Callable | None = None,
        writer_factory: Callable = SessionWriter,
        clock: Callable[[], float] = time.monotonic,
        queue_capacity: int = 4096,
    ) -> None:
        if queue_capacity < 1:
            raise ValueError("queue_capacity must be positive")
        self.listener_factory = listener_factory
        self.writer_factory = writer_factory
        self.clock = clock
        self.queue_capacity = queue_capacity
        self.events: queue.Queue[tuple[str, dict[str, str]]] = queue.Queue(maxsize=queue_capacity)
        self.listener = None
        self.writer = None
        self.path: Path | None = None
        self.session_id = 0
        self.started_at = 0.0
        self.duration_seconds = 0
        self.count = 0
        self.stop_reason: str | None = None
        self.last_error: str | None = None
        self.overflowed = False
        self.escape_requested = False
        self.callback_error: str | None = None

    @property
    def running(self) -> bool:
        return self.writer is not None

    @property
    def remaining_seconds(self) -> int:
        if not self.running:
            return 0
        return max(0, math.ceil(self.duration_seconds - (self.clock() - self.started_at)))

    def start(self, directory: Path, duration_seconds: int) -> Path:
        if self.running:
            raise RuntimeError("A session is already running")
        if not 60 <= duration_seconds <= 60 * 60:
            raise ValueError("Session duration must be between 1 and 60 minutes")

        listener_factory = self.listener_factory
        if listener_factory is None:
            from pynput.keyboard import Listener

            listener_factory = Listener

        path = new_session_path(directory)
        writer = self.writer_factory(path)
        self.session_id += 1
        session_id = self.session_id
        self.events = queue.Queue(maxsize=self.queue_capacity)
        self.overflowed = False
        self.escape_requested = False
        self.callback_error = None
        self.last_error = None
        self.stop_reason = None
        self.count = 0

        def on_press(key: object) -> None:
            if session_id != self.session_id:
                return
            try:
                normalized = normalize_key(key)
                if normalized == {"kind": "special", "value": "esc"}:
                    self.escape_requested = True
                event = (utc_now(), normalized)
                self.events.put_nowait(event)
            except queue.Full:
                self.overflowed = True
            except Exception as exc:
                # Exceptions in a pynput callback can terminate its listener.
                self.callback_error = str(exc)

        try:
            listener = listener_factory(on_press=on_press)
            listener.start()
        except Exception:
            self.session_id += 1
            try:
                writer.close("listener_error")
            except OSError:
                pass
            raise

        self.writer = writer
        self.listener = listener
        self.path = path
        self.started_at = self.clock()
        self.duration_seconds = duration_seconds
        return path

    def _drain(self) -> bool:
        while True:
            try:
                timestamp, key = self.events.get_nowait()
            except queue.Empty:
                return True
            try:
                self.writer.write_key(timestamp, key)
            except OSError as exc:
                self.last_error = f"Could not write session file: {exc}"
                return False
            self.count += 1

    def poll(self) -> None:
        if not self.running:
            return
        if not self._drain():
            self.stop("write_error", drain=False)
        elif self.overflowed:
            self.last_error = "Event buffer filled; recording stopped to avoid silent data loss."
            self.stop("queue_overflow")
        elif self.callback_error is not None:
            self.last_error = f"Keyboard callback failed: {self.callback_error}"
            self.stop("callback_error")
        elif self.escape_requested:
            self.stop("escape_key")
        elif self.remaining_seconds == 0:
            self.stop("time_limit")
        elif self.listener is not None and not self.listener.running:
            self.stop("listener_stopped")

    def stop(self, reason: str = "user_stopped", drain: bool = True) -> None:
        if not self.running:
            return
        listener = self.listener
        if listener is not None:
            try:
                listener.stop()
            except Exception as exc:
                self.last_error = f"Keyboard listener failed to stop cleanly: {exc}"
                reason = "listener_error"
            try:
                listener.join(timeout=1)
            except Exception as exc:
                self.last_error = f"Keyboard listener failed to finish cleanly: {exc}"
                reason = "listener_error"
            if listener.running:
                self.last_error = "Keyboard listener is still running after a stop request."
                reason = "listener_error"
        self.session_id += 1
        if drain and not self._drain():
            reason = "write_error"
        try:
            self.writer.close(reason)
        except OSError as exc:
            self.last_error = f"Could not finish session file: {exc}"
        finally:
            self.writer = None
            self.listener = None
            self.stop_reason = reason

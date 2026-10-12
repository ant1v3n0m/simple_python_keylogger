"""Visible, time-limited keyboard event recorder for a local test session."""

from __future__ import annotations

import queue
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from keylog import SessionWriter, new_session_path, normalize_key, utc_now


MAX_SESSION_SECONDS = 15 * 60
POLL_MS = 100


class RecorderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Keyboard event recorder")
        self.root.geometry("530x260")
        self.root.resizable(False, False)

        self.events: queue.Queue[tuple[int, str, dict[str, str]]] = queue.Queue()
        self.listener = None
        self.writer: SessionWriter | None = None
        self.session_id = 0
        self.started_at = 0.0
        self.count = 0

        self.status = tk.StringVar(value="Stopped")
        self.details = tk.StringVar(value="Choose Start to begin a local recording session.")
        self.location = tk.StringVar(value="No session file yet")

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Keyboard event recorder", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Records keys across apps while this window is open and visible.").pack(anchor="w", pady=(6, 14))
        ttk.Label(frame, textvariable=self.status, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.details).pack(anchor="w", pady=(3, 8))
        ttk.Label(frame, textvariable=self.location, wraplength=480).pack(anchor="w", pady=(0, 12))

        controls = ttk.Frame(frame)
        controls.pack(anchor="w")
        self.start_button = ttk.Button(controls, text="Start recording", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(controls, text="Stop recording", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=10)

        root.bind("<Unmap>", self.on_unmap)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(POLL_MS, self.poll)

    def start(self) -> None:
        if self.writer is not None:
            return
        try:
            from pynput.keyboard import Listener
        except ImportError:
            messagebox.showerror("Missing dependency", "Install dependencies with: python -m pip install -r requirements.txt")
            return

        try:
            path = new_session_path(Path(__file__).resolve().parent / "logs")
            writer = SessionWriter(path)
        except OSError as exc:
            messagebox.showerror("Cannot create session file", str(exc))
            return

        self.session_id += 1
        session_id = self.session_id

        def on_press(key: object) -> None:
            if session_id == self.session_id:
                self.events.put((session_id, utc_now(), normalize_key(key)))

        try:
            listener = Listener(on_press=on_press)
            listener.start()
        except Exception as exc:
            writer.close("listener_error")
            messagebox.showerror("Cannot start keyboard listener", str(exc))
            return

        self.writer = writer
        self.listener = listener
        self.started_at = time.monotonic()
        self.count = 0
        self.status.set("Recording — visible session")
        self.details.set("0 key events · automatic stop after 15 minutes")
        self.location.set(f"Saved locally: {path}")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def stop(self, reason: str = "user_stopped") -> None:
        if self.writer is None:
            return
        if self.listener is not None:
            self.listener.stop()
            self.listener = None
        self.drain_events()
        if self.writer is None:
            return
        self.session_id += 1
        if self.writer is not None:
            try:
                self.writer.close(reason)
            except OSError as exc:
                messagebox.showerror("Could not finish session file", str(exc))
            self.writer = None
        self.status.set("Stopped")
        self.details.set(f"{self.count} key events recorded")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def drain_events(self) -> None:
        while True:
            try:
                session_id, timestamp, key = self.events.get_nowait()
            except queue.Empty:
                break
            if self.writer is None or session_id != self.session_id:
                continue
            try:
                self.writer.write_key(timestamp, key)
                self.count += 1
            except OSError as exc:
                if self.listener is not None:
                    self.listener.stop()
                    self.listener = None
                try:
                    self.writer.close("write_error")
                except OSError:
                    pass
                self.writer = None
                self.session_id += 1
                self.status.set("Stopped — file error")
                self.details.set(str(exc))
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                break

    def poll(self) -> None:
        if self.writer is not None:
            self.drain_events()
            if self.writer is not None:
                elapsed = int(time.monotonic() - self.started_at)
                remaining = max(0, MAX_SESSION_SECONDS - elapsed)
                self.details.set(f"{self.count} key events · {remaining // 60:02}:{remaining % 60:02} remaining")
                if remaining == 0:
                    self.stop("time_limit")
                elif self.listener is not None and not self.listener.running:
                    self.stop("listener_stopped")
        self.root.after(POLL_MS, self.poll)

    def on_unmap(self, _event: tk.Event) -> None:
        if self.root.state() == "iconic":
            self.stop("window_minimized")

    def close(self) -> None:
        self.stop("window_closed")
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    RecorderApp(root)
    root.mainloop()

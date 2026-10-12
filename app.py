"""Visible desktop interface for opt-in keyboard recording sessions."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from keylog import default_log_directory
from recorder import Recorder


POLL_MS = 100
DURATION_CHOICES = ("5", "15", "30")


class RecorderApp:
    def __init__(self, root: tk.Tk, recorder: Recorder | None = None) -> None:
        self.root = root
        self.recorder = recorder or Recorder()
        self.root.title("Keyboard event recorder")
        self.root.geometry("650x360")
        self.root.resizable(False, False)

        self.folder = tk.StringVar(value=str(default_log_directory()))
        self.duration = tk.StringVar(value="15")
        self.status = tk.StringVar(value="Stopped")
        self.details = tk.StringVar(value="Choose a folder and click Start recording.")
        self.location = tk.StringVar(value="No session file yet")

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Keyboard event recorder", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Records keys across apps only during a visible session.").pack(anchor="w", pady=(6, 15))

        folder_row = ttk.Frame(frame)
        folder_row.pack(fill="x", pady=(0, 8))
        ttk.Label(folder_row, text="Save in:").pack(side="left")
        ttk.Entry(folder_row, textvariable=self.folder, state="readonly", width=60).pack(side="left", padx=8)
        self.folder_button = ttk.Button(folder_row, text="Choose…", command=self.choose_folder)
        self.folder_button.pack(side="left")

        duration_row = ttk.Frame(frame)
        duration_row.pack(anchor="w", pady=(0, 12))
        ttk.Label(duration_row, text="Session limit:").pack(side="left")
        self.duration_box = ttk.Combobox(
            duration_row, textvariable=self.duration, values=DURATION_CHOICES, state="readonly", width=5
        )
        self.duration_box.pack(side="left", padx=(8, 4))
        ttk.Label(duration_row, text="minutes").pack(side="left")

        ttk.Label(frame, textvariable=self.status, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.details, wraplength=600).pack(anchor="w", pady=(3, 5))
        ttk.Label(frame, textvariable=self.location, wraplength=600).pack(anchor="w", pady=(0, 13))

        controls = ttk.Frame(frame)
        controls.pack(anchor="w")
        self.start_button = ttk.Button(controls, text="Start recording", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(controls, text="Stop recording", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        ttk.Label(
            frame,
            text="Session files are plain text and may contain private input. Use only with permission.",
            wraplength=600,
        ).pack(anchor="w", pady=(13, 0))

        root.bind("<Unmap>", self.on_unmap)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(POLL_MS, self.poll)

    def choose_folder(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.folder.get(), title="Choose session folder")
        if chosen:
            self.folder.set(chosen)

    def start(self) -> None:
        try:
            self.recorder.start(Path(self.folder.get()), int(self.duration.get()) * 60)
        except Exception as exc:
            messagebox.showerror("Could not start recording", str(exc))
            return
        self.render()

    def stop(self, reason: str = "user_stopped") -> None:
        self.recorder.stop(reason)
        self.render()

    def poll(self) -> None:
        self.recorder.poll()
        self.render()
        self.root.after(POLL_MS, self.poll)

    def render(self) -> None:
        if self.recorder.running:
            remaining = self.recorder.remaining_seconds
            self.status.set("Recording — visible session")
            self.details.set(
                f"{self.recorder.count} key events · {remaining // 60:02}:{remaining % 60:02} remaining"
            )
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.folder_button.configure(state="disabled")
            self.duration_box.configure(state="disabled")
        else:
            self.status.set("Stopped — error" if self.recorder.last_error else "Stopped")
            if self.recorder.last_error:
                self.details.set(self.recorder.last_error)
            elif self.recorder.stop_reason:
                self.details.set(
                    f"{self.recorder.count} key events · stopped: {self.recorder.stop_reason.replace('_', ' ')}"
                )
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.folder_button.configure(state="normal")
            self.duration_box.configure(state="readonly")
        if self.recorder.path is not None:
            self.location.set(f"Saved locally: {self.recorder.path}")

    def on_unmap(self, _event: tk.Event) -> None:
        if self.root.state() == "iconic":
            self.stop("window_minimized")

    def close(self) -> None:
        self.stop("window_closed")
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    RecorderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

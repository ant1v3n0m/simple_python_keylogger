# Keyboard event recorder

A small, visible Python keylogger for testing keyboard input on a computer you control. It records key press events across desktop apps only after you click **Start recording**. Each session is local, time-limited, and easy to stop.

## What changed

- A desktop window shows whether recording is active, the event count, the remaining time, and the file path.
- **Stop recording**, closing the window, minimizing it, or reaching 15 minutes ends the session.
- Each press is a timestamped JSON Lines event. Character input is stored as Unicode; special keys such as Backspace are named events. The logger never rewrites earlier events.
- Session files have unique names and are created exclusively, so an old session cannot be overwritten.
- Files remain in the local `logs/` directory, which Git ignores. The program has no network, background startup, or remote reporting features.

## Install and run

Use Python 3.10 or newer on a desktop with a graphical session. From this repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.pyw
```

The app uses `pynput` for keyboard events and Tkinter for its window. Some operating systems may require keyboard monitoring permission. The recorder cannot capture keys in sessions or apps that the operating system denies it access to.

Click **Start recording** to create a new file under `logs/`. Click **Stop recording** when finished. Every new start creates a separate file. The location of the current session file appears in the window.

## Log format

Each line is an independent JSON object. For example:

```jsonl
{"time":"2026-10-12T10:00:00.000+00:00","event":"start"}
{"time":"2026-10-12T10:00:01.000+00:00","event":"key","kind":"character","value":"a"}
{"time":"2026-10-12T10:00:02.000+00:00","event":"key","kind":"special","value":"backspace"}
{"time":"2026-10-12T10:00:03.000+00:00","event":"stop","reason":"user_stopped"}
```

Backspace is recorded as an event rather than deleting a previous line. This preserves the actual sequence of key presses. Timestamps are in UTC.

## Privacy

Use this only for a session you have permission to record. Global keyboard events can include passwords, messages, and other private input. Avoid entering secrets while a session is active. Review and delete session files when you no longer need them. The `logs/` directory is excluded from Git, but copies and backups of those files still need care.

## Tests

```powershell
python -m unittest discover -s tests -v
```

The tests cover key normalization, Unicode and special-key records, session boundaries, and overwrite protection. They do not simulate operating system keyboard events.

# Keyboard event recorder

An installable, visible Python keylogger for testing keyboard input on a computer you control. Recording begins only after you click **Start recording** and ends on request, when the window is minimized or closed, or when the session limit is reached.

## Features

- Choose a local output folder and a 5, 15, or 30 minute session limit.
- See recording status, event count, remaining time, and output path in the window.
- Save timestamped JSON Lines records for Unicode characters and named special keys.
- Keep each session in a unique file. Backspace remains an event rather than rewriting history.
- Stop on listener, callback, buffer, or file errors. A full event buffer is reported instead of silently losing keys.
- Keep session data outside the installed application by default. There is no network reporting or automatic startup.

## Install and run

Use Python 3.10 or newer in a graphical desktop session. On Windows, from this repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\keyboard-recorder.exe
```

You can also run `.\.venv\Scripts\python.exe main.pyw`. On macOS or Linux, activate the virtual environment and run `keyboard-recorder`; keyboard monitoring permissions or an X11 session may be required. Protected apps and secure input fields may not be available to the listener.

The default session folder is `%LOCALAPPDATA%\KeyboardEventRecorder\Sessions` on Windows, `~/Library/Application Support/KeyboardEventRecorder/Sessions` on macOS, and `$XDG_STATE_HOME/keyboard-event-recorder/sessions` on Linux (or `~/.local/state/keyboard-event-recorder/sessions` when `XDG_STATE_HOME` is unset). You can choose another folder before starting a session.

## Log format

Each line is a separate JSON object. For example:

```jsonl
{"time":"2026-10-12T10:00:00.000+00:00","event":"start","schema_version":1}
{"time":"2026-10-12T10:00:01.000+00:00","event":"key","kind":"character","value":"a"}
{"time":"2026-10-12T10:00:02.000+00:00","event":"key","kind":"special","value":"backspace"}
{"time":"2026-10-12T10:00:03.000+00:00","event":"stop","reason":"user_stopped"}
```

Timestamps are in UTC. A session ends with a `stop` record when the file can be written. A crash or storage failure may leave a partial final line; JSON Lines readers should handle that possibility.

## Privacy and limits

Use this only for a session you have permission to record. Global keyboard events can include passwords, messages, and other private input. Avoid entering secrets while recording, and delete session files when you no longer need them. The program does not identify password fields or automatically redact sensitive text. The files are local JSON Lines, not encrypted.

This is a desktop input testing tool. It does not promise capture from elevated, protected, remote, or secure desktop sessions. Whether those events are available depends on the operating system and its permissions.

## Project layout and tests

- `app.py`: desktop interface and session controls.
- `recorder.py`: bounded event queue and start/stop lifecycle.
- `keylog.py`: key normalization and session file format.
- `main.pyw`: Windows double-click launcher.
- `tests/`: normalization, file safety, restart, timeout, overflow, and write-error tests.

Run the tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

CI runs the tests on Windows with Python 3.10 and 3.13. The tests use simulated key events; they do not collect input from the test machine.

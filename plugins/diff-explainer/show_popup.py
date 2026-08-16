#!/usr/bin/env python3
"""Invoked by the /diff-explainer:explain command. Reads the most recently
recorded file change (written by hook_script.py) and opens the popup for
it, as a fully detached process, without blocking the command."""

import json
import os
import subprocess
import sys
import tempfile

STATE_FILE = os.path.expanduser("~/.claude-diff-explainer/latest.json")


def main():
    if not os.path.exists(STATE_FILE):
        print("No recent file changes recorded yet — edit or create a file, then run this again.")
        return

    try:
        with open(STATE_FILE) as f:
            diff_data = json.load(f)
    except (json.JSONDecodeError, OSError):
        print("Couldn't read the last recorded change.")
        return

    # Copy into a fresh temp file so popup_app.py (which deletes its input
    # file after reading) doesn't consume the persistent state file —
    # that way running /diff-explainer:explain again before the next edit
    # still works.
    fd, temp_path = tempfile.mkstemp(prefix="diff-explainer-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(diff_data, f)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    popup_script = os.path.join(script_dir, "popup_app.py")

    subprocess.Popen(
        [sys.executable, popup_script, temp_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )

    print(f"Opened the diff explainer popup for {diff_data.get('file_path', 'the last change')}.")


if __name__ == "__main__":
    main()

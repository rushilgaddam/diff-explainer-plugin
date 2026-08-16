#!/usr/bin/env python3
"""PostToolUse hook: builds a diff for the edit that just happened and hands
it off to a detached popup process, without blocking Claude Code."""

import difflib
import json
import os
import subprocess
import sys
import tempfile


def build_diff_for_edit(tool_input):
    old = tool_input.get("old_string", "")
    new = tool_input.get("new_string", "")
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile="before",
            tofile="after",
        )
    )


def build_diff_for_multiedit(tool_input):
    parts = []
    for edit in tool_input.get("edits", []):
        old = edit.get("old_string", "")
        new = edit.get("new_string", "")
        parts.append(
            "".join(
                difflib.unified_diff(
                    old.splitlines(keepends=True),
                    new.splitlines(keepends=True),
                    fromfile="before",
                    tofile="after",
                )
            )
        )
    return "".join(parts)


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    cwd = payload.get("cwd", "")
    file_path = tool_input.get("file_path", "")

    if tool_name == "Edit":
        diff = build_diff_for_edit(tool_input)
        kind = "edit"
    elif tool_name == "MultiEdit":
        diff = build_diff_for_multiedit(tool_input)
        kind = "multi_edit"
    elif tool_name == "Write":
        diff = tool_input.get("content", "")
        kind = "write"
    else:
        return

    if not diff or not diff.strip():
        return

    fd, temp_path = tempfile.mkstemp(prefix="diff-explainer-", suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(
            {
                "file_path": file_path,
                "diff": diff,
                "kind": kind,
                "tool_name": tool_name,
                "cwd": cwd,
            },
            f,
        )

    script_dir = os.path.dirname(os.path.abspath(__file__))
    popup_script = os.path.join(script_dir, "popup_app.py")

    subprocess.Popen(
        [sys.executable, popup_script, temp_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )


if __name__ == "__main__":
    main()

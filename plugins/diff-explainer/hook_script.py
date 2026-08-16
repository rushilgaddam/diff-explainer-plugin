#!/usr/bin/env python3
"""PostToolUse hook: builds a diff for the edit that just happened and
records it to disk for later review. Does NOT open the popup itself — the
popup only opens when the user runs the /diff-explainer:explain command.
This keeps the hook a fast, synchronous file write with no subprocess
spawn, so it never blocks Claude Code."""

import difflib
import json
import os
import sys

STATE_FILE = os.path.expanduser("~/.claude-diff-explainer/latest.json")


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

    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp_path = STATE_FILE + ".tmp"
    with open(tmp_path, "w") as f:
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
    os.replace(tmp_path, STATE_FILE)


if __name__ == "__main__":
    main()

---
description: Open the diff-explainer popup for the most recent file change Claude Code made
disable-model-invocation: true
allowed-tools: Bash(python3:${CLAUDE_PLUGIN_ROOT}/*)
---

Run the diff-explainer popup for the most recently recorded file change:

!`python3 ${CLAUDE_PLUGIN_ROOT}/show_popup.py`

Relay the line above back to the user as-is. Don't add your own explanation
of the diff — the popup handles that itself in a separate window.

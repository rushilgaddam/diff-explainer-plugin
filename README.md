# diff-explainer

A Claude Code plugin that explains file changes in a small dark-themed chat
popup, on demand, and lets you ask follow-up questions — all without
blocking or touching your main Claude Code session.

The popup does **not** appear automatically on every edit. It opens only
when you explicitly run `/diff-explainer:explain`, showing the most recent
change Claude Code made.

## How it works

1. Claude Code fires the `PostToolUse` hook after every `Edit`, `Write`, or
   `MultiEdit` call.
2. `hook_script.py` reads the tool call off stdin, builds a unified diff
   (or grabs the raw content for a fresh `Write`), and writes it to
   `~/.claude-diff-explainer/latest.json`, overwriting whatever was there
   before. That's it — no window opens, no process is spawned. This keeps
   the hook a fast, synchronous file write that never blocks Claude Code.
3. When you want to see it, run `/diff-explainer:explain` in your Claude
   Code session. That's a plugin skill/command
   (`plugins/diff-explainer/skills/explain/SKILL.md`) which runs
   `show_popup.py`.
4. `show_popup.py` reads `latest.json`, copies it to a temp file, and spawns
   `popup_app.py` as a fully detached background process.
5. `popup_app.py` reads the temp file, opens a small `pywebview` window
   (`ui.html`), and makes its own, separate call to the Anthropic API to
   generate the initial explanation.
6. The popup's chat box lets you keep asking follow-up questions; each one
   is a fresh API call scoped to that popup's own conversation.

Because the popup is a separate OS process from Claude Code, closing it,
crashing it, or leaving it open indefinitely has no effect on your Claude
Code session. And because opening it is a manual action, it never
interrupts your flow while Claude is working.

## Setup

1. Get an Anthropic API key and export it in your shell profile:

   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

   Restart your terminal (or `source` your profile) so the variable is
   available to processes spawned by Claude Code.

2. From inside a Claude Code session, run:

   ```
   /plugin marketplace add ./diff-explainer-plugin
   /plugin install diff-explainer@diff-explainer-tools
   ```

3. Edit or create a file with Claude Code as usual, then run
   `/diff-explainer:explain` whenever you want to see it explained. A popup
   window opens showing the explanation and a chat box for follow-ups.

Dependencies (`pywebview`, `anthropic`) are installed automatically on
first run via `pip install --user`, so there's no manual `pip install`
step on a fresh machine — just Python 3 and network access.

## Distributing it to others

1. Push this directory to a GitHub repo (e.g.
   `your-username/diff-explainer-plugin`).
2. Anyone who wants it runs, from inside Claude Code:

   ```
   /plugin marketplace add your-username/diff-explainer-plugin
   /plugin install diff-explainer@diff-explainer-tools
   ```

3. Each person needs their **own** `ANTHROPIC_API_KEY` set in their shell
   environment — the plugin never bundles or shares a key.

## Auto-installing for a team

To have the plugin install automatically for everyone working in a shared
project, add it to that project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "diff-explainer-tools": {
      "source": {
        "source": "github",
        "repo": "your-username/diff-explainer-plugin"
      }
    }
  },
  "enabledPlugins": {
    "diff-explainer@diff-explainer-tools": true
  }
}
```

Commit that file, and anyone who opens the project with Claude Code will
have the marketplace and plugin enabled automatically (they still each
need their own `ANTHROPIC_API_KEY`).

## Before pushing

Run this from the repo root to catch marketplace/plugin JSON errors before
they reach anyone else:

```bash
claude plugin validate .
```

## Known rough edges

- No fixed window placement — the popup opens wherever your OS/window
  manager decides.
- Only the single most recent change is tracked — if you make several
  edits before running `/diff-explainer:explain`, only the last one is
  shown; earlier ones are silently overwritten in `latest.json`.
- The state file (`~/.claude-diff-explainer/latest.json`) isn't scoped per
  project or session — it's overwritten globally by whichever Claude Code
  session edited a file most recently.
- Conversations aren't persisted — once you close a popup, that chat
  history is gone.
- Very large `Write` contents are sent to the model uncapped, which can
  get slow or expensive for big generated files.

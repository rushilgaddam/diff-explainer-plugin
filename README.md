# diff-explainer

A Claude Code plugin that pops up a small dark-themed chat window every time
Claude Code edits or creates a file, explains the change in plain language,
and lets you ask follow-up questions — all without blocking or touching your
main Claude Code session.

## How it works

1. Claude Code fires the `PostToolUse` hook after every `Edit`, `Write`, or
   `MultiEdit` call.
2. `hook_script.py` reads the tool call off stdin, builds a unified diff
   (or grabs the raw content for a fresh `Write`), writes it to a temp file,
   and spawns `popup_app.py` as a fully detached background process. The
   hook then exits immediately — it never blocks the main session.
3. `popup_app.py` reads the temp file, opens a small `pywebview` window
   (`ui.html`), and makes its own, separate call to the Anthropic API to
   generate the initial explanation.
4. The popup's chat box lets you keep asking follow-up questions; each one
   is a fresh API call scoped to that popup's own conversation.

Because the popup is a separate OS process from Claude Code, closing it,
crashing it, or leaving it open indefinitely has no effect on your Claude
Code session.

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

3. Edit or create a file with Claude Code as usual. A popup window should
   appear explaining the change within a few seconds.

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
- No debouncing — several rapid-fire edits (e.g. from a `MultiEdit`-heavy
  refactor) will spawn multiple popups at once.
- Conversations aren't persisted — once you close a popup, that chat
  history is gone.
- Very large `Write` contents are sent to the model uncapped, which can
  get slow or expensive for big generated files.

#!/usr/bin/env python3
"""Standalone popup process spawned (detached) by hook_script.py.

Self-installs its two dependencies on first run, reads the diff payload
written by the hook, then opens a small pywebview chat window backed by
the Anthropic API.
"""

import importlib
import json
import os
import subprocess
import sys


def _ensure_installed(module_name, package_name=None):
    package_name = package_name or module_name
    try:
        importlib.import_module(module_name)
    except ImportError:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "--user", package_name],
            check=False,
        )


_ensure_installed("webview", "pywebview")
_ensure_installed("anthropic")

import webview  # noqa: E402
import anthropic  # noqa: E402


SYSTEM_PROMPT = """You are a terse coding tutor embedded in a small popup \
that appears whenever Claude Code edits or creates a file. On the first \
message, explain in 2-4 sentences what changed and why, in plain language \
— do not restate the diff line by line. On follow-up questions, answer \
directly and concisely, assuming a competent-programmer audience. Cap \
responses at roughly 120 words unless the user explicitly asks for more \
detail. Do not use markdown headers or code fences; your output renders \
in a plain text chat bubble."""


class Api:
    def __init__(self, diff_data):
        self.diff_data = diff_data
        self.messages = []
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.missing_key = not bool(api_key)
        if not self.missing_key:
            self.client = anthropic.Anthropic()

    def get_meta(self):
        return {
            "file_path": self.diff_data.get("file_path", ""),
            "kind": self.diff_data.get("kind", ""),
        }

    def get_initial_explanation(self):
        if self.missing_key:
            return (
                "ANTHROPIC_API_KEY isn't set, so I can't reach the API. "
                "Set it with `export ANTHROPIC_API_KEY=sk-ant-...` and "
                "restart your terminal, then trigger a new edit."
            )

        file_path = self.diff_data.get("file_path", "unknown file")
        diff = self.diff_data.get("diff", "")
        kind = self.diff_data.get("kind", "edit")

        user_text = (
            f"File: {file_path}\n"
            f"Change kind: {kind}\n\n"
            f"Diff / content:\n{diff}"
        )
        self.messages.append({"role": "user", "content": user_text})
        reply = self._call_model()
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def send_message(self, user_text):
        self.messages.append({"role": "user", "content": user_text})
        reply = self._call_model()
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def _call_model(self):
        try:
            response = self.client.messages.create(
                model="claude-sonnet-5",
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=self.messages,
            )
            return "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()
        except Exception as e:
            return f"(error talking to the API: {e})"


def main():
    temp_path = sys.argv[1]
    with open(temp_path) as f:
        diff_data = json.load(f)
    os.remove(temp_path)

    api = Api(diff_data)

    file_label = os.path.basename(diff_data.get("file_path", "") or "file")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(script_dir, "ui.html")

    webview.create_window(
        f"Diff Explainer — {file_label}",
        ui_path,
        js_api=api,
        width=440,
        height=560,
        on_top=True,
        background_color="#1e1f22",
    )
    webview.start()


if __name__ == "__main__":
    main()

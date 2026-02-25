#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path


def is_powermode_session(cwd: str, session_id: str) -> bool:
    """Check if powermode is active for this session."""
    if not cwd or not session_id:
        return False
    state_file = Path(cwd) / ".powermode" / "active-mode.json"
    if not state_file.exists():
        return False
    try:
        data = json.loads(state_file.read_text())
        return data.get("session_id") == session_id
    except (json.JSONDecodeError, OSError):
        return False


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        json.dump({"continue": True}, sys.stdout)
        return

    cwd = hook_input.get("cwd", "")
    session_id = hook_input.get("session_id", "")

    if not is_powermode_session(cwd, session_id):
        json.dump({"continue": True}, sys.stdout)
        return

    state_file = Path(cwd) / ".powermode" / "context-state.json"

    additional_context = None

    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                state = json.load(f)

            tool_calls = state.get("tool_calls", 0)

            if tool_calls >= 10:
                tokens = state.get("tokens", 0)
                token_percent = state.get("token_percent", 0)
                modified_files = state.get("modified_files", [])
                current_task = state.get("current_task", "")

                files_str = ", ".join(modified_files[:3])
                if len(modified_files) > 3:
                    files_str += f", +{len(modified_files) - 3} more"

                task_hint = f", task: {current_task[:30]}" if current_task else ""

                additional_context = f"[Session Context: ~{tokens}K tokens ({token_percent}%), {tool_calls} calls, modified: {files_str}{task_hint}]"

                if len(additional_context) > 500:
                    additional_context = additional_context[:497] + "...]"

        except (json.JSONDecodeError, ValueError, KeyError):
            pass

    output: dict = {"continue": True}
    if additional_context:
        output["hookSpecificOutput"] = {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        }

    json.dump(output, sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

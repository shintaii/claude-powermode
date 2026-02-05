#!/usr/bin/env python3
"""
Workflow Reinforcer Hook (PostToolUse: AskUserQuestion)

After a user answers a clarifying question, re-injects the Power Mode
methodology reminder so Claude doesn't drift back to default behavior
(e.g., editing files directly instead of delegating to pm-implementer).

Only injects when a .powermode/context-state.json exists (active session).

Exit codes:
- 0: Always exits cleanly
"""

import json
import sys
from pathlib import Path

REINFORCEMENT = """[POWER MODE REMINDER - Post-Clarification]

The user answered your question. Continue using Power Mode methodology:
- IMPLEMENT via pm-implementer (Task tool) - do NOT write code yourself
- VERIFY via pm-verifier after implementation
- Keep using session_id for follow-ups with the same agent"""


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    cwd = input_data.get("cwd", ".")
    session_id = input_data.get("session_id", "")

    if tool_name != "AskUserQuestion":
        print(json.dumps({"continue": True}))
        return

    state_file = Path(cwd) / ".powermode" / "active-mode.json"

    # Only reinforce if powermode session is active (same session)
    powermode_active = False
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                data = json.load(f)
            powermode_active = (
                data.get("mode") == "powermode"
                and data.get("session_id") == session_id
            )
        except (json.JSONDecodeError, IOError):
            pass

    if powermode_active:
        print(json.dumps({
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": REINFORCEMENT.strip(),
            },
        }))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()

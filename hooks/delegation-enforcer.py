#!/usr/bin/env python3
"""Delegation Enforcer Hook (PreToolUse: Edit, Write)

Warns the main agent when it attempts to Edit/Write files directly
while Power Mode is active. The delegation principle requires using
pm-implementer for code changes.

Fires on: PreToolUse (Edit, Write)

Exit codes:
- 0: Always exits cleanly
"""

import json
import sys
from pathlib import Path

WARNING = """[POWER MODE DELEGATION WARNING]

You are editing files directly while Power Mode is active. This violates the delegation principle.

DELEGATE to pm-implementer instead:
Task(subagent_type="pm-implementer", prompt="...")

Only edit directly for truly trivial changes (typos, single-line fixes classified as 'Trivial' or 'Explicit' intent)."""


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IOError):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {},
            }
        }))
        return

    tool_input = input_data.get("tool_input", {})
    cwd = input_data.get("cwd", ".")

    active_mode_file = Path(cwd) / ".powermode" / "active-mode.json"

    powermode_active = False
    try:
        if active_mode_file.exists():
            mode_data = json.loads(active_mode_file.read_text())
            powermode_active = mode_data.get("mode") == "powermode"
    except (json.JSONDecodeError, IOError, OSError):
        pass

    if powermode_active:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": WARNING.strip(),
                "updatedInput": {**tool_input},
            }
        }))
    else:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {**tool_input},
            }
        }))


if __name__ == "__main__":
    main()

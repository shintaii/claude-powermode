#!/usr/bin/env python3
"""Post-Question Reinforcer Hook (PostToolUse: AskUserQuestion)

When Power Mode is active, reminds the agent to delegate code changes
to pm-implementer and verify via pm-verifier after user answers a question.

Fires on: PostToolUse (AskUserQuestion)

Exit codes:
- 0: Always exits cleanly
"""

import json
import sys
from pathlib import Path

REINFORCEMENT_MSG = (
    "[POWER MODE REMINDER] After receiving user input: "
    "delegate code changes to pm-implementer (Task tool), "
    "verify via pm-verifier, do NOT edit code directly."
)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IOError):
        print(json.dumps({"continue": True}))
        sys.exit(0)

    cwd = input_data.get("cwd", ".")
    session_id = input_data.get("session_id", "")

    active_mode_file = Path(cwd) / ".powermode" / "active-mode.json"

    try:
        if active_mode_file.exists():
            mode_data = json.loads(active_mode_file.read_text())
            if (
                mode_data.get("mode") == "powermode"
                and mode_data.get("session_id") == session_id
            ):
                print(json.dumps({
                    "continue": True,
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": REINFORCEMENT_MSG,
                    },
                }))
                sys.exit(0)
    except (json.JSONDecodeError, IOError, OSError):
        pass

    print(json.dumps({"continue": True}))
    sys.exit(0)


if __name__ == "__main__":
    main()

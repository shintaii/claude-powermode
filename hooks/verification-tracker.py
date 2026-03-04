#!/usr/bin/env python3
"""Verification Tracker Hook (SubagentStop: powermode:pm-verifier)

After pm-verifier completes:
- Clears pending-verification (unblocks next implementer)
- Injects reminder to run simplify via additionalContext

Fires on: SubagentStop (powermode:pm-verifier)
"""

import json
import sys
from pathlib import Path


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IOError):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SubagentStop", "additionalContext": "Parse error, allowing"}}))
        sys.exit(0)

    cwd = input_data.get("cwd", ".")
    state_dir = Path(cwd) / ".powermode"
    pending_verification = state_dir / "pending-verification.json"

    try:
        if pending_verification.exists():
            pending_verification.unlink()
    except (IOError, OSError):
        pass

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SubagentStop",
            "additionalContext": (
                "[POWER MODE] Verification complete. "
                "Run Skill(skill='simplify') now — this is MANDATORY after verification completes. "
                "Do NOT skip simplify."
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SubagentStop", "additionalContext": "Error, allowing"}}))
    sys.exit(0)

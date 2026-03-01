#!/usr/bin/env python3
"""Verification Tracker Hook (SubagentStop: powermode:pm-verifier)

After pm-verifier completes:
- Clears pending-verification (unblocks next implementer)
- Sets pending-completion (enforces simplify + commit before session ends)

Fires on: SubagentStop (powermode:pm-verifier)
"""

import json
import sys
from pathlib import Path


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IOError):
        print(json.dumps({"decision": "approve", "reason": "Parse error, allowing"}))
        sys.exit(0)

    cwd = input_data.get("cwd", ".")
    state_dir = Path(cwd) / ".powermode"
    pending_verification = state_dir / "pending-verification.json"
    pending_completion = state_dir / "pending-completion.json"

    try:
        if pending_verification.exists():
            pending_verification.unlink()
            # Set pending-completion to enforce simplify + commit
            state_dir.mkdir(parents=True, exist_ok=True)
            pending_completion.write_text(json.dumps({"awaiting": "simplify+commit"}))
    except (IOError, OSError):
        pass

    print(json.dumps({
        "decision": "approve",
        "reason": "Verification complete. Pending completion set (simplify + commit required).",
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"decision": "approve", "reason": "Error, allowing"}))
    sys.exit(0)

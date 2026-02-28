#!/usr/bin/env python3
"""Verification Tracker Hook (SubagentStop: powermode:pm-verifier)

Clears the pending-verification flag after pm-verifier completes,
allowing the next pm-implementer to proceed.

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
    pending_file = Path(cwd) / ".powermode" / "pending-verification.json"

    try:
        if pending_file.exists():
            pending_file.unlink()
    except (IOError, OSError):
        pass

    print(json.dumps({
        "decision": "approve",
        "reason": "Verification complete. Pending flag cleared.",
    }))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"decision": "approve", "reason": "Error, allowing"}))
    sys.exit(0)

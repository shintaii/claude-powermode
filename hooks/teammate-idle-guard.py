#!/usr/bin/env python3
"""TeammateIdle hook: force teammate to commit if they have uncommitted changes.

Fires when a teammate is about to go idle. If they have uncommitted changes,
exit 2 sends feedback that forces them to continue and commit.
Only applies to powermode teammates.
"""
import json
import subprocess
import sys


def main():
    try:
        event_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        # Can't parse — let them go idle
        sys.exit(0)

    agent_type = event_data.get("agent_type", "")
    if not agent_type.startswith("powermode:"):
        sys.exit(0)

    cwd = event_data.get("cwd", ".")
    teammate_name = event_data.get("teammate_name", "unknown")

    # Check for uncommitted changes
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=cwd, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            changed_count = len(result.stdout.strip().splitlines())
            feedback = (
                f"You ({teammate_name}) have {changed_count} uncommitted change(s). "
                "You must commit your implementation before going idle. "
                "Run: git add <changed files> && git commit -m '<feature-slug>: <description>'"
            )
            print(feedback, file=sys.stderr)
            sys.exit(2)
    except (subprocess.TimeoutExpired, OSError):
        pass

    # No issues — allow idle
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

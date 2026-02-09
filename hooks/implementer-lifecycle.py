#!/usr/bin/env python3
"""Implementer Lifecycle Hook (SubagentStart + SubagentStop: powermode:implementer)

Manages the implementer session file lifecycle:
- SubagentStart: Creates .powermode/implementer-session.json
- SubagentStop: Deletes .powermode/implementer-session.json

Replaces the old timestamp-based session hack in task-containment-enforcer.

Fires on: SubagentStart (powermode:implementer), SubagentStop (powermode:implementer)

Exit codes:
- 0: Always exits cleanly
"""

import json
import sys
from pathlib import Path


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IOError):
        # Safe default for both event types
        print(json.dumps({"decision": "approve", "reason": "Parse error, allowing"}))
        sys.exit(0)

    hook_event = input_data.get("hook_event_name", "")
    agent_type = input_data.get("agent_type", "")
    agent_id = input_data.get("agent_id", "unknown")
    cwd = input_data.get("cwd", ".")

    powermode_dir = Path(cwd) / ".powermode"
    session_file = powermode_dir / "implementer-session.json"

    if hook_event == "SubagentStart":
        try:
            session_id = input_data.get("session_id", "")
            powermode_dir.mkdir(parents=True, exist_ok=True)
            session_file.write_text(json.dumps({
                "agent": "pm-implementer",
                "agent_id": agent_id,
                "session_id": session_id,
            }))
        except (IOError, OSError):
            pass

        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": f"[POWER MODE] Implementer session registered (agent_id={agent_id})",
            }
        }))

    elif hook_event == "SubagentStop":
        try:
            if session_file.exists():
                session_file.unlink()
        except (IOError, OSError):
            pass

        print(json.dumps({
            "decision": "approve",
            "reason": f"Implementer session cleaned up (agent_id={agent_id})",
        }))

    else:
        # Unknown event - safe default
        print(json.dumps({"decision": "approve", "reason": "Unknown event, allowing"}))

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

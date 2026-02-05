#!/usr/bin/env python3
"""Delegation Enforcer Hook (PreToolUse: Edit, Write)

BLOCKS direct Edit/Write when Power Mode is active. The delegation
principle requires using pm-implementer for code changes.

Bypass mechanisms:
1. pm-implementer creates .powermode/implementer-session.json before editing
2. Escape hatch after 5 blocked attempts (for edge cases)

Fires on: PreToolUse (Edit, Write)

Exit codes:
- 0: Always exits cleanly
"""

import json
import sys
import time
from pathlib import Path

ESCAPE_THRESHOLD = 10
SESSION_EXPIRY_SECONDS = 600  # 10 minutes

BLOCK_MSG = """[EDIT DENIED - POLICY VIOLATION]

This edit has been BLOCKED by Power Mode policy. RETRYING WILL NOT HELP.

You MUST delegate code changes to pm-implementer:
  Task(subagent_type="powermode:implementer", prompt="<describe what to implement>")

DO NOT:
- Try to edit directly again (it will keep failing)
- Rationalize why you should be allowed to edit
- Use the escape hatch unless you ARE pm-implementer

Attempt {attempt}/{threshold}. Escape hatch for pm-implementer only."""

ALLOW_IMPLEMENTER_MSG = """[POWER MODE: Edit allowed - pm-implementer session active]"""

ALLOW_ESCAPE_MSG = """[POWER MODE: Edit allowed via escape hatch after {attempts} attempts]

If you're the main agent, this is a workflow violation."""


def load_json(path: Path) -> dict | None:
    try:
        if path.exists():
            return json.loads(path.read_text())
    except (json.JSONDecodeError, IOError, OSError):
        pass
    return None


def save_json(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    except (IOError, OSError):
        pass


def check_implementer_session(powermode_dir: Path) -> bool:
    """Check if pm-implementer has an active session."""
    session_file = powermode_dir / "implementer-session.json"
    session = load_json(session_file)
    if not session:
        return False

    if session.get("agent") != "pm-implementer":
        return False

    ts = session.get("ts", 0)
    if time.time() - ts > SESSION_EXPIRY_SECONDS:
        return False

    return True


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

    powermode_dir = Path(cwd) / ".powermode"
    active_mode_file = powermode_dir / "active-mode.json"
    state_file = powermode_dir / "delegation-state.json"

    mode_data = load_json(active_mode_file)
    powermode_active = mode_data and mode_data.get("mode") == "powermode"

    if not powermode_active:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {**tool_input},
            }
        }))
        return

    if check_implementer_session(powermode_dir):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": ALLOW_IMPLEMENTER_MSG.strip(),
                "updatedInput": {**tool_input},
            }
        }))
        return

    state = load_json(state_file) or {}
    attempt_count = state.get("direct_edit_attempts", 0) + 1
    state["direct_edit_attempts"] = attempt_count
    save_json(state_file, state)

    if attempt_count >= ESCAPE_THRESHOLD:
        state["direct_edit_attempts"] = 0
        save_json(state_file, state)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": ALLOW_ESCAPE_MSG.format(attempts=attempt_count).strip(),
                "updatedInput": {**tool_input},
            }
        }))
    else:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "additionalContext": BLOCK_MSG.format(
                    attempt=attempt_count,
                    threshold=ESCAPE_THRESHOLD,
                    remaining=ESCAPE_THRESHOLD - attempt_count
                ).strip(),
                "updatedInput": {**tool_input},
            }
        }))


if __name__ == "__main__":
    main()

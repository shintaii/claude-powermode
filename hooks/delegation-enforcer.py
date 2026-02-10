#!/usr/bin/env python3
"""Delegation Enforcer Hook (PreToolUse: Edit, Write)

BLOCKS direct Edit/Write when Power Mode is active. The delegation
principle requires using pm-implementer for code changes.

Bypass mechanisms:
1. pm-implementer creates .powermode/implementer-session.json before editing
2. Escape hatch after 10 blocked attempts (for edge cases)

Fires on: PreToolUse (Edit, Write)

Exit codes:
- 0: Always exits cleanly
"""

import json
import sys
from pathlib import Path

ESCAPE_THRESHOLD = 10

BLOCK_MSG = """[EDIT DENIED - POLICY VIOLATION]

This edit has been BLOCKED by Power Mode policy. RETRYING WILL NOT HELP.

You MUST delegate code changes to pm-implementer:
  Task(subagent_type="powermode:pm-implementer", prompt="<describe what to implement>")

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


def check_implementer_session(powermode_dir: Path, session_id: str = "") -> bool:
    """Check if pm-implementer has an active session.

    Session files are managed by implementer-lifecycle.py via
    SubagentStart/SubagentStop hooks — no expiry needed.
    Supports multiple concurrent implementers (team mode) via
    implementer-sessions/ directory with per-agent files.
    """
    # Check new multi-agent directory first
    sessions_dir = powermode_dir / "implementer-sessions"
    if sessions_dir.is_dir():
        for session_file in sessions_dir.glob("*.json"):
            session = load_json(session_file)
            if not session:
                continue
            if session.get("agent") != "pm-implementer":
                continue
            if session_id and session.get("session_id") != session_id:
                continue
            return True

    # Backward compat: check legacy single file
    session_file = powermode_dir / "implementer-session.json"
    session = load_json(session_file)
    if not session:
        return False
    if session.get("agent") != "pm-implementer":
        return False
    if session_id and session.get("session_id") != session_id:
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
    session_id = input_data.get("session_id", "")

    # Allow writes to .powermode/ state files (not project code)
    target_path = tool_input.get("file_path", "")
    if target_path:
        try:
            powermode_path = Path(cwd) / ".powermode"
            if Path(target_path).resolve().is_relative_to(powermode_path.resolve()):
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                        "updatedInput": {**tool_input},
                    }
                }))
                return
        except (ValueError, OSError):
            pass

    powermode_dir = Path(cwd) / ".powermode"
    active_mode_file = powermode_dir / "active-mode.json"
    state_file = powermode_dir / "delegation-state.json"

    mode_data = load_json(active_mode_file)
    # Only consider powermode active if it's from the same session
    powermode_active = (
        mode_data
        and mode_data.get("mode") == "powermode"
        and mode_data.get("session_id") == session_id
    )

    if not powermode_active:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {**tool_input},
            }
        }))
        return

    if check_implementer_session(powermode_dir, session_id):
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
    session_state = state.get(session_id, {}) if session_id else state
    attempt_count = session_state.get("direct_edit_attempts", 0) + 1
    session_state["direct_edit_attempts"] = attempt_count
    if session_id:
        state[session_id] = session_state
    else:
        state = session_state
    save_json(state_file, state)

    if attempt_count >= ESCAPE_THRESHOLD:
        session_state["direct_edit_attempts"] = 0
        if session_id:
            state[session_id] = session_state
        else:
            state = session_state
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
    try:
        main()
    except Exception:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "updatedInput": {}}}))
    sys.exit(0)

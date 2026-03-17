#!/usr/bin/env python3
"""Task Containment Enforcer Hook

Injects scope constraints into EVERY delegate_task call to prevent:
1. Tasks growing too large (context rot)
2. Scope creep within subagents
3. Drift from original task

Fires on: PreToolUse (Task, delegate_task)
"""

import sys
import json
from pathlib import Path

# Compact containment reminder (agent definitions have the full rules)
CONTAINMENT_REMINDER = """
=== CONTAINMENT ===
Hard limits: 30 tool calls, 15 file reads, 25 turns. Stay focused on the exact request.
If task is too big: STOP early with "Task too large, recommend splitting".
At completion: summarize in 3-5 bullets (done / not done / issues).
"""


def is_powermode_active(cwd: str, session_id: str) -> bool:
    active_mode_file = Path(cwd) / ".powermode" / "active-mode.json"
    try:
        if active_mode_file.exists():
            data = json.loads(active_mode_file.read_text())
            return (
                data.get("mode") == "powermode"
                and data.get("session_id") == session_id
            )
    except (json.JSONDecodeError, IOError, OSError):
        pass
    return False


def extract_task_prompt(tool_input: dict) -> str:
    """Extract the prompt from Task/delegate_task input."""
    return tool_input.get("prompt", "")


def should_enforce(tool_name: str) -> bool:
    """Check if this tool call needs containment enforcement."""
    return tool_name.lower() in ["task", "delegate_task"]


def estimate_task_complexity(prompt: str) -> str:
    """Estimate if the task is likely to be large."""
    complexity_signals = {
        "high": [
            "implement",
            "build",
            "create a full",
            "refactor",
            "migrate",
            "integrate",
            "add support for",
            "entire",
        ],
        "medium": [
            "fix",
            "update",
            "add",
            "modify",
            "change",
            "test",
            "verify",
            "check",
        ],
        "low": ["find", "search", "read", "look", "what is", "explore", "check if"],
    }

    prompt_lower = prompt.lower()

    for signal in complexity_signals["high"]:
        if signal in prompt_lower:
            return "HIGH"

    for signal in complexity_signals["medium"]:
        if signal in prompt_lower:
            return "MEDIUM"

    return "LOW"


def get_containment_reminder(complexity: str) -> str:
    """Get appropriate reminder based on task complexity."""
    if complexity == "HIGH":
        return f"""
{CONTAINMENT_REMINDER}
⚠️ HIGH COMPLEXITY — consider splitting into subtasks. What's the MINIMUM viable outcome?
"""
    elif complexity == "MEDIUM":
        return CONTAINMENT_REMINDER
    else:
        return ""


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if not should_enforce(tool_name):
        print(json.dumps({"continue": True}))
        return

    cwd = input_data.get("cwd", ".")
    session_id = input_data.get("session_id", "")

    if not is_powermode_active(cwd, session_id):
        # Outside powermode, just allow without injecting containment rules
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {**tool_input},
            }
        }))
        return

    # Block new pm-implementer if verification is pending
    # Note: resume calls use SendMessage (separate tool), so any Agent/Task call
    # reaching here is always a NEW agent — no need to check for resume.
    subagent_type = tool_input.get("subagent_type", "")
    if "pm-implementer" in subagent_type:
        pending_file = Path(cwd) / ".powermode" / "pending-verification.json"
        if pending_file.exists():
            deny_reason = (
                "[BLOCKED] Verification pending. You MUST run pm-verifier on the "
                "previous implementer's changes before starting a new implementer. "
                "Use: Task(subagent_type=\"powermode:pm-verifier\", prompt=\"Verify...\")"
            )
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": deny_reason,
                    "additionalContext": deny_reason,
                    "updatedInput": {**tool_input},
                }
            }))
            return

    prompt = extract_task_prompt(tool_input)
    if not prompt:
        print(json.dumps({"continue": True}))
        return

    # Estimate complexity
    complexity = estimate_task_complexity(prompt)

    # Get appropriate containment reminder
    reminder = get_containment_reminder(complexity)

    # Inject containment rules into the prompt
    enhanced_prompt = f"{prompt}\n\n{reminder}"

    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": {**tool_input, "prompt": enhanced_prompt},
        }
    }

    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "updatedInput": {}}}))
    sys.exit(0)

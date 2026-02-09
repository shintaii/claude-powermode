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
import re

# Token budget guidance (conservative to prevent rot)
TOKEN_BUDGET_WARNING = """
=== TASK CONTAINMENT RULES (MANDATORY) ===

You are a CONTAINED subagent. Your context window is LIMITED.

**HARD LIMITS:**
- Maximum tool calls: 30 (prefer <20)
- Maximum file reads: 15 files
- Maximum turns: 25
- If you hit these limits: STOP, summarize progress, return results

**ATOMIC TASK PRINCIPLE:**
- Complete ONE specific thing, not multiple
- If task feels too big: Return early with "Task too large, recommend splitting"
- Do NOT explore tangentially - stay focused on the exact request

**MANDATORY BEHAVIORS:**
1. Start with a clear 1-sentence goal statement
2. Track your progress: "Completed X of Y steps"
3. If >50% through and struggling: STOP and report blockers
4. At completion: Summarize what you did in 3-5 bullet points

**FORBIDDEN:**
- Reading files "just to understand context" beyond what's needed
- Refactoring code that wasn't asked for
- Adding features beyond the explicit request
- Continuing after hitting a blocker - report it instead

**EVIDENCE REQUIRED:**
Your final response MUST include:
- What was accomplished (specific files/functions)
- What was NOT done (explicit)
- Any issues found
- Recommended follow-up (if any)
"""

CHECKPOINT_REMINDER = """
**CHECKPOINT**: After completing your task, verify:
- [ ] Did I stay within scope?
- [ ] Did I accomplish the specific goal?
- [ ] Can I summarize what I did in <5 bullets?

If any checkbox is NO, you went too far.
"""


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
{TOKEN_BUDGET_WARNING}

⚠️ HIGH COMPLEXITY DETECTED ⚠️

This task appears complex. Consider:
1. Can it be broken into smaller subtasks?
2. What's the MINIMUM viable outcome?
3. Set explicit stopping points

{CHECKPOINT_REMINDER}
"""
    elif complexity == "MEDIUM":
        return f"""
{TOKEN_BUDGET_WARNING}

{CHECKPOINT_REMINDER}
"""
    else:
        # Low complexity - lighter touch
        return """
=== TASK SCOPE ===
Stay focused. Complete the specific request and return results.
Don't explore beyond what's needed.
"""


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

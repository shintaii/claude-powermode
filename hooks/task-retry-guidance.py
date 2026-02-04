#!/usr/bin/env python3
"""
Task Retry Guidance Hook for Power Mode

Provides retry guidance when Task tool fails with common errors.
Also reminds about session_id for continuation.

Exit codes:
- 0: No issues or guidance provided
- 2: Error detected, guidance in stderr
"""

import json
import sys
import re

# Error patterns and their fixes
ERROR_PATTERNS = {
    r"subagent.*(not found|unknown|invalid)": """
TASK FAILED - Unknown agent type

Available agents in Power Mode:
- pm-explorer: Fast codebase search (Haiku)
- pm-researcher: External docs/OSS research (Sonnet)
- pm-oracle: Architecture/debugging advisor (Opus)
- pm-implementer: Code implementation (Opus)
- pm-verifier: Quality verification (Sonnet)
- pm-analyser: Pre-planning analysis (Opus)
- pm-powerplanner: Strategic planning (Opus)
- pm-planreviewer: Plan review (Sonnet)

Example: Task(subagent_type="pm-explorer", prompt="...")
""",
    r"(timeout|timed out)": """
TASK FAILED - Timeout

The subagent took too long. Try:
1. Break the task into smaller pieces
2. Be more specific in your prompt
3. Use run_in_background=true for long tasks:
   Task(subagent_type="...", run_in_background=true, prompt="...")
""",
    r"(empty|no response|no output)": """
TASK RETURNED EMPTY

The subagent didn't produce output. Try:
1. Make the prompt more specific
2. Ensure the task is actionable
3. Check if the agent type matches the task
""",
    r"session.*not found": """
TASK FAILED - Session not found

The session_id may have expired. Start a fresh task without session_id.
""",
}


def extract_session_id(output: str) -> str | None:
    """Extract session_id from task output."""
    # Look for session_id patterns
    patterns = [
        r'session_id["\s:=]+["\']?(ses_[a-zA-Z0-9]+)',
        r"Session ID[:\s]+`?(ses_[a-zA-Z0-9]+)",
        r'continue.*session_id="(ses_[a-zA-Z0-9]+)"',
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_response = input_data.get("tool_response", {})

    if tool_name != "Task":
        print(json.dumps({"continue": True}))
        return

    # Get output from response
    output = ""
    if isinstance(tool_response, dict):
        output = (
            tool_response.get("output", "")
            or tool_response.get("result", "")
            or str(tool_response)
        )
    elif isinstance(tool_response, str):
        output = tool_response

    output_lower = output.lower()

    # Check for errors
    for pattern, guidance in ERROR_PATTERNS.items():
        if re.search(pattern, output_lower):
            payload = {
                "continue": True,
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": guidance.strip(),
                },
            }
            print(json.dumps(payload))
            return

    # If successful, append session continuation hint
    session_id = extract_session_id(output)
    if session_id:
        hint = (
            "To continue this task or fix issues, use session_id: "
            f'Task(session_id="{session_id}", prompt="Fix: <specific issue>")'
        )
        payload = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": hint,
            },
        }
        print(json.dumps(payload))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()

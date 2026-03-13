#!/usr/bin/env python3
"""Failure Accountability Hook (PostToolUse: Bash)

When a Bash command output contains test failures, errors, or non-zero exit
codes, injects a reminder to investigate — not dismiss as "pre-existing" or
"unrelated to our changes".

Always active (not gated on powermode). This is a behavioral correction.

Fires on: PostToolUse (Bash)
"""

import json
import re
import sys

# Patterns that indicate real failures in command output
FAILURE_PATTERNS = [
    # Test frameworks
    r"\bFAIL(ED|URE)?\b",
    r"tests?\s+failed",
    r"failures?:\s*[1-9]",
    r"errors?:\s*[1-9]",
    r"Assertion(Error|Failed)",
    r"AssertError",
    # Python errors
    r"Traceback \(most recent call last\)",
    r"SyntaxError:",
    r"TypeError:",
    r"ImportError:",
    r"ModuleNotFoundError:",
    r"NameError:",
    r"AttributeError:",
    r"ValueError:",
    r"IndentationError:",
    # JS/TS errors
    r"SyntaxError:",
    r"ReferenceError:",
    r"Cannot find module",
    r"ERR!",
    # Build errors
    r"error\[E\d+\]",           # Rust
    r"error TS\d+:",            # TypeScript
    r"BUILD FAILED",
    r"compilation failed",
    r"compile error",
    # Generic
    r"exit code [1-9]",
    r"exited with code [1-9]",
    r"non-zero exit",
]

# Commands that are just checking status — don't warn on these
IGNORE_COMMANDS = [
    r"git\s+(status|log|diff|branch|show)",
    r"ls\b",
    r"cat\b",
    r"head\b",
    r"tail\b",
    r"wc\b",
    r"echo\b",
    r"pwd\b",
    r"which\b",
    r"pip\s+(show|list|freeze)",
    r"npm\s+(list|ls|outdated)",
]

COMPILED_FAILURES = [re.compile(p, re.IGNORECASE) for p in FAILURE_PATTERNS]
COMPILED_IGNORES = [re.compile(p, re.IGNORECASE) for p in IGNORE_COMMANDS]

REMINDER = (
    "[FAILURE ACCOUNTABILITY] The command output contains errors or test failures. "
    "Fix them. It does not matter whether they are related to your current task or not. "
    "A healthy codebase has zero failing tests, zero syntax errors, and zero type errors. "
    "Do NOT skip, dismiss, or label them as 'pre-existing' or 'unrelated'. Fix them now."
)


def get_output_text(tool_response):
    """Extract text from tool_response regardless of format."""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        # Could be {stdout, stderr, exitCode} or {output} or {content}
        parts = []
        for key in ("stdout", "stderr", "output", "content", "text"):
            val = tool_response.get(key)
            if isinstance(val, str):
                parts.append(val)
        return "\n".join(parts) if parts else json.dumps(tool_response)
    return str(tool_response)


def is_status_command(tool_input):
    """Check if command is just a status/info check — skip those."""
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
    elif isinstance(tool_input, str):
        command = tool_input
    if not command:
        return False
    return any(p.search(command) for p in COMPILED_IGNORES)


def has_failures(text):
    """Check if output text contains failure indicators."""
    return any(p.search(text) for p in COMPILED_FAILURES)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IOError):
        print(json.dumps({"continue": True}))
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})

    # Skip status/info commands
    if is_status_command(tool_input):
        print(json.dumps({"continue": True}))
        sys.exit(0)

    output_text = get_output_text(tool_response)

    if has_failures(output_text):
        print(json.dumps({
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": REMINDER,
            },
        }))
    else:
        print(json.dumps({"continue": True}))

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

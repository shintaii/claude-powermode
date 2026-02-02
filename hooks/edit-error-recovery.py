#!/usr/bin/env python3
"""
Edit Error Recovery Hook for Power Mode

Provides guidance when Edit tool fails with common errors:
- "oldString not found in content"
- "oldString found multiple times"

Exit codes:
- 0: Success, guidance provided in stdout (will be shown to Claude)
- 2: N/A for PostToolUseFailure
"""

import json
import sys

# Error patterns and their recovery guidance
ERROR_PATTERNS = {
    "oldString not found": """
EDIT FAILED - oldString not found

RECOVERY STEPS:
1. READ the file first to see its CURRENT state
2. VERIFY the exact content you're trying to match
3. Check for:
   - Whitespace differences (tabs vs spaces, trailing spaces)
   - Line ending differences
   - The content may have already been changed
4. Copy the EXACT text from the file, then retry

DO NOT guess or assume the file content. READ it first.
""",
    "oldString found multiple times": """
EDIT FAILED - oldString found multiple times

RECOVERY STEPS:
1. READ the file to see ALL occurrences
2. Include MORE CONTEXT in oldString to make it unique:
   - Add the line before
   - Add the line after
   - Include function/class name context
3. Or use replaceAll=true if you want to replace ALL occurrences

Example - instead of:
  oldString: "return None"
Use:
  oldString: "def my_function():\\n    return None"
""",
    "file does not exist": """
EDIT FAILED - File does not exist

RECOVERY STEPS:
1. Use WRITE tool instead to create a new file
2. Or check the file path for typos
3. Use GLOB to find similar files if unsure of location
""",
    "permission denied": """
EDIT FAILED - Permission denied

RECOVERY STEPS:
1. Check if the file is read-only
2. Check if you have write permissions to the directory
3. The file may be locked by another process
""",
}


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_response = input_data.get("tool_response", {})

    if tool_name != "Edit":
        sys.exit(0)

    # Get error message from response
    error_msg = ""
    if isinstance(tool_response, dict):
        error_msg = tool_response.get("error", "") or tool_response.get("message", "")
    elif isinstance(tool_response, str):
        error_msg = tool_response

    error_msg_lower = error_msg.lower()

    # Find matching error pattern
    for pattern, guidance in ERROR_PATTERNS.items():
        if pattern.lower() in error_msg_lower:
            payload = {
                "continue": True,
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUseFailure",
                    "additionalContext": guidance.strip(),
                },
            }
            print(json.dumps(payload))
            sys.exit(0)

    # Generic fallback for unknown errors
    if error_msg:
        fallback = f"""EDIT FAILED - {error_msg}

RECOVERY STEPS:
1. READ the file to verify its current state
2. Check the file path is correct
3. Verify the oldString matches exactly
4. Try again with the correct content"""
        payload = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": fallback,
            },
        }
        print(json.dumps(payload))
    else:
        print(json.dumps({"continue": True}))

    sys.exit(0)


if __name__ == "__main__":
    main()

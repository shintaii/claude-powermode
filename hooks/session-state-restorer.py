#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({"continue": True}))
        return

    cwd = input_data.get("cwd", "")
    if not cwd:
        print(json.dumps({"continue": True}))
        return

    recovery_file = Path(cwd) / ".powermode" / "recovery.json"
    additional_context = ""

    if recovery_file.exists():
        try:
            with open(recovery_file, "r") as f:
                recovery_data = json.load(f)

            session_id = recovery_data.get("session_id", "unknown")
            context_state = recovery_data.get("context_state", {})
            tokens_before = context_state.get("estimated_tokens", "unknown")
            token_percentage = context_state.get("percentage", "unknown")
            if isinstance(token_percentage, (int, float)):
                token_percentage = f"{token_percentage:.1f}"
            timestamp = recovery_data.get("saved_at", "unknown")

            additional_context = (
                f"[Session Recovery: Context was compacted. Previous state:\n"
                f"- Session: {session_id}\n"
                f"- Estimated tokens before: ~{tokens_before} ({token_percentage}%)\n"
                f"- Last saved: {timestamp}\n"
                f"Continue from where you left off.]"
            )

            restored_file = Path(str(recovery_file) + ".restored")
            try:
                recovery_file.rename(restored_file)
            except (OSError, IOError):
                pass

        except (json.JSONDecodeError, IOError, KeyError):
            additional_context = ""

    if additional_context:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": additional_context,
            },
        }
    else:
        output = {"continue": True}
    print(json.dumps(output))


if __name__ == "__main__":
    main()

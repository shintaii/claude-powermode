#!/usr/bin/env python3
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile

CHARS_PER_TOKEN = 3.5
CONTEXT_LIMIT = 200_000
WARNING_70_PERCENT = int(CONTEXT_LIMIT * 0.70)
WARNING_85_PERCENT = int(CONTEXT_LIMIT * 0.85)


def estimate_tokens(text: str) -> int:
    if not isinstance(text, str):
        text = json.dumps(text)
    return int(len(text) / CHARS_PER_TOKEN)


def load_state(state_file: Path) -> dict:
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "session_id": None,
        "tool_calls": 0,
        "estimated_tokens": 0,
        "percentage": 0.0,
        "modified_files": [],
        "warned_70": False,
        "warned_85": False,
        "last_updated": None,
    }


def save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=state_file.parent, text=True)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
        os.rename(temp_path, state_file)
    except (IOError, OSError):
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def extract_modified_files(tool_response: dict) -> list:
    modified = []
    if isinstance(tool_response, dict):
        if "modified_files" in tool_response:
            modified = tool_response.get("modified_files", [])
        elif "file_path" in tool_response:
            modified = [tool_response["file_path"]]
    return modified


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        print(json.dumps({"continue": True}))
        return

    session_id = hook_input.get("session_id")
    cwd = hook_input.get("cwd", ".")
    tool_name = hook_input.get("tool_name", "unknown")
    tool_input = hook_input.get("tool_input", {})
    tool_response = hook_input.get("tool_response", {})

    state_dir = Path(cwd) / ".powermode"
    state_file = state_dir / "context-state.json"

    state = load_state(state_file)

    if session_id and state.get("session_id") != session_id:
        state = {
            "session_id": session_id,
            "tool_calls": 0,
            "estimated_tokens": 0,
            "percentage": 0.0,
            "modified_files": [],
            "warned_70": False,
            "warned_85": False,
            "last_updated": None,
        }

    input_tokens = estimate_tokens(tool_input)
    response_tokens = estimate_tokens(tool_response)
    call_tokens = input_tokens + response_tokens

    state["tool_calls"] += 1
    state["estimated_tokens"] += call_tokens
    state["percentage"] = (state["estimated_tokens"] / CONTEXT_LIMIT) * 100
    state["last_updated"] = datetime.now(timezone.utc).isoformat()

    modified = extract_modified_files(tool_response)
    if modified:
        state["modified_files"] = list(set(state["modified_files"] + modified))

    warnings = []

    if state["estimated_tokens"] >= WARNING_85_PERCENT and not state["warned_85"]:
        state["warned_85"] = True
        warnings.append(
            f"⚠️  CRITICAL: Context usage at {state['percentage']:.1f}% "
            f"({state['estimated_tokens']:,} / {CONTEXT_LIMIT:,} tokens)"
        )

    elif state["estimated_tokens"] >= WARNING_70_PERCENT and not state["warned_70"]:
        state["warned_70"] = True
        warnings.append(
            f"⚠️  WARNING: Context usage at {state['percentage']:.1f}% "
            f"({state['estimated_tokens']:,} / {CONTEXT_LIMIT:,} tokens)"
        )

    save_state(state_file, state)

    output = {"continue": True}
    if warnings:
        output["hookSpecificOutput"] = {
            "hookEventName": "PostToolUse",
            "additionalContext": " | ".join(warnings),
        }

    print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

#!/usr/bin/env python3
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def main():
    try:
        event_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"continue": True}), file=sys.stdout)
        print(f"Failed to parse input: {e}", file=sys.stderr)
        return

    hook_event = event_data.get("hook_event_name")
    cwd = event_data.get("cwd", os.getcwd())
    session_id = event_data.get("session_id", "unknown")

    recovery_dir = Path(cwd) / ".powermode"
    recovery_file = recovery_dir / "recovery.json"

    try:
        recovery_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(json.dumps({"continue": True}), file=sys.stdout)
        print(f"Failed to create .powermode directory: {e}", file=sys.stderr)
        return

    context_state = {}
    context_file = recovery_dir / "context-state.json"
    if context_file.exists():
        try:
            with open(context_file, "r") as f:
                context_state = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not read context-state.json: {e}", file=sys.stderr)

    recovery_data = {
        "session_id": session_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "trigger": hook_event.lower() if hook_event else "unknown",
        "trigger_detail": event_data.get(
            "trigger", event_data.get("reason", "unknown")
        ),
        "context_state": context_state,
        "transcript_path": event_data.get("transcript_path", ""),
    }

    try:
        fd, temp_path = tempfile.mkstemp(dir=str(recovery_dir), text=True)
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(recovery_data, f, indent=2)
            os.rename(temp_path, str(recovery_file))
        except OSError:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise
    except OSError as e:
        print(json.dumps({"continue": True}), file=sys.stdout)
        print(f"Failed to write recovery state: {e}", file=sys.stderr)
        return

    print(json.dumps({"continue": True}), file=sys.stdout)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

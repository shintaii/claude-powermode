#!/usr/bin/env python3
"""PostCompact hook: reset context-state.json after compaction.

After compaction, the token estimates in context-state.json are stale —
they reflect pre-compaction usage. This hook resets them to avoid
false warnings from context-monitor.py.
"""
import json
import os
import sys
import tempfile
from pathlib import Path


def main():
    try:
        event_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({"continue": True}))
        return

    cwd = event_data.get("cwd", os.getcwd())
    state_file = Path(cwd) / ".powermode" / "context-state.json"

    if not state_file.exists():
        print(json.dumps({"continue": True}))
        return

    try:
        with open(state_file, "r") as f:
            state = json.load(f)
    except (json.JSONDecodeError, OSError):
        print(json.dumps({"continue": True}))
        return

    # Reset token estimate to ~15% of pre-compaction value.
    # Compaction aggressively summarizes, so the real token count
    # drops significantly. 15% is conservative — better to warn
    # slightly early than not at all.
    pre_compact_tokens = state.get("estimated_tokens", 0)
    state["estimated_tokens"] = int(pre_compact_tokens * 0.15)
    state["percentage"] = (state["estimated_tokens"] / 500_000) * 100
    state["warned_70"] = False
    state["warned_85"] = False
    state["compacted_at"] = pre_compact_tokens

    try:
        fd, temp_path = tempfile.mkstemp(dir=str(state_file.parent), text=True)
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(state, f, indent=2)
            os.rename(temp_path, str(state_file))
        except OSError:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
    except OSError:
        pass

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

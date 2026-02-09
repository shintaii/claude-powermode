#!/usr/bin/env python3
"""
Keyword Detector Hook for Power Mode

Detects special keywords in user prompts and injects mode-specific context:
- "powermode" / "power mode" - Activates full Power Mode methodology
- "ultrawork" / "ulw" - Maximum intensity mode
- "think" / "reason" / "analyze deeply" - Extended thinking mode

Exit codes:
- 0: Context added to stdout (will be injected)
"""

import json
import sys
import re
import os
from pathlib import Path

# Persistent modes - these stay active for the entire session once triggered
PERSISTENT_MODES = {
    r"# Power Mode|^/powermode\b|^/pm-plan\b|^/pm-team\b": "powermode",
}

# Mode context injections
MODE_CONTEXTS = {
    "powermode": """
[POWER MODE ACTIVATED]

You are now in Power Mode. Follow the methodology:

1. EXPLORE first - Use pm-explorer agents in parallel
2. PLAN with todos - Create atomic, trackable tasks
3. IMPLEMENT via pm-implementer - Don't code yourself
4. VERIFY via pm-verifier - Always before "done"

Available agents: pm-explorer, pm-researcher, pm-oracle, pm-implementer, pm-verifier, pm-analyser, pm-powerplanner, pm-planreviewer

Commands: /pm-plan [goal], /pm-team [goal]
""",
}

# Transient keywords - only injected when matched in the current prompt
TRANSIENT_KEYWORDS = {
    r"\b(think\s+hard|reason\s+deeply|analyze\s+deeply|think\s+carefully)\b": """
[DEEP THINKING MODE]

Take your time on this one:
- Consider multiple approaches before deciding
- Think through edge cases and failure modes
- Weigh tradeoffs explicitly
- If complex architecture: consult pm-oracle

Don't rush. Quality over speed for this task.
""",
    r"\b(create\s+a?\s*plan|make\s+a?\s*plan|plan\s+this|plan\s+for)\b": """
[PLANNING REQUESTED]

Use the Power Mode planning workflow:
1. Run /pm-plan [goal] or manually:
   - pm-analyser: Analyze for hidden requirements
   - pm-powerplanner: Create comprehensive plan
   - pm-planreviewer: Review until quality bar met

The plan should have atomic, verifiable tasks.
""",
}


def load_active_mode(cwd: str, session_id: str) -> str | None:
    """Load persisted active mode from state file, only if same session."""
    state_file = Path(cwd) / ".powermode" / "active-mode.json"
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                data = json.load(f)
            # Only honor the mode if it's from the same session
            if data.get("session_id") == session_id:
                return data.get("mode")
        except (json.JSONDecodeError, IOError):
            pass
    return None


def save_active_mode(cwd: str, mode: str, session_id: str) -> None:
    """Persist active mode to state file with session scope."""
    state_dir = Path(cwd) / ".powermode"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "active-mode.json"
    try:
        with open(state_file, "w") as f:
            json.dump({"mode": mode, "session_id": session_id}, f)
    except IOError:
        pass


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    prompt = input_data.get("prompt", "")
    cwd = input_data.get("cwd", "")
    session_id = input_data.get("session_id", "")

    if not prompt:
        print(json.dumps({"continue": True}))
        return

    prompt_lower = prompt.lower()
    contexts = []

    # Check for persistent mode activation via keyword
    newly_activated = None
    for pattern, mode_name in PERSISTENT_MODES.items():
        if re.search(pattern, prompt_lower, re.MULTILINE):
            newly_activated = mode_name
            break

    if newly_activated and cwd and session_id:
        save_active_mode(cwd, newly_activated, session_id)
        contexts.append(MODE_CONTEXTS[newly_activated].strip())
    elif not newly_activated and cwd and session_id:
        # No keyword match - check if a persistent mode is already active (same session only)
        active_mode = load_active_mode(cwd, session_id)
        if active_mode and active_mode in MODE_CONTEXTS:
            contexts.append(MODE_CONTEXTS[active_mode].strip())

    # Check transient keywords
    for pattern, context in TRANSIENT_KEYWORDS.items():
        if re.search(pattern, prompt_lower):
            contexts.append(context.strip())

    # Output with proper UserPromptSubmit schema
    if contexts:
        payload = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n\n".join(contexts),
            },
        }
        print(json.dumps(payload))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

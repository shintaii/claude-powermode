#!/usr/bin/env python3
"""Subagent Context Injector (SubagentStart: powermode:*)

Injects role-specific reminders when any powermode agent spawns.
Keeps agents focused on their designated responsibilities.

Fires on: SubagentStart (powermode:.*)

Exit codes:
- 0: Always exits cleanly
"""

import json
import sys

AGENT_CONTEXT = {
    "powermode:pm-explorer": "You are pm-explorer. Stay READ-ONLY. Use Glob, Grep, Read only. Do NOT modify any files.",
    "powermode:pm-researcher": "You are pm-researcher. Research external docs and patterns. Do NOT modify project files.",
    "powermode:pm-oracle": "You are pm-oracle. Provide architecture guidance and decisions. Do NOT implement code directly.",
    "powermode:pm-implementer": "You are pm-implementer. Execute focused code changes. Verify with diagnostics before reporting done.",
    "powermode:pm-verifier": "You are pm-verifier. Verify implementation quality. Do NOT fix issues yourself — only report them with evidence.",
    "powermode:pm-analyser": "You are pm-analyser. Analyze the codebase to inform planning. Do NOT implement changes.",
    "powermode:pm-powerplanner": "You are pm-powerplanner. Create implementation plans. Do NOT implement code.",
    "powermode:pm-planreviewer": "You are pm-planreviewer. Review plans for completeness and risks. Do NOT implement changes.",
}


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IOError):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": "",
            }
        }))
        sys.exit(0)

    agent_type = input_data.get("agent_type", "")

    context = AGENT_CONTEXT.get(agent_type, "")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": context,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()

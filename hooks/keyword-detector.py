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

# Keyword patterns and their injected context
KEYWORDS = {
    # Power Mode activation
    r"\b(powermode|power\s*mode)\b": """
[POWER MODE ACTIVATED]

You are now in Power Mode. Follow the methodology:

1. EXPLORE first - Use pm-explorer agents in parallel
2. PLAN with todos - Create atomic, trackable tasks
3. IMPLEMENT via pm-implementer - Don't code yourself
4. VERIFY via pm-verifier - Always before "done"

Available agents: pm-explorer, pm-librarian, pm-oracle, pm-implementer, pm-verifier, pm-metis, pm-prometheus, pm-momus

Commands: /pm-plan [goal], /pm-ralph-loop [goal]
""",
    # Ultrawork mode
    r"\b(ultrawork|ulw)\b": """
[ULTRAWORK MODE ACTIVATED]

Maximum intensity mode engaged:
- Fire MULTIPLE parallel agents for exploration
- Use background tasks aggressively
- Don't stop until the task is FULLY complete
- Verify everything with evidence

Work continuously. No half measures. Ship it.
""",
    # Think/analyze mode
    r"\b(think\s+hard|reason\s+deeply|analyze\s+deeply|think\s+carefully)\b": """
[DEEP THINKING MODE]

Take your time on this one:
- Consider multiple approaches before deciding
- Think through edge cases and failure modes
- Weigh tradeoffs explicitly
- If complex architecture: consult pm-oracle

Don't rush. Quality over speed for this task.
""",
    # Plan request
    r"\b(create\s+a?\s*plan|make\s+a?\s*plan|plan\s+this|plan\s+for)\b": """
[PLANNING REQUESTED]

Use the Power Mode planning workflow:
1. Run /pm-plan [goal] or manually:
   - pm-metis: Analyze for hidden requirements
   - pm-prometheus: Create comprehensive plan
   - pm-momus: Review until quality bar met

The plan should have atomic, verifiable tasks.
""",
}


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    prompt = input_data.get("prompt", "")
    if not prompt:
        print(json.dumps({"continue": True}))
        return

    prompt_lower = prompt.lower()

    # Check for keywords and collect all matching contexts
    contexts = []
    for pattern, context in KEYWORDS.items():
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
    main()

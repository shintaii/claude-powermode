#!/usr/bin/env python3
"""Plan Checkpoint Validator Hook

Periodically validates that implementation matches the original plan.
Detects drift early before it compounds.

Fires on: PostToolUse (TodoWrite) - after every todo update
- Checks completed todos against plan
- Warns if tasks seem to drift from plan
- Suggests checkpoint review

Also: Fires on Stop (prompt-based) - validates before session ends
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime


def is_powermode_active(cwd: str, session_id: str) -> bool:
    active_mode_file = Path(cwd) / ".powermode" / "active-mode.json"
    try:
        if active_mode_file.exists():
            data = json.loads(active_mode_file.read_text())
            return (
                data.get("mode") == "powermode"
                and data.get("session_id") == session_id
            )
    except (json.JSONDecodeError, IOError, OSError):
        pass
    return False


def find_active_plan(cwd: str) -> tuple[str | None, str | None]:
    """Find the active plan file in .powermode/ or .planning/ directories."""

    # Check for .powermode/boulder.json (powermode pattern)
    powermode_boulder = Path(cwd) / ".powermode" / "boulder.json"
    if powermode_boulder.exists():
        try:
            boulder = json.loads(powermode_boulder.read_text())
            plan_path = boulder.get("active_plan")
            if plan_path and Path(plan_path).exists():
                return plan_path, Path(plan_path).read_text()
        except:
            pass

    # Check for .planning/ROADMAP.md (common pattern)
    planning_roadmap = Path(cwd) / ".planning" / "ROADMAP.md"
    if planning_roadmap.exists():
        return str(planning_roadmap), planning_roadmap.read_text()

    # Check for .planning/STATE.md
    planning_state = Path(cwd) / ".planning" / "STATE.md"
    if planning_state.exists():
        return str(planning_state), planning_state.read_text()

    # Check for plan files in .claude/plans/
    claude_plans = Path.home() / ".claude" / "plans"
    if claude_plans.exists():
        plans = sorted(
            claude_plans.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if plans:
            return str(plans[0]), plans[0].read_text()

    return None, None


def extract_plan_tasks(plan_content: str) -> list[str]:
    """Extract task items from a plan document."""
    tasks = []

    # Match various task patterns
    # - [ ] Task description
    # - [x] Completed task
    # 1. Task item
    # - Task item
    patterns = [
        r"- \[[ x]\] (.+)",  # Checkbox format
        r"^\d+\.\s+(.+)",  # Numbered list
        r"^- (.+)",  # Bullet list
        r"###\s+Task[:\s]*(.+)",  # Task headers
    ]

    import re

    for line in plan_content.split("\n"):
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                task = match.group(1).strip()
                if len(task) > 10:  # Skip very short items
                    tasks.append(task)
                break

    return tasks


def count_completed_todos(todos: list) -> tuple[int, int, list[str]]:
    """Count completed and total todos, return completed task names."""
    completed = 0
    total = 0
    completed_names = []

    for todo in todos:
        if isinstance(todo, dict):
            total += 1
            if todo.get("status") == "completed":
                completed += 1
                completed_names.append(todo.get("content", ""))

    return completed, total, completed_names


def check_alignment(plan_tasks: list[str], completed_todos: list[str]) -> dict:
    """Check if completed todos align with plan tasks."""

    if not plan_tasks:
        return {"aligned": True, "message": "No plan found to validate against."}

    # Simple keyword matching to detect drift
    plan_keywords = set()
    for task in plan_tasks:
        words = task.lower().split()
        plan_keywords.update(w for w in words if len(w) > 3)

    completed_keywords = set()
    for todo in completed_todos:
        words = todo.lower().split()
        completed_keywords.update(w for w in words if len(w) > 3)

    # Calculate overlap
    if not completed_keywords:
        return {"aligned": True, "message": "No completed todos yet."}

    overlap = plan_keywords.intersection(completed_keywords)
    overlap_ratio = len(overlap) / len(completed_keywords) if completed_keywords else 0

    if overlap_ratio < 0.3:
        return {
            "aligned": False,
            "message": f"⚠️ DRIFT DETECTED: Only {overlap_ratio:.0%} overlap between completed work and plan.",
            "suggestion": "Review plan to ensure work aligns with original requirements.",
        }
    elif overlap_ratio < 0.5:
        return {
            "aligned": True,
            "message": f"📋 Moderate alignment ({overlap_ratio:.0%}). Consider a checkpoint review.",
            "suggestion": None,
        }
    else:
        return {
            "aligned": True,
            "message": f"✓ Good alignment ({overlap_ratio:.0%}) with plan.",
            "suggestion": None,
        }


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_response = input_data.get("tool_response", {})
    cwd = input_data.get("cwd", os.getcwd())
    session_id = input_data.get("session_id", "")

    if not is_powermode_active(cwd, session_id):
        print(json.dumps({"continue": True}))
        return

    # Only fire on TodoWrite
    if tool_name.lower() not in ["todowrite", "mcp_todowrite"]:
        print(json.dumps({"continue": True}))
        return

    # Parse todos from response
    todos = []
    if isinstance(tool_response, dict):
        todos = tool_response.get("newTodos", [])
    if not todos and isinstance(tool_response, str):
        try:
            todos = json.loads(tool_response)
        except:
            pass

    completed, total, completed_names = count_completed_todos(todos)

    # Only check at certain intervals (25%, 50%, 75%, 100%)
    if total == 0:
        print(json.dumps({"continue": True}))
        return

    progress = completed / total
    checkpoints = [0.25, 0.50, 0.75, 1.0]

    # Check if we just crossed a checkpoint
    prev_progress = (completed - 1) / total if completed > 0 else 0
    crossed_checkpoint = any(prev_progress < cp <= progress for cp in checkpoints)

    if not crossed_checkpoint:
        print(json.dumps({"continue": True}))
        return

    # Find and validate against plan
    plan_path, plan_content = find_active_plan(cwd)

    if not plan_content:
        checkpoint_msg = f"""
[CHECKPOINT: {progress:.0%} Complete ({completed}/{total} tasks)]

No active plan found to validate against.
Consider: Are you still aligned with the original goal?
"""
    else:
        plan_tasks = extract_plan_tasks(plan_content)
        alignment = check_alignment(plan_tasks, completed_names)

        checkpoint_msg = f"""
[CHECKPOINT: {progress:.0%} Complete ({completed}/{total} tasks)]

Plan: {plan_path}
{alignment["message"]}
"""
        if alignment.get("suggestion"):
            checkpoint_msg += f"\nRecommendation: {alignment['suggestion']}"

        if not alignment["aligned"]:
            checkpoint_msg += """

⚠️ MANDATORY: Before continuing, review:
1. Does completed work match original requirements?
2. Are there plan items being missed?
3. Should we course-correct before continuing?
"""

    # Output with proper PostToolUse schema
    payload = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": checkpoint_msg.strip(),
        },
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

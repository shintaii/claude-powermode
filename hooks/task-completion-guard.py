#!/usr/bin/env python3
"""TaskCompleted hook: block task completion if quality checks fail.

Fires when a teammate marks a task complete. Blocks completion (exit 2)
if there are uncommitted changes or TODO/stub patterns in changed files.
Only applies to powermode teammates.
"""
import json
import subprocess
import sys


def main():
    try:
        event_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({"continue": True}))
        return

    agent_type = event_data.get("agent_type", "")
    if not agent_type.startswith("powermode:"):
        print(json.dumps({"continue": True}))
        return

    cwd = event_data.get("cwd", ".")
    task_subject = event_data.get("task_subject", "unknown")
    errors = []

    # Check 1: uncommitted changes
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=cwd, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            changed_count = len(result.stdout.strip().splitlines())
            errors.append(
                f"You have {changed_count} uncommitted change(s). "
                "Commit your work before marking the task complete."
            )
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Check 2: TODO/stub patterns in staged + unstaged changed files
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=cwd, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            changed_files = result.stdout.strip().splitlines()
            stub_patterns = ["TODO", "FIXME", "NotImplementedError", "# stub", "// stub", "pass  #"]
            for filepath in changed_files[:20]:  # cap to avoid slowness
                try:
                    result = subprocess.run(
                        ["grep", "-n", "-E", "|".join(stub_patterns), filepath],
                        capture_output=True, text=True, cwd=cwd, timeout=3
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        matches = result.stdout.strip().splitlines()[:3]
                        errors.append(
                            f"Found stub/TODO patterns in {filepath}:\n"
                            + "\n".join(f"  {m}" for m in matches)
                        )
                except (subprocess.TimeoutExpired, OSError):
                    pass
    except (subprocess.TimeoutExpired, OSError):
        pass

    if errors:
        feedback = (
            f"Cannot mark '{task_subject}' as complete. Fix these issues first:\n\n"
            + "\n\n".join(errors)
        )
        print(feedback, file=sys.stderr)
        sys.exit(2)

    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

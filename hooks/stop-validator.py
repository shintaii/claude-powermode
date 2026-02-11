#!/usr/bin/env python3
import json
import sys
import os
import re
from pathlib import Path

MAX_BLOCK_ATTEMPTS = 3


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


def get_attempt_count(state_dir: Path, session_id: str) -> int:
    attempt_file = state_dir / "stop-attempts.json"
    if attempt_file.exists():
        try:
            with open(attempt_file) as f:
                data = json.load(f)
                return data.get(session_id, 0)
        except (json.JSONDecodeError, IOError):
            pass
    return 0


def increment_attempt(state_dir: Path, session_id: str) -> int:
    attempt_file = state_dir / "stop-attempts.json"
    state_dir.mkdir(parents=True, exist_ok=True)

    data = {}
    if attempt_file.exists():
        try:
            with open(attempt_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    data[session_id] = data.get(session_id, 0) + 1

    with open(attempt_file, "w") as f:
        json.dump(data, f)

    return data[session_id]


def normalize_path(path_value: str, cwd: str) -> str | None:
    if not path_value:
        return None
    cleaned = path_value.strip().strip('"').strip("'")
    if cleaned.startswith("@"):
        cleaned = cleaned[1:]
    if not cleaned:
        return None
    if os.path.isabs(cleaned):
        return os.path.normcase(os.path.abspath(cleaned))
    return os.path.normcase(os.path.abspath(os.path.join(cwd, cleaned)))


def iter_message_text(message: object):
    if isinstance(message, str):
        yield message
        return
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if isinstance(content, str):
        yield content
        return
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    yield text


def iter_tool_uses(message: object):
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                yield item


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({"decision": "approve"}))
        return

    cwd = input_data.get("cwd", os.getcwd())
    session_id = input_data.get("session_id", "unknown")
    transcript_path = input_data.get("transcript_path", "")
    state_dir = Path(cwd) / ".powermode"

    if not is_powermode_active(cwd, session_id):
        print(json.dumps({"decision": "approve"}))
        return

    pending_todos = []
    in_progress_todos = []
    referenced_prds = set()
    updated_prds = set()
    modified_prd_folders = set()
    modified_prd_readmes = set()

    if transcript_path and Path(transcript_path).exists():
        try:
            with open(transcript_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        message = entry.get("message")

                        for tool_use in iter_tool_uses(message):
                            tool_name = tool_use.get("name")
                            tool_input = tool_use.get("input", {})
                            file_path = tool_input.get("file_path") or tool_input.get(
                                "filePath"
                            )
                            normalized = (
                                normalize_path(file_path, cwd) if file_path else None
                            )
                            # Only track PRD modifications, not reads
                            # Reading a PRD shouldn't require updating it
                            if (
                                normalized
                                and ("/prd/" in normalized.lower() or "/prds/" in normalized.lower())
                                and normalized.endswith(".md")
                                and tool_name in {"Write", "Edit", "ApplyPatch", "apply_patch"}
                            ):
                                referenced_prds.add(normalized)
                                updated_prds.add(normalized)

                                # Track PRD folder README updates
                                norm_lower = normalized.lower()
                                if ".powermode/prds/" in norm_lower or ".powermode\\prds\\" in norm_lower:
                                    folder = os.path.dirname(normalized)
                                    basename = os.path.basename(normalized).lower()
                                    if basename == "readme.md":
                                        modified_prd_readmes.add(folder)
                                    else:
                                        modified_prd_folders.add(folder)

                        tool_result = entry.get("toolUseResult", {})
                        if "newTodos" in tool_result:
                            todos = tool_result.get("newTodos", [])
                            pending_todos = []
                            in_progress_todos = []
                            for todo in todos if isinstance(todos, list) else []:
                                if isinstance(todo, dict):
                                    status = todo.get("status", "")
                                    content = todo.get("content", "")[:50]
                                    if status == "pending":
                                        pending_todos.append(content)
                                    elif status == "in_progress":
                                        in_progress_todos.append(content)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    incomplete = pending_todos + in_progress_todos
    missing_prd_updates = sorted(referenced_prds - updated_prds)
    folders_missing_readme = sorted(modified_prd_folders - modified_prd_readmes)

    if incomplete or missing_prd_updates or folders_missing_readme:
        attempt = increment_attempt(state_dir, session_id)

        if attempt >= MAX_BLOCK_ATTEMPTS:
            parts = []
            if incomplete:
                parts.append(f"{len(incomplete)} todos left incomplete")
            if missing_prd_updates:
                parts.append(f"{len(missing_prd_updates)} PRD file(s) not updated")
            if folders_missing_readme:
                parts.append(f"{len(folders_missing_readme)} PRD README(s) not updated")
            warning = (
                "[STOP HOOK] Approved after "
                + str(attempt)
                + " attempts. "
                + "; ".join(parts)
                + "."
            )
            print(json.dumps({"decision": "approve", "reason": warning}))
        else:
            issue_parts = []
            action_parts = []
            if incomplete:
                todo_list = ", ".join(incomplete[:3])
                if len(incomplete) > 3:
                    todo_list += f" (+{len(incomplete) - 3} more)"
                issue_parts.append(f"{len(incomplete)} incomplete todos ({todo_list})")
                action_parts.append(
                    "CONTINUE THE WORKFLOW - complete the remaining steps, then mark todos done"
                )
            if missing_prd_updates:
                prd_list = ", ".join([Path(p).name for p in missing_prd_updates[:3]])
                if len(missing_prd_updates) > 3:
                    prd_list += f" (+{len(missing_prd_updates) - 3} more)"
                issue_parts.append(f"PRD not updated ({prd_list})")
                action_parts.append("Update the referenced PRD file(s)")
            if folders_missing_readme:
                folder_list = ", ".join(
                    [os.path.basename(f) for f in folders_missing_readme[:3]]
                )
                if len(folders_missing_readme) > 3:
                    folder_list += f" (+{len(folders_missing_readme) - 3} more)"
                issue_parts.append(
                    f"PRD README not updated ({folder_list})"
                )
                action_parts.append(
                    "Update the README.md status column in the PRD folder(s)"
                )

            reason = (
                "BLOCKED: "
                + " | ".join(issue_parts)
                + ". ACTION REQUIRED: "
                + "; ".join(action_parts)
                + f". [Attempt {attempt}/{MAX_BLOCK_ATTEMPTS} - will auto-approve after {MAX_BLOCK_ATTEMPTS}]"
            )
            print(json.dumps({"decision": "block", "reason": reason}))
    else:
        print(json.dumps({"decision": "approve"}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"decision": "approve"}))
    sys.exit(0)

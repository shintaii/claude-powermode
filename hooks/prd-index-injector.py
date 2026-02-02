#!/usr/bin/env python3
"""
PRD Index Injector Hook for Power Mode

When a PRD file is referenced in a prompt (e.g. @resources/prd/.../02-...md),
this hook injects the folder README.md (if present) into context.

Skips injection when:
- README.md does not exist (single PRD case)
- README.md already referenced
- README.md already injected for this session
"""

import json
import os
import re
import sys
from pathlib import Path

PRD_DIR_NAMES = {"prd", "prds"}


def normalize_path(path_value: str, cwd: str) -> Path | None:
    if not path_value:
        return None
    cleaned = path_value.strip().strip('"').strip("'")
    if cleaned.startswith("@"):
        cleaned = cleaned[1:]
    if not cleaned:
        return None
    path = Path(cleaned)
    if not path.is_absolute():
        path = Path(cwd) / path
    return path.resolve()


def is_prd_path(path: Path) -> bool:
    return any(part.lower() in PRD_DIR_NAMES for part in path.parts)


def load_state(state_file: Path, session_id: str) -> set[str]:
    if not session_id or not state_file.exists():
        return set()
    try:
        data = json.loads(state_file.read_text())
        if data.get("session_id") != session_id:
            return set()
        folders = data.get("folders", [])
        if isinstance(folders, list):
            return set(str(f) for f in folders)
    except (json.JSONDecodeError, OSError):
        return set()
    return set()


def save_state(state_file: Path, session_id: str, folders: set[str]) -> None:
    if not session_id:
        return
    state_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"session_id": session_id, "folders": sorted(folders)}
    try:
        state_file.write_text(json.dumps(payload))
    except OSError:
        pass


def extract_md_paths(prompt: str) -> list[str]:
    if not prompt:
        return []
    return re.findall(r"@?[^\s]+\.md", prompt)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({"continue": True}))
        return

    prompt = input_data.get("prompt", "")
    cwd = input_data.get("cwd", os.getcwd())
    session_id = input_data.get("session_id", "")

    candidates = extract_md_paths(prompt)
    if not candidates:
        print(json.dumps({"continue": True}))
        return

    state_file = Path(cwd) / ".powermode" / "prd-index-state.json"
    injected_folders = load_state(state_file, session_id)
    injections = []

    for raw_path in candidates:
        path = normalize_path(raw_path, cwd)
        if not path:
            continue
        if not is_prd_path(path):
            continue

        if path.name.lower() == "readme.md":
            injected_folders.add(str(path.parent))
            continue

        readme_path = path.parent / "README.md"
        if not readme_path.exists():
            continue

        folder_key = str(path.parent)
        if folder_key in injected_folders:
            continue

        try:
            content = readme_path.read_text()
        except OSError:
            continue

        if not content.strip():
            continue

        injected_folders.add(folder_key)
        injections.append(f"[PRD INDEX: {readme_path}]\n{content.strip()}")

    if injections:
        save_state(state_file, session_id, injected_folders)
        payload = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n\n".join(injections),
            },
        }
        print(json.dumps(payload))
    else:
        if injected_folders:
            save_state(state_file, session_id, injected_folders)
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()

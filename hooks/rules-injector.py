#!/usr/bin/env python3
"""
Rules Injector Hook for Power Mode

Injects .rules files based on file patterns when reading files.
Similar to Cursor's rules feature.

Rules files can be:
- .claude/rules/*.md (project-level)
- ~/.claude/rules/*.md (user-level)

Rules files use frontmatter to specify which files they apply to:
---
globs: ["*.py", "src/**/*.ts"]
---
Rule content here...

Exit codes:
- 0: Rules injected via stdout (added to context)
"""

import json
import sys
import os
import re
from pathlib import Path
from fnmatch import fnmatch

PRD_DIR_NAMES = {"prd", "prds"}


def resolve_path(file_path: str, cwd: str) -> Path:
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(cwd) / path
    return path


def load_prd_state(state_file: Path, session_id: str) -> set[str]:
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


def save_prd_state(state_file: Path, session_id: str, folders: set[str]) -> None:
    if not session_id:
        return
    state_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"session_id": session_id, "folders": sorted(folders)}
    try:
        state_file.write_text(json.dumps(payload))
    except OSError:
        pass


def is_prd_path(path: Path) -> bool:
    return any(part.lower() in PRD_DIR_NAMES for part in path.parts)


def get_prd_index_injection(
    cwd: str, session_id: str | None, file_path: str
) -> str | None:
    if not file_path:
        return None
    path = resolve_path(file_path, cwd)
    if path.name.lower() == "readme.md":
        return None
    if not is_prd_path(path):
        return None

    readme_path = path.parent / "README.md"
    if not readme_path.exists():
        return None

    state_file = Path(cwd) / ".powermode" / "prd-index-state.json"
    injected_folders = load_prd_state(state_file, session_id or "")
    folder_key = str(path.parent.resolve())
    if folder_key in injected_folders:
        return None

    try:
        content = readme_path.read_text()
    except OSError:
        return None

    if not content.strip():
        return None

    injected_folders.add(folder_key)
    save_prd_state(state_file, session_id or "", injected_folders)
    return f"[PRD INDEX: {readme_path}]\n{content.strip()}"


# Cache for loaded rules (to avoid re-reading on every file read)
_rules_cache = {}


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from content."""
    if not content.startswith("---"):
        return {}, content

    # Find end of frontmatter
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return {}, content

    frontmatter_text = content[3 : end_match.start() + 3]
    body = content[end_match.end() + 3 :]

    # Simple YAML parsing for globs
    frontmatter = {}

    # Parse globs: ["*.py", "*.ts"]
    globs_match = re.search(r"globs:\s*\[(.*?)\]", frontmatter_text, re.DOTALL)
    if globs_match:
        globs_text = globs_match.group(1)
        # Extract quoted strings
        globs = re.findall(r'["\']([^"\']+)["\']', globs_text)
        frontmatter["globs"] = globs

    # Parse patterns: ["pattern1", "pattern2"]
    patterns_match = re.search(r"patterns:\s*\[(.*?)\]", frontmatter_text, re.DOTALL)
    if patterns_match:
        patterns_text = patterns_match.group(1)
        patterns = re.findall(r'["\']([^"\']+)["\']', patterns_text)
        frontmatter["patterns"] = patterns

    # Parse description
    desc_match = re.search(r'description:\s*["\']?([^"\'\n]+)', frontmatter_text)
    if desc_match:
        frontmatter["description"] = desc_match.group(1).strip()

    return frontmatter, body


def load_rules_from_dir(rules_dir: Path) -> list[dict]:
    """Load all rules from a directory."""
    if not rules_dir.exists():
        return []

    rules = []
    for rules_file in rules_dir.glob("*.md"):
        try:
            content = rules_file.read_text()
            frontmatter, body = parse_frontmatter(content)

            if body.strip():
                rules.append(
                    {
                        "file": str(rules_file),
                        "globs": frontmatter.get("globs", ["*"]),
                        "patterns": frontmatter.get("patterns", []),
                        "description": frontmatter.get("description", rules_file.stem),
                        "content": body.strip(),
                    }
                )
        except Exception:
            continue

    return rules


def get_all_rules(project_dir: str) -> list[dict]:
    """Get all rules from project and user directories."""
    cache_key = project_dir
    if cache_key in _rules_cache:
        return _rules_cache[cache_key]

    rules = []

    # Project-level rules
    project_rules_dir = Path(project_dir) / ".claude" / "rules"
    rules.extend(load_rules_from_dir(project_rules_dir))

    # User-level rules
    home = os.environ.get("HOME", "")
    if home:
        user_rules_dir = Path(home) / ".claude" / "rules"
        rules.extend(load_rules_from_dir(user_rules_dir))

    _rules_cache[cache_key] = rules
    return rules


def matches_file(rule: dict, file_path: str) -> bool:
    """Check if a rule applies to a file path."""
    file_name = os.path.basename(file_path)

    # Check globs
    for glob_pattern in rule.get("globs", []):
        if fnmatch(file_name, glob_pattern):
            return True
        if fnmatch(file_path, glob_pattern):
            return True

    # Check regex patterns
    for pattern in rule.get("patterns", []):
        try:
            if re.search(pattern, file_path):
                return True
        except re.error:
            continue

    return False


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    cwd = input_data.get("cwd", os.getcwd())
    session_id = input_data.get("session_id")

    if tool_name != "Read":
        print(json.dumps({"continue": True}))
        return

    file_path = tool_input.get("file_path", "")
    if not file_path:
        print(json.dumps({"continue": True}))
        return

    # Get all applicable rules
    rules = get_all_rules(cwd)
    applicable_rules = [r for r in rules if matches_file(r, file_path)]

    # Output rules to inject
    output = []
    for rule in applicable_rules:
        output.append(f"[RULE: {rule['description']}]")
        output.append(rule["content"])
        output.append("")

    prd_injection = get_prd_index_injection(cwd, session_id, file_path)
    if prd_injection:
        output.append(prd_injection)

    if output:
        injected = "\n".join(output)
        payload = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": injected,
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

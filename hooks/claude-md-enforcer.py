#!/usr/bin/env python3
"""CLAUDE.md Rules Enforcer Hook

Injects CLAUDE.md rules as system reminders on every prompt.
Reads from hierarchy: ~/.claude/CLAUDE.md, ancestors, project-level.
Emphasizes simplicity, clarification, and testing principles.
"""

import os
import sys
import json
import hashlib
from pathlib import Path


def find_claude_md_files(cwd: str) -> list[tuple[str, str]]:
    """Find all CLAUDE.md files in hierarchy order (user-level first, closest last)."""
    files = []
    seen_paths = set()

    # 1. User-level: ~/.claude/CLAUDE.md
    user_level = Path.home() / ".claude" / "CLAUDE.md"
    if user_level.exists():
        files.append(("~/.claude/CLAUDE.md", user_level.read_text()))
        seen_paths.add(user_level.resolve())

    # 2. Walk up from CWD to root, collect all CLAUDE.md files
    current = Path(cwd).resolve()
    ancestors = []

    while current != current.parent:
        # Check ./CLAUDE.md
        claude_md = current / "CLAUDE.md"
        if claude_md.exists() and claude_md.resolve() not in seen_paths:
            rel_path = (
                str(claude_md.relative_to(Path(cwd).resolve()))
                if claude_md.is_relative_to(Path(cwd).resolve())
                else str(claude_md)
            )
            ancestors.append((rel_path, claude_md.read_text()))
            seen_paths.add(claude_md.resolve())

        # Check ./.claude/CLAUDE.md
        claude_dir_md = current / ".claude" / "CLAUDE.md"
        if claude_dir_md.exists() and claude_dir_md.resolve() not in seen_paths:
            rel_path = (
                str(claude_dir_md.relative_to(Path(cwd).resolve()))
                if claude_dir_md.is_relative_to(Path(cwd).resolve())
                else str(claude_dir_md)
            )
            ancestors.append((rel_path, claude_dir_md.read_text()))
            seen_paths.add(claude_dir_md.resolve())

        current = current.parent

    # Reverse so closest to CWD is last (highest priority in mental model)
    ancestors.reverse()
    files.extend(ancestors)

    return files


def extract_key_rules(content: str, max_length: int = 1500) -> str:
    """Extract key rules from CLAUDE.md content, truncate if needed."""
    # If short enough, return as-is
    if len(content) <= max_length:
        return content.strip()

    # Try to extract sections with key markers
    lines = content.split("\n")
    key_sections = []
    current_section = []
    in_key_section = False

    key_markers = [
        "communication",
        "style",
        "test",
        "mock",
        "simple",
        "clarif",
        "principle",
        "must",
        "never",
        "always",
        "important",
        "critical",
    ]

    for line in lines:
        line_lower = line.lower()

        # Check if this line starts a key section
        if line.startswith("#") and any(marker in line_lower for marker in key_markers):
            if current_section:
                key_sections.append("\n".join(current_section))
            current_section = [line]
            in_key_section = True
        elif in_key_section:
            if line.startswith("#") and not any(
                marker in line_lower for marker in key_markers
            ):
                key_sections.append("\n".join(current_section))
                current_section = []
                in_key_section = False
            else:
                current_section.append(line)

    if current_section:
        key_sections.append("\n".join(current_section))

    if key_sections:
        extracted = "\n\n".join(key_sections)
        if len(extracted) <= max_length:
            return extracted.strip()
        return extracted[:max_length].strip() + "..."

    # Fallback: just truncate
    return content[:max_length].strip() + "..."


def build_reminder(claude_files: list[tuple[str, str]]) -> str:
    """Build the system reminder from CLAUDE.md files."""
    parts = [
        "[SYSTEM REMINDER - CLAUDE.md RULES ENFORCEMENT]",
        "",
        "You MUST follow these rules from the user's CLAUDE.md files.",
        "Failure to follow = poor quality work that wastes user's time.",
        "",
    ]

    # Add content from each file
    for path, content in claude_files:
        extracted = extract_key_rules(content)
        parts.append(f"=== {path} ===")
        parts.append(extracted)
        parts.append("")

    # Add critical reminders for known problem areas
    parts.extend(
        [
            "=== CRITICAL ENFORCEMENT (Most Violated Rules) ===",
            "",
            '1. SIMPLICITY: "Can this be solved with a simple loop or conditional?"',
            "   - 20-line surgical fix > 200-line architectural refactor",
            "   - Start SIMPLEST, add complexity only if proven necessary",
            "",
            "2. CLARIFICATION: Confidence < 80% = MUST ASK",
            "   - Use mcp_question tool (multiple choice) - NOT prose questions",
            "   - Present options with descriptions, let user choose",
            "",
            "3. TESTING: Test CORE PURPOSE only",
            "   - Expand existing test files before creating new ones",
            "   - Only mock EXTERNAL APIs (Amazon exception: use Sandbox)",
            "   - 5 error scenarios? Test 1 representative one, not all 5",
            "",
            '4. NO FLATTERY: Never say "Great question!", "You\'re right", etc.',
            "   - Challenge if user is wrong. Be honest, not agreeable.",
            "",
            "These rules are NON-NEGOTIABLE. The user explicitly asked for enforcement.",
            "",
        ]
    )

    return "\n".join(parts)


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    cwd = input_data.get("cwd", os.getcwd())

    # Find all CLAUDE.md files
    claude_files = find_claude_md_files(cwd)

    if not claude_files:
        # No CLAUDE.md files found, nothing to enforce
        print(json.dumps({"continue": True}))
        return

    # Build the reminder
    reminder = build_reminder(claude_files)

    # Output with proper UserPromptSubmit schema
    result = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": reminder,
        },
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()

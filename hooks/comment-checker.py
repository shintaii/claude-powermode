#!/usr/bin/env python3
"""
Comment Checker Hook for Power Mode

Detects unnecessary AI-generated comments ("agent memo" patterns) after Write/Edit operations.
Based on OhMyOpenCode's comment-checker implementation.

Supports comment syntax for:
- Python, Ruby, Shell, YAML, Dockerfile (#)
- JavaScript, TypeScript, Java, C, C++, Go, Rust, Swift, Kotlin, Scala, PHP (// and /* */)
- HTML, XML, Vue, Svelte (<!-- -->)
- CSS, SCSS, Less (/* */)
- SQL, Lua (--)
- Python docstrings (triple quotes)
- JSX/TSX ({/* */})

Exit codes:
- 0: No problematic comments found (or not applicable)
- 2: Problematic comments detected - warning in stderr
"""

import json
import re
import sys
from pathlib import Path

# Agent memo patterns - common AI-generated comment patterns that are usually unnecessary
AGENT_MEMO_PATTERNS = [
    # Change tracking comments (almost never useful)
    r"(?i)^\s*[\#/*<!\-]*\s*changed?\s+(from|to)\b",
    r"(?i)^\s*[\#/*<!\-]*\s*modified?\s+(from|to)?\b",
    r"(?i)^\s*[\#/*<!\-]*\s*updated?\s+(from|to)?\b",
    r"(?i)^\s*[\#/*<!\-]*\s*added?\b.*(?:for|to|this)",
    r"(?i)^\s*[\#/*<!\-]*\s*removed?\b",
    r"(?i)^\s*[\#/*<!\-]*\s*deleted?\b",
    # Implementation comments (the code should speak for itself)
    r"(?i)^\s*[\#/*<!\-]*\s*implemented?\b",
    r"(?i)^\s*[\#/*<!\-]*\s*this\s+(implements?|adds?|removes?|handles?|creates?|returns?)\b",
    r"(?i)^\s*[\#/*<!\-]*\s*here\s+we\b",
    r"(?i)^\s*[\#/*<!\-]*\s*now\s+we\b",
    r"(?i)^\s*[\#/*<!\-]*\s*we\s+(need|must|should|have)\s+to\b",
    # Obvious/redundant comments
    r"(?i)^\s*[\#/*<!\-]*\s*note:\s*\w",
    r"(?i)^\s*[\#/*<!\-]*\s*important:\s*\w",
    r"(?i)^\s*[\#/*<!\-]*\s*todo:\s*(implement|add|fix|update|remove)",
    r"(?i)^\s*[\#/*<!\-]*\s*fixme:\s*\w",
    # Self-referential comments
    r"(?i)^\s*[\#/*<!\-]*\s*(the\s+)?following\s+(code|function|method|class)",
    r"(?i)^\s*[\#/*<!\-]*\s*this\s+(function|method|class|component|module)\s+(will|does|is|should)",
    r"(?i)^\s*[\#/*<!\-]*\s*(this|the)\s+(is|are)\s+(a|an|the)\s+",
    # Explaining obvious things
    r"(?i)^\s*[\#/*<!\-]*\s*import(s|ing)?\s+(the\s+)?",
    r"(?i)^\s*[\#/*<!\-]*\s*define(s|d)?\s+(a|an|the)\s+",
    r"(?i)^\s*[\#/*<!\-]*\s*create(s|d)?\s+(a|an|the)\s+",
    r"(?i)^\s*[\#/*<!\-]*\s*return(s|ing)?\s+(the\s+)?",
    r"(?i)^\s*[\#/*<!\-]*\s*set(s|ting)?\s+(the\s+)?",
    r"(?i)^\s*[\#/*<!\-]*\s*get(s|ting)?\s+(the\s+)?",
    r"(?i)^\s*[\#/*<!\-]*\s*call(s|ing)?\s+(the\s+)?",
    r"(?i)^\s*[\#/*<!\-]*\s*check(s|ing)?\s+(if|whether)\s+",
    r"(?i)^\s*[\#/*<!\-]*\s*loop(s|ing)?\s+(through|over)\s+",
]

# Patterns that should be ALLOWED (not flagged)
ALLOWED_PATTERNS = [
    # BDD/Testing keywords
    r"(?i)\b(given|when|then|arrange|act|assert)\b",
    # Linter/tool directives
    r"(?i)(eslint|tslint|prettier|stylelint|biome)[-:]?(disable|ignore|enable)",
    r"(?i)@ts-(ignore|expect-error|nocheck|check)",
    r"(?i)#\s*noqa",
    r"(?i)#\s*type:\s*ignore",
    r"(?i)#\s*pylint:",
    r"(?i)#\s*pragma:",
    r"(?i)#\s*nosec",
    r"(?i)noinspection",
    r"(?i)@suppress",
    r"(?i)NOLINT",
    r"(?i)coverity\[",
    # Region markers
    r"(?i)#\s*(region|endregion)",
    r"(?i)//\s*(region|endregion)",
    # Shebangs
    r"^#!",
    # License/copyright headers
    r"(?i)(copyright|license|spdx|all rights reserved)",
    # JSDoc/docstring/documentation tags
    r"(?i)@(param|returns?|throws?|example|deprecated|see|since|version|type|typedef|callback|template|author|description|summary)",
    r"(?i):(param|returns?|raises?|type|rtype|yields?):",  # Sphinx style
    # TODO with issue references (these are legitimate)
    r"(?i)todo[:\s]*#\d+",
    r"(?i)todo[:\s]*(https?://|[A-Z]+-\d+)",
    r"(?i)fixme[:\s]*(https?://|[A-Z]+-\d+)",
    # URLs (comments with links are usually meaningful)
    r"https?://",
    # Explanations of WHY (heuristic: contains "because", "since", "due to", etc.)
    r"(?i)\b(because|since|due\s+to|in\s+order\s+to|to\s+avoid|to\s+prevent|workaround|hack\s+for|bug\s+in)\b",
]

# Language-specific comment syntax
COMMENT_SYNTAX = {
    # Hash comments
    ".py": {"single": ["#"], "multi": [('"""', '"""'), ("'''", "'''")]},
    ".rb": {"single": ["#"], "multi": [("=begin", "=end")]},
    ".sh": {"single": ["#"], "multi": []},
    ".bash": {"single": ["#"], "multi": []},
    ".zsh": {"single": ["#"], "multi": []},
    ".yaml": {"single": ["#"], "multi": []},
    ".yml": {"single": ["#"], "multi": []},
    ".dockerfile": {"single": ["#"], "multi": []},
    ".toml": {"single": ["#"], "multi": []},
    ".ini": {"single": ["#", ";"], "multi": []},
    ".conf": {"single": ["#"], "multi": []},
    # C-style comments
    ".js": {"single": ["//"], "multi": [("/*", "*/")]},
    ".jsx": {"single": ["//"], "multi": [("/*", "*/"), ("{/*", "*/}")]},
    ".ts": {"single": ["//"], "multi": [("/*", "*/")]},
    ".tsx": {"single": ["//"], "multi": [("/*", "*/"), ("{/*", "*/}")]},
    ".java": {"single": ["//"], "multi": [("/*", "*/")]},
    ".c": {"single": ["//"], "multi": [("/*", "*/")]},
    ".cpp": {"single": ["//"], "multi": [("/*", "*/")]},
    ".h": {"single": ["//"], "multi": [("/*", "*/")]},
    ".hpp": {"single": ["//"], "multi": [("/*", "*/")]},
    ".go": {"single": ["//"], "multi": [("/*", "*/")]},
    ".rs": {"single": ["//"], "multi": [("/*", "*/")]},
    ".swift": {"single": ["//"], "multi": [("/*", "*/")]},
    ".kt": {"single": ["//"], "multi": [("/*", "*/")]},
    ".kts": {"single": ["//"], "multi": [("/*", "*/")]},
    ".scala": {"single": ["//"], "multi": [("/*", "*/")]},
    ".php": {"single": ["//", "#"], "multi": [("/*", "*/")]},
    ".cs": {"single": ["//"], "multi": [("/*", "*/")]},
    ".m": {"single": ["//"], "multi": [("/*", "*/")]},  # Objective-C
    ".mm": {"single": ["//"], "multi": [("/*", "*/")]},
    ".dart": {"single": ["//"], "multi": [("/*", "*/")]},
    ".groovy": {"single": ["//"], "multi": [("/*", "*/")]},
    ".gradle": {"single": ["//"], "multi": [("/*", "*/")]},
    # HTML-style comments
    ".html": {"single": [], "multi": [("<!--", "-->")]},
    ".htm": {"single": [], "multi": [("<!--", "-->")]},
    ".xml": {"single": [], "multi": [("<!--", "-->")]},
    ".svg": {"single": [], "multi": [("<!--", "-->")]},
    ".vue": {"single": ["//"], "multi": [("/*", "*/"), ("<!--", "-->")]},
    ".svelte": {"single": ["//"], "multi": [("/*", "*/"), ("<!--", "-->")]},
    ".astro": {"single": ["//"], "multi": [("/*", "*/"), ("<!--", "-->")]},
    # CSS-style comments
    ".css": {"single": [], "multi": [("/*", "*/")]},
    ".scss": {"single": ["//"], "multi": [("/*", "*/")]},
    ".sass": {"single": ["//"], "multi": [("/*", "*/")]},
    ".less": {"single": ["//"], "multi": [("/*", "*/")]},
    ".styl": {"single": ["//"], "multi": [("/*", "*/")]},
    # SQL-style comments
    ".sql": {"single": ["--"], "multi": [("/*", "*/")]},
    # Lua comments
    ".lua": {"single": ["--"], "multi": [("--[[", "]]")]},
    # Haskell/Elm comments
    ".hs": {"single": ["--"], "multi": [("{-", "-}")]},
    ".elm": {"single": ["--"], "multi": [("{-", "-}")]},
    # Lisp-style comments
    ".lisp": {"single": [";"], "multi": []},
    ".el": {"single": [";"], "multi": []},
    ".clj": {"single": [";"], "multi": []},
    ".cljs": {"single": [";"], "multi": []},
    # R comments
    ".r": {"single": ["#"], "multi": []},
    # Julia comments
    ".jl": {"single": ["#"], "multi": [("#=", "=#")]},
    # Markdown (in code blocks, treat as no comments to check)
    ".md": {"single": [], "multi": []},
    ".mdx": {"single": [], "multi": []},
}


def get_comment_syntax(file_ext: str) -> dict:
    """Get comment syntax for a file extension."""
    ext = file_ext.lower()
    # Handle Dockerfile specially
    if "dockerfile" in ext.lower():
        ext = ".dockerfile"
    return COMMENT_SYNTAX.get(ext, {"single": [], "multi": []})


def extract_comments(content: str, file_ext: str) -> list[tuple[int, str]]:
    """Extract comments from code content. Returns list of (line_number, comment_text)."""
    syntax = get_comment_syntax(file_ext)

    if not syntax["single"] and not syntax["multi"]:
        return []

    comments = []
    lines = content.split("\n")

    # Track multi-line comment state
    in_multiline = False
    multiline_start = 0
    multiline_content = []
    multiline_end_marker = ""

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check if we're inside a multi-line comment
        if in_multiline:
            multiline_content.append(stripped)
            if multiline_end_marker in line:
                in_multiline = False
                full_comment = " ".join(multiline_content)
                comments.append((multiline_start, full_comment))
                multiline_content = []
            continue

        # Check for multi-line comment start
        found_multi = False
        for start_marker, end_marker in syntax["multi"]:
            if start_marker in line:
                # Check if it's a single-line multi-line comment
                start_idx = line.find(start_marker)
                after_start = line[start_idx + len(start_marker) :]

                if end_marker in after_start:
                    # Single line: /* comment */
                    end_idx = after_start.find(end_marker)
                    comment = start_marker + after_start[: end_idx + len(end_marker)]
                    comments.append((i, comment.strip()))
                else:
                    # Start of multi-line
                    in_multiline = True
                    multiline_start = i
                    multiline_content = [line[start_idx:].strip()]
                    multiline_end_marker = end_marker
                found_multi = True
                break

        if found_multi:
            continue

        # Check for single-line comments
        for marker in syntax["single"]:
            if marker in line:
                idx = line.find(marker)
                # Simple heuristic: make sure it's not inside a string
                before = line[:idx]
                # Count unescaped quotes
                double_quotes = len(re.findall(r'(?<!\\)"', before))
                single_quotes = len(re.findall(r"(?<!\\)'", before))
                backticks = len(re.findall(r"(?<!\\)`", before))

                # If inside a string, skip
                if (
                    double_quotes % 2 != 0
                    or single_quotes % 2 != 0
                    or backticks % 2 != 0
                ):
                    continue

                comment = line[idx:].strip()
                comments.append((i, comment))
                break

    return comments


def is_allowed_comment(comment: str) -> bool:
    """Check if comment matches allowed patterns (should not be flagged)."""
    for pattern in ALLOWED_PATTERNS:
        if re.search(pattern, comment):
            return True
    return False


def is_agent_memo(comment: str) -> bool:
    """Check if comment matches agent memo patterns (should be flagged)."""
    # Skip very short comments (likely not agent memos)
    stripped = re.sub(r"^[\s#/*<!\-]+", "", comment).strip()
    if len(stripped) < 10:
        return False

    for pattern in AGENT_MEMO_PATTERNS:
        if re.search(pattern, comment):
            return True
    return False


def check_for_new_comments(
    old_content: str, new_content: str, file_path: str
) -> list[dict]:
    """For Edit operations, only flag NEW comments (not existing ones)."""
    file_ext = Path(file_path).suffix.lower()

    syntax = get_comment_syntax(file_ext)
    if not syntax["single"] and not syntax["multi"]:
        return []

    old_comments = set(c[1] for c in extract_comments(old_content, file_ext))
    new_comments = extract_comments(new_content, file_ext)

    problematic = []
    for line_num, comment in new_comments:
        # Skip if comment existed before
        if comment in old_comments:
            continue

        # Skip allowed patterns
        if is_allowed_comment(comment):
            continue

        # Check if it's an agent memo pattern
        if is_agent_memo(comment):
            problematic.append(
                {"line": line_num, "comment": comment, "type": "agent_memo"}
            )

    return problematic


def check_content_for_comments(content: str, file_path: str) -> list[dict]:
    """For Write operations, check all comments."""
    file_ext = Path(file_path).suffix.lower()

    syntax = get_comment_syntax(file_ext)
    if not syntax["single"] and not syntax["multi"]:
        return []

    comments = extract_comments(content, file_ext)

    problematic = []
    for line_num, comment in comments:
        # Skip allowed patterns
        if is_allowed_comment(comment):
            continue

        # Check if it's an agent memo pattern
        if is_agent_memo(comment):
            problematic.append(
                {"line": line_num, "comment": comment, "type": "agent_memo"}
            )

    return problematic


def format_warning(problems: list[dict], file_path: str) -> str:
    """Format the warning message for Claude."""
    msg = [
        "COMMENT CHECK - REVIEW REQUIRED",
        "",
        f"Detected {len(problems)} potentially unnecessary comment(s) in {Path(file_path).name}:",
        "",
    ]

    for p in problems[:5]:  # Limit to first 5
        comment_preview = p["comment"][:70].replace("\n", " ")
        if len(p["comment"]) > 70:
            comment_preview += "..."
        msg.append(f"  Line {p['line']}: {comment_preview}")

    if len(problems) > 5:
        msg.append(f"  ... and {len(problems) - 5} more")

    msg.extend(
        [
            "",
            "ACTION REQUIRED:",
            "1. If comment explains WHY (not WHAT): Keep it",
            "2. If comment is a linter directive, BDD, or contains URL/issue ref: Keep it",
            "3. If comment just describes what code does: REMOVE IT",
            "4. If comment tracks changes (Added/Modified/Changed): REMOVE IT",
            "",
            "The code should be self-documenting. Good comments explain WHY, not WHAT.",
        ]
    )

    return "\n".join(msg)


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Get file path
    file_path = tool_input.get("file_path", "")
    if not file_path:
        print(json.dumps({"continue": True}))
        return

    # Check if we support this file type
    file_ext = Path(file_path).suffix.lower()
    syntax = get_comment_syntax(file_ext)
    if not syntax["single"] and not syntax["multi"]:
        print(json.dumps({"continue": True}))
        return

    problems = []

    if tool_name == "Edit":
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")

        # Only check the new content for agent memo patterns
        # We compare old vs new to only flag NEW comments
        problems = check_for_new_comments(old_string, new_string, file_path)

    elif tool_name == "Write":
        content = tool_input.get("content", "")
        # For new files, check all comments
        problems = check_content_for_comments(content, file_path)

    if problems:
        warning = format_warning(problems, file_path)
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": warning,
            },
        }
        print(json.dumps(output))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"continue": True}))
    sys.exit(0)

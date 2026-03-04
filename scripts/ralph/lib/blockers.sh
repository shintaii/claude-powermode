#!/usr/bin/env bash
# lib/blockers.sh — BLOCKED.md and issues.md detection

# ── Check for BLOCKED.md ────────────────────────────────────────────────────
# Returns 0 if blocked, 1 if clear
check_blocked() {
    local project_dir="$1"
    if [[ -f "$project_dir/BLOCKED.md" ]]; then
        return 0
    fi
    return 1
}

# ── Get blocker message ─────────────────────────────────────────────────────
get_blocker_message() {
    local project_dir="$1"
    if [[ -f "$project_dir/BLOCKED.md" ]]; then
        # Return first non-empty, non-header line
        python3 -c "
with open('$project_dir/BLOCKED.md') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            print(line)
            break
"
    fi
}

# ── Check for blocking issues ───────────────────────────────────────────────
# Returns 0 if blocking issues found, 1 if clear
check_blocking_issues() {
    local project_dir="$1"
    local issues_file="$project_dir/issues.md"

    if [[ ! -f "$issues_file" ]]; then
        return 1
    fi

    python3 -c "
import sys

with open('$issues_file') as f:
    content = f.read()

# Look for high-severity OPEN issues in table format:
# | ID | Severity | Status | Description |
blocking = False
for line in content.split('\n'):
    line = line.strip()
    if not line.startswith('|'):
        continue
    cells = [c.strip().lower() for c in line.split('|')[1:-1]]
    if len(cells) < 3:
        continue
    # Check for high/critical severity + open status
    severity = cells[1] if len(cells) > 1 else ''
    status = cells[2] if len(cells) > 2 else ''
    if severity in ('high', 'critical') and status == 'open':
        blocking = True
        break

sys.exit(0 if blocking else 1)
"
}

# ── Get blocking issue details ──────────────────────────────────────────────
get_blocking_issue_summary() {
    local project_dir="$1"
    local issues_file="$project_dir/issues.md"

    if [[ ! -f "$issues_file" ]]; then
        return
    fi

    python3 -c "
with open('$issues_file') as f:
    content = f.read()

issues = []
for line in content.split('\n'):
    line = line.strip()
    if not line.startswith('|'):
        continue
    cells = [c.strip() for c in line.split('|')[1:-1]]
    if len(cells) < 4:
        continue
    severity = cells[1].lower() if len(cells) > 1 else ''
    status = cells[2].lower() if len(cells) > 2 else ''
    desc = cells[3] if len(cells) > 3 else ''
    if severity in ('high', 'critical') and status == 'open':
        issues.append(f'  > [{cells[1]}] {desc}')

print('\n'.join(issues))
"
}

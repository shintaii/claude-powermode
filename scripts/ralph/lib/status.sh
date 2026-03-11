#!/usr/bin/env bash
# lib/status.sh — status.json parsing and task resolution

# ── Project path resolution ─────────────────────────────────────────────────
get_project_path() {
    local slug="$1"
    local path=".powermode/projects/$slug"
    if [[ -d "$path" ]]; then
        echo "$path"
    else
        echo ""
        return 1
    fi
}

# ── Read project status ─────────────────────────────────────────────────────
# Returns: status|total|done|next_feat|next_task
read_project_status() {
    local project_dir="$1"
    local status_file="$project_dir/status.json"

    if [[ ! -f "$status_file" ]]; then
        echo "missing|0|0||"
        return 1
    fi

    python3 -c "
import json, sys

with open('$status_file') as f:
    data = json.load(f)

status = data.get('status', 'unknown')
features = data.get('features', {})

total = 0
done = 0
next_feat = ''
next_task = ''

# Iterate features in sorted order (01-xxx, 02-xxx, etc.)
for feat_key in sorted(features.keys()):
    feat = features[feat_key]
    tasks = feat.get('tasks', {})
    for task_key in sorted(tasks.keys()):
        total += 1
        if tasks[task_key] == 'done':
            done += 1
        elif not next_task:
            next_feat = feat_key
            next_task = task_key

print(f'{status}|{total}|{done}|{next_feat}|{next_task}')
"
}

# ── Get pending tasks ordered by dependency ─────────────────────────────────
# Parses feature README.md dependency table, returns ordered pending tasks
get_pending_tasks_ordered() {
    local feature_dir="$1"
    local readme="$feature_dir/README.md"

    if [[ ! -f "$readme" ]]; then
        echo ""
        return 1
    fi

    python3 -c "
import re, sys

with open('$readme') as f:
    content = f.read()

# Parse markdown table rows: | # | File | Domain | Test Focus | Dependencies | Status |
rows = []
for line in content.split('\n'):
    line = line.strip()
    if not line.startswith('|'):
        continue
    cells = [c.strip() for c in line.split('|')[1:-1]]
    if len(cells) < 6:
        continue
    # Skip header and separator rows
    if cells[0] in ('#', '---', '') or cells[0].startswith('-'):
        continue
    try:
        num = int(cells[0])
    except ValueError:
        continue
    rows.append({
        'num': num,
        'file': cells[1],
        'deps': cells[4],
        'status': cells[5]
    })

# Filter to pending/in_progress tasks
pending = [r for r in rows if r['status'].lower() in ('pending', 'in progress')]

# Topological sort by dependencies
def deps_of(row):
    d = row['deps'].strip()
    if d.lower().startswith('none') or d == '':
        return []
    return [int(x.strip()) for x in d.split(',') if x.strip().isdigit()]

done_nums = {r['num'] for r in rows if r['status'].lower() == 'done'}
ordered = []
remaining = list(pending)
max_iters = len(remaining) + 1
for _ in range(max_iters):
    if not remaining:
        break
    added = []
    for r in remaining:
        if all(d in done_nums for d in deps_of(r)):
            ordered.append(r)
            done_nums.add(r['num'])
            added.append(r)
    for a in added:
        remaining.remove(a)
    if not added:
        # Remaining have unmet deps — add them anyway as blocked
        ordered.extend(remaining)
        break

for r in ordered:
    print(r['file'])
"
}

# ── Check if task dependencies are met ──────────────────────────────────────
check_deps_met() {
    local project_dir="$1"
    local feature="$2"
    local deps_string="$3"

    if [[ -z "$deps_string" || "$deps_string" == None* || "$deps_string" == none* ]]; then
        return 0
    fi

    python3 -c "
import json, sys

with open('$project_dir/status.json') as f:
    data = json.load(f)

feat = data.get('features', {}).get('$feature', {})
tasks = feat.get('tasks', {})

deps = [d.strip() for d in '$deps_string'.split(',') if d.strip()]
for dep in deps:
    # dep is a number like '01' — find matching task key
    matched = False
    for task_key, task_status in tasks.items():
        if task_key.startswith(dep.zfill(2)):
            if task_status == 'done':
                matched = True
            break
    if not matched:
        sys.exit(1)
sys.exit(0)
"
}

# ── Count done tasks ────────────────────────────────────────────────────────
count_done_tasks() {
    local project_dir="$1"
    python3 -c "
import json
with open('$project_dir/status.json') as f:
    data = json.load(f)
count = sum(1 for f in data.get('features', {}).values()
            for t in f.get('tasks', {}).values() if t == 'done')
print(count)
"
}

# ── Sync README status → status.json ───────────────────────────────────────
# Reads the feature README table and updates status.json for any tasks
# marked "Done" in README but not in status.json (drift repair)
sync_readme_to_status() {
    local project_dir="$1"
    local feature="$2"
    local feature_dir="$project_dir/features/$feature"
    local readme="$feature_dir/README.md"
    local status_file="$project_dir/status.json"

    [[ -f "$readme" ]] || return 1
    [[ -f "$status_file" ]] || return 1

    python3 -c "
import json, re

with open('$readme') as f:
    content = f.read()

with open('$status_file') as f:
    data = json.load(f)

feat = data.get('features', {}).get('$feature', {})
tasks = feat.get('tasks', {})

changed = False
for line in content.split('\n'):
    line = line.strip()
    if not line.startswith('|'):
        continue
    cells = [c.strip() for c in line.split('|')[1:-1]]
    if len(cells) < 6:
        continue
    try:
        num = int(cells[0])
    except ValueError:
        continue

    file_name = cells[1].strip()
    readme_status = cells[5].strip().lower()
    # Derive task key from file name (e.g., '01-project-setup.md' → '01-project-setup')
    task_key = file_name.replace('.md', '')

    if readme_status == 'done' and tasks.get(task_key) != 'done':
        tasks[task_key] = 'done'
        changed = True

if changed:
    # Update counts
    done_count = sum(1 for v in tasks.values() if v == 'done')
    feat['tasks_done'] = done_count
    feat['tasks'] = tasks
    data['features']['$feature'] = feat
    with open('$status_file', 'w') as f:
        json.dump(data, f, indent=2)
    print(f'synced')
else:
    print('ok')
"
}

# ── Check if specific task is done ──────────────────────────────────────────
is_task_done() {
    local project_dir="$1"
    local feature="$2"
    local task="$3"

    python3 -c "
import json, sys
with open('$project_dir/status.json') as f:
    data = json.load(f)
feat = data.get('features', {}).get('$feature', {})
status = feat.get('tasks', {}).get('$task', 'pending')
sys.exit(0 if status == 'done' else 1)
"
}

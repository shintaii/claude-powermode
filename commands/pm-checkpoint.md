---
name: pm-checkpoint
description: Manual checkpoint - validate work alignment with plan and check context usage
allowed-tools: "*"
---

# Checkpoint Validation

Performing manual checkpoint to verify work alignment and context health.

## 1. Check Context Usage

Read the context state file to assess token usage:

```
Read file: {cwd}/.powermode/context-state.json

If exists, report:
- Estimated tokens: X (~Y% of 200K limit)
- Tool calls this session: N
- Modified files: [list]

If >70%: WARN - Consider /compact before continuing
If >85%: CRITICAL - Strongly recommend /compact now
```

## 2. Check Plan Alignment

Compare current work against the active plan:

```
1. Read plan from:
   - .powermode/boulder.json (active_plan field)
   - OR .planning/ROADMAP.md
   - OR most recent .powermode/plans/*.md

2. Read current todos using todoread

3. Calculate alignment:
   - Extract task keywords from plan
   - Extract keywords from completed todos
   - Overlap ratio = intersection / completed_keywords
   
4. Report:
   - Progress: X/Y tasks complete
   - Alignment: N% (GOOD if >70%, WARNING if 50-70%, DRIFT if <50%)
```

## 3. Check for Drift Indicators

Look for signs of scope creep or deviation:

- Are completed tasks mentioned in the plan?
- Are there plan tasks that should be done but aren't in todos?
- Are there todos that weren't in the original plan?

## 4. Generate Report

```
╔══════════════════════════════════════════════╗
║           CHECKPOINT REPORT                  ║
╠══════════════════════════════════════════════╣
║ Context Usage: ~85K tokens (42%)       [OK]  ║
║ Progress: 3/7 tasks complete          [42%]  ║
║ Plan Alignment: 78%                  [GOOD]  ║
╠══════════════════════════════════════════════╣
║ Status: ON TRACK                             ║
╚══════════════════════════════════════════════╝

Modified files this session:
- src/hooks/context-monitor.py
- src/hooks/session-recovery.py

Next planned task:
- Create /pm-checkpoint command

Recommendations:
- [None - continue with current plan]
```

## 5. Actions Based on Report

| Condition | Action |
|-----------|--------|
| Context >85% | Run `/compact` before continuing |
| Alignment <50% | Stop and review plan with user |
| Progress 100% | Verify all acceptance criteria met |
| Drift detected | Ask user if deviation is intentional |

---

**Run this checkpoint now by reading the state files and current todos.**

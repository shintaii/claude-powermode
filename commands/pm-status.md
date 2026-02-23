---
name: pm-status
description: Show project status dashboard with drift detection between status.json and feature READMEs.
allowed-tools: "*"
---

# Project Status Dashboard

Checking status for: `$ARGUMENTS`

## Step 1: Find Project

If `$ARGUMENTS` contains a project slug, use it. Otherwise:

1. Read `.powermode/projects/index.json`
2. List all projects with their status
3. Ask user to select a project (use AskUserQuestion)

## Step 2: Gather Data

1. Read `.powermode/projects/<slug>/status.json` for machine state
2. Read ALL feature `README.md` files under `.powermode/projects/<slug>/features/*/README.md`
3. Parse the "Status" column from each README's task table (look for `| Done |` or `| Pending |` etc.)

## Step 3: Cross-Reference for Drift

For each feature and its tasks, compare:
- **status.json** task status (e.g., `"pending"`, `"done"`, `"in_progress"`)
- **README** Status column value (e.g., `Done`, `Pending`, `In Progress`)

Build a drift list where these disagree.

## Step 4: Present Dashboard

Show a summary like this:

```
Project: <slug>
Status: <status> | <done>/<total> tasks done (<percent>%)

Features:
  <feature-name>          [DONE] <done>/<total> tasks
  <feature-name>          [----] <done>/<total> tasks  <- NEXT
  <feature-name>          [WIP-] <done>/<total> tasks

Next task: <NN-feature>/<task-slug>
Run: /powermode .powermode/projects/<slug>/features/<NN-feature>/<task-slug>.md
```

Status indicators:
- `[DONE]` — all tasks done
- `[WIP-]` — some tasks done (in progress)
- `[----]` — no tasks started

Mark the first pending feature with `<- NEXT`.

The "Next task" is the first pending task (by number) in the first non-done feature.

## Step 5: Show Drift Warnings (if any)

If drift was detected between README and status.json, show:

```
Drift detected:
  - <NN-feature>/<task>: README=Done, status.json=pending
  - <NN-feature>/<task>: README=Pending, status.json=done
  Action: Update status.json to match README (READMEs are source of truth)
```

## Step 6: User Action

Ask the user what to do (use AskUserQuestion):

- **Start next task** — Begin work on the next pending task (run `/powermode` with that task's PRD)
- **Fix drift** — Update status.json to match the README status values. Recalculate `tasks_done` counts and feature statuses. Update the `updated` timestamp.
- **Just viewing** — No action needed

### Fix Drift Implementation

If the user selects "Fix drift":

1. For each drifted task, update status.json task status to match README
2. Recalculate `tasks_done` for each feature
3. Set feature status: `"done"` if all tasks done, `"in_progress"` if some done, `"pending"` if none done
4. Update the `updated` timestamp to now
5. Write the updated status.json
6. Show what changed

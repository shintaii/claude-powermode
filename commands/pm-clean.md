---
name: pm-clean
description: Archive and remove completed projects. Creates a summary in .powermode/archive/ before cleaning up project files and references.
allowed-tools: "*"
---

# Clean Project

Cleaning project: `$ARGUMENTS`

## Step 1: Load Projects

1. Read `.powermode/projects/index.json`
2. For each project, read its `status.json` to determine completion status
3. A project is "done" when all features and tasks have status `Done`

If `index.json` doesn't exist or has no projects, tell the user there's nothing to clean and stop.

## Step 2: Select Project(s)

Parse `$ARGUMENTS`:

- **Specific slug** (e.g., `my-project`) → select that project
- **`all`** → select all done projects. If none are done, tell the user and stop
- **Empty** → show interactive list via AskUserQuestion with project names, statuses, and completion percentages. Let user pick one

## Step 3: Guard Non-Done Projects

If any selected project is NOT fully done:

> "⚠️ Project `<slug>` is not complete (<X>% done). Archive anyway?"

Ask for explicit confirmation via AskUserQuestion with options: "Yes, archive it" / "No, skip it"

Skip projects the user declines.

If no projects remain after filtering, stop.

## Step 4: Preview

Show the user what will happen for each selected project:

```
Project: <slug> (<status>, <X>% complete)

Files to delete:
  .powermode/projects/<slug>/  (entire directory)

References to update:
  .powermode/projects/index.json  (remove entry)
  .powermode/recovery.json        (clear active_project if matching)

Archive will be created at:
  .powermode/archive/<slug>.md
```

Ask for confirmation via AskUserQuestion: "Proceed with cleanup?" — "Yes, clean up" / "No, cancel"

## Step 5: Archive

For each project, create `.powermode/archive/<slug>.md`:

```markdown
# Archive: <slug>

**Created:** <created date from index.json or project.md>  |  **Archived:** <today's date>  |  **Status:** <final status>

## Project Scope
<full content from project.md>

## Features & Tasks
<from status.json — list each feature with its tasks and their final statuses>

Format:
### Feature: <feature-name>
- [x] Task 1 — Done
- [x] Task 2 — Done
- [ ] Task 3 — Pending

## Decisions
<full content from decisions.md, or "No decisions logged.">

## Implementation Notes
<content from any NOTES.md files found in feature directories, prefixed with feature name. Or "No notes captured.">
```

Create the `.powermode/archive/` directory if it doesn't exist.

## Step 6: Clean

For each archived project:

1. **`index.json`** — remove the project entry from the `projects` array. Write the updated file
2. **Project directory** — delete `.powermode/projects/<slug>/` entirely (use `rm -rf`)
3. **`recovery.json`** — read the file. If `active_project` matches the slug, set it to `null`. Write back. If the file doesn't exist, skip

## Step 7: Report

Show a summary:

```
Cleaned N project(s):

  ✓ <slug-1> → archived to .powermode/archive/<slug-1>.md
  ✓ <slug-2> → archived to .powermode/archive/<slug-2>.md

Index updated. Recovery state cleared.
```

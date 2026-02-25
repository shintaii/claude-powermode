---
name: pm-review
description: Manually run verification/review on recent changes. Use when verification was skipped, after fixes, or to re-check work.
allowed-tools: "*"
---

# Manual Verification Review

Run the powermode verification step on demand.

## Arguments

```
$ARGUMENTS
```

## Determine Scope

Parse `$ARGUMENTS` to determine what to verify:

1. **No arguments** → Verify all uncommitted changes (git diff + git diff --cached)
2. **File paths** (e.g., `src/foo.ts src/bar.ts`) → Verify those specific files
3. **Project/feature reference** (e.g., `@.powermode/projects/<slug>/features/<NN-feature>/`) → Verify against that feature's task PRDs
4. **Task PRD path** (e.g., `@.powermode/projects/<slug>/features/<NN-feature>/<NN-task>.md`) → Verify against that specific task PRD

## Execution

### Step 1: Gather Context

Based on scope, collect:
- **Changed files**: Run `git diff --name-only` (unstaged) and `git diff --cached --name-only` (staged) to identify what changed
- **PRD requirements**: If a project/feature/task reference was given, read the relevant PRD(s) to extract acceptance criteria
- **If no arguments**: Also check for a recent `status.json` to find the active project and current task

### Step 2: Run Verifier

Fire the `pm-verifier` agent with the collected context:

```
Task(subagent_type="powermode:pm-verifier", prompt="
  Verify the following changes. Run the full verification checklist.

  ## Changed Files
  <list of files from Step 1>

  ## Requirements
  <PRD acceptance criteria if available, otherwise 'Review changes for correctness, patterns, and quality'>

  ## Additional Context
  <any $ARGUMENTS context>
")
```

### Step 3: Report

Display the verifier's report to the user. If findings exist, summarize:
- **BLOCKER/MAJOR** items that need attention
- **Verdict** (PASS / FAIL / PASS WITH NOTES)

If the verification is against a task PRD and it passes, ask the user if they want to mark the task as Done in the feature README.

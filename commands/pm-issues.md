---
name: pm-issues
description: Review open issues in a project and optionally convert them to new task PRDs.
allowed-tools: "*"
---

# Project Issues Manager

Managing issues for: `$ARGUMENTS`

## Step 1: Find Project

If `$ARGUMENTS` contains a project slug, use it. Otherwise:

1. Read `.powermode/projects/index.json`
2. For each project, check if `issues.md` exists and has `## OPEN` entries
3. List projects with open issue counts
4. Ask user to select a project (use AskUserQuestion)

## Step 2: Read Issues

1. Read `.powermode/projects/<project-slug>/issues.md`
2. Parse all `## OPEN` entries
3. Group by feature

## Step 3: Present Issues

Show issues grouped by feature:

```
Project: <project-slug>

Feature: user-auth (2 open issues)
  1. [medium] Rate limiting not specified
     Found by: pm-implementer during user-auth/01-login-api
     Suggested: Create task PRD for rate limiting

  2. [low] Password complexity rules unclear
     Found by: pm-verifier during user-auth/02-signup-flow
     Suggested: Add to existing signup PRD

Feature: payments (1 open issue)
  3. [high] Refund flow not covered
     Found by: pm-implementer during payments/01-stripe-integration
     Suggested: Create new task PRD
```

## Step 4: User Action

Ask the user what to do (use AskUserQuestion):

- **Convert selected issues to PRDs** - Select which issues to turn into new task PRDs
- **Review all and decide per-issue** - Go through each issue one by one
- **Close resolved issues** - Mark issues as resolved that are no longer relevant
- **Just viewing** - No action needed

## Step 5: Convert to PRDs (if selected)

For each selected issue:

1. Run analyser on the issue description:
```
Task(subagent_type="powermode:pm-analyser", prompt="
  Analyze this issue for a task PRD:
  ISSUE: <issue description>
  FEATURE: <feature-slug>
  PROJECT: <project-slug>
  Provide directives for a single task PRD.
")
```

2. Run powerplanner for the task PRD:
```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a TASK-LEVEL plan for this issue:
  ISSUE: <issue description>
  ANALYSER OUTPUT: [analyser findings]
  FEATURE: <feature-slug>
  This will become a new task PRD in the feature.
")
```

3. Write the task PRD to the feature folder:
   - Determine next number (e.g., if 03 is the last, create 04-<slug>.md)
   - Write the PRD file

4. Update the feature README with the new task row

5. Update `status.json` with the new task entry

6. Mark the issue as RESOLVED in `issues.md`:
```markdown
## RESOLVED | YYYY-MM-DD | <Issue Title>
**Found by:** <original finder>
**Feature:** <feature-slug>
**Resolution:** Converted to task PRD: <NN-task-slug>.md
```

## Step 6: Report

Show what was done:
```
Processed X issue(s) for project <project-slug>:
- Converted to PRD: <list>
- Still open: <count>

New PRD files:
- .powermode/projects/<slug>/features/<feature>/04-<task>.md
```

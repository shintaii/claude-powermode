---
name: pm-tests
description: Add or review tests for an existing task PRD, feature, or project. Presents current tests, lets user refine them, then verifies with pm-verifier.
allowed-tools: "*"
---

# Test Manager

Target: `$ARGUMENTS`

## Step 1: Detect Scope

Parse `$ARGUMENTS`:

| Input | Scope |
|-------|-------|
| Path ending in `.md` | **Task** — single PRD |
| Path ending in feature folder | **Feature** — all PRDs in folder |
| Project slug (match in `index.json`) | **Project** — all features |
| Empty | Ask user via AskUserQuestion to pick project/feature/task |

## Step 2: Read Existing Tests

**Task scope:** Read the PRD file. Extract the `## Tests` table.

**Feature scope:** Read all task PRDs in the feature folder (skip README.md, NOTES.md). Extract `## Tests` from each. Also read the feature README for any `## Feature Tests` section.

**Project scope:** Delegate to pm-explorer:
```
Task(subagent_type="powermode:pm-explorer", model="haiku", prompt="
  Read all task PRDs under .powermode/projects/<slug>/features/.
  For each PRD, extract the full ## Tests table.
  Also read each feature README for ## Feature Tests sections.
  Also read project.md for ## Project Tests section.
  Return a structured summary grouped by feature.
")
```

## Step 3: Present Tests to User

Present a consolidated view using AskUserQuestion:

```
Here are the current tests for <target>:

**[Feature: 01-auth]**
  01-login-api.md:
  | T1 | unit | Login with valid credentials | Returns 200 + JWT |
  | T2 | unit | Login with wrong password | Returns 401 |

  02-signup.md:
  | T1 | integration | Register new user | User created in DB, email sent |

  Feature Tests (## Feature Tests in README):
  [none defined]

**[Feature: 02-dashboard]**
  ...
```

Options:
- Approve as-is — run verifier now
- Add tests to specific PRD(s) — tell me which
- Change existing tests — tell me which
- Add feature-level tests
- Add project-level tests
- Simplify — remove redundant tests

## Step 4: Apply Changes (if requested)

Delegate updates to a subagent:

```
Task(subagent_type="general-purpose", prompt="
  Update the ## Tests section in these files:

  [list files and exact changes needed]

  Rules:
  - Keep the markdown table format: | ID | Type | Description | Expected Result |
  - Test IDs: T1, T2, T3... (task-scoped)
  - Every test needs a concrete expected result with exact values
  - Test types: unit, integration, e2e, functional, manual
  - Feature tests go in the feature README under ## Feature Tests
  - Project tests go in project.md under ## Project Tests
")
```

## Step 5: Verify

Run pm-verifier on the target scope:

**Task scope:**
```
Task(subagent_type="powermode:pm-verifier", prompt="
  Verify the implementation of <PRD path>.
  Read the PRD. Verify each test ID (T1, T2...) from the ## Tests table passes.
  Check: builds, tests pass, no regressions.
  CRITICAL: Scan for stubs, TODOs, placeholders, empty function bodies. Any stub = BLOCKER.
")
```

**Feature scope:**
```
Task(subagent_type="powermode:pm-verifier", prompt="
  Verify the feature at <feature folder path>.
  Read each task PRD. Verify each test ID from each ## Tests table passes.
  Also verify ## Feature Tests from the feature README.
  Check: builds, tests pass, no regressions.
  CRITICAL: Any stub = BLOCKER.
")
```

**Project scope:**
```
Task(subagent_type="powermode:pm-verifier", prompt="
  Verify all features of project <slug>.
  For each feature: read task PRDs and verify ## Tests tables.
  Also verify ## Feature Tests in each feature README.
  Also verify ## Project Tests in project.md.
  Check: builds, tests pass, no regressions.
  CRITICAL: Any stub = BLOCKER.
")
```

## Step 6: Report

Show verdict and any failures:

```
Tests verified for: <target>
Verdict: PASS / FAIL / PASS WITH NOTES

[If FAIL or PASS WITH NOTES: list specific failing test IDs and what failed]

Suggestion: /powermode <path> to implement fixes
```

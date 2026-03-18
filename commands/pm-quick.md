---
name: pm-quick
description: Lightweight implement-verify loop for small changes. Explore → plan → implement → verify → done. No PRDs, no project structure. Use for single-scope tasks like adding a table, fixing a function, or small feature additions.
allowed-tools: "*"
---

# Quick Mode

Fast, disciplined execution for small changes. No PRD files, no project hierarchy — just the core loop.

**Task:** `$ARGUMENTS`

If `$ARGUMENTS` is empty, ask the user what they want to do via AskUserQuestion (free text).

---

## Phase 1: Explore

Fire pm-explorer to understand the relevant code:

```
Agent(subagent_type="powermode:pm-explorer", model="haiku", prompt="
  The user wants to: $ARGUMENTS

  Find the relevant files, understand the current implementation, and report:
  1. Which files need to change
  2. Current state of those files (key functions, components, structure)
  3. Any dependencies or side effects to watch for
  4. Existing patterns to follow (naming, style, architecture)
")
```

If the task is trivial and you already know the codebase well enough (e.g. user pointed to a specific file), skip this step.

---

## Phase 2: Plan

Based on the explorer's findings, write a **brief inline plan**. This is NOT a PRD — it lives in the conversation only.

Format:

```
## Quick Plan

**Goal:** <one sentence>

**Changes:**
1. <file> — <what to do>
2. <file> — <what to do>
3. ...

**Approach:** <1-2 sentences on how>

**Tests:** <needed / not needed — and why>
```

Present this to the user and wait for confirmation via AskUserQuestion:

Options:
- **Go** — execute as planned
- **Adjust** — user provides modifications (free text)
- **Cancel** — stop

If the user adjusts, update the plan and re-present. Do NOT proceed without explicit "Go".

---

## Phase 3: Implement

Delegate to pm-implementer with the confirmed plan:

```
Agent(subagent_type="powermode:pm-implementer", prompt="
  ## Task
  <the user's original request>

  ## Plan (confirmed by user)
  <the confirmed plan from Phase 2>

  ## Explorer Findings
  <relevant findings from Phase 1>

  Implement this change. Follow existing patterns. Commit when done.
")
```

Save the returned `agentId` for potential fix cycles.

---

## Phase 4: Verify

Run pm-verifier on the changes:

```
Agent(subagent_type="powermode:pm-verifier", prompt="
  Verify the implementation of: <task description>

  Files changed: <list from implementer output>

  Focus on:
  - Stub/placeholder detection
  - Wiring verification (is new code reachable?)
  - CLAUDE.md compliance
  - Simplicity review
  - Comment audit
")
```

### Handling Results

- **PASS** → proceed to Phase 5
- **PASS WITH NOTES** → resume implementer with findings, re-verify once, then accept:
  ```
  SendMessage(to="<implementer-agentId>", content="
    Verifier found issues: <findings>
    Fix these, then commit.
  ")
  ```
  Re-verify once. Accept result regardless of second verdict.
- **FAIL** → resume implementer with blockers, re-verify. Max 3 attempts total. If still failing after 3, stop and present to user.

---

## Phase 5: Codex Second-Opinion

If Codex CLI is installed, run a quick review:

```
Skill(skill="pm-codex-review", args="commit HEAD --effort high")
```

- Act on CRITICAL/MAJOR findings only (feed to implementer)
- Skip if Codex not installed — do not block
- One pass only, no loops

---

## Phase 6: Simplify

```
Skill(skill="simplify")
```

MANDATORY. Do not skip.

---

## Done

After simplify completes, report:

```
## Quick Mode Complete

**Task:** <description>
**Files changed:** <list>
**Status:** Done

Changes committed and verified.
```

Stop. Do not ask "anything else?" — the user will tell you if they need more.

---

## Rules

- **No PRD files** — the plan lives in conversation only
- **No project structure** — no .powermode/projects/ involvement
- **No status tracking** — no status.json updates
- **Still disciplined** — explore, plan, verify, simplify are not optional
- **User confirms plan** — never implement without explicit "Go"
- **Follow existing patterns** — pm-implementer must match codebase conventions
- **If the task is too big** — if the explorer reveals the change touches 5+ files or requires architectural decisions, recommend `/powermode` instead. Ask the user via AskUserQuestion:
  - **Continue with /pm-quick** — user's call
  - **Switch to /powermode** — full workflow with PRDs

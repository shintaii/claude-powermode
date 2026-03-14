# Powermode Plugin

Disciplined engineering workflow for Claude Code: consistent exploration, planning, implementation, verification, and guardrails against drift.

## Installation

```bash
# Add the marketplace
claude plugin marketplace add shintaii/claude-powermode

# Install the plugin
claude plugin install powermode@claude-powermode

# Verify
claude plugin list | grep powermode
```

## Updating

```bash
claude plugin update powermode@claude-powermode
```

---

## Quick Start: Which Command Do I Use?

| I have... | I want... | Use |
|-----------|-----------|-----|
| An idea/goal | A detailed plan + PRD files | `/pm-plan add user authentication` |
| An existing document (spec, issue, PRD) | Split into implementable PRDs | `/pm-plan @path/to/doc.md` |
| An existing project folder | See structure and next steps | `/pm-plan @.powermode/projects/my-project/` |
| A project/feature ready to implement | Implementation (auto-detects team mode) | `/powermode @.powermode/projects/my-project/` |
| Started work, want methodology | Enable powermode workflow | `/powermode` |
| Doubt about current progress | Check alignment with plan | `/pm-checkpoint` |
| Want project dashboard | See status of all features/tasks | `/pm-status` |
| Need to re-verify recent changes | Manual verification run | `/pm-review` |
| Want a second opinion on code | Codex (GPT-5.4) code review | `/pm-codex-review` |

---

## Commands

### `/powermode` - Activate the Methodology

Enables the disciplined explore → plan → implement → verify → simplify workflow. Lists available agents and enables all guardrails.

```
/powermode
> Now help me refactor the auth module
```

Can also resume a project directly: `/powermode my-project-slug`

### `/pm-plan [goal]` - Unified Planning

Auto-detects input type and acts accordingly:

| Input | Mode | Example |
|-------|------|---------|
| Plain text goal | Plans from scratch | `/pm-plan add user authentication` |
| `@` document reference | Transforms doc into PRDs | `/pm-plan @docs/payment-spec.md` |
| `@` folder reference | Shows existing structure | `/pm-plan @.powermode/projects/auth/` |

**Workflow:** Analyser → Powerplanner → Planreviewer (max 3 review iterations) → PRD files written to `.powermode/projects/`.

### `/pm-checkpoint` - Manual Progress Check

Compares current state to the plan. Identifies drift or missed steps.

### `/pm-status` - Project Dashboard

Shows status of all projects, features, and tasks with completion percentages. Detects drift between `status.json` and feature READMEs.

### `/pm-review` - Manual Verification

Runs pm-verifier on recent changes. Use when verification was skipped, after manual fixes, or to re-check work.

### `/pm-export` - Export Documentation

Copies all project markdown files to a user-specified folder, preserving structure.

### `/pm-issues` - Review Open Issues

Lists open issues tracked in project `issues.md` files. Can convert issues to new task PRDs.

### `/pm-codex-review` - Second-Opinion Code Review

Runs OpenAI's Codex CLI (GPT-5.4) as an independent reviewer, then optionally feeds findings to pm-implementer.

| Usage | What it reviews |
|-------|----------------|
| `/pm-codex-review` | All uncommitted changes |
| `/pm-codex-review staged` | Only staged changes |
| `/pm-codex-review pr` | Current branch's PR |
| `/pm-codex-review pr 42` | PR #42 |
| `/pm-codex-review commit abc123` | Specific commit (any git ref) |
| `/pm-codex-review branch` | All commits since `main` |
| `/pm-codex-review branch develop` | All commits since `develop` |
| `/pm-codex-review src/foo.py` | Specific files |

Flags: `--model <model>`, `--effort <level>`. Free-text after the mode is treated as additional review instructions.

Requires [Codex CLI](https://github.com/openai/codex) (`npm install -g @openai/codex`).

### `/pm-uiux` - UI/UX Review & Build

Comprehensive UI/UX review, audit, and implementation using the powermode workflow. Reviews existing interfaces or builds new ones.

---

## Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| **pm-explorer** | Haiku | Fast codebase search, finding files and patterns |
| **pm-researcher** | Sonnet | External docs, library research, OSS examples |
| **pm-analyser** | Opus | Pre-planning gap analysis, hidden requirements |
| **pm-powerplanner** | Opus | Strategic planning, comprehensive work plans |
| **pm-planreviewer** | Sonnet | Plan review, iterates until quality bar met |
| **pm-oracle** | Opus | Architecture decisions, deep reasoning, stuck debugging |
| **pm-implementer** | Sonnet | Focused code implementation (auto-commits per task) |
| **pm-verifier** | Sonnet | Quality verification with evidence |
| **pm-uat-runner** | Sonnet | UAT via Playwright MCP — browser-based user journey tests |

---

## Per-Task Execution Cycle

Every task follows this strict sequence (steps c-e are hook-enforced):

```
a. EXPLORE with pm-explorer (if needed)
b. IMPLEMENT with pm-implementer → auto-commits, returns agentId
c. VERIFY with pm-verifier — MANDATORY, enforced by hook
d. If FAIL → resume implementer via agentId → re-verify (max 3 attempts)
e. After verification → /simplify for code quality polish
f. Move to next task
```

**Verification is hook-enforced:** starting a new pm-implementer without running pm-verifier first is automatically BLOCKED. Resume calls (fix cycles) bypass this check.

**After 3 consecutive verification failures:** stop → revert → consult pm-oracle → ask user.

### TDD Classification

The planner classifies each task as needing tests or not. Cleanup, config, and docs tasks skip the test-writer step automatically.

### UAT (Feature/Project Scope)

For feature and project scopes, planning generates `UAT_SCENARIOS.md` with browser-based user journey tests. After all tasks pass verification, `pm-uat-runner` executes scenarios via Playwright MCP with a fix-and-retry loop. Task-scoped work skips UAT.

---

## Project Structure

Powermode uses hierarchical planning: Project → Feature → Task.

```
.powermode/projects/
├── index.json                          # Master index of all projects
└── my-project/
    ├── project.md                      # Scope, goals, high-level requirements
    ├── status.json                     # Machine-readable state (features, tasks, completion)
    ├── decisions.md                    # Decision log (append-only)
    ├── issues.md                       # Issues/gaps tracker
    └── features/
        ├── 01-auth/
        │   ├── README.md               # Feature index with dependency table
        │   ├── 01-database-schema.md   # Task PRD
        │   ├── 02-api-endpoints.md     # Task PRD (depends on 01)
        │   ├── 03-frontend-ui.md       # Task PRD (depends on 02)
        │   └── NOTES.md               # Implementation discoveries
        └── 02-payments/
            ├── README.md
            └── 01-stripe-setup.md
```

- Features are numbered for implementation order
- Each task PRD contains scope, requirements, acceptance criteria, test focus, and dependencies
- `status.json` tracks completion state per feature and task
- Runtime files (`.powermode/*.json`) are gitignored; project files are committed

---

## Typical Workflows

### New Feature (from scratch)

```
1. /pm-plan add payment processing
2. Review generated PRDs in .powermode/projects/payments/
3. /powermode @.powermode/projects/payments/
4. (automatic) implement → verify → simplify per task, auto-commits
```

### Feature from Existing Spec

```
1. /pm-plan @docs/payment-spec.md
2. Review generated PRDs
3. /powermode @.powermode/projects/payments/
```

### Quick Fix (no planning needed)

```
1. /powermode
2. "Fix the null pointer in auth.py line 42"
3. (uses pm-explorer → pm-implementer → pm-verifier → /simplify)
```

### Resume a Project

```
1. /powermode my-project-slug
2. (picks up from last completed task)
```

---

## Automatic Behaviors (Hooks)

These run automatically — you don't invoke them:

| Hook | What It Does |
|------|--------------|
| **Stop validator** | Blocks exit if todos incomplete (escape hatch after 3 attempts) |
| **PRD enforcement** | Blocks exit if referenced PRD wasn't updated |
| **Verification tracker** | Clears pending-verification flag when pm-verifier finishes |
| **Context monitor** | Tracks token usage, warns at 70% |
| **Session recovery** | Saves/restores state across compaction |
| **CLAUDE.md enforcer** | Reminds of project rules on each prompt |
| **Delegation enforcer** | Blocks direct Edit/Write in Power Mode (must use pm-implementer) |
| **Task containment** | Injects scope constraints into subagent prompts; blocks new implementer if verification pending |
| **Implementer lifecycle** | Manages implementer sessions via SubagentStart/Stop; sets verification-pending flag |
| **Subagent context** | Injects role reminders when any pm-* agent spawns |
| **PRD index injector** | Auto-injects PRD structure when `@` references are used |
| **Keyword detector** | Detects powermode-related keywords and activates workflow |
| **Failure accountability** | Forces investigation of test/build failures — prevents dismissing as "pre-existing" |
| **Post-compact reset** | Resets context-state.json after compaction to avoid stale token warnings |
| **Task completion guard** | Blocks task completion if uncommitted changes or TODO/stub patterns remain |
| **Teammate idle guard** | Forces teammates with uncommitted changes to commit before going idle |

---

## How It Works

- **Context tracking** writes `.powermode/context-state.json` in the current workspace
- **Stop hook** reads the session transcript and blocks stop if todos are pending/in_progress
- **Escape hatch** auto-approves after 3 consecutive stop attempts with a warning
- **Session recovery** stores `.powermode/recovery.json` on SessionEnd/PreCompact and restores on SessionStart
- **PRD enforcement** blocks stop when referenced PRDs were not updated
- **Verification enforcement** blocks new pm-implementer calls until pm-verifier has run
- **Auto-commit** implementer commits after each task PRD completion (local only, no push)
- **Post-verify polish** `/simplify` is called by the orchestrator after verification completes — any verdict (PASS, or after PASS WITH NOTES/FAIL fix cycles). 3 parallel review agents: code reuse, quality, efficiency
- **Agent-aware hooks** hooks check `agent_type` to distinguish subagent vs orchestrator — subagents (`powermode:*`) bypass stop/todo checks
- **Context limits** optimized for Opus 4.6 1M context window (warns at 500K tokens)

---

## Manual Hook Tests

```bash
# Stop hook
echo '{"cwd":"/tmp","transcript_path":"/path/to/session.jsonl"}' | python3 hooks/stop-validator.py

# Context monitor
echo '{"session_id":"test","cwd":"/tmp","tool_name":"Bash","tool_input":{},"tool_response":{}}' | python3 hooks/context-monitor.py

# Task containment
echo '{"tool_name":"Task","tool_input":{"prompt":"test","subagent_type":"pm-implementer"},"cwd":"/tmp","session_id":"test"}' | python3 hooks/task-containment-enforcer.py

# Verification tracker
echo '{"hook_event_name":"SubagentStop","agent_type":"powermode:pm-verifier","cwd":"/tmp"}' | python3 hooks/verification-tracker.py
```

---

## Troubleshooting

### PostToolUse hook error spam

- Cause: invalid schema in PostToolUse output
- Fix: ensure `hookSpecificOutput` uses correct event name

### Stop hook never blocks

- Cause: wrong transcript parsing
- Fix: `stop-validator.py` must read `toolUseResult.newTodos` from JSONL transcripts

### Duplicate hooks file

- Cause: `plugin.json` includes `"hooks": "./hooks/hooks.json"`
- Fix: remove that key — hooks auto-load from `hooks/hooks.json`

### Important: hooks.json auto-load

Claude Code auto-loads `hooks/hooks.json`. Do NOT reference it in `plugin.json` or you will get:

```
Hook load failed: Duplicate hooks file detected
```

---

## Credits

Heavily inspired by [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) — thank you for the foundational ideas.

## License

MIT — see [LICENSE](LICENSE)

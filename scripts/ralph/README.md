# RALPH Loop

Fresh-context loop orchestrator for Powermode. Runs each task in a clean Claude session to avoid context window degradation on large projects.

## Setup

```bash
ln -s <plugin-path>/scripts/ralph/ralph.sh /usr/local/bin/ralph
```

## Usage

```bash
# Plan: idea → full project with PRDs
ralph plan "Build a payment processing system"
ralph plan requirements.md --slug payments

# Implement: execute PRDs one by one
ralph implement payments
ralph implement payments --feature 01-auth

# Verify: iterative verify + simplify
ralph verify payments
ralph verify payments --scope task --feature 01-auth

# Status: check progress
ralph status payments
```

## How It Works

### `ralph plan`
1. **Research + Scaffold** (opus) — runs `/pm-plan`, creates project structure + research.md
2. **PRD sessions** (sonnet) — one fresh session per task PRD, using research.md as context
3. **Consistency review** (sonnet) — cross-PRD check for gaps/overlaps/contradictions

### `ralph implement`
Loop until done or blocked:
1. Check for BLOCKED.md and high-severity issues
2. Get next pending task (respects dependency order)
3. Run `/powermode @<task-prd-path>` in fresh session
4. Verify task was marked done, check for new blockers
5. Resumable — reads status.json each iteration

### `ralph verify`
Per verification unit (auto-detected scope):
1. **Verify** — static analysis, build, tests, stub detection, security
2. **Fix** (if FAIL) — fix BLOCKER + MAJOR issues, re-verify
3. **Simplify** — code reuse, quality pass
4. **Final verify** — regression check

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RALPH_RESEARCH_MODEL` | opus | Research session model |
| `RALPH_PRD_MODEL` | sonnet | PRD writing model |
| `RALPH_REVIEW_MODEL` | sonnet | Review session model |
| `RALPH_IMPLEMENT_MODEL` | opus | Implementation model |
| `RALPH_VERIFY_MODEL` | sonnet | Verification model |
| `RALPH_FIX_MODEL` | opus | Fix session model |
| `RALPH_MAX_BUDGET` | 10.00 | Per-session cost cap |
| `RALPH_MAX_ITERATIONS` | 50 | Max implementation iterations |
| `RALPH_MAX_VERIFY_ITERS` | 3 | Max verify loops per unit |

## Logs

Stored in `.powermode/ralph/`:
```
plan-<slug>-<timestamp>.log
implement-<slug>-<timestamp>.log
verify-<slug>-<timestamp>.log
```

## Requirements

- `claude` CLI on PATH
- `python3` on PATH
- `git` on PATH
- `--dangerously-skip-permissions` enabled (unattended operation)

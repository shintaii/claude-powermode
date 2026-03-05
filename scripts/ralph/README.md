# RALPH Loop

Fresh-context loop orchestrator for Powermode. Runs each task in a clean Claude session to avoid context window degradation on large projects.

## Setup

```bash
ln -s <plugin-path>/scripts/ralph/ralph.sh /usr/local/bin/ralph
```

## Usage

```bash
# 1. Plan interactively with /pm-plan, then review PRDs with ralph
ralph plan <project-slug>

# 2. Implement PRDs one by one in fresh sessions
ralph implement <project-slug>
ralph implement <project-slug> --feature 01-auth

# 3. Verify: iterative verify + fix + simplify
ralph verify <project-slug>
ralph verify <project-slug> --scope feature --feature 01-auth

# 4. Check progress
ralph status <project-slug>
```

## How It Works

### `ralph plan <slug>`

Assumes you already ran `/pm-plan` interactively to create the project + PRDs.

Reviews each PRD in a fresh session — cross-checks against original goal, project.md, and sibling PRDs. Fixes gaps or contradictions in place.

> **Tip:** Save your original goal for context: `echo "Build a payment system" > .powermode/projects/<slug>/goal.md`

### `ralph implement <slug>`

Loop until all tasks done or blocked:

1. Check for `BLOCKED.md` and high-severity issues
2. Get next pending task (respects dependency order from feature READMEs)
3. Run `/powermode @<task-prd-path>` in a fresh session with system context injected
4. Verify task was marked done; repair status.json drift from README if needed
5. Resumable — reads `status.json` each iteration

### `ralph verify <slug>`

Per verification unit (feature or project scope):

1. **Verify** — static analysis, build, tests, stub detection
2. **Fix** (if FAIL) — fix BLOCKER + MAJOR issues, re-verify (max 3 loops)
3. **Simplify** — code reuse + quality pass
4. **Final verify** — regression check

Task-level verification is handled by powermode during implementation — ralph verify runs cross-cutting checks at feature or project level.

## Flags

| Flag | Description |
|------|-------------|
| `--verbose`, `-v` | Show prompts and truncated Claude output |
| `--live`, `-l` | Stream Claude's output in real-time |
| `--model X` | Override the model for this command |
| `--budget X` | Per-session cost cap (default: $10.00) |
| `--max-iters N` | Safety valve on iteration count |
| `--feature X` | Filter to a specific feature (implement/verify) |
| `--scope feature\|project` | Verify scope (default: auto-detected by feature count) |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RALPH_REVIEW_MODEL` | sonnet | PRD review model |
| `RALPH_IMPLEMENT_MODEL` | opus | Implementation model |
| `RALPH_VERIFY_MODEL` | sonnet | Verification model |
| `RALPH_FIX_MODEL` | opus | Fix session model |
| `RALPH_MAX_BUDGET` | 10.00 | Per-session cost cap |
| `RALPH_MAX_ITERATIONS` | 50 | Max implementation iterations |
| `RALPH_MAX_VERIFY_ITERS` | 3 | Max verify loops per unit |
| `RALPH_VERBOSE` | 0 | Set to 1 for verbose output |
| `RALPH_LIVE` | 0 | Set to 1 to stream Claude output live |

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

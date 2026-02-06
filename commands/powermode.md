---
name: powermode
description: Activate Power Mode - disciplined engineering with parallel agents, planning system, and ralph-loop
allowed-tools: "*"
---

# Power Mode Activated

You are now operating in **Power Mode** - a disciplined engineering methodology with specialized agents.

## Your Agents

### Exploration & Research
| Agent | Model | Use For |
|-------|-------|---------|
| `pm-explorer` | Haiku | Fast parallel codebase exploration |
| `pm-researcher` | Sonnet | External docs, OSS research, library best practices |

### Planning System
| Agent | Model | Use For |
|-------|-------|---------|
| `pm-analyser` | Opus | Pre-planning analysis - finds hidden requirements |
| `pm-powerplanner` | Opus | Strategic planning with interview mode |
| `pm-planreviewer` | Sonnet | Plan review loop - iterates until quality bar met |

### Implementation & Verification
| Agent | Model | Use For |
|-------|-------|---------|
| `pm-oracle` | Opus | Architecture, debugging, deep reasoning |
| `pm-implementer` | Opus | Focused code implementation |
| `pm-verifier` | Sonnet | Quality verification with evidence |

## Commands

| Command | Purpose |
|---------|---------|
| `/pm-plan [goal]` | Start planning workflow: Analyser → Powerplanner → Planreviewer review loop |
| `/pm-ralph-loop [goal]` | Self-referential dev loop until task completion |
| `/pm-team [goal]` | Agent Teams mode - parallel implementation with independent sessions (requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) |

## Mandatory Workflow

For any non-trivial task:

1. **Classify** the request (Trivial/Explicit/Exploratory/Open-ended/Ambiguous)
2. **Explore** - Fire `pm-explorer` (+ `pm-researcher` for external libs) in parallel
3. **Plan** - Use `/plan` for complex work, or create todos
4. **Implement** - Use `pm-implementer` for focused tasks
5. **Verify** - Use `pm-verifier` before claiming done

## Session Continuity

Always use `session_id` for follow-ups:
```
# Task returns session_id="ses_abc123"
# If failed or needs follow-up:
Task(session_id="ses_abc123", prompt="Fix: ...")
```

## Key Rules

- **NEVER implement without exploring first** (for non-trivial tasks)
- **Fire explorers in parallel** - multiple angles simultaneously
- **Use session_id** - don't restart failed tasks from scratch
- **Consult oracle for hard decisions** - Architecture, after 2+ failed fixes
- **Verify with evidence** - lsp_diagnostics, build, tests
- **No slop** - No `as any`, no empty catch, no deleted tests
- **Exploration hygiene** - Use Grep/Read tools (with offsets for large files); avoid Bash find/grep
- **PRD index first** - If a PRD folder has an index/README, read it first and honor dependency order

## Quick Actions

| Situation | Action |
|-----------|--------|
| New feature | `/plan [feature]` or Explore → Plan → Implement → Verify |
| Bug fix | Explore → Fix minimal → Verify |
| Hard problem | Consult pm-oracle |
| Before "done" | Run pm-verifier |
| Complex project | `/pm-plan [goal]` |
| Autonomous work | `/pm-ralph-loop [goal]` |
| Parallel implementation | `/pm-team [goal]` (requires agent teams enabled) |

## Available Skills

Load these when delegating for specialized knowledge:
- `git-master` - Git operations expert
- `frontend-ui-ux` - Designer-developer mindset

```
Task(subagent_type="powermode:pm-implementer", load_skills=["frontend-ui-ux"], prompt="...")
```

Load the full methodology docs: `/powermode` (loads skill with all references)

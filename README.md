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

---

## Quick Start: Which Command Do I Use?

| I have... | I want... | Use |
|-----------|-----------|-----|
| An idea/goal | A detailed plan + PRD files | `/pm-plan add user authentication` |
| An existing document (spec, issue, PRD) | Split into implementable PRDs | `/pm-plan @path/to/doc.md` |
| An existing PRD folder | See structure and next steps | `/pm-plan @.powermode/prds/feature/` |
| A PRD ready to implement | Parallel team implementation | `/pm-team @.powermode/prds/feature/README.md` |
| Started work, want methodology | Enable powermode workflow | `/powermode` |
| Doubt about current progress | Check alignment with plan | `/pm-checkpoint` |

---

## Commands Explained

### `/powermode` - Activate the Methodology

**When:** You want disciplined engineering on any task.

**What it does:**
- Reminds you of the explore → plan → implement → verify workflow
- Lists available agents and when to use them
- Enables all guardrails

**Example:**
```
/powermode
> Now help me refactor the auth module
```

---

### `/pm-plan [goal]` - Create a Plan from Scratch

**When:** You have an idea or goal but no written spec.

**Input:** A description of what you want to build.

**Workflow:**
```
1. ANALYSER      → Finds hidden requirements, ambiguities
2. POWERPLANNER  → Creates comprehensive plan (may interview you)
3. PLANREVIEWER  → Reviews until quality bar met (max 3 iterations)
4. PRD FILES     → Writes plan to .powermode/prds/<feature>/
5. READY         → Suggests next command
```

**Output:** A folder with:
- `README.md` - Index with dependency order
- `01-<title>.md`, `02-<title>.md`, ... - Numbered PRDs

**Example:**
```
/pm-plan add multi-tenancy support to the application
```

---

### `/pm-plan` - Unified Planning (auto-detects input)

`/pm-plan` automatically detects what you give it:

| Input | Mode | Example |
|-------|------|---------|
| Plain text goal | Plans from scratch | `/pm-plan add user authentication` |
| `@` document reference | Transforms doc into PRDs | `/pm-plan @docs/DJANGO_INTEGRATION.md` |
| `@` folder reference | Shows existing PRD structure | `/pm-plan @.powermode/prds/auth/` |

---

### `/pm-checkpoint` - Manual Progress Check

**When:** Mid-implementation, you want to verify you're on track.

**What it does:**
- Compares current state to the plan
- Identifies drift or missed steps
- Suggests corrections

**Example:**
```
/pm-checkpoint
```

---

## Agents Reference

Use these with the `Task` tool for specific purposes:

### Exploration

| Agent | Model | Use When |
|-------|-------|----------|
| `pm-explorer` | Haiku | Finding files, patterns, understanding codebase structure |
| `pm-researcher` | Sonnet | Looking up external library docs, API references, best practices |

### Planning

| Agent | Model | Use When |
|-------|-------|----------|
| `pm-analyser` | Opus | Pre-planning: find hidden requirements, ambiguities |
| `pm-powerplanner` | Opus | Create comprehensive work plans |
| `pm-planreviewer` | Sonnet | Review plans for gaps, iterate until solid |

### Implementation

| Agent | Model | Use When |
|-------|-------|----------|
| `pm-oracle` | Opus | Hard architecture decisions, debugging stuck problems |
| `pm-implementer` | Opus | Focused code changes (single task at a time) |
| `pm-verifier` | Sonnet | Verify work with evidence (tests, build, lsp) |

---

## Typical Workflows

### New Feature (from scratch)

```
1. /pm-plan add payment processing
2. Review generated PRDs in .powermode/prds/payment/
3. /pm-team @.powermode/prds/payment/README.md
4. (automatic) Parallel implementation with verification
```

### Feature from Existing Spec

```
1. /pm-plan @docs/payment-spec.md
2. Review generated PRDs
3. /pm-team @.powermode/prds/payment/README.md
```

### Quick Fix (no planning needed)

```
1. /powermode
2. "Fix the null pointer in auth.py line 42"
3. (uses pm-explorer → fix → pm-verifier automatically)
```

### Research Task

```
1. /powermode
2. "How does the payment module handle refunds?"
3. (uses pm-explorer, no implementation)
```

---

## Automatic Behaviors (Hooks)

These run automatically - you don't invoke them:

| Hook | What It Does |
|------|--------------|
| **Stop validator** | Blocks exit if todos incomplete (3 attempts = escape hatch) |
| **PRD enforcement** | Blocks exit if referenced PRD wasn't updated |
| **Context monitor** | Tracks token usage, warns at 70% |
| **Session recovery** | Saves/restores state across compaction |
| **CLAUDE.md enforcer** | Reminds you of project rules |
| **Comment checker** | Flags unnecessary comments (agent-scoped to pm-implementer) |
| **Delegation enforcer** | Blocks direct Edit/Write in Power Mode (must use pm-implementer) |
| **Task containment** | Injects scope constraints into subagent prompts |
| **Implementer lifecycle** | Creates/cleans up implementer sessions via SubagentStart/Stop |
| **Subagent context** | Injects role reminders when any pm-* agent spawns |
| **Workflow reinforcer** | Reminds about Power Mode methodology after user answers questions (prompt-based) |
| **Edit error recovery** | Provides contextual recovery guidance on Edit failures (prompt-based) |
| **Task retry guidance** | Analyzes Task errors and suggests correct agents (prompt-based) |

---

## PRD File Structure

Powermode-generated PRDs are stored separately from user files:

```
.powermode/prds/
├── index.json                 # Tracks all PRD sets with metadata
├── auth-feature/
│   ├── README.md              # Index: purpose, dependency order, table of PRDs
│   ├── 01-database-schema.md  # First PRD (no dependencies)
│   ├── 02-api-endpoints.md    # Second PRD (depends on 01)
│   └── 03-frontend-ui.md      # Third PRD (depends on 02)
└── payment-v2/
    ├── README.md
    └── 01-stripe-integration.md
```

**Why separate?** User PRDs (from external tools, manual creation) stay in their own folders. Powermode output never conflicts.

**Git tracking:** `.powermode/prds/` is committed to git. Runtime files (`.powermode/*.json`) are gitignored.

Each PRD contains:
- Clear scope and requirements
- Acceptance criteria
- Test focus (what to verify)
- Dependencies on other PRDs

## How It Works

- **Context tracking** writes `.powermode/context-state.json` in the current workspace.
- **Stop hook** reads the session transcript and blocks stop if todos are pending/in_progress.
- **Escape hatch** auto-approves after 3 consecutive stop attempts with a warning.
- **Session recovery** stores `.powermode/recovery.json` on SessionEnd/PreCompact and restores on SessionStart.
- **PRD enforcement** blocks stop when referenced PRDs were not updated.

## Updating

```bash
claude plugin update powermode@claude-powermode
```

### Important: hooks.json auto-load

Claude Code auto-loads `hooks/hooks.json`. Do NOT reference it in `plugin.json` or you will get:

```
Hook load failed: Duplicate hooks file detected
```

## Manual Hook Tests

### Stop hook

```bash
echo '{"cwd":"/tmp","transcript_path":"/path/to/session.jsonl"}' | python3 hooks/stop-validator.py
```

### Context monitor

```bash
echo '{"session_id":"test","cwd":"/tmp","tool_name":"Bash","tool_input":{},"tool_response":{}}' | python3 hooks/context-monitor.py
```

## Troubleshooting

### PostToolUse hook error spam

- Cause: invalid schema in PostToolUse output
- Fix: ensure `hookSpecificOutput.for PostToolUse` is used

### Stop hook never blocks

- Cause: wrong transcript parsing
- Fix: `stop-validator.py` must read `toolUseResult.newTodos` from JSONL transcripts

### Duplicate hooks file

- Cause: `plugin.json` includes `"hooks": "./hooks/hooks.json"`
- Fix: remove that key (hooks auto-load)

## Version Notes

- **2.7.0**: SubagentStart/Stop lifecycle for implementer sessions, agent-scoped comment-checker, prompt-based hooks (workflow-reinforcer, edit-error-recovery, task-retry-guidance), subagent context injection for all pm-* agents
- **2.8.0**: Merge pm-prdmaker into pm-plan (unified planning with auto-detect), add /pm-team command for agent teams
- **2.6.15**: Fix pm-prdmaker workflow (explicit Task calls), pm-plan now outputs PRD files, expanded README
- **2.6.14**: Add delegation-enforcer hook
- **2.6.13**: Persist powermode activation across prompts
- **2.6.10**: Add PRD NOTES.md tracking, fix stop-hook false positives (require @ prefix)
- **2.6.8**: Open source release, GitHub marketplace support
- **2.6.5**: PRD maker delegates writing to sub-agents (context preservation)
- **2.6.4**: All hooks use proper output schemas (8 hooks fixed)
- **2.6.3**: PRD maker always applies split rules
- **2.6.2**: PRD index auto-inject for @prompt references
- **2.6.1**: PRD index auto-inject on PRD read
- **2.6.0**: PRD maker command + PRD index guidance
- **2.5.6**: PostToolUse JSON output for rules/task hooks
- **2.5.5**: stop hook PRD enforcement + exploration hygiene notes
- **2.5.4**: removed duplicate hooks reference in plugin.json
- **2.5.3**: PostToolUse output schema fix
- **2.5.2**: stop hook improvements + escape hatch

## Credits

Heavily inspired by [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) - thank you for the foundational ideas.

## License

MIT - see [LICENSE](LICENSE)

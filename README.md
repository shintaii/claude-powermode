# Powermode Plugin

Disciplined engineering workflow for Claude Code: consistent exploration, planning, implementation, verification, and guardrails against drift. This plugin turns the "power mode" methodology into concrete hooks, commands, and skills.

## Installation

### Via GitHub Marketplace (Recommended)

Add this repository as a plugin marketplace, then install:

```bash
# Add the marketplace
claude plugin marketplace add https://github.com/shintaii/claude-powermode

# Install the plugin
claude plugin install powermode

# Verify
claude plugin list | grep powermode
```

### Manual Installation

Clone and copy to your local plugins:

```bash
git clone https://github.com/shintaii/claude-powermode.git
mkdir -p ~/.claude/plugins/cache/local-plugins/powermode/
cp -r claude-powermode/* ~/.claude/plugins/cache/local-plugins/powermode/
cp -r claude-powermode/.claude-plugin ~/.claude/plugins/cache/local-plugins/powermode/
```

## Goals

- Enforce a structured workflow (explore → plan → implement → verify)
- Prevent unfinished work (todo enforcement + stop hook)
- Preserve context across compaction and sessions
- Add guardrails for risky actions and comment hygiene
- Provide reusable specialist agents for research, planning, and verification

## What It Does

### Hooks (automatic)

- **PostToolUse**
  - `context-monitor.py`: tracks tool call count and estimated token usage
  - `comment-checker.py`: ensures comments are necessary
  - `task-retry-guidance.py`: suggests recovery steps after Task retries
  - `rules-injector.py`: injects repo rules after file reads
  - `plan-checkpoint-validator.py`: checks plan/todo drift after TodoWrite
- **PostToolUseFailure**
  - `edit-error-recovery.py`: guidance for Edit failures
- **UserPromptSubmit**
  - `claude-md-enforcer.py`: enforces CLAUDE.md rules
  - `keyword-detector.py`: detects key terms and injects guidance
  - `context-summary-injector.py`: injects context when tool usage is high
- **Stop**
  - `stop-validator.py`: blocks exit if todos are incomplete (with escape hatch)
- **PreCompact / SessionEnd / SessionStart**
  - `session-state-saver.py`: saves state before compaction/end
  - `session-state-restorer.py`: restores state after compaction

### Commands

- `/powermode`: activate methodology
- `/pm-plan`: structured planning loop (Metis → Prometheus → Momus)
- `/pm-ralph-loop`: self-referential dev loop
- `/pm-checkpoint`: manual drift check
- `/pm-prdmaker`: create or split PRDs (adds index README when multiple)

### Agents

- **pm-explorer** (Haiku): fast codebase search
- **pm-librarian** (Sonnet): external docs / library research
- **pm-metis / pm-prometheus / pm-momus**: plan creation and review
- **pm-oracle** (Opus): architecture & deep reasoning
- **pm-implementer** (Opus): code changes
- **pm-verifier** (Sonnet): verification with evidence

## How It Works

- **Context tracking** writes `.powermode/context-state.json` in the current workspace.
- **Stop hook** reads the session transcript and blocks stop if todos are pending/in_progress.
- **Escape hatch** auto-approves after 3 consecutive stop attempts with a warning.
- **Session recovery** stores `.powermode/recovery.json` on SessionEnd/PreCompact and restores on SessionStart.
- **PRD enforcement** blocks stop when referenced PRDs were not updated.

## Updating

```bash
claude plugin update powermode
```

Or pull the latest and reinstall manually.

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

## License

MIT - see [LICENSE](LICENSE)

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **powermode** Claude Code plugin - a disciplined engineering workflow with hooks, commands, agents, and skills.

**Distribution:** GitHub Marketplace at `shintaii/claude-powermode`

## Plugin Structure

```
powermode/
├── .claude-plugin/plugin.json  # Manifest (version, components)
├── hooks/hooks.json            # Hook registrations (auto-loaded, NOT in plugin.json)
├── hooks/*.py                  # Python hook scripts
├── agents/*.md                 # Agent definitions (explorer, researcher, oracle, etc.)
├── commands/*.md               # Slash commands (/powermode, /pm-plan, etc.)
├── skills/*/SKILL.md           # Skill definitions
└── .powermode/                 # Runtime state (context-state.json, recovery.json)
```

## Development Commands

```bash
# Test a hook manually:
echo '{"cwd":"/tmp","transcript_path":"..."}' | python3 hooks/stop-validator.py

# Verify installation:
claude plugin list | grep -A3 powermode
```

## Hook Development Rules

### Output Schemas (critical)
- **PostToolUse/UserPromptSubmit/SessionStart**: `{"continue": true, "hookSpecificOutput": {"hookEventName": "<event>", "additionalContext": "..."}}`
- **PreToolUse**: `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "updatedInput": {...}}}`
- **Stop**: `{"decision": "approve|block", "reason": "..."}`
- **PostToolUseFailure**: `{"continue": true, "hookSpecificOutput": {"hookEventName": "PostToolUseFailure", "additionalContext": "..."}}`
- Always output valid JSON on ALL code paths (including early returns and errors)
- Always `sys.exit(0)` - never crash or block on errors

### Common Pitfalls
- **Duplicate hooks file**: Do NOT add `"hooks": "./hooks/hooks.json"` to plugin.json - it auto-loads
- **Import paths**: Use `${CLAUDE_PLUGIN_ROOT}` for portable paths in hooks.json
- **Transcript parsing**: Read `toolUseResult.newTodos` from JSONL, not raw text

### Hook Validation
After making hook changes, use:
```
plugin-dev:plugin-validator  # Full plugin validation
plugin-dev:skill-reviewer    # Review specific implementations
```

## Agent Model Assignment

| Agent | Model | Purpose |
|-------|-------|---------|
| pm-explorer | haiku | Fast codebase search |
| pm-researcher | sonnet | External docs research |
| pm-analyser/powerplanner/planreviewer | sonnet | Planning loop |
| pm-oracle | opus | Architecture decisions |
| pm-implementer | opus | Code changes |
| pm-verifier | sonnet | Verification with evidence |

## Key Behaviors

- **Stop hook**: Blocks exit if todos pending/in_progress. Escape hatch after 3 attempts.
- **PRD enforcement**: Blocks stop if referenced PRD files weren't updated.
- **Context tracking**: Writes `.powermode/context-state.json` with tool counts and token estimates.
- **Session recovery**: Saves/restores state on PreCompact/SessionEnd/SessionStart.
- **PRD maker**: Delegates PRD writing to sub-agents sequentially (max 2 per batch).

## Plugin Development Skills

Use these skills when modifying this plugin:

| Skill | When to Use |
|-------|-------------|
| `plugin-dev:plugin-validator` | After structural changes - validates entire plugin |
| `plugin-dev:skill-reviewer` | After modifying skills or agents |
| `plugin-dev:plugin-structure` | Scaffolding plugins, directory layout, plugin.json |
| `plugin-dev:hook-development` | Creating/modifying hooks (PreToolUse, PostToolUse, Stop, etc.) |
| `plugin-dev:agent-development` | Creating agents, system prompts, model assignment |
| `plugin-dev:skill-development` | Creating skills, SKILL.md structure, progressive disclosure |
| `plugin-dev:command-development` | Creating slash commands, YAML frontmatter, arguments |
| `plugin-dev:plugin-settings` | Using `.local.md` files for plugin configuration |
| `plugin-dev:mcp-integration` | Adding MCP servers to plugins |

### Development Workflow

1. Make changes
2. Run `plugin-dev:plugin-validator` to validate
3. Test hooks manually: `echo '{"cwd":"/tmp"}' | python3 hooks/<hook>.py`
4. Bump version in `.claude-plugin/plugin.json`
5. Commit, tag, and push (see Release Workflow)

### Release Workflow

```bash
# 1. Bump version in plugin.json
# 2. Commit and tag
git add -A && git commit -m "Release vX.Y.Z: <description>"
git tag vX.Y.Z
git push origin main vX.Y.Z
```

Users update via: `claude plugin update powermode@claude-powermode`

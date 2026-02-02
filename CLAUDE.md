# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **powermode** Claude Code plugin - a disciplined engineering workflow with hooks, commands, agents, and skills. Current version: 2.6.8.

## Plugin Structure

```
powermode/
├── .claude-plugin/plugin.json  # Manifest (version, components)
├── hooks/hooks.json            # Hook registrations (auto-loaded, NOT in plugin.json)
├── hooks/*.py                  # Python hook scripts
├── agents/*.md                 # Agent definitions (explorer, librarian, oracle, etc.)
├── commands/*.md               # Slash commands (/powermode, /pm-plan, etc.)
├── skills/*/SKILL.md           # Skill definitions
└── .powermode/                 # Runtime state (context-state.json, recovery.json)
```

## Development Commands

```bash
# Bump version in plugin.json, then copy to cache:
cp -r ./* ~/.claude/plugins/cache/local-plugins/powermode/<version>/
cp -r ./.claude-plugin ~/.claude/plugins/cache/local-plugins/powermode/<version>/

# Verify installation:
claude plugin list | grep -A3 powermode

# Test a hook manually:
echo '{"cwd":"/tmp","transcript_path":"..."}' | python3 hooks/stop-validator.py
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
| pm-librarian | sonnet | External docs research |
| pm-metis/prometheus/momus | sonnet | Planning loop |
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
4. Bump version in plugin.json
5. Deploy: `cp -r ./* ~/.claude/plugins/cache/local-plugins/powermode/<version>/`

### Release Workflow

On every version bump:
1. Update version in `.claude-plugin/plugin.json`
2. Commit changes
3. **Tag the release**: `git tag v<version> && git push origin v<version>`
4. Update remote: `git push origin main`

Example:
```bash
# After bumping to 2.6.9
git add -A && git commit -m "Release v2.6.9: <description>"
git tag v2.6.9
git push origin main v2.6.9
```

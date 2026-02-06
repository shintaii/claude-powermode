---
name: pm-team
description: Activate Agent Teams mode for parallel implementation with multiple independent Claude Code sessions
allowed-tools: "*"
---

# Agent Teams Mode

You are orchestrating a **team of independent Claude Code sessions** for parallel implementation.

## Pre-Flight Check

**FIRST**: Check if agent teams is enabled by looking at your available tools. If you have access to `TeamCreate`, `SendMessage`, `TaskCreate`, `TaskList`, `TaskGet`, `TaskUpdate`, and `TaskOutput` tools, agent teams is enabled.

If agent teams is NOT available, tell the user:

> Agent teams is not enabled. To enable it:
> 1. Add to `~/.claude/settings.json`: `{"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}}`
> 2. Or set: `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
> 3. Restart Claude Code
>
> Falling back to standard powermode subagent workflow.

Then fall back to the standard `/powermode` workflow using subagents.

## Goal

```
$ARGUMENTS
```

## When to Use Teams vs Subagents

| Use Teams For | Keep Subagents For |
|---|---|
| 3+ independent implementation tasks | Quick exploration (pm-explorer) |
| Work spanning different files/modules | External research (pm-researcher) |
| Parallel feature development | Planning pipeline (analyser/planner/reviewer) |
| Large refactoring across modules | Architecture decisions (pm-oracle) |

**Teams are for PARALLEL IMPLEMENTATION. Exploration and planning stay as subagents.**

## Workflow

### Phase 1: Explore & Plan (Subagents - as normal)

Use standard powermode subagents for exploration and planning:

```
Task(subagent_type="powermode:pm-explorer", run_in_background=true, prompt="...")
Task(subagent_type="powermode:pm-explorer", run_in_background=true, prompt="...")
```

Break the goal into **independent, file-scoped tasks** that can be parallelized.

### Phase 2: Create Team

```
TeamCreate(team_name="pm-<feature-slug>", description="<goal summary>")
```

### Phase 3: Create Tasks

Create tasks for the shared task list. Each task should:
- Own specific files (no overlap between tasks)
- Be self-contained with clear acceptance criteria
- Include file paths, patterns to follow, and test requirements

```
TaskCreate(subject="Implement X", description="...", activeForm="Implementing X")
TaskCreate(subject="Implement Y", description="...", activeForm="Implementing Y")
TaskCreate(subject="Add tests for X", description="...", activeForm="Testing X")
```

Set dependencies where needed:
```
TaskUpdate(taskId="3", addBlockedBy=["1"])  // Tests wait for implementation
```

### Phase 4: Spawn Teammates

Spawn implementation teammates. Each gets assigned specific tasks.

```
Task(
  subagent_type="powermode:pm-implementer",
  team_name="pm-<feature-slug>",
  name="impl-1",
  prompt="You are an implementer on a powermode team. Check TaskList for your assigned tasks. Work through them in order. Follow powermode discipline: explore files before editing, verify your changes compile/pass tests. When done with a task, mark it completed and check for the next one."
)
```

**Guidelines for teammate spawning:**
- **2-4 teammates** is the sweet spot (more = more coordination overhead + cost)
- Use **Sonnet** model for teammates to manage cost: `Task(..., model="sonnet")`
- Each teammate should own **different files** to avoid conflicts
- Assign tasks via `TaskUpdate(taskId="1", owner="impl-1")`

### Phase 5: Monitor & Coordinate

As team lead, your job is coordination:

1. **Monitor progress** via `TaskList` - check task statuses
2. **Unblock** teammates via `SendMessage` if they get stuck
3. **Reassign** tasks if a teammate is blocked: `TaskUpdate(taskId="X", owner="impl-2")`
4. **Don't implement yourself** - delegate to teammates or subagents

Messages from teammates arrive automatically. Respond with:
```
SendMessage(type="message", recipient="impl-1", content="...", summary="...")
```

### Phase 6: Verify & Cleanup

After all tasks complete:

1. **Run pm-verifier** as a subagent to check the combined work:
   ```
   Task(subagent_type="powermode:pm-verifier", prompt="Verify the implementation of <goal>. Check: builds, tests pass, no regressions.")
   ```

2. **Shutdown teammates**:
   ```
   SendMessage(type="shutdown_request", recipient="impl-1", content="All tasks complete")
   SendMessage(type="shutdown_request", recipient="impl-2", content="All tasks complete")
   ```

3. **Delete team** after all teammates confirm shutdown:
   ```
   TeamDelete()
   ```

## Cost Awareness

Agent teams are **significantly more expensive** than subagents:
- Each teammate is a full Claude Code session with its own context
- Broadcasts cost N messages (N = team size)
- Use `SendMessage` (DM) over `broadcast` for most communication
- Prefer Sonnet model for implementation teammates
- Only use teams when you genuinely have 3+ parallel tasks

## Anti-Patterns

- **Don't use teams for sequential work** - use subagents
- **Don't spawn more than 4 teammates** - coordination overhead outweighs benefit
- **Don't have teammates edit the same files** - causes conflicts
- **Don't implement as lead** - delegate everything
- **Don't forget to cleanup** - always TeamDelete when done

## Quick Reference

| Action | Tool |
|--------|------|
| Create team | `TeamCreate(team_name="pm-x")` |
| Add task | `TaskCreate(subject="...", description="...")` |
| Assign task | `TaskUpdate(taskId="1", owner="impl-1")` |
| Check progress | `TaskList()` |
| Message teammate | `SendMessage(type="message", recipient="impl-1", ...)` |
| Shutdown teammate | `SendMessage(type="shutdown_request", recipient="impl-1", ...)` |
| Cleanup team | `TeamDelete()` |

---

**Start with Phase 1: Explore the goal using subagents, then break it into parallel tasks.**

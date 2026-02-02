---
name: pm-ralph-loop
description: Start a self-referential development loop that continues until task completion. Named after Anthropic's Ralph plugin.
allowed-tools: "*"
---

# Ralph Loop Activated

You are now in a **Ralph Loop** - a self-referential development loop that continues until the task is fully complete.

## How Ralph Loop Works

1. **Work continuously** toward the goal: `$ARGUMENTS`
2. **Keep going** until the task is 100% complete
3. **When truly done**, output: `<promise>DONE</promise>`
4. If you stop without the promise tag, the loop will automatically continue

## Your Goal

```
$ARGUMENTS
```

## Loop Rules

### Continue Working When:
- Task is not complete
- There are still todos to finish
- Tests are failing
- Build is broken
- Verification hasn't passed

### Output `<promise>DONE</promise>` Only When:
- All acceptance criteria met
- All tests pass (or pre-existing failures documented)
- Build succeeds
- pm-verifier confirms completion
- No remaining todos

## Workflow in Ralph Loop

Use the full Power Mode methodology:
1. Explore with `pm-explorer` (parallel) to understand codebase
2. Plan with todos for multi-step work
3. Implement with `pm-implementer` 
4. Verify with `pm-verifier`
5. If issues found, fix them and verify again

## Session Continuity

If something fails:
- Use `session_id` from the failed Task to continue: `Task(session_id="...", prompt="Fix: ...")`
- Don't restart from scratch - continue where you left off

## When To Stop Without Completion

Only output completion without `<promise>DONE</promise>` if:
- You hit a blocker that requires user input
- You need clarification that blocks progress
- You've tried 3+ times to fix the same issue

In these cases, clearly explain what's blocking and what you need.

## Anti-Patterns

- **Don't claim done prematurely** - Verify first
- **Don't skip verification** - Run pm-verifier
- **Don't ignore failing tests** - Fix them or document pre-existing
- **Don't leave todos incomplete** - Finish them all

---

**Start working on the goal now. Keep going until it's truly done.**

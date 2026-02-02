# Verification Checklist

**NOTHING is "done" without PROOF it works.**

## Pre-Implementation: Define Success

BEFORE writing ANY code, define what "working" means:

| Criteria Type | Description | Example |
|---------------|-------------|---------|
| **Functional** | What specific behavior must work | "Button click triggers API call" |
| **Observable** | What can be measured/seen | "Console shows 'success', no errors" |
| **Pass/Fail** | Binary, no ambiguity | "Returns 200 OK" not "should work" |

---

## During Implementation: Incremental Checks

### After Each Logical Change

1. **Save the file** - Let LSP process it
2. **Check lsp_diagnostics** - Zero new errors on changed files
3. **If error introduced** - Fix immediately, don't accumulate

### After Each Todo Item

1. Run relevant tests (if they exist)
2. Quick manual check if applicable
3. Mark todo complete only after verification

---

## Post-Implementation: Full Verification

### Mandatory Evidence

| Action | Required Evidence | How to Get It |
|--------|-------------------|---------------|
| File edit | Clean diagnostics | `lsp_diagnostics` on changed files |
| New code | No type errors | `lsp_diagnostics` shows 0 errors |
| Build | Exit code 0 | Run build command, check output |
| Tests | All pass | Run test command, check output |
| Feature | Works as expected | Describe what you tested |

### Verification Workflow

```
1. lsp_diagnostics on ALL changed files
   └── Any errors? Fix them first.

2. Run build (if project has build step)
   └── npm run build / cargo build / etc.
   └── Exit code must be 0

3. Run tests (if tests exist)
   └── npm test / pytest / cargo test
   └── All must pass (or note pre-existing failures)

4. Manual verification (for features)
   └── Actually use the feature
   └── Describe what you did and saw
```

---

## Evidence Template

When reporting completion, include:

```
## Verification Evidence

### Diagnostics
- [file1.ts]: 0 errors
- [file2.ts]: 0 errors

### Build
- Command: `npm run build`
- Result: Exit code 0, no errors

### Tests
- Command: `npm test`
- Result: 15 passed, 0 failed

### Manual Verification
- [What I did]: [What I observed]
- [Specific test case]: [Result]
```

---

## Failure Handling

### If Verification Fails

1. **Don't panic** - This is expected sometimes
2. **Read the error** - Actually understand what went wrong
3. **Fix the root cause** - Not the symptom
4. **Re-verify** - Run full verification again

### After 3 Consecutive Failures

**STOP. Do not continue.**

1. **Revert** to last known working state
2. **Document** what you tried:
   - Attempt 1: [What you did, what failed]
   - Attempt 2: [What you did, what failed]
   - Attempt 3: [What you did, what failed]
3. **Ask user** for guidance

```
I've attempted to fix this 3 times without success.

**Attempts:**
1. [Description] - Failed because [reason]
2. [Description] - Failed because [reason]
3. [Description] - Failed because [reason]

**Current state:** Reverted to working state.

**Options:**
A) [Alternative approach 1]
B) [Alternative approach 2]
C) You provide more context about [specific thing]

How would you like to proceed?
```

---

## Anti-Patterns (NEVER DO)

| Violation | Why It's Wrong |
|-----------|----------------|
| "It should work now" | No evidence. Run it. |
| "I added the tests" | Did they pass? Run them. |
| "Fixed the bug" | How do you know? What did you test? |
| "Implementation complete" | Did you verify against success criteria? |
| Skipping test execution | Tests exist to be RUN |
| Claiming done with errors | Fix them first |
| Deleting failing tests | Fix the code, not the tests |

---

## Quick Checklist

Before saying "done", verify:

- [ ] `lsp_diagnostics` clean on all changed files
- [ ] Build passes (if applicable)
- [ ] Tests pass (if applicable)
- [ ] Feature actually works (if applicable)
- [ ] Pre-existing issues noted (if any)
- [ ] Evidence included in response

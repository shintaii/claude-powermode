# Exploration Prompts & Templates

Use these templates to systematically explore a codebase before implementation.

## Codebase Assessment

### Quick Health Check

Run these searches to assess codebase state:

```bash
# Check for linting/formatting config
ls -la .eslintrc* .prettierrc* tsconfig.json pyproject.toml setup.cfg

# Check for test infrastructure
ls -la *test* *spec* pytest.ini jest.config* vitest.config*

# Check git history health
git log --oneline -20
```

### Pattern Discovery

**Find similar implementations:**
```
# If adding a new API endpoint, find existing endpoints:
Grep: "export.*function.*Handler" or "app.get\(" or "@app.route"

# If adding a new component, find existing components:
Glob: "**/components/**/*.tsx" or "**/components/**/*.vue"

# If adding a new model/type, find existing ones:
Grep: "interface.*{" or "type.*=" or "class.*{"
```

**Check for established patterns:**
```
# Error handling patterns
Grep: "catch|throw|Error|try {"

# Logging patterns
Grep: "console\.|logger\.|log\("

# Validation patterns  
Grep: "validate|schema|zod|yup|joi"
```

---

## Feature Implementation Exploration

### Before Adding a Feature

1. **Find related code:**
   - Search for keywords from the feature
   - Find files in the same domain
   - Check for existing partial implementations

2. **Understand the architecture:**
   - Where does similar functionality live?
   - What's the data flow?
   - What dependencies are used?

3. **Check test patterns:**
   - How are similar features tested?
   - What mocking patterns are used?
   - What's the test file structure?

### Template: Feature Exploration

```
## Exploring: [Feature Name]

### Related Code Found:
- [File 1]: [What it does, relevance]
- [File 2]: [What it does, relevance]

### Existing Patterns:
- Error handling: [Pattern used]
- Data flow: [Description]
- Testing: [Approach used]

### Dependencies Involved:
- [Dep 1]: [How it's used]
- [Dep 2]: [How it's used]

### Proposed Approach:
Based on existing patterns, I'll:
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Files to Create/Modify:
- [ ] [File 1] - [What change]
- [ ] [File 2] - [What change]
```

---

## Bug Fix Exploration

### Before Fixing a Bug

1. **Reproduce understanding:**
   - What's the expected behavior?
   - What's the actual behavior?
   - Can you see it in tests?

2. **Trace the code path:**
   - Where does the bug manifest?
   - What calls that code?
   - What are the inputs?

3. **Find similar fixes:**
   - Search git history for related fixes
   - Check if pattern exists elsewhere

### Template: Bug Exploration

```
## Investigating: [Bug Description]

### Reproduction:
- Expected: [behavior]
- Actual: [behavior]
- Steps: [how to trigger]

### Code Path:
1. Entry: [file:line]
2. Through: [file:line]
3. Bug at: [file:line]

### Root Cause:
[Description of why the bug happens]

### Fix Approach:
[Minimal change to fix, not refactor]

### Verification:
- [ ] Add/update test for this case
- [ ] Existing tests still pass
- [ ] Manual verification
```

---

## Refactoring Exploration

### Before Refactoring

1. **Map the blast radius:**
   - What depends on this code?
   - What does this code depend on?
   - How many files affected?

2. **Check test coverage:**
   - Are there tests for current behavior?
   - Will tests catch regressions?

3. **Identify safe boundaries:**
   - Can you refactor in small steps?
   - What's the minimal viable change?

### Template: Refactor Exploration

```
## Refactoring: [Area/File]

### Current State:
- [Problem 1]: [Description]
- [Problem 2]: [Description]

### Dependencies (what uses this):
- [File 1]: [How it uses this]
- [File 2]: [How it uses this]

### Test Coverage:
- Covered: [What's tested]
- Not covered: [What's missing]

### Proposed Changes:
Phase 1 (safe):
- [ ] [Change 1]
- [ ] [Change 2]

Phase 2 (verify first):
- [ ] [Change 3]

### Verification Plan:
1. Run existing tests after each phase
2. Manual check: [What to verify]
```

---

## Stop Conditions

**Stop exploring when:**
- You have enough context to proceed confidently
- Same information appearing across multiple sources
- 2 search iterations yielded no new useful data
- Direct answer found

**DO NOT over-explore.** Time is precious. If you've found the pattern, start implementing.

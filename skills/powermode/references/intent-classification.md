# Intent Classification Guide

Classify EVERY request before taking action. This prevents wasted effort and ensures appropriate depth.

## Classification Types

### Trivial
**Signals:**
- Single file operation
- Known location
- Direct answer possible
- <5 minutes of work

**Examples:**
- "What does this function do?" (with file path)
- "Add a comment to line 42"
- "What's the syntax for X?"

**Action:** Execute directly, no exploration needed.

---

### Explicit
**Signals:**
- Specific file/line mentioned
- Clear, unambiguous command
- User knows exactly what they want

**Examples:**
- "Change the color in Button.tsx from blue to red"
- "Add error handling to the fetch call on line 156"
- "Rename `getUserData` to `fetchUserProfile`"

**Action:** Execute directly. User has done the thinking.

---

### Exploratory
**Signals:**
- "How does X work?"
- "Find Y"
- "Where is Z defined?"
- Understanding-focused, not action-focused

**Examples:**
- "How does authentication work in this app?"
- "Find all usages of the deprecated API"
- "What's the data flow from form submission to database?"

**Action:** 
1. Search codebase systematically
2. Explain findings
3. Wait for follow-up before implementing

---

### Open-ended
**Signals:**
- "Improve", "Refactor", "Add feature"
- "Make it better"
- "Optimize"
- Vague outcome, multiple valid approaches

**Examples:**
- "Add user authentication"
- "Improve the performance"
- "Refactor the utils folder"
- "Make the UI more responsive"

**Action:**
1. Explore codebase first
2. Assess codebase state
3. Create detailed todos
4. Propose approach (if codebase is chaotic)
5. Implement with verification

---

### Ambiguous
**Signals:**
- Multiple valid interpretations
- Missing critical information
- Scope unclear

**Examples:**
- "Fix the bug" (which bug?)
- "Update the tests" (which tests? how?)
- "Add validation" (what kind? where?)

**Action:** Ask ONE clarifying question before proceeding.

---

## When to Ask for Clarification

### MUST Ask
| Situation | Why |
|-----------|-----|
| Multiple interpretations, 2x+ effort difference | Avoid wasted work |
| Missing critical info (file, error, context) | Can't proceed without it |
| User's design seems flawed | Better to raise early |

### DON'T Ask
| Situation | Why |
|-----------|-----|
| Single valid interpretation | Just do it |
| Similar effort for all options | Pick reasonable default, note assumption |
| You can figure it out from codebase | Explore first |

---

## Clarification Template

```
I want to make sure I understand correctly.

**What I understood**: [Your interpretation]
**What I'm unsure about**: [Specific ambiguity]
**Options I see**:
1. [Option A] - [effort/implications]
2. [Option B] - [effort/implications]

**My recommendation**: [suggestion with reasoning]

Should I proceed with [recommendation], or would you prefer differently?
```

---

## Quick Decision Tree

```
Is the request trivial/explicit?
├── YES → Execute directly
└── NO → Is it exploratory?
    ├── YES → Search and explain, wait for follow-up
    └── NO → Is it ambiguous?
        ├── YES → Ask ONE clarifying question
        └── NO → It's open-ended
            └── Full methodology: Explore → Plan → Todos → Implement → Verify
```

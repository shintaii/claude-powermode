---
name: pm-plan
description: Unified planning command - detects input type (goal, document, PRD folder) and acts accordingly. Creates, transforms, or manages PRDs.
allowed-tools: "*"
---

# Planning Workflow

Starting planning for: `$ARGUMENTS`

## STEP 0: Detect Input Type

Analyze `$ARGUMENTS` to determine the mode:

| Input | Mode | What to do |
|-------|------|------------|
| Plain text (a goal or feature description) | **Goal mode** | Plan from scratch → Create PRDs |
| References a `.md` file (e.g., `@path/to/spec.md`) | **Document mode** | Transform that document into PRDs |
| References a folder (e.g., `@resources/prd/feature/`) | **Folder mode** | Detect existing PRDs, show structure, offer next steps |

**Determine the mode now, then jump to the corresponding section below.**

---

## MODE: Goal (plan from scratch)

You have a goal or feature description. Run the full planning pipeline.

### Create Workflow Todos

**YOU MUST create these 4 todos NOW using TaskCreate before proceeding:**

1. TaskCreate: subject="Run Analyser", description="Pre-planning analysis", activeForm="Running Analyser"
2. TaskCreate: subject="Run Powerplanner", description="Create work plan", activeForm="Running Powerplanner"
3. TaskCreate: subject="Run Planreviewer", description="Review plan", activeForm="Running Planreviewer"
4. TaskCreate: subject="Write PRD files", description="Persist plan as PRDs", activeForm="Writing PRDs"

### Step 1: Analyse

Mark Analyser todo as in_progress, then:

```
Task(subagent_type="powermode:pm-analyser", prompt="
  Analyze this request for hidden requirements and ambiguities:

  REQUEST: $ARGUMENTS

  Identify:
  1. Hidden requirements not explicitly stated
  2. Ambiguities that need clarification
  3. AI-slop risks to avoid
  4. Questions for the user (if blocking)
  5. Directives for the planning phase
")
```

Mark Analyser todo completed. If blocking questions found, ask the user first.

### Step 2: Plan

Mark Powerplanner todo as in_progress, then:

```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a comprehensive work plan for:

  REQUEST: $ARGUMENTS

  ANALYSER DIRECTIVES:
  [Include directives from Analyser]

  Interview the user if requirements are unclear.
  Explore the codebase to understand constraints.
  Create a detailed, actionable plan.
")
```

Mark Powerplanner todo completed.

### Step 3: Review

Mark Planreviewer todo as in_progress, then:

```
Task(subagent_type="powermode:pm-planreviewer", prompt="
  Review this plan for completeness and clarity:

  [Plan from Powerplanner]

  Check:
  - Task clarity (can an implementer understand exactly what to do?)
  - Verification criteria (how do we know each task is done?)
  - Context completeness (file paths, patterns, dependencies)
  - Logical coherence (no gaps, no duplicates)

  Return OKAY or NEEDS REVISION with specific improvements.
")
```

If NEEDS REVISION: fix issues, re-run Planreviewer (max 3 iterations).
Mark Planreviewer todo completed when OKAY.

### Step 4: Write PRDs

Jump to **PRD WRITING** section below.

---

## MODE: Document (transform existing doc into PRDs)

You have a source document (spec, issue, RFC, etc.) to transform into implementable PRDs.

### Create Workflow Todos

**YOU MUST create these 4 todos NOW using TaskCreate:**

1. TaskCreate: subject="Research codebase", description="Explore codebase for context", activeForm="Researching codebase"
2. TaskCreate: subject="Analyse document", description="Analyse doc for PRD splitting", activeForm="Analysing document"
3. TaskCreate: subject="Plan PRD split", description="Determine split strategy", activeForm="Planning PRD split"
4. TaskCreate: subject="Write PRD files", description="Write PRDs from document", activeForm="Writing PRDs"

### Step 1: Research

Mark research todo as in_progress. Read the source document, then explore the codebase:

```
Task(subagent_type="powermode:pm-explorer", prompt="
  Find existing patterns, files, and architecture relevant to:

  DOCUMENT SUMMARY: [summarize the source document]

  Look for:
  1. Related existing code/files
  2. Patterns to follow
  3. Dependencies and integration points
  4. Test patterns in this area
")
```

If the document references external libraries/APIs, also fire:

```
Task(subagent_type="powermode:pm-researcher", prompt="
  Research external dependencies: [library/API names from document]
  Find: best practices, gotchas, integration patterns
")
```

Mark research todo completed.

### Step 2: Analyse

Mark analyse todo as in_progress, then:

```
Task(subagent_type="powermode:pm-analyser", prompt="
  Analyze this document for PRD splitting:

  DOCUMENT: [summarize source document]
  CODEBASE CONTEXT: [explorer findings]

  Identify:
  1. Distinct domains/areas touched
  2. Testable chunks
  3. Dependencies between parts
  4. Hidden requirements not in the document
")
```

Mark analyse todo completed.

### Step 3: Plan Split & Review

Mark plan todo as in_progress. Plan the split, then review:

```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a PRD split strategy:
  ANALYSER OUTPUT: [analyser findings]
  Determine: how many PRDs, what each covers, dependency order, test focus
")
```

Review with Planreviewer (same as Goal mode Step 3). Max 3 iterations until OKAY.
Mark plan todo completed.

### Step 4: Write PRDs

Jump to **PRD WRITING** section below.

---

## MODE: Folder (existing PRDs)

You have an existing PRD folder. Analyse what's there, check quality, and help the user work with it.

### Step 1: Read & Inventory

1. List all `.md` files in the folder
2. Look for `README.md` or `index.md` - note if missing
3. Read **every PRD** in the folder (use pm-explorer for parallel reading if 4+)

### Step 2: Analyse Each PRD Against Split Rules

For each PRD, evaluate against these rules:

| Rule | Flag if... |
|------|-----------|
| **Domain boundary** | PRD touches more than one area of the codebase |
| **Size** | PRD would require ~120k+ tokens of implementation work |
| **Testability** | PRD cannot be verified with focused tests |
| **Dependency clarity** | PRD has unclear or circular dependencies |

Use pm-analyser to evaluate:

```
Task(subagent_type="powermode:pm-analyser", prompt="
  Analyse these existing PRDs for quality and split-readiness:

  PRD FILES:
  [list each PRD with a brief summary]

  For each PRD, evaluate:
  1. Does it cross domain boundaries? (should be split)
  2. Is it too large for one implementation session? (~120k token limit)
  3. Can it be tested with focused tests?
  4. Are dependencies between PRDs clear?

  Flag any PRDs that should be split and explain why.
  Note if a README/index is missing.
")
```

### Step 3: Present Report

Report to the user:

```
Found PRD folder: <path>
├── 01-<title>.md    ✓ OK
├── 02-<title>.md    ⚠ SHOULD SPLIT (crosses domain boundary: API + frontend)
├── 03-<title>.md    ✓ OK
├── 04-<title>.md    ✓ OK
└── README.md        ✗ MISSING

Issues found:
- 02-<title>.md: Covers both API endpoints and frontend components.
  Recommend splitting into 02a-api-endpoints.md and 02b-frontend-components.md
- No README/index: dependency order is unclear
```

### Step 4: Offer Actions

Ask the user what they want to do (use AskUserQuestion with multiple select):

- **Split flagged PRDs** → Run Analyser + Powerplanner on the oversized PRD, then rewrite as multiple PRDs in the same folder. Renumber subsequent PRDs to maintain order.
- **Create missing README** → Generate a README index with dependency order based on analysis
- **Implement as-is** → Skip fixes. Suggest: `/powermode @<folder>/README.md` or first PRD
- **Add a new PRD** → Run Goal mode, target the same folder

### If Splitting a PRD

When the user chooses to split a flagged PRD:

1. Read the full PRD content
2. Run the planning pipeline (Analyser → Powerplanner → Planreviewer) on just that PRD
3. Replace the original PRD with the split PRDs, renumbering the folder:
   - Original: `01, 02, 03, 04` where 02 needs splitting
   - Result: `01, 02a, 02b, 03, 04` (or renumber to `01, 02, 03, 04, 05`)
4. Update the README index if it exists

### If Creating README

Generate a README with:
- Folder purpose/scope
- Dependency order table
- Each PRD: file, domain, test focus, dependencies, status

Use this table format:

```markdown
| # | File | Domain | Test Focus | Dependencies | Status |
|---|------|--------|-----------|--------------|--------|
| 1 | 01-database-schema.md | Database | Schema + migrations | None | Pending |
| 2 | 02-api-endpoints.md | API | Endpoint auth | 01 | Pending |
| 3 | 03-frontend-ui.md | Frontend | UI components | 02 | Pending |
```

Status values: `Pending`, `In Progress`, `Done`

---

## PRD WRITING (shared by Goal and Document modes)

Mark PRD writing todo as in_progress.

### Output Location

**All powermode-generated PRDs go to `.powermode/prds/<slug>/`** - never to user's own folders.

This keeps powermode output separate from user-created PRDs and avoids conflicts.

#### Slug Generation

Derive the slug from the goal or document name:
- Use kebab-case, max 30 characters
- Examples: `auth-feature`, `payment-v2`, `api-refactor`
- If slug already exists in `.powermode/prds/`, append a number: `auth-feature-2`

#### Index Tracking

After creating a PRD set, update `.powermode/prds/index.json`:

```json
{
  "prd_sets": [
    {
      "slug": "auth-feature",
      "created": "2026-02-06T12:00:00Z",
      "source": "goal: add user authentication",
      "prd_count": 3,
      "status": "ready"
    }
  ]
}
```

If `index.json` doesn't exist, create it. If it does, append the new entry.

### Split Rules

Split into multiple PRDs if:
1. **Testable chunk**: cannot be tested with 1+ focused tests
2. **Domain boundary**: touches more than one area of the codebase
3. **Size**: a single PRD would exceed ~120k tokens of work

### Delegate Writing

PRD writing MUST be delegated to sub-agents to preserve main context.

**If 1 PRD needed:**
```
Task(subagent_type="general-purpose", prompt="
  Write a single PRD file at .powermode/prds/<slug>/<slug>.md

  APPROVED PLAN: [include plan]

  Include: scope, requirements, acceptance criteria, test focus, dependencies
", description="Write PRD")
```

**If 2+ PRDs needed:**

First create the folder and README index yourself (brief, just the structure).
Then delegate writing in batches of max 2 PRDs per Task:

```
Task(subagent_type="general-purpose", prompt="
  Write these PRDs to .powermode/prds/<slug>/:
  - 01-<title>.md: <scope>
  - 02-<title>.md: <scope>

  Each PRD must include: scope, requirements, acceptance criteria, test focus, dependencies

  APPROVED PLAN: [include relevant sections]
", description="Write PRDs 01-02")
```

- **Sequential execution** - wait for each batch before starting next
- Max 2 PRDs per Task to keep sub-agent context manageable

### After Writing

Mark PRD writing todo completed.

Update `.powermode/prds/index.json` with the new PRD set entry.

Present:
1. List all created PRD files with paths
2. Explain the split rationale (if split)
3. Suggest next command:
   - `/powermode @.powermode/prds/<slug>/README.md` to implement (auto-detects team mode if available)

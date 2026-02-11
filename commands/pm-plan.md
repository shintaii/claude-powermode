---
name: pm-plan
description: Unified planning command - detects input type (goal, document, PRD folder) and acts accordingly. Creates hierarchical project/feature/task PRDs.
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

### Step 1: Analyse (determines scope)

Create initial todos:

1. TaskCreate: subject="Run Analyser", description="Pre-planning analysis + scope classification", activeForm="Running Analyser"

Mark Analyser todo as in_progress, then:

```
Task(subagent_type="powermode:pm-analyser", prompt="
  Analyze this request for hidden requirements, ambiguities, and SCOPE CLASSIFICATION:

  REQUEST: $ARGUMENTS

  IMPORTANT: Check .powermode/projects/index.json for existing projects.
  Read the file if it exists (it may not exist yet).

  Identify:
  1. Hidden requirements not explicitly stated
  2. Ambiguities that need clarification
  3. AI-slop risks to avoid
  4. Questions for the user (if blocking)
  5. Directives for the planning phase
  6. SCOPE CLASSIFICATION: Project / Feature / Task
     - Project: multiple domains, 5+ functional areas, multiple user roles
     - Feature: single domain, 2-5 tasks
     - Task: single responsibility, one concern
  7. If existing project match found, name it
  8. Suggest slug for new project/feature
")
```

Mark Analyser todo completed. If blocking questions found, ask the user first.

**Now create remaining todos based on the scope level from Analyser output:**

---

### SCOPE: Project (5+ tasks, multiple features)

Create these additional todos:

2. TaskCreate: subject="Run Powerplanner", description="Create project plan with feature decomposition", activeForm="Running Powerplanner"
3. TaskCreate: subject="Run Planreviewer", description="Review plan", activeForm="Running Planreviewer"
4. TaskCreate: subject="Create project scaffold", description="Create project.md, status.json, decisions.md, issues.md", activeForm="Creating project scaffold"
5. TaskCreate: subject="Create feature structures", description="Create feature folders with READMEs", activeForm="Creating feature structures"
6. TaskCreate: subject="Write task PRDs", description="Write task PRDs per feature", activeForm="Writing task PRDs"

#### Step 2: Plan

Mark Powerplanner todo as in_progress, then:

```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a PROJECT-LEVEL work plan for:

  REQUEST: $ARGUMENTS

  ANALYSER OUTPUT:
  [Include full analyser output including scope classification and feature list]

  Use the Project-Level Plan template.
  Decompose into features, each with task PRDs.
  Define cross-feature dependencies and implementation order.
  Interview the user if requirements are unclear.
  Explore the codebase to understand constraints.
")
```

Mark Powerplanner todo completed.

#### Step 3: Review

Mark Planreviewer todo as in_progress, then:

```
Task(subagent_type="powermode:pm-planreviewer", prompt="
  Review this PROJECT-LEVEL plan:

  [Plan from Powerplanner]

  Check:
  - Feature decomposition makes sense (no overlapping domains)
  - Task clarity (can an implementer understand exactly what to do?)
  - Cross-feature dependencies are explicit
  - Implementation order is logical
  - Verification criteria exist for each task

  Return OKAY or NEEDS REVISION with specific improvements.
")
```

If NEEDS REVISION: fix issues, re-run Planreviewer (max 3 iterations).
Mark Planreviewer todo completed when OKAY.

#### Step 4: Create Project Scaffold

Mark scaffold todo as in_progress.

Determine project slug (from analyser suggestion or plan). If adding to existing project, skip scaffold creation.

**Create `.powermode/projects/<project-slug>/` with:**

1. **`project.md`** - Project scope and goals from the plan overview
2. **`status.json`** - Initial state:
```json
{
  "version": 1,
  "slug": "<project-slug>",
  "created": "<ISO timestamp>",
  "updated": "<ISO timestamp>",
  "status": "planning",
  "features": {}
}
```
3. **`decisions.md`** - Empty decision log:
```markdown
# Decision Log
```
4. **`issues.md`** - Empty issues tracker:
```markdown
# Issues & Gaps
```

**Update `.powermode/projects/index.json`:**

If it doesn't exist, create it:
```json
{
  "projects": []
}
```

Append new project entry:
```json
{
  "slug": "<project-slug>",
  "created": "<ISO timestamp>",
  "source": "goal: <original request summary>",
  "status": "planning"
}
```

Mark scaffold todo completed.

#### Step 5: Create Feature Structures

Mark feature structures todo as in_progress.

For each feature in the plan, create:
- `.powermode/projects/<project-slug>/features/<feature-slug>/README.md`

README format:
```markdown
# Feature: [Feature Name]

[Brief feature description from plan]

## Task PRDs

| # | File | Domain | Test Focus | Dependencies | Status |
|---|------|--------|-----------|--------------|--------|
| 1 | 01-<task>.md | [area] | [test focus] | None | Pending |
| 2 | 02-<task>.md | [area] | [test focus] | 01 | Pending |
```

Update `status.json` with feature entries:
```json
{
  "features": {
    "<feature-slug>": {
      "status": "pending",
      "tasks_total": N,
      "tasks_done": 0,
      "tasks": {
        "01-<task>": "pending",
        "02-<task>": "pending"
      }
    }
  }
}
```

Mark feature structures todo completed.

#### Step 6: Write Task PRDs

Jump to **PRD WRITING** section below, targeting feature folders.

---

### SCOPE: Feature (2-5 tasks, single domain)

Create these additional todos:

2. TaskCreate: subject="Run Powerplanner", description="Create feature plan with task PRDs", activeForm="Running Powerplanner"
3. TaskCreate: subject="Run Planreviewer", description="Review plan", activeForm="Running Planreviewer"
4. TaskCreate: subject="Write PRD files", description="Create feature folder + task PRDs", activeForm="Writing PRDs"

#### Step 2: Plan

Mark Powerplanner todo as in_progress.

**Check for existing project match** (from analyser output). If match found, ask user to confirm adding to that project. If no match, auto-create a minimal project.

```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a FEATURE-LEVEL work plan for:

  REQUEST: $ARGUMENTS

  ANALYSER OUTPUT:
  [Include full analyser output]

  Use the Feature-Level Plan template.
  Define task PRDs with dependency order.
  Interview the user if requirements are unclear.
  Explore the codebase to understand constraints.
")
```

Mark Powerplanner todo completed.

#### Step 3: Review

Same as Project scope Step 3 but review as feature-level plan.

#### Step 4: Write PRDs

**If no existing project:** Create a minimal project first:
- `.powermode/projects/<project-slug>/project.md` (one-liner description)
- `.powermode/projects/<project-slug>/status.json` (minimal)
- Update `.powermode/projects/index.json`
- No `decisions.md` / `issues.md` yet (created on demand when first needed)

Then create the feature folder and jump to **PRD WRITING** section.

---

### SCOPE: Task (single PRD)

Create these additional todos:

2. TaskCreate: subject="Run Powerplanner", description="Create task plan", activeForm="Running Powerplanner"
3. TaskCreate: subject="Run Planreviewer", description="Review plan", activeForm="Running Planreviewer"
4. TaskCreate: subject="Write PRD file", description="Write single task PRD", activeForm="Writing PRD"

#### Step 2: Plan

Mark Powerplanner todo as in_progress.

```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a TASK-LEVEL work plan for:

  REQUEST: $ARGUMENTS

  ANALYSER OUTPUT:
  [Include full analyser output]

  Use the Task-Level Plan template.
  This is a single-responsibility task.
  Interview the user if requirements are unclear.
  Explore the codebase to understand constraints.
")
```

Mark Powerplanner todo completed.

#### Step 3: Review

Same as Project scope Step 3 but review as task-level plan.

#### Step 4: Write PRD

**Auto-create minimal project** from task description (e.g., slug: `add-logout-button`):
- `.powermode/projects/<project-slug>/project.md` (one-liner)
- `.powermode/projects/<project-slug>/status.json` (minimal)
- Update `.powermode/projects/index.json`
- Create feature folder (same slug as project for standalone tasks)
- Write single task PRD

Jump to **PRD WRITING** section.

---

## MODE: Document (transform existing doc into PRDs)

You have a source document (spec, issue, RFC, etc.) to transform into implementable PRDs.

### Create Workflow Todos

**YOU MUST create these 4 todos NOW using TaskCreate:**

1. TaskCreate: subject="Research codebase", description="Explore codebase for context", activeForm="Researching codebase"
2. TaskCreate: subject="Analyse document", description="Analyse doc for PRD splitting + scope classification", activeForm="Analysing document"
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
  Analyze this document for PRD splitting and SCOPE CLASSIFICATION:

  DOCUMENT: [summarize source document]
  CODEBASE CONTEXT: [explorer findings]

  IMPORTANT: Check .powermode/projects/index.json for existing projects.

  Identify:
  1. Distinct domains/areas touched
  2. Testable chunks
  3. Dependencies between parts
  4. Hidden requirements not in the document
  5. SCOPE CLASSIFICATION: Project / Feature / Task
  6. Existing project match (if any)
")
```

Mark analyse todo completed.

### Step 3: Plan Split & Review

Mark plan todo as in_progress. Plan the split using the scope-appropriate template:

```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a PRD split strategy:
  ANALYSER OUTPUT: [analyser findings including scope level]
  Determine: scope level, features (if project), task PRDs per feature, dependency order
  Use the appropriate plan template for the scope level.
")
```

Review with Planreviewer (same as Goal mode). Max 3 iterations until OKAY.
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
├── 01-<title>.md    OK
├── 02-<title>.md    SHOULD SPLIT (crosses domain boundary: API + frontend)
├── 03-<title>.md    OK
├── 04-<title>.md    OK
└── README.md        MISSING

Issues found:
- 02-<title>.md: Covers both API endpoints and frontend components.
  Recommend splitting into 02a-api-endpoints.md and 02b-frontend-components.md
- No README/index: dependency order is unclear
```

### Step 4: Offer Actions

Ask the user what they want to do (use AskUserQuestion with multiple select):

- **Split flagged PRDs** - Run Analyser + Powerplanner on the oversized PRD, then rewrite as multiple PRDs in the same folder. Renumber subsequent PRDs to maintain order.
- **Create missing README** - Generate a README index with dependency order based on analysis
- **Implement as-is** - Skip fixes. Suggest: `/powermode @<folder>/README.md` or first PRD
- **Add a new PRD** - Run Goal mode, target the same folder

### If Splitting a PRD

When the user chooses to split a flagged PRD:

1. Read the full PRD content
2. Run the planning pipeline (Analyser -> Powerplanner -> Planreviewer) on just that PRD
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

## PRD WRITING (shared by all Goal scope levels and Document mode)

Mark PRD writing todo as in_progress.

### Output Location

**All powermode-generated PRDs go to `.powermode/projects/<project-slug>/features/<feature-slug>/`**

This keeps powermode output hierarchical and organized.

**Backward compatibility:** Old `.powermode/prds/` paths continue to work. New PRDs always use the projects structure.

#### Slug Generation

Derive slugs from the goal, feature, or document name:
- Use kebab-case, max 30 characters
- Examples: `auth-feature`, `payment-v2`, `api-refactor`
- If slug already exists, append a number: `auth-feature-2`

#### Project Structure Guarantee

Before writing PRDs, ensure the project structure exists:
1. `.powermode/projects/index.json` - Create or update
2. `.powermode/projects/<project-slug>/project.md` - Create if missing
3. `.powermode/projects/<project-slug>/status.json` - Create if missing
4. `.powermode/projects/<project-slug>/features/<feature-slug>/README.md` - Create or update

### Split Rules

Split into multiple task PRDs if:
1. **Testable chunk**: cannot be tested with 1+ focused tests
2. **Domain boundary**: touches more than one area of the codebase
3. **Size**: a single PRD would exceed ~120k tokens of work

### Delegate Writing

PRD writing MUST be delegated to sub-agents to preserve main context.

**If 1 task PRD needed:**
```
Task(subagent_type="general-purpose", prompt="
  Write a single task PRD file at .powermode/projects/<project-slug>/features/<feature-slug>/01-<task>.md

  APPROVED PLAN: [include plan]

  Include: scope, requirements, acceptance criteria, test focus, dependencies
", description="Write PRD")
```

**If 2+ task PRDs needed:**

First create the feature folder and README index yourself (brief, just the structure).
Then delegate writing in batches of max 2 PRDs per Task:

```
Task(subagent_type="general-purpose", prompt="
  Write these task PRDs to .powermode/projects/<project-slug>/features/<feature-slug>/:
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

**Update status.json** with task entries and set feature status to "pending".

**Update index.json** project entry status to "ready".

Present:
1. List all created PRD files with paths
2. Show the project structure tree
3. Explain the split rationale (if split)
4. Suggest next command:
   - `/powermode @.powermode/projects/<project-slug>/features/<feature-slug>/README.md` to implement a feature
   - `/powermode @.powermode/projects/<project-slug>/project.md` to implement the full project (auto-detects team mode if available)

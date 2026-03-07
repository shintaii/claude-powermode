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

### Step 1.5: Define Success Criteria

Before creating tasks, ask the user to define what success looks like. This drives test generation and keeps the plan grounded in real outcomes.

Using AskUserQuestion, present the analyser's scope and feature/task breakdown, then ask:

"Before we plan the tasks, let's define what success looks like.

**Scope detected:** [Project / Feature / Task]
**Key pieces:** [list features or task areas from analyser output]

For each piece, what are the expected inputs and outputs?
- What data/action goes in?
- What result, state change, or behavior comes out?
- Any edge cases that must work?

You can answer per-piece, or describe overall outcomes — I'll use this to define tests before writing the PRDs."

**Options:**
- The plan captures it — proceed with AI-derived tests
- Let me define outcomes (free text)
- Skip — add tests after

Store the user's response as **SUCCESS_CRITERIA** and pass it into the Powerplanner prompt below.

If user chooses "Skip", SUCCESS_CRITERIA = "(none — derive from plan)".

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

  SUCCESS CRITERIA (user-defined inputs/outputs):
  [Include SUCCESS_CRITERIA from Step 1.5]

  Use the Project-Level Plan template.
  Decompose into features, each with task PRDs.
  Define cross-feature dependencies and implementation order.
  Use the SUCCESS CRITERIA to write concrete test assertions in each task PRD's ## Tests section.
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

Determine project slug (from analyser suggestion or plan). If re-planning an existing project, preserve `decisions.md` and `issues.md` but update `project.md` and reset `status.json` features to match the new plan. If adding a feature to an existing project, skip scaffold creation.

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

**Clean up stale feature directories (re-plan scenario):**

If `.powermode/projects/<project-slug>/features/` already exists and contains directories:

1. List existing feature directories
2. Compare against the new plan's feature list
3. Identify **orphaned directories** — directories that don't match any feature in the new plan
4. If orphans found, present them to the user using AskUserQuestion:

"Found existing feature directories that aren't in the new plan:
- `04-webhooks/` (not in new plan)
- `05-simulation/` (not in new plan)

These appear to be leftovers from a previous plan."

Options:
- Delete orphaned directories (recommended)
- Keep them (I'll clean up manually)
- Let me review each one

If deleting, remove the orphaned directories AND their entries from `status.json`.

**Also clean up stale entries in `status.json`:** Remove any feature keys from `status.json` that reference directories no longer present (or no longer in the plan).

For each feature in the plan, create:
- `.powermode/projects/<project-slug>/features/<NN-feature-slug>/README.md`

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
    "<NN-feature-slug>": {
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

#### Step 7: Confirm Tests with User

TaskCreate: subject="Confirm tests with user", description="Test confirmation", activeForm="Confirming tests"

Mark todo as in_progress.

Read all task PRDs just written. Extract every `## Tests` section.

Present a consolidated test summary to the user using AskUserQuestion:

"Here are the tests defined for your project (informed by your success criteria):

**Task Tests** (verify individual work):
[grouped by feature, show each task's tests from ## Tests sections]

**Feature Tests** (verify feature works as a whole):
[feature-level tests — suggest integration tests for cross-task behavior]

**Project Tests** (verify everything works together):
[project-level tests — suggest e2e tests for critical user journeys]

Test stubs have been scaffolded to: [list test file paths]"

Options:
- Looks good — ready to implement
- I want to add/change tests (tell me which)
- Simplify — fewer tests

If user wants changes:
1. Update the relevant PRD files (## Tests sections)
2. Update feature READMEs (add/update ## Feature Tests section)
3. Update project.md (add/update ## Project Tests section)
4. Update scaffolded test stub files to match

Mark todo completed.

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

  SUCCESS CRITERIA (user-defined inputs/outputs):
  [Include SUCCESS_CRITERIA from Step 1.5]

  Use the Feature-Level Plan template.
  Define task PRDs with dependency order.
  Use the SUCCESS CRITERIA to write concrete test assertions in each task PRD's ## Tests section.
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

#### Step 5: Confirm Tests with User

TaskCreate: subject="Confirm tests with user", description="Test confirmation", activeForm="Confirming tests"

Mark todo as in_progress.

Read all task PRDs just written. Extract every `## Tests` section.

Present a consolidated test summary to the user using AskUserQuestion:

"Here are the tests defined for this feature (informed by your success criteria):

**Task Tests** (verify individual work):
[show each task's tests from ## Tests sections]

**Feature Tests** (verify feature works as a whole):
[feature-level tests — suggest integration tests for cross-task behavior]

Test stubs have been scaffolded to: [list test file paths]"

Options:
- Looks good — ready to implement
- I want to add/change tests (tell me which)
- Simplify — fewer tests

If user wants changes:
1. Update the relevant PRD files (## Tests sections)
2. Update feature README (add/update ## Feature Tests section)
3. Update scaffolded test stub files to match

Mark todo completed.

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

  SUCCESS CRITERIA (user-defined inputs/outputs):
  [Include SUCCESS_CRITERIA from Step 1.5]

  Use the Task-Level Plan template.
  This is a single-responsibility task.
  Use the SUCCESS CRITERIA to write concrete test assertions in the ## Tests section.
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

#### Step 5: Confirm Tests with User

TaskCreate: subject="Confirm tests with user", description="Test confirmation", activeForm="Confirming tests"

Mark todo as in_progress.

Read the task PRD just written. Extract the `## Tests` section.

Present the tests to the user using AskUserQuestion:

"Here are the tests defined for this task (informed by your success criteria):

**Tests:**
[show the task's tests from ## Tests section]

Test stubs have been scaffolded to: [list test file paths]"

Options:
- Looks good — ready to implement
- I want to add/change tests (tell me which)
- Simplify — fewer tests

If user wants changes:
1. Update the PRD's ## Tests section
2. Update scaffolded test stub files to match

Mark todo completed.

---

## MODE: Document (transform existing doc into PRDs)

You have a source document (spec, issue, RFC, etc.) to transform into implementable PRDs.

### Create Workflow Todos

**YOU MUST create these 5 todos NOW using TaskCreate:**

1. TaskCreate: subject="Research codebase", description="Explore codebase for context", activeForm="Researching codebase"
2. TaskCreate: subject="Analyse document", description="Analyse doc for PRD splitting + scope classification", activeForm="Analysing document"
3. TaskCreate: subject="Define success criteria", description="Capture expected inputs/outputs from user before planning", activeForm="Defining success criteria"
4. TaskCreate: subject="Plan PRD split", description="Determine split strategy", activeForm="Planning PRD split"
5. TaskCreate: subject="Write PRD files", description="Write PRDs from document", activeForm="Writing PRDs"

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

### Step 2.5: Define Success Criteria

Mark success criteria todo as in_progress.

Using AskUserQuestion, present the analyser's scope and feature/task breakdown, then ask:

"Before we plan the tasks, let's define what success looks like.

**Scope detected:** [Project / Feature / Task]
**Key pieces:** [list features or task areas from analyser output]

For each piece, what are the expected inputs and outputs?
- What data/action goes in?
- What result, state change, or behavior comes out?
- Any edge cases that must work?

You can answer per-piece, or describe overall outcomes — I'll use this to define tests before writing the PRDs."

**Options:**
- The doc captures it — proceed with AI-derived tests
- Let me define outcomes (free text)
- Skip — add tests after

Store the user's response as **SUCCESS_CRITERIA** and pass it into the Powerplanner prompt below.

If user chooses "The doc captures it" or "Skip", SUCCESS_CRITERIA = "(none — derive from document)".

Mark success criteria todo completed.

### Step 3: Plan Split & Review

Mark plan todo as in_progress. Plan the split using the scope-appropriate template:

```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a PRD split strategy:
  ANALYSER OUTPUT: [analyser findings including scope level]
  SUCCESS CRITERIA (user-defined inputs/outputs): [Include SUCCESS_CRITERIA from Step 2.5]
  Determine: scope level, features (if project), task PRDs per feature, dependency order
  Use the SUCCESS CRITERIA to write concrete test assertions in each task PRD's ## Tests section.
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

**All powermode-generated PRDs go to `.powermode/projects/<project-slug>/features/<NN-feature-slug>/`**

This keeps powermode output hierarchical and organized.

**Backward compatibility:** Old `.powermode/prds/` paths continue to work. New PRDs always use the projects structure.

#### Slug Generation

Derive slugs from the goal, feature, or document name:
- Use kebab-case, max 30 characters
- **Feature directories are numbered** by implementation order: `01-auth`, `02-dashboard`, `03-api-refactor`
- The number comes from the Implementation Order in the plan
- Task files within features are also numbered: `01-<task>.md`, `02-<task>.md`
- If slug already exists, append a suffix: `01-auth-v2`

#### Project Structure Guarantee

Before writing PRDs, ensure the project structure exists:
1. `.powermode/projects/index.json` - Create or update
2. `.powermode/projects/<project-slug>/project.md` - Create if missing
3. `.powermode/projects/<project-slug>/status.json` - Create if missing
4. `.powermode/projects/<project-slug>/features/<NN-feature-slug>/README.md` - Create or update

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
  Write a single task PRD file at .powermode/projects/<project-slug>/features/<NN-feature-slug>/01-<task>.md

  APPROVED PLAN: [include plan]

  Include: scope, requirements, acceptance criteria, tests (structured ## Tests table), dependencies

  CRITICAL PRD RULES:
  - Start the PRD with '## Implementation Rules' anti-stub header (every function = real logic, no stubs/TODOs/placeholders, tests assert real computed values, if a dependency doesn't exist STOP and create BLOCKED.md in project root)
  - Describe type definitions as specs (prose/tables) — do NOT reference other task PRDs
  - No fenced code blocks — PRDs are functional specs, not implementation code
  - Test assertions must include exact expected values (not 'has items' but 'has exactly 1 item with code X')
  - Include anti-stub canary test: grep for TODO/FIXME/NotImplemented/stub/mock/noop on all changed files, assert zero matches
  - NEVER use language that permits stubbing ('can be stubbed', 'implement later')
  - Each PRD must be fully implementable standalone
  - Include a ## Tests section with a markdown table: | ID | Type | Description | Expected Result |
  - Test IDs: T1, T2, T3... (task-scoped)
  - Minimum 1 test per task PRD
  - Include both technical tests (unit/integration) AND functional tests (user-visible behavior)
  - Every test needs a concrete expected result with exact values
  - Test types: unit, integration, e2e, functional, manual
", description="Write PRD")
```

**If 2+ task PRDs needed:**

First create the feature folder and README index yourself (brief, just the structure).
Then delegate writing in batches of max 2 PRDs per Task:

```
Task(subagent_type="general-purpose", prompt="
  Write these task PRDs to .powermode/projects/<project-slug>/features/<NN-feature-slug>/:
  - 01-<title>.md: <scope>
  - 02-<title>.md: <scope>

  Each PRD must include: scope, requirements, acceptance criteria, tests (structured ## Tests table), dependencies

  CRITICAL PRD RULES:
  - Start every PRD with '## Implementation Rules' anti-stub header (every function = real logic, no stubs/TODOs/placeholders, tests assert real computed values, if a dependency doesn't exist STOP and create BLOCKED.md in project root)
  - Describe type definitions as specs (prose/tables) — do NOT reference other task PRDs
  - No fenced code blocks — PRDs are functional specs, not implementation code
  - Test assertions must include exact expected values (not 'has items' but 'has exactly 1 item with code X')
  - Include anti-stub canary test: grep for TODO/FIXME/NotImplemented/stub/mock/noop on all changed files, assert zero matches
  - NEVER use language that permits stubbing ('can be stubbed', 'implement later')
  - Each PRD must be fully implementable standalone
  - Include a ## Tests section with a markdown table: | ID | Type | Description | Expected Result |
  - Test IDs: T1, T2, T3... (task-scoped)
  - Minimum 1 test per task PRD
  - Include both technical tests (unit/integration) AND functional tests (user-visible behavior)
  - Every test needs a concrete expected result with exact values
  - Test types: unit, integration, e2e, functional, manual

  APPROVED PLAN: [include relevant sections]
", description="Write PRDs 01-02")
```

- **Sequential execution** - wait for each batch before starting next
- Max 2 PRDs per Task to keep sub-agent context manageable

### PRD Content Rules

Task PRDs should NOT contain awareness of total project scope. Avoid:
- "This is task 5 of 12" — just describe the task
- "After this, Task 06 will build on..." — focus on this task only
- Listing all other tasks in the feature

NEVER reference other tasks by number. Use a Prerequisites section instead:
- BAD: "Dependencies: Task 01", "Depends on Task 03 for the User model"
- GOOD: "Prerequisites (must already exist in codebase): `UserModel` in `models/user.go` with fields: `id` (uuid), `name` (string), `org_id` (uuid). If these don't exist, STOP and create BLOCKED.md."

### After Writing

Mark PRD writing todo completed.

**Update status.json** with task entries and set feature status to "pending".

**Update index.json** project entry status to "ready".

### Scaffold Test Files (Optional Stubs)

**Note:** Real test files are written by `pm-test-writer` at implementation time, not during planning.
This step creates minimal stubs so the user can preview test structure. They will be overwritten by `pm-test-writer`.

Delegate test scaffolding to a sub-agent:

```
Task(subagent_type="general-purpose", prompt="
  Scaffold minimal test stubs for the PRDs just written.
  These are PLACEHOLDERS — pm-test-writer will write real tests before implementation.

  STEP 1: Detect test framework
  Check these files (read whichever exist):
  - package.json → look for jest, vitest, mocha in devDependencies/scripts
  - requirements.txt or pyproject.toml → look for pytest
  - go.mod → Go standard testing
  - pom.xml or build.gradle → JUnit
  If no framework detected, skip scaffolding and report 'no framework detected'.

  STEP 2: Read PRD tests
  Read all ## Tests sections from these PRDs:
  [list all PRD file paths just written]

  STEP 3: Generate stub files
  For each PRD, create ONE test stub file:
  - File name mirrors the PRD: 01-<task>.test.js / test_01_<task>.py / etc.
  - Location: test directory used by the project (check existing test files for conventions)
  - Each test in the PRD's ## Tests table → one stub with test name and TODO comment
  - Use the Test ID (T1, T2...) as the test name

  Report: which test files were created, which framework was used, or why scaffolding was skipped.
", description="Scaffold test stubs")
```

Present:
1. List all created PRD files with paths
2. List scaffolded test files (or note if skipped)
3. Show the project structure tree
4. Explain the split rationale (if split)
5. Suggest next command:
   - `/powermode @.powermode/projects/<project-slug>/features/<NN-feature-slug>/README.md` to implement a feature
   - `/powermode @.powermode/projects/<project-slug>/project.md` to implement the full project (auto-detects team mode if available)

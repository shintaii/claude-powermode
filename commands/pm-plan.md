---
name: pm-plan
description: Start the planning workflow with Analyser analysis -> Powerplanner planning -> Planreviewer review loop
allowed-tools: "*"
---

# Planning Workflow Initiated

Starting the structured planning workflow for: `$ARGUMENTS`

## MANDATORY FIRST ACTION

**YOU MUST create these 4 todos NOW using the TaskCreate tool before proceeding:**

1. TaskCreate with subject="Run Analyser", description="Pre-planning analysis", activeForm="Running Analyser"
2. TaskCreate with subject="Run Powerplanner", description="Create work plan", activeForm="Running Powerplanner"
3. TaskCreate with subject="Run Planreviewer", description="Review plan", activeForm="Running Planreviewer"
4. TaskCreate with subject="Write PRD files", description="Persist plan", activeForm="Writing PRDs"

**DO NOT proceed to Step 1 until all 4 todos are created. The stop-validator will BLOCK completion until all todos are marked complete.**

## Planning Pipeline

```
1. ANALYSER (Pre-Planning Analysis)
   ↓ Identifies hidden requirements, ambiguities, AI-slop risks

2. POWERPLANNER (Strategic Planning)
   ↓ Interviews for requirements, creates comprehensive plan

3. PLANREVIEWER (Plan Review Loop)
   ↓ Reviews plan for gaps, iterates until quality bar met

4. PRD FILES (Persist the Plan)
   ↓ Delegate to sub-agents to write PRD folder structure

5. READY FOR IMPLEMENTATION
```

## Step 1: Pre-Planning Analysis (Analyser)

**Mark todo as in_progress, then run Analyser:**

First, analyze the request for hidden complexity:

```
Task(subagent_type="pm-analyser", prompt="
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

**After Analyser completes, mark its todo as completed.**

## Step 2: Requirements Gathering (Powerplanner)

**Mark Powerplanner todo as in_progress.**

If Analyser identifies blocking questions, ask the user first.
Then proceed to planning:

```
Task(subagent_type="pm-powerplanner", prompt="
  Create a comprehensive work plan for:
  
  REQUEST: $ARGUMENTS
  
  ANALYSER DIRECTIVES:
  [Include directives from Analyser analysis]
  
  Interview the user if requirements are unclear.
  Explore the codebase to understand constraints.
  Create a detailed, actionable plan.
")
```

**After Powerplanner completes, mark its todo as completed.**

## Step 3: Plan Review Loop (Planreviewer)

**Mark Planreviewer todo as in_progress.**

Review the plan until it meets quality standards:

```
Task(subagent_type="pm-planreviewer", prompt="
  Review this plan for completeness and clarity:
  
  [Plan from Powerplanner]
  
  Check for:
  - Task clarity (can an implementer understand exactly what to do?)
  - Verification criteria (how do we know each task is done?)
  - Context completeness (file paths, patterns, dependencies)
  - Logical coherence (no gaps, no duplicates)
  
  Return OKAY or NEEDS REVISION with specific improvements.
")
```

### Planreviewer Loop

If Planreviewer returns `NEEDS REVISION`:
1. Update the plan based on Planreviewer feedback
2. Re-run Planreviewer review
3. Repeat until `OKAY` (max 3 iterations)

```
Iteration 1: Planreviewer reviews → NEEDS REVISION
Iteration 2: Fix issues → Planreviewer reviews → NEEDS REVISION  
Iteration 3: Fix issues → Planreviewer reviews → OKAY ✓
```

**After Planreviewer approves (returns OKAY), mark its todo as completed.**

## Step 4: Write PRD Files

**Mark PRD writing todo as in_progress.**

Once Planreviewer approves, persist the plan as PRD files.

### Determine PRD Location

Use the first existing directory:
1. `resources/prd/`
2. `resources/prds/`
3. `docs/prd/`
4. `docs/prds/`

If none exist, create: `resources/prd/<feature-slug>/`.

### Delegate PRD Writing

```
Task(subagent_type="general-purpose", prompt="
  Write PRD files to <path>:

  APPROVED PLAN:
  [Include the approved plan from Planreviewer]

  Create:
  - README.md (index with dependency order)
  - 01-<title>.md, 02-<title>.md, ... (numbered PRDs)

  Each PRD must include:
  - Clear scope and requirements
  - Acceptance criteria
  - Test focus
  - Dependencies on other PRDs

  Use prd skill format.
", description="Write PRD files")
```

- Max 2 PRDs per Task call to manage sub-agent context
- Sequential execution (wait for each batch before starting next)

**After all PRD files are written, mark the PRD writing todo as completed.**

## Step 5: Ready for Implementation

After PRDs are written:
1. List all created PRD files
2. Offer to start implementation with `/powermode @<prd-path>/README.md`
3. Or let user review and modify PRDs first

---

## Quick Reference

| Agent | Role | Output |
|-------|------|--------|
| pm-analyser | Pre-analysis | Hidden requirements, directives |
| pm-powerplanner | Planning | Comprehensive work plan |
| pm-planreviewer | Review | OKAY or NEEDS REVISION |
| general-purpose | PRD writing | PRD files in folder structure |

**Start by creating the 4 workflow todos, then run Analyser analysis.**

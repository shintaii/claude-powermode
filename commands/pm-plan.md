---
name: pm-plan
description: Start the planning workflow with Analyser analysis -> Powerplanner planning -> Planreviewer review loop
allowed-tools: "*"
---

# Planning Workflow Initiated

Starting the structured planning workflow for: `$ARGUMENTS`

## Planning Pipeline

```
1. ANALYSER (Pre-Planning Analysis)
   ↓ Identifies hidden requirements, ambiguities, AI-slop risks
   
2. POWERPLANNER (Strategic Planning)  
   ↓ Interviews for requirements, creates comprehensive plan
   
3. PLANREVIEWER (Plan Review Loop)
   ↓ Reviews plan for gaps, iterates until quality bar met
   
4. READY FOR IMPLEMENTATION
```

## Step 1: Pre-Planning Analysis (Analyser)

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

## Step 2: Requirements Gathering (Powerplanner)

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

## Step 3: Plan Review Loop (Planreviewer)

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

## Step 4: Ready for Implementation

Once Planreviewer approves:
1. Present the final plan to the user
2. Offer to start implementation with `/pm-ralph-loop`
3. Or let user review and modify first

---

## Quick Reference

| Agent | Role | Output |
|-------|------|--------|
| pm-analyser | Pre-analysis | Hidden requirements, directives |
| pm-powerplanner | Planning | Comprehensive work plan |
| pm-planreviewer | Review | OKAY or NEEDS REVISION |

**Start by running Analyser analysis now.**

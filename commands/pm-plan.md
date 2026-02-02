---
name: pm-plan
description: Start the planning workflow with Metis analysis -> Prometheus planning -> Momus review loop
allowed-tools: "*"
---

# Planning Workflow Initiated

Starting the structured planning workflow for: `$ARGUMENTS`

## Planning Pipeline

```
1. METIS (Pre-Planning Analysis)
   ↓ Identifies hidden requirements, ambiguities, AI-slop risks
   
2. PROMETHEUS (Strategic Planning)  
   ↓ Interviews for requirements, creates comprehensive plan
   
3. MOMUS (Plan Review Loop)
   ↓ Reviews plan for gaps, iterates until quality bar met
   
4. READY FOR IMPLEMENTATION
```

## Step 1: Pre-Planning Analysis (Metis)

First, analyze the request for hidden complexity:

```
Task(subagent_type="pm-metis", prompt="
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

## Step 2: Requirements Gathering (Prometheus)

If Metis identifies blocking questions, ask the user first.
Then proceed to planning:

```
Task(subagent_type="pm-prometheus", prompt="
  Create a comprehensive work plan for:
  
  REQUEST: $ARGUMENTS
  
  METIS DIRECTIVES:
  [Include directives from Metis analysis]
  
  Interview the user if requirements are unclear.
  Explore the codebase to understand constraints.
  Create a detailed, actionable plan.
")
```

## Step 3: Plan Review Loop (Momus)

Review the plan until it meets quality standards:

```
Task(subagent_type="pm-momus", prompt="
  Review this plan for completeness and clarity:
  
  [Plan from Prometheus]
  
  Check for:
  - Task clarity (can an implementer understand exactly what to do?)
  - Verification criteria (how do we know each task is done?)
  - Context completeness (file paths, patterns, dependencies)
  - Logical coherence (no gaps, no duplicates)
  
  Return OKAY or NEEDS REVISION with specific improvements.
")
```

### Momus Loop

If Momus returns `NEEDS REVISION`:
1. Update the plan based on Momus feedback
2. Re-run Momus review
3. Repeat until `OKAY` (max 3 iterations)

```
Iteration 1: Momus reviews → NEEDS REVISION
Iteration 2: Fix issues → Momus reviews → NEEDS REVISION  
Iteration 3: Fix issues → Momus reviews → OKAY ✓
```

## Step 4: Ready for Implementation

Once Momus approves:
1. Present the final plan to the user
2. Offer to start implementation with `/pm-ralph-loop`
3. Or let user review and modify first

---

## Quick Reference

| Agent | Role | Output |
|-------|------|--------|
| pm-metis | Pre-analysis | Hidden requirements, directives |
| pm-prometheus | Planning | Comprehensive work plan |
| pm-momus | Review | OKAY or NEEDS REVISION |

**Start by running Metis analysis now.**

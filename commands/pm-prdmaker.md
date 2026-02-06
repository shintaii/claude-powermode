---
name: pm-prdmaker
description: Create or split PRDs for a feature using powermode workflow
allowed-tools: "*"
---

# PRD Maker / Splitter

You are transforming an existing document (PRD, GitHub issue, spec) into powermode-compatible PRDs.

## Step 1: Research the Codebase (MANDATORY)

Before doing anything else, explore how this feature relates to the existing codebase:

```
Task(subagent_type="powermode:pm-explorer", prompt="
  Find existing patterns, files, and architecture relevant to:

  DOCUMENT SUMMARY: [summarize the input document]

  Look for:
  1. Related existing code/files
  2. Patterns to follow
  3. Dependencies and integration points
  4. Test patterns in this area
")
```

If the document references external libraries or APIs:

```
Task(subagent_type="powermode:pm-researcher", prompt="
  Research external dependencies for:

  [Library/API names from document]

  Find: best practices, gotchas, integration patterns
")
```

## Step 2: Analyze with Planning Loop

Run the full planning loop to understand scope and split strategy:

```
Task(subagent_type="powermode:pm-analyser", prompt="
  Analyze this document for PRD splitting:

  DOCUMENT: [paste or summarize input document]
  CODEBASE CONTEXT: [include explorer findings]

  Identify:
  1. Distinct domains/areas touched
  2. Testable chunks
  3. Dependencies between parts
  4. Hidden requirements not in the document
")
```

Then plan the split:

```
Task(subagent_type="powermode:pm-powerplanner", prompt="
  Create a PRD split strategy:

  ANALYSER OUTPUT: [include analyser findings]

  Determine:
  1. How many PRDs needed (use split rules below)
  2. What each PRD covers
  3. Dependency order between PRDs
  4. Test focus for each PRD
")
```

Review the strategy:

```
Task(subagent_type="powermode:pm-planreviewer", prompt="
  Review this PRD split strategy:

  [Powerplanner output]

  Check:
  - Each PRD is testable with focused tests
  - Each PRD stays within one domain
  - Dependencies are correctly ordered
  - Nothing is missing from original document

  Return OKAY or NEEDS REVISION.
")
```

If NEEDS REVISION, iterate until OKAY (max 3 iterations).

## Step 3: Delegate PRD Writing

Once the split strategy is approved, delegate writing to sub-agents.

### Split Rules

Split into multiple PRDs if any of the following are true:

1. **Testable chunk**: cannot be tested with 1+ focused tests.
2. **Domain boundary**: touches more than one domain/area of the codebase.
3. **Size**: a single PRD would exceed ~120k tokens of work.

Each PRD must:
- be testable (at least one focused test or verification step)
- stay within one domain
- be small enough to execute within context limits

## Sub-Agent Delegation (critical for context management)

PRD writing MUST be delegated to sub-agents to preserve main context.

### Strategy

1. **Main context**: Explore, plan, determine split, create folder + README index.
2. **Sub-agents**: Use `Task` to write PRD files. Max 2 PRDs per agent, sequential execution.

### How to delegate

```
Task(
  prompt="Write these PRDs to <path>:
    - 01-<title>.md: <scope>
    - 02-<title>.md: <scope>

  Use prd skill format. Context: <planning output>",
  description="Write PRDs 01-02"
)
```

- **Always sequential**: Launch one Task at a time, wait for completion before starting next
- Max 2 PRDs per Task to keep sub-agent context manageable
- This prevents context overload and allows reviewing output between batches

## Output Structure

### If 1 PRD

- Sub-agent creates a single PRD file in the primary PRD directory.

### If 2+ PRDs

- Main context creates folder with `README.md` (index).
- Sub-agents create numbered PRDs: `01-<short-title>.md`, `02-<short-title>.md`, ...

The index README must include:
- Purpose and scope
- Dependency order (sequence)
- A table with: PRD file, domain, test focus, dependencies

## PRD Location (auto-detect)

Use the first existing directory in this order:

1. `resources/prd/`
2. `resources/prds/`
3. `docs/prd/`
4. `docs/prds/`

If none exist, create: `resources/prd/<feature-slug>/`.

## Final Response

- Confirm sub-agent completion (all PRDs written)
- List all created files with paths
- Explain whether it was split and why
- Provide the recommended next command, e.g.:
  - `/powermode @resources/prd/<feature>/README.md`
  - `/powermode @resources/prd/<feature>/02-some-prd.md`

## Why sub-agents?

Writing PRDs directly in main context wastes tokens that aren't needed after creation. With 10+ PRDs, this can consume 50%+ of context. Sub-agents discard their context after completion, keeping main context lean for orchestration and follow-up work.

## Why sequential (not parallel)?

Parallel sub-agents can overload context and make it hard to review intermediate output. Sequential execution (max 2 PRDs per batch) allows reviewing each batch before continuing.

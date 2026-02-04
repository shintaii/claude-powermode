---
name: pm-prdmaker
description: Create or split PRDs for a feature using powermode workflow
allowed-tools: "*"
---

# PRD Maker / Splitter

You are creating Product Requirements Documents (PRDs) for a feature request.

## Workflow (mandatory)

1. Classify intent (trivial / explicit / exploratory / open-ended / ambiguous).
2. Explore with `pm-explorer` (parallel) to find existing patterns if the feature touches code.
3. Use `pm-researcher` for external libraries or APIs.
4. Plan with Analyser → Powerplanner → Planreviewer review loop.
5. Determine PRD split (how many, what domains, dependencies).
6. **Delegate PRD writing to sub-agents** (see below).

## Split Rules (always applied, no need to restate)

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

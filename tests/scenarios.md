# Powermode test scenarios

Manual scenarios to validate commands, hooks, and specialist agents. These are ordered from complex to light. Each scenario lists a prompt and the expected evidence.

## 1) Planning loop quality (metis + prometheus + momus)

Purpose
- Validate /pm-plan orchestration and plan review quality.

Steps
1. Run: `/pm-plan`
2. Prompt:
   "Add multi-tenant billing with per-tenant rate limits, invoice export, and audit log. Keep existing API structure."

Expected evidence
- pm-metis runs first and flags hidden requirements and ambiguities.
- pm-prometheus produces a structured plan with file paths and verification steps.
- pm-momus reviews the plan and returns NEEDS REVISION if gaps exist.
- After revisions, pm-momus can return OKAY.

## 2) Architecture decision (oracle)

Purpose
- Validate deep architecture reasoning and structured output from pm-oracle.

Setup
- Create a minimal PRD file: `resources/prd/orchestrator/01-architecture.md` with tradeoffs (event sourcing vs relational) and constraints (scale, auditability, cost).

Steps
1. Run: `/powermode @resources/prd/orchestrator/01-architecture.md`
2. Prompt: "Choose an architecture and justify the decision."

Expected evidence
- pm-oracle is consulted for the decision.
- Output follows the pm-oracle format (Analysis, Options Evaluated, Recommendation, Risks).
- Recommendation is tied to constraints from the PRD.

## 3) External docs research (librarian)

Purpose
- Validate external documentation research and citation quality.

Steps
1. Run: `/powermode`
2. Prompt: "Use pm-librarian to summarize the official OpenAPI 3.1 spec changes vs 3.0. Cite sources."

Expected evidence
- pm-librarian is used for research.
- Sources are cited and match official docs.
- Summary is concise and accurate.

## 4) PRD index auto-inject + PRD enforcement

Purpose
- Validate README index injection and stop-validator PRD enforcement.

Steps
1. Run: `/pm-prdmaker` with a long feature request that splits into multiple PRDs.
2. Confirm a folder with `README.md` index was created under `resources/prd/<feature>/`.
3. Run: `/powermode @resources/prd/<feature>/02-<name>.md`
4. Attempt to stop without editing the referenced PRD.
5. Edit the PRD file and attempt to stop again.

Expected evidence
- `README.md` is auto-injected when referencing a PRD in the folder.
- `.powermode/prd-index-state.json` records the injected folder.
- Stop hook blocks until the referenced PRD was updated.

## 5) Stop hook todo enforcement + escape hatch

Purpose
- Validate stop hook behavior for incomplete todos.

Steps
1. Create a todo list with 2 items (any small task).
2. Mark only one as completed.
3. Attempt to stop.
4. Attempt to stop 3 times without completing all todos.

Expected evidence
- Stop hook blocks due to incomplete todos.
- After 3 consecutive attempts, escape hatch allows stopping with a warning.

## 6) Context monitor state file (light)

Purpose
- Validate context tracking state file creation and updates.

Steps
1. Run: `/powermode`
2. Perform several tool calls (Read/Glob/Grep/Bash).
3. Check `.powermode/context-state.json` in the workspace.

Expected evidence
- `.powermode/context-state.json` exists and updates tool counts.

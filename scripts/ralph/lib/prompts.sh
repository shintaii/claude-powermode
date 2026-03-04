#!/usr/bin/env bash
# lib/prompts.sh — Prompt templates for each RALPH session type

# ── Planning prompts ────────────────────────────────────────────────────────

build_plan_prompt() {
    local goal="$1"
    cat <<EOF
/pm-plan $goal

This is an automated RALPH planning session.
Complete the FULL planning phase in this single session:

1. Research the goal (read existing code, understand requirements)
2. Create project structure: project.md, status.json, feature directories
3. Write ALL task PRD files — every task listed in the README tables needs a PRD
4. Each PRD must include: objective, scope, acceptance criteria, test focus, implementation notes
5. Each PRD must include a ## Tests section with structured table (| ID | Type | Description | Expected Result |)
6. Save research findings to research.md in the project root
7. Commit everything when done

Do NOT implement any code. Only write planning documents and PRDs.
EOF
}

build_prd_review_prompt() {
    local project_dir="$1"
    local prd_path="$2"
    local original_goal="$3"

    # Build list of all other PRD paths for context
    local other_prds=""
    for f in "$project_dir"/features/*/*.md; do
        [[ -f "$f" ]] || continue
        [[ "$(basename "$f")" == "README.md" ]] && continue
        [[ "$(basename "$f")" == "NOTES.md" ]] && continue
        [[ "$f" == "$prd_path" ]] && continue
        other_prds="$other_prds- $f"$'\n'
    done

    cat <<EOF
You are reviewing a SINGLE PRD for quality and consistency.

ORIGINAL USER GOAL:
$original_goal

FILES TO READ:
1. $project_dir/project.md (overall project scope)
2. $prd_path (THE PRD you are reviewing — this is your focus)
3. The feature README in the same directory as the PRD

OTHER PRDs in this project (read these for cross-reference):
${other_prds:-  (none)}

REVIEW CHECKLIST:
1. Does this PRD align with the original user goal?
2. Is it complete? Does it have: objective, scope, acceptance criteria, test focus?
3. Does it have a ## Tests section with concrete test cases?
4. Does it overlap or contradict any other PRD?
5. Are its dependencies correct per the feature README?
6. Is the scope right-sized — not too large, not too small?
7. Are the acceptance criteria specific and verifiable?

If changes are needed:
- Edit the PRD file directly
- Update the feature README if dependencies changed
- Commit your changes

If the PRD is good as-is, just confirm with a brief summary of what it covers.
EOF
}

# ── Implementation prompts ──────────────────────────────────────────────────

build_implement_prompt() {
    local task_prd_path="$1"
    cat <<EOF
/powermode @$task_prd_path
EOF
}

# ── Verification prompts ────────────────────────────────────────────────────

build_verify_prompt() {
    local unit_name="$1"
    local unit_path="$2"
    local scope="$3"

    cat <<EOF
Run verification on: $unit_name (scope: $scope)

Read the PRD(s) at: $unit_path

Perform comprehensive verification:
1. Static analysis — lint, type checking if applicable
2. Build check — does it compile/build cleanly?
3. Test execution — run relevant tests, check coverage
4. Stub detection — find any TODO/FIXME/placeholder implementations
5. Security scan — check for obvious vulnerabilities
6. PRD compliance — does the implementation match acceptance criteria?
7. Defined test verification — read ## Tests from PRD, verify each defined test passes or exists

Output your verdict as exactly one of:
- VERDICT: PASS
- VERDICT: FAIL
- VERDICT: PASS WITH NOTES

If FAIL or PASS WITH NOTES, list issues with severity:
- BLOCKER: [description]
- MAJOR: [description]
- MINOR: [description]
EOF
}

build_fix_prompt() {
    local unit_name="$1"
    local verify_output="$2"

    cat <<EOF
Fix verification issues for: $unit_name

The verifier found these issues:
$verify_output

Fix BLOCKER and MAJOR issues only. Ignore MINOR issues.
Run tests after fixing to confirm the fixes work.
Commit your fixes.
EOF
}

build_simplify_prompt() {
    local unit_name="$1"

    cat <<EOF
/simplify

Run the simplify skill on recent changes for: $unit_name
Focus on code reuse, quality, and efficiency.
Only make minimal, safe improvements.
Commit any changes.
EOF
}

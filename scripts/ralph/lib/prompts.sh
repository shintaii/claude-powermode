#!/usr/bin/env bash
# lib/prompts.sh — Prompt templates for each RALPH session type

# ── System prompt context injection ────────────────────────────────────────
# Builds --append-system-prompt content with project state awareness

build_system_context() {
    local project_dir="$1"
    local session_type="$2"  # plan|implement|verify|fix|simplify
    local task_info="${3:-}"  # e.g., "01-cli-todo-core/02-core-module"

    local context=""

    # Project structure awareness
    context+="You are running inside a RALPH automated session (type: $session_type)."$'\n'
    context+="This is a non-interactive session — complete your work fully, then stop."$'\n'
    context+="Do not use ToolSearch — the /powermode skill is already available."$'\n'
    context+=""$'\n'

    # Status.json location and update instructions
    if [[ -f "$project_dir/status.json" ]]; then
        context+="PROJECT STATE:"$'\n'
        context+="- status.json: $project_dir/status.json"$'\n'
        context+="- Project dir: $project_dir"$'\n'

        # Include current status summary
        local status_summary
        status_summary=$(python3 -c "
import json
with open('$project_dir/status.json') as f:
    data = json.load(f)
features = data.get('features', {})
for fk in sorted(features.keys()):
    f = features[fk]
    tasks = f.get('tasks', {})
    done = sum(1 for v in tasks.values() if v == 'done')
    total = len(tasks)
    print(f'  {fk}: {done}/{total} done')
    for tk in sorted(tasks.keys()):
        print(f'    {tk}: {tasks[tk]}')
" 2>/dev/null || echo "  (could not read)")
        context+="$status_summary"$'\n'
        context+=""$'\n'
    fi

    # Session-type specific instructions
    case "$session_type" in
        test-write)
            context+="You are writing FAILING TESTS from a PRD. This is a test-first session."$'\n'
            context+="RULES:"$'\n'
            context+="- You write test files ONLY. You may NOT write production/source code."$'\n'
            context+="- Every test must FAIL when run. If a test passes, investigate why."$'\n'
            context+="- Each test maps to a Test ID from the PRD's ## Tests table."$'\n'
            context+="- Use real assertions with exact expected values. No placeholder assertions."$'\n'
            context+="- Detect the project's test framework and follow existing conventions."$'\n'
            context+="- Run the tests to confirm they fail. Fix syntax errors only."$'\n'
            context+="- Commit test files when done."$'\n'
            if [[ -n "$task_info" ]]; then
                context+=""$'\n'
                context+="You are writing tests for task: $task_info"$'\n'
            fi
            ;;
        implement)
            context+="THE FULL TDD CYCLE MUST COMPLETE:"$'\n'
            context+="1. Test files already exist (written by test-write session). Do NOT modify them."$'\n'
            context+="2. Implement the task (delegate to pm-implementer) — make tests pass"$'\n'
            context+="3. Verify with pm-verifier — if FAIL or PASS WITH NOTES, fix and re-verify (max 3 attempts)"$'\n'
            context+="4. Run /simplify after verification passes"$'\n'
            context+="5. Update the task status to 'Done' in the feature README table"$'\n'
            context+="6. Update status.json — set the task status to 'done' and increment tasks_done"$'\n'
            context+="7. Commit all changes including status.json"$'\n'
            context+=""$'\n'
            context+="CRITICAL: Test files are READ-ONLY. Do NOT create, modify, or delete test files."$'\n'
            context+="Do NOT mark a task as done if tests fail or verification fails."$'\n'
            if [[ -n "$task_info" ]]; then
                context+=""$'\n'
                context+="You are implementing task: $task_info"$'\n'
            fi
            ;;
        verify)
            context+="Output your verdict as exactly one of: VERDICT: PASS / VERDICT: FAIL / VERDICT: PASS WITH NOTES"$'\n'
            context+="Tests were written by pm-test-writer, code by pm-implementer."$'\n'
            context+="Run tests once as sanity check. Focus on quality gates:"$'\n'
            context+="- Stub/placeholder detection"$'\n'
            context+="- Wiring verification (is new code reachable?)"$'\n'
            context+="- CLAUDE.md compliance"$'\n'
            context+="- Simplicity review"$'\n'
            context+="- Comment audit"$'\n'
            ;;
        fix)
            context+="Fix BLOCKER and MAJOR issues only. Run tests after fixing. Commit fixes."$'\n'
            context+="CRITICAL: Do NOT modify test files. Only fix production code."$'\n'
            ;;
    esac

    # Include decisions.md if it exists
    if [[ -f "$project_dir/decisions.md" ]]; then
        context+=""$'\n'
        context+="PRIOR DECISIONS (read $project_dir/decisions.md for full context):"$'\n'
        # Include last 10 lines as preview
        context+="$(tail -10 "$project_dir/decisions.md" 2>/dev/null)"$'\n'
    fi

    # Include issues.md if it exists
    if [[ -f "$project_dir/issues.md" ]]; then
        context+=""$'\n'
        context+="KNOWN ISSUES (read $project_dir/issues.md for full context):"$'\n'
        context+="$(tail -10 "$project_dir/issues.md" 2>/dev/null)"$'\n'
    fi

    echo "$context"
}

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

# ── Test writing prompts ───────────────────────────────────────────────────

build_test_write_prompt() {
    local task_prd_path="$1"
    cat <<EOF
Read this task PRD and write failing tests: @$task_prd_path

Use the pm-test-writer agent to create real, runnable test files from the PRD's ## Tests section.
Detect the project's test framework. Write one test per Test ID. Run them to confirm they all fail.
Commit the test files.

Do NOT write any production code. Only test files.
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

#!/usr/bin/env bash
# ralph-plan.sh — PRD review loop
# Assumes pm-plan was already run. Reviews each PRD in a fresh session,
# cross-checking against the original goal + project.md + other PRDs.

set -euo pipefail

REAL_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || python3 -c "import os; print(os.path.realpath('${BASH_SOURCE[0]}'))")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_PATH")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/status.sh"
source "$SCRIPT_DIR/lib/prompts.sh"

# ── Parse args ──────────────────────────────────────────────────────────────
POSITIONAL_ARGS=()
parse_common_args "$@"

if [[ ${#POSITIONAL_ARGS[@]} -lt 1 ]]; then
    log_error "Usage: ralph plan <project-slug> [--model X] [--budget X]"
    echo "  Run pm-plan first to create the project, then ralph plan to review PRDs."
    exit 1
fi

slug="${POSITIONAL_ARGS[0]}"
project_dir=$(get_project_path "$slug") || { log_error "Project '$slug' not found. Run pm-plan first."; exit 1; }

REVIEW_MODEL="${RALPH_MODEL:-${RALPH_REVIEW_MODEL:-sonnet}}"
BUDGET="${RALPH_BUDGET:-${RALPH_MAX_BUDGET:-2.00}}"

SESSION_START_TIME=$(date +%s)
init_log "plan" "$slug"

# ── Read original goal ─────────────────────────────────────────────────────
GOAL=""
if [[ -f "$project_dir/goal.md" ]]; then
    GOAL=$(cat "$project_dir/goal.md")
elif [[ ${#POSITIONAL_ARGS[@]} -ge 2 ]]; then
    GOAL="${POSITIONAL_ARGS[1]}"
fi

if [[ -z "$GOAL" ]]; then
    log_warn "No goal.md found — reviews will lack original goal context"
    log_info "Tip: echo 'your goal' > $project_dir/goal.md"
fi

# ── Collect PRD files ────────────────────────────────────────────────────────
prd_files=()
for feature_dir in "$project_dir"/features/*/; do
    [[ -d "$feature_dir" ]] || continue
    for prd_file in "$feature_dir"/*.md; do
        [[ -f "$prd_file" ]] || continue
        [[ "$(basename "$prd_file")" == "README.md" ]] && continue
        [[ "$(basename "$prd_file")" == "NOTES.md" ]] && continue
        prd_files+=("$prd_file")
    done
done

if [[ ${#prd_files[@]} -eq 0 ]]; then
    log_error "No PRD files found in $project_dir/features/"
    exit 1
fi

# ── Header ──────────────────────────────────────────────────────────────────
IFS='|' read -r status total done _ _ <<< "$(read_project_status "$project_dir")"

print_header "RALPH Review: $slug"
echo -e "  PRDs: ${#prd_files[@]} | Model: $REVIEW_MODEL | Budget: \$$BUDGET/session"
echo ""

# ── Review loop ──────────────────────────────────────────────────────────────
reviewed=0
review_failed=0

for prd_path in "${prd_files[@]}"; do
    reviewed=$((reviewed + 1))
    prd_rel="${prd_path#"$project_dir"/features/}"

    log_run "Review $reviewed/${#prd_files[@]}: $prd_rel"

    prompt=$(build_prd_review_prompt "$project_dir" "$prd_path" "$GOAL")
    review_context=$(build_system_context "$project_dir" "plan" "$prd_rel")
    review_flags=("--model" "$REVIEW_MODEL" "--max-turns" "15" "--max-budget-usd" "$BUDGET" "--append-system-prompt" "$review_context")

    if run_claude_session "$prompt" "${review_flags[@]}"; then
        log_success "$prd_rel ($(format_session_stats))"
        # Show what the reviewer found/did
        print_session_result "$CLAUDE_RESULT" "$CLAUDE_LINES_ADDED" "$CLAUDE_LINES_REMOVED"
        append_log "Review $reviewed ($prd_rel): cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s turns=$CLAUDE_TURNS tokens_in=$CLAUDE_TOKENS_IN tokens_out=$CLAUDE_TOKENS_OUT error=false"
    else
        log_error "Review failed: $prd_rel"
        if [[ -n "$CLAUDE_ERROR" ]]; then
            echo -e "          ${DIM}Error: ${CLAUDE_ERROR:0:200}${RESET}"
        fi
        append_log "Review $reviewed ($prd_rel): cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s turns=$CLAUDE_TURNS tokens_in=$CLAUDE_TOKENS_IN tokens_out=$CLAUDE_TOKENS_OUT error=true"
        review_failed=$((review_failed + 1))
    fi
done

# ── Summary ─────────────────────────────────────────────────────────────────
IFS='|' read -r status total done _ _ <<< "$(read_project_status "$project_dir")"
status_msg=""
if [[ $review_failed -gt 0 ]]; then
    status_msg="$review_failed review(s) failed — check and re-run"
else
    status_msg="All PRDs reviewed — next: ralph implement $slug"
fi

print_summary "$reviewed" "$review_failed" "$total" "$done" "$status_msg"
echo -e "  Log: $LOG_FILE"
echo ""

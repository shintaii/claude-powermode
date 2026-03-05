#!/usr/bin/env bash
# ralph-implement.sh — Implementation RALPH loop
# Implements a project PRD-by-PRD in fresh sessions

set -euo pipefail

REAL_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || python3 -c "import os; print(os.path.realpath('${BASH_SOURCE[0]}'))")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_PATH")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/status.sh"
source "$SCRIPT_DIR/lib/blockers.sh"
source "$SCRIPT_DIR/lib/prompts.sh"

# ── Parse args ──────────────────────────────────────────────────────────────
POSITIONAL_ARGS=()
parse_common_args "$@"

if [[ ${#POSITIONAL_ARGS[@]} -lt 1 ]]; then
    log_error "Usage: ralph implement <project-slug> [--feature X] [--model X] [--budget X] [--max-iters N]"
    exit 1
fi

slug="${POSITIONAL_ARGS[0]}"
project_dir=$(get_project_path "$slug") || { log_error "Project '$slug' not found"; exit 1; }

MODEL="${RALPH_MODEL:-${RALPH_IMPLEMENT_MODEL:-opus}}"
BUDGET="${RALPH_BUDGET:-${RALPH_MAX_BUDGET:-10.00}}"
MAX_ITERS="${RALPH_MAX_ITERS:-${RALPH_MAX_ITERATIONS:-50}}"
FEATURE_FILTER="${RALPH_FEATURE:-}"

SESSION_START_TIME=$(date +%s)
init_log "implement" "$slug"

# ── Header ──────────────────────────────────────────────────────────────────
IFS='|' read -r status total done next_feat next_task <<< "$(read_project_status "$project_dir")"

print_header "RALPH Implement: $slug"
echo -e "  Status: $done/$total done ($status)"
if [[ -n "$FEATURE_FILTER" ]]; then
    echo -e "  Filter: feature=$FEATURE_FILTER"
fi
echo -e "  ${DIM}Model: $MODEL | Budget: \$$BUDGET/session | Max: $MAX_ITERS iterations${RESET}"
echo ""

# ── Main loop ───────────────────────────────────────────────────────────────
iteration=0
tasks_done=0
tasks_failed=0

while [[ $iteration -lt $MAX_ITERS ]]; do
    iteration=$((iteration + 1))
    elapsed=0
    if [[ -n "$SESSION_START_TIME" ]]; then
        elapsed=$(( $(date +%s) - SESSION_START_TIME ))
    fi

    # 1. Check blockers
    if check_blocked "$project_dir"; then
        log_error "BLOCKED.md exists"
        echo -e "         $(get_blocker_message "$project_dir")"
        append_log "Iteration $iteration: BLOCKED — $(get_blocker_message "$project_dir")"
        break
    fi

    if check_blocking_issues "$project_dir"; then
        log_error "High-severity blocking issues found"
        get_blocking_issue_summary "$project_dir"
        append_log "Iteration $iteration: BLOCKED — high-severity issues"
        break
    fi

    # 2. Find next task
    local_next_feat=""
    local_next_task=""
    local_task_prd=""

    for feature_dir in "$project_dir"/features/*/; do
        [[ -d "$feature_dir" ]] || continue
        feature_name=$(basename "$feature_dir")

        # Apply feature filter
        if [[ -n "$FEATURE_FILTER" && "$feature_name" != *"$FEATURE_FILTER"* ]]; then
            continue
        fi

        pending=$(get_pending_tasks_ordered "$feature_dir")
        while IFS= read -r task_file; do
            [[ -z "$task_file" ]] && continue

            # Check if this task's deps are met
            task_num="${task_file%%-*}"
            # Read deps from README
            deps=$(python3 -c "
import re
with open('$feature_dir/README.md') as f:
    for line in f:
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) >= 6 and cells[1].strip() == '$task_file':
            print(cells[4])
            break
" 2>/dev/null || echo "None")

            if check_deps_met "$project_dir" "$feature_name" "$deps"; then
                local_next_feat="$feature_name"
                local_next_task="$task_file"
                local_task_prd="$feature_dir/$task_file"
                break 2
            fi
        done <<< "$pending"
    done

    # No more tasks
    if [[ -z "$local_next_task" ]]; then
        log_success "No more pending tasks with met dependencies"
        break
    fi

    # 3. Run implementation session
    log_run "Iteration $iteration: $local_next_feat/$local_next_task ($(format_duration $elapsed) elapsed)"

    prompt=$(build_implement_prompt "$local_task_prd")
    system_context=$(build_system_context "$project_dir" "implement" "$local_next_feat/$local_next_task")
    impl_flags=("--model" "$MODEL" "--max-turns" "50" "--max-budget-usd" "$BUDGET" "--append-system-prompt" "$system_context")

    if run_claude_session "$prompt" "${impl_flags[@]}"; then
        log_success "$local_next_feat/$local_next_task ($(format_session_stats))"
        print_session_result "$CLAUDE_RESULT" "$CLAUDE_LINES_ADDED" "$CLAUDE_LINES_REMOVED"
        append_log "Iteration $iteration ($local_next_feat/$local_next_task): cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s turns=$CLAUDE_TURNS tokens_in=$CLAUDE_TOKENS_IN tokens_out=$CLAUDE_TOKENS_OUT error=false"
    else
        log_error "$local_next_feat/$local_next_task failed: $CLAUDE_ERROR"
        append_log "Iteration $iteration ($local_next_feat/$local_next_task): cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s turns=$CLAUDE_TURNS tokens_in=$CLAUDE_TOKENS_IN tokens_out=$CLAUDE_TOKENS_OUT error=true"
        tasks_failed=$((tasks_failed + 1))
        # Continue to next task rather than stopping entirely
        continue
    fi

    # 4. Post-checks
    # Re-read status to check if task was marked done
    task_base="${local_next_task%.md}"
    if is_task_done "$project_dir" "$local_next_feat" "$task_base"; then
        tasks_done=$((tasks_done + 1))
        IFS='|' read -r _ _ updated_done _ _ <<< "$(read_project_status "$project_dir")"
        log_success "Task marked done ($updated_done/$total total)"
    else
        # Drift repair: README may say Done but status.json wasn't updated
        sync_result=$(sync_readme_to_status "$project_dir" "$local_next_feat" 2>/dev/null || echo "error")
        if [[ "$sync_result" == "synced" ]] && is_task_done "$project_dir" "$local_next_feat" "$task_base"; then
            tasks_done=$((tasks_done + 1))
            IFS='|' read -r _ _ updated_done _ _ <<< "$(read_project_status "$project_dir")"
            log_success "Task done (synced from README) ($updated_done/$total total)"
        else
            log_warn "Task not marked done — may need manual check"
        fi
    fi

    # Check if blockers appeared during implementation
    if check_blocked "$project_dir"; then
        log_error "BLOCKED.md created during implementation"
        echo -e "         $(get_blocker_message "$project_dir")"
        append_log "Post-iteration $iteration: BLOCKED.md appeared"
        break
    fi

    if check_blocking_issues "$project_dir"; then
        log_error "New blocking issues detected"
        get_blocking_issue_summary "$project_dir"
        append_log "Post-iteration $iteration: blocking issues appeared"
        break
    fi
done

if [[ $iteration -ge $MAX_ITERS ]]; then
    log_warn "Reached max iterations ($MAX_ITERS)"
fi

# ── Summary ─────────────────────────────────────────────────────────────────
IFS='|' read -r status total done _ _ <<< "$(read_project_status "$project_dir")"

status_msg=""
if check_blocked "$project_dir" 2>/dev/null; then
    status_msg="BLOCKED — resolve BLOCKED.md then: ralph implement $slug"
elif [[ $done -ge $total ]]; then
    status_msg="Complete — next: ralph verify $slug"
else
    status_msg="Paused at $done/$total — resume: ralph implement $slug"
fi

print_summary "$tasks_done" "$tasks_failed" "$total" "$done" "$status_msg"
echo -e "  Log: $LOG_FILE"
echo ""

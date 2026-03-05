#!/usr/bin/env bash
# ralph-verify.sh — Verify + simplify RALPH loop
# Iterative verify → fix → simplify until clean per unit

set -euo pipefail

REAL_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || python3 -c "import os; print(os.path.realpath('${BASH_SOURCE[0]}'))")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_PATH")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/status.sh"
source "$SCRIPT_DIR/lib/prompts.sh"

# ── Parse args ──────────────────────────────────────────────────────────────
POSITIONAL_ARGS=()
SCOPE=""

# Parse --scope separately, then common args
TEMP_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --scope) SCOPE="$2"; shift 2 ;;
        *)       TEMP_ARGS+=("$1"); shift ;;
    esac
done
parse_common_args "${TEMP_ARGS[@]}"

if [[ ${#POSITIONAL_ARGS[@]} -lt 1 ]]; then
    log_error "Usage: ralph verify <project-slug> [--scope feature|project] [--feature X] [--max-iters N]"
    exit 1
fi

slug="${POSITIONAL_ARGS[0]}"
project_dir=$(get_project_path "$slug") || { log_error "Project '$slug' not found"; exit 1; }

VERIFY_MODEL="${RALPH_MODEL:-${RALPH_VERIFY_MODEL:-sonnet}}"
FIX_MODEL="${RALPH_FIX_MODEL:-opus}"
MAX_VERIFY_ITERS="${RALPH_MAX_ITERS:-${RALPH_MAX_VERIFY_ITERS:-3}}"
FEATURE_FILTER="${RALPH_FEATURE:-}"

SESSION_START_TIME=$(date +%s)
init_log "verify" "$slug"

# ── Auto-detect scope ──────────────────────────────────────────────────────
# Task-level verification is handled by powermode during implementation.
# Ralph verify only runs at feature or project level (cross-cutting checks).
if [[ -z "$SCOPE" ]]; then
    # Count features to decide
    feature_count=0
    for fd in "$project_dir"/features/*/; do
        [[ -d "$fd" ]] && feature_count=$((feature_count + 1))
    done
    if [[ $feature_count -le 3 ]]; then
        SCOPE="feature"
    else
        SCOPE="project"
    fi
    log_info "Auto-detected scope: $SCOPE ($feature_count features)"
elif [[ "$SCOPE" == "task" ]]; then
    log_warn "Task-level verification is already done by powermode during implementation."
    log_warn "Use --scope feature or --scope project for cross-cutting verification."
    SCOPE="feature"
fi

IFS='|' read -r status total done _ _ <<< "$(read_project_status "$project_dir")"

print_header "RALPH Verify: $slug"
echo -e "  Status: $done/$total done | Scope: $SCOPE"
echo -e "  ${DIM}Verify: $VERIFY_MODEL | Fix: $FIX_MODEL | Max iters: $MAX_VERIFY_ITERS${RESET}"
echo ""

# ── Build verification units ───────────────────────────────────────────────
# Each unit = (name, path, scope)
UNITS=()

case "$SCOPE" in
    feature)
        for feature_dir in "$project_dir"/features/*/; do
            [[ -d "$feature_dir" ]] || continue
            feature_name=$(basename "$feature_dir")
            if [[ -n "$FEATURE_FILTER" && "$feature_name" != *"$FEATURE_FILTER"* ]]; then
                continue
            fi
            UNITS+=("$feature_name|$feature_dir|feature")
        done
        ;;
    project)
        UNITS+=("$slug|$project_dir|project")
        ;;
esac

if [[ ${#UNITS[@]} -eq 0 ]]; then
    log_info "No verification units found"
    exit 0
fi

log_info "Found ${#UNITS[@]} verification unit(s)"

# ── Verify each unit ───────────────────────────────────────────────────────
units_passed=0
units_failed=0
units_warned=0

for unit_entry in "${UNITS[@]}"; do
    IFS='|' read -r unit_name unit_path unit_scope <<< "$unit_entry"

    echo ""
    log_run "Verifying: $unit_name ($unit_scope)"

    verify_iter=0
    unit_passed=false
    last_verify_output=""

    while [[ $verify_iter -lt $MAX_VERIFY_ITERS ]]; do
        verify_iter=$((verify_iter + 1))

        # ── VERIFY session ──────────────────────────────────────────────
        prompt=$(build_verify_prompt "$unit_name" "$unit_path" "$unit_scope")
        system_context=$(build_system_context "$project_dir" "verify" "$unit_name")
        verify_flags=("--model" "$VERIFY_MODEL" "--max-turns" "25" "--max-budget-usd" "3.00" "--append-system-prompt" "$system_context")

        if run_claude_session "$prompt" "${verify_flags[@]}"; then
            log_success "Verify pass $verify_iter ($(format_session_stats))"
            print_session_result "$CLAUDE_RESULT" "$CLAUDE_LINES_ADDED" "$CLAUDE_LINES_REMOVED"
            append_log "Verify $unit_name iter=$verify_iter: cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s error=false"
        else
            log_error "Verify session failed"
            append_log "Verify $unit_name iter=$verify_iter: cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s error=true"
            break
        fi

        last_verify_output="$CLAUDE_RESULT"

        # Parse verdict
        verdict=$(python3 -c "
import re
text = '''$CLAUDE_RESULT'''
m = re.search(r'VERDICT:\s*(PASS WITH NOTES|PASS|FAIL)', text, re.IGNORECASE)
if m:
    print(m.group(1).upper())
else:
    print('UNKNOWN')
")

        case "$verdict" in
            PASS)
                log_success "Verdict: PASS"
                unit_passed=true
                break
                ;;
            FAIL|"PASS WITH NOTES")
                log_warn "Verdict: $verdict (iter $verify_iter/$MAX_VERIFY_ITERS)"

                if [[ $verify_iter -ge $MAX_VERIFY_ITERS ]]; then
                    log_warn "Max verify iterations reached"
                    break
                fi

                # ── FIX session ─────────────────────────────────────────
                log_run "Fix session (model: $FIX_MODEL)"
                fix_prompt=$(build_fix_prompt "$unit_name" "$last_verify_output")
                fix_context=$(build_system_context "$project_dir" "fix" "$unit_name")
                fix_flags=("--model" "$FIX_MODEL" "--max-turns" "30" "--max-budget-usd" "5.00" "--append-system-prompt" "$fix_context")

                if run_claude_session "$fix_prompt" "${fix_flags[@]}"; then
                    log_success "Fix applied ($(format_session_stats))"
                    print_session_result "$CLAUDE_RESULT" "$CLAUDE_LINES_ADDED" "$CLAUDE_LINES_REMOVED"
                    append_log "Fix $unit_name iter=$verify_iter: cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s error=false"
                else
                    log_error "Fix session failed"
                    append_log "Fix $unit_name iter=$verify_iter: cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s error=true"
                    break
                fi
                ;;
            *)
                log_warn "Could not parse verdict — treating as FAIL"
                break
                ;;
        esac
    done

    # ── SIMPLIFY session ────────────────────────────────────────────────
    log_run "Simplify: $unit_name"
    simplify_prompt=$(build_simplify_prompt "$unit_name")
    simplify_context=$(build_system_context "$project_dir" "simplify" "$unit_name")
    simplify_flags=("--model" "$VERIFY_MODEL" "--max-turns" "15" "--max-budget-usd" "2.00" "--append-system-prompt" "$simplify_context")

    if run_claude_session "$simplify_prompt" "${simplify_flags[@]}"; then
        log_success "Simplify ($(format_session_stats))"
        print_session_result "$CLAUDE_RESULT" "$CLAUDE_LINES_ADDED" "$CLAUDE_LINES_REMOVED"
        append_log "Simplify $unit_name: cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s error=false"
    else
        log_warn "Simplify session failed — continuing"
        append_log "Simplify $unit_name: cost=$CLAUDE_COST duration=${CLAUDE_DURATION}s error=true"
    fi

    # ── FINAL VERIFY (regression check) ─────────────────────────────────
    log_run "Final verify (regression check): $unit_name"
    prompt=$(build_verify_prompt "$unit_name" "$unit_path" "$unit_scope")
    final_context=$(build_system_context "$project_dir" "verify" "$unit_name")
    final_flags=("--model" "$VERIFY_MODEL" "--max-turns" "20" "--max-budget-usd" "2.00" "--append-system-prompt" "$final_context")

    if run_claude_session "$prompt" "${final_flags[@]}"; then
        final_verdict=$(python3 -c "
import re
text = '''$CLAUDE_RESULT'''
m = re.search(r'VERDICT:\s*(PASS WITH NOTES|PASS|FAIL)', text, re.IGNORECASE)
if m:
    print(m.group(1).upper())
else:
    print('UNKNOWN')
")
        case "$final_verdict" in
            PASS|"PASS WITH NOTES")
                log_success "$unit_name: CLEAN"
                units_passed=$((units_passed + 1))
                ;;
            *)
                log_warn "$unit_name: NEEDS MANUAL REVIEW (post-simplify regression)"
                units_warned=$((units_warned + 1))
                ;;
        esac
        append_log "Final verify $unit_name: verdict=$final_verdict cost=$CLAUDE_COST"
    else
        log_error "Final verify failed"
        units_failed=$((units_failed + 1))
        append_log "Final verify $unit_name: error=true cost=$CLAUDE_COST"
    fi
done

# ── Summary ─────────────────────────────────────────────────────────────────
total_units=${#UNITS[@]}
status_msg=""
if [[ $units_warned -gt 0 || $units_failed -gt 0 ]]; then
    status_msg="$units_warned need manual review, $units_failed failed"
else
    status_msg="All units clean"
fi

print_summary "$units_passed" "$units_failed" "$total_units" "$units_passed" "$status_msg"
echo -e "  Log: $LOG_FILE"
echo ""

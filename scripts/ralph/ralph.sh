#!/usr/bin/env bash
# ralph.sh — RALPH loop dispatcher
# Usage: ralph plan|implement|verify|status [args...]

set -euo pipefail

REAL_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || python3 -c "import os; print(os.path.realpath('${BASH_SOURCE[0]}'))")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_PATH")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

usage() {
    echo -e "${BOLD}RALPH${RESET} — Fresh-context loop orchestrator for Powermode"
    echo ""
    echo -e "${BOLD}Usage:${RESET}"
    echo "  ralph plan <project-slug>       [--model X] [--budget X]"
    echo "  ralph implement <project-slug>  [--feature X] [--model X] [--budget X] [--max-iters N]"
    echo "  ralph verify <project-slug>     [--scope feature|project] [--feature X] [--max-iters N]"
    echo "  ralph status <project-slug>"
    echo ""
    echo -e "${BOLD}Environment variables:${RESET}"
    echo "  RALPH_PLAN_MODEL        Model for planning session (default: opus)"
    echo "  RALPH_REVIEW_MODEL      Model for PRD review loop (default: sonnet)"
    echo "  RALPH_TEST_MODEL        Model for test-writing sessions (default: sonnet)"
    echo "  RALPH_IMPLEMENT_MODEL   Model for implementation (default: opus)"
    echo "  RALPH_VERIFY_MODEL      Model for verification (default: sonnet)"
    echo "  RALPH_FIX_MODEL         Model for fix sessions (default: opus)"
    echo "  RALPH_MAX_BUDGET        Per-session cost cap (default: 10.00)"
    echo "  RALPH_TEST_BUDGET       Per-session cost cap for test writing (default: 2.00)"
    echo "  RALPH_MAX_ITERATIONS    Max iterations safety valve (default: 50)"
    echo "  RALPH_MAX_VERIFY_ITERS  Max verify loops per unit (default: 3)"
    echo ""
    echo -e "${BOLD}Flags:${RESET}"
    echo "  --verbose, -v           Show prompts and truncated Claude output"
    echo "  --live, -l              Stream Claude's output in real-time (like interactive mode)"
    echo ""
    echo -e "${BOLD}Stopping:${RESET}"
    echo "  Ctrl+C                  Stop after current session finishes cleanup"
    echo "  kill \$(cat .ralph-pid)  Kill from another terminal"
    echo ""
    echo -e "${BOLD}Setup:${RESET}"
    echo "  ln -s <plugin-path>/scripts/ralph/ralph.sh /usr/local/bin/ralph"
}

if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
    plan|implement|verify)
        check_prerequisites
        exec bash "$SCRIPT_DIR/ralph-${COMMAND}.sh" "$@"
        ;;
    status)
        if [[ $# -lt 1 ]]; then
            log_error "Usage: ralph status <project-slug>"
            exit 1
        fi
        source "$SCRIPT_DIR/lib/status.sh"
        slug="$1"
        project_dir=$(get_project_path "$slug") || { log_error "Project '$slug' not found"; exit 1; }

        IFS='|' read -r status total done next_feat next_task <<< "$(read_project_status "$project_dir")"

        print_header "RALPH Status: $slug"
        echo -e "  Status: ${BOLD}$status${RESET}"
        echo -e "  Progress: $done/$total done"

        if [[ -n "$next_task" ]]; then
            echo -e "  Next: ${CYAN}$next_feat/$next_task${RESET}"
        else
            echo -e "  ${GREEN}All tasks complete${RESET}"
        fi

        source "$SCRIPT_DIR/lib/blockers.sh"
        if check_blocked "$project_dir"; then
            echo -e "  ${RED}BLOCKED${RESET} — $(get_blocker_message "$project_dir")"
        fi
        if check_blocking_issues "$project_dir"; then
            echo -e "  ${RED}Blocking issues:${RESET}"
            get_blocking_issue_summary "$project_dir"
        fi
        echo ""
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        echo "Run 'ralph help' for usage."
        exit 1
        ;;
esac

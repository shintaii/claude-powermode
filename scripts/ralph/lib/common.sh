#!/usr/bin/env bash
# lib/common.sh — Shared utilities for RALPH loop scripts

set -euo pipefail

# ── Ctrl+C handling ─────────────────────────────────────────────────────────
RALPH_INTERRUPTED=0

_ralph_cleanup() {
    RALPH_INTERRUPTED=1
    echo "" >&2
    echo -e "  \033[1;33m[STOP]\033[0m  Interrupted — progress saved in status.json" >&2
    echo -e "         Resume with the same command to continue." >&2
    # Kill all child processes recursively
    local children
    children=$(jobs -p 2>/dev/null)
    if [[ -n "$children" ]]; then
        kill $children 2>/dev/null || true
    fi
    # Also kill by process group
    kill -- -$$ 2>/dev/null || true
    exit 130
}

trap _ralph_cleanup INT TERM

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ── Logging ─────────────────────────────────────────────────────────────────
log_info()    { echo -e "  ${CYAN}[INFO]${RESET}  $*"; }
log_success() { echo -e "  ${GREEN}[OK]${RESET}    $*"; }
log_warn()    { echo -e "  ${YELLOW}[WARN]${RESET}  $*"; }
log_error()   { echo -e "  ${RED}[ERR]${RESET}   $*"; }
log_run()     { echo -e "  ${CYAN}[RUN]${RESET}   $*"; }

# ── Verbosity ───────────────────────────────────────────────────────────────
RALPH_VERBOSE="${RALPH_VERBOSE:-0}"
RALPH_LIVE="${RALPH_LIVE:-0}"

# ── Cost tracking ───────────────────────────────────────────────────────────
TOTAL_COST=0
TOTAL_SESSIONS=0
TOTAL_TURNS=0
TOTAL_TOKENS_IN=0
TOTAL_TOKENS_OUT=0
TOTAL_LINES_ADDED=0
TOTAL_LINES_REMOVED=0
SESSION_START_TIME=""

# ── Prerequisites ───────────────────────────────────────────────────────────
check_prerequisites() {
    local missing=()
    command -v claude >/dev/null 2>&1 || missing+=("claude")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    command -v git >/dev/null 2>&1 || missing+=("git")

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing[*]}"
        exit 1
    fi
}

# ── Core: run_claude_session ────────────────────────────────────────────────
# Usage: run_claude_session "<prompt>" [extra-flags...]
# Sets: CLAUDE_RESULT, CLAUDE_COST, CLAUDE_ERROR, CLAUDE_TURNS,
#        CLAUDE_DURATION, CLAUDE_SESSION_ID
run_claude_session() {
    local prompt="$1"
    shift
    local extra_flags=("$@")

    CLAUDE_RESULT=""
    CLAUDE_COST="0"
    CLAUDE_ERROR=""
    CLAUDE_TURNS="0"
    CLAUDE_DURATION="0"
    CLAUDE_SESSION_ID=""
    CLAUDE_TOKENS_IN="0"
    CLAUDE_TOKENS_OUT="0"
    CLAUDE_LINES_ADDED="0"
    CLAUDE_LINES_REMOVED="0"

    local start_ts
    start_ts=$(date +%s)

    # Snapshot git state before session
    local git_head_before
    git_head_before=$(git rev-parse HEAD 2>/dev/null || echo "")

    # Show prompt in verbose mode
    if [[ "$RALPH_VERBOSE" == "1" ]]; then
        echo -e "          ${DIM}━━━ Prompt ━━━${RESET}"
        echo "$prompt" | sed 's/^/          /'
        echo -e "          ${DIM}━━━━━━━━━━━━━━${RESET}"
    fi

    # Use stream-json with verbose for live progress feedback
    local tmp_output
    tmp_output=$(mktemp)
    local exit_code=0

    claude -p \
        --output-format stream-json \
        --verbose \
        --include-partial-messages \
        --dangerously-skip-permissions \
        --no-session-persistence \
        "${extra_flags[@]}" \
        "$prompt" 2>&1 | python3 -u -c "
import json, sys, time, os

verbose = os.environ.get('RALPH_VERBOSE', '0') == '1'
live = os.environ.get('RALPH_LIVE', '0') == '1'
tool_count = 0
result_data = {}
start = time.time()
in_tool = False
current_tool = ''
text_buffer = ''
live_needs_newline = False  # track if live text needs a newline before next tool line
DIM = '\033[2m'
CYAN = '\033[0;36m'
RESET = '\033[0m'

def timestamp():
    elapsed = int(time.time() - start)
    mins, secs = divmod(elapsed, 60)
    return f'{mins}m{secs:02d}s' if mins else f'{secs}s'

def flush_live_newline():
    global live_needs_newline
    if live_needs_newline:
        sys.stderr.write(f'{RESET}\n')
        sys.stderr.flush()
        live_needs_newline = False

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue

    etype = event.get('type', '')

    # ── Handle SDK-style stream events (from --include-partial-messages) ──
    if etype == 'stream_event':
        inner = event.get('event', {})
        inner_type = inner.get('type', '')

        if inner_type == 'content_block_start':
            block = inner.get('content_block', {})
            if block.get('type') == 'tool_use':
                # Flush any buffered text (verbose mode)
                if verbose and text_buffer.strip():
                    for tl in text_buffer.strip().split('\n'):
                        print(f'          {DIM}{tl}{RESET}', file=sys.stderr)
                    text_buffer = ''
                # End live text block if active
                flush_live_newline()
                current_tool = block.get('name', '?')
                tool_count += 1
                in_tool = True
                print(f'\r          \u21b3 [{tool_count}] {current_tool} ({timestamp()}){\" \" * 20}', end='', flush=True, file=sys.stderr)
            elif block.get('type') == 'text':
                in_tool = False
                if live:
                    # Start a new dimmed text block
                    sys.stderr.write(f'\n          {DIM}')
                    sys.stderr.flush()

        elif inner_type == 'content_block_delta':
            delta = inner.get('delta', {})
            if delta.get('type') == 'text_delta' and not in_tool:
                text = delta.get('text', '')
                if live and text:
                    # Stream text directly — indent newlines
                    indented = text.replace('\n', f'\n          ')
                    sys.stderr.write(indented)
                    sys.stderr.flush()
                    live_needs_newline = True
                elif verbose:
                    text_buffer += text

        elif inner_type == 'content_block_stop':
            if in_tool:
                in_tool = False
            elif live:
                flush_live_newline()

        continue

    # ── Handle assistant messages (complete turns, from --verbose) ──
    if etype == 'assistant':
        msg = event.get('message', {})
        if isinstance(msg, dict):
            for block in msg.get('content', []):
                if not isinstance(block, dict):
                    continue
                if block.get('type') == 'tool_use':
                    flush_live_newline()
                    tool_name = block.get('name', '?')
                    tool_count += 1
                    print(f'\r          \u21b3 [{tool_count}] {tool_name} ({timestamp()}){\" \" * 20}', end='', flush=True, file=sys.stderr)
                    # Show tool input in verbose mode
                    if verbose:
                        inp = block.get('input', {})
                        if isinstance(inp, dict):
                            if tool_name in ('Read', 'Glob', 'Grep'):
                                path = inp.get('file_path', inp.get('pattern', inp.get('path', '')))
                                if path:
                                    print(f'\n          {DIM}  \u2192 {path}{RESET}', end='', flush=True, file=sys.stderr)
                            elif tool_name in ('Write', 'Edit'):
                                path = inp.get('file_path', '')
                                if path:
                                    print(f'\n          {DIM}  \u2192 {path}{RESET}', end='', flush=True, file=sys.stderr)
                            elif tool_name == 'Bash':
                                cmd = inp.get('command', '')
                                if cmd:
                                    short = cmd[:80] + ('...' if len(cmd) > 80 else '')
                                    print(f'\n          {DIM}  $ {short}{RESET}', end='', flush=True, file=sys.stderr)
                elif block.get('type') == 'text':
                    if verbose and not live:
                        text = block.get('text', '')
                        if text.strip():
                            for tl in text.strip().split('\n')[:5]:
                                print(f'\n          {DIM}{tl[:120]}{RESET}', end='', flush=True, file=sys.stderr)
                            if len(text.strip().split('\n')) > 5:
                                print(f'\n          {DIM}  ... ({len(text.strip().split(chr(10)))} lines){RESET}', end='', flush=True, file=sys.stderr)

    # Capture the last event as result
    result_data = event

# Flush remaining
flush_live_newline()
if verbose and not live and text_buffer.strip():
    for tl in text_buffer.strip().split('\n'):
        print(f'          {DIM}{tl}{RESET}', file=sys.stderr)

# Clear progress line
if tool_count > 0:
    print('', file=sys.stderr)

json.dump(result_data, sys.stdout)
" > "$tmp_output" || exit_code=$?

    local end_ts
    end_ts=$(date +%s)
    CLAUDE_DURATION=$(( end_ts - start_ts ))

    local raw_output
    raw_output=$(cat "$tmp_output")
    rm -f "$tmp_output"

    if [[ $exit_code -ne 0 && -z "$raw_output" ]]; then
        CLAUDE_ERROR="Claude exited with code $exit_code"
        return 1
    fi

    # Parse result JSON
    eval "$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    cost = data.get('total_cost_usd', data.get('cost_usd', 0)) or 0
    turns = data.get('num_turns', 0) or 0
    session_id = data.get('session_id', '') or ''
    result = data.get('result', '') or ''
    is_error = data.get('is_error', False)
    usage = data.get('usage', {}) or {}
    tokens_in = usage.get('input_tokens', 0) or 0
    tokens_out = usage.get('output_tokens', 0) or 0
    # Also check for cache tokens
    cache_read = usage.get('cache_read_input_tokens', 0) or 0
    cache_create = usage.get('cache_creation_input_tokens', 0) or 0
    tokens_in = tokens_in + cache_read + cache_create
    result_escaped = result.replace(\"'\", \"'\\\"'\\\"'\")
    print(f\"CLAUDE_COST='{round(cost, 2)}'\")
    print(f\"CLAUDE_TURNS='{turns}'\")
    print(f\"CLAUDE_SESSION_ID='{session_id}'\")
    print(f\"CLAUDE_TOKENS_IN='{tokens_in}'\")
    print(f\"CLAUDE_TOKENS_OUT='{tokens_out}'\")
    print(f\"CLAUDE_RESULT='{result_escaped}'\")
    if is_error:
        error_escaped = result.replace(\"'\", \"'\\\"'\\\"'\")
        print(f\"CLAUDE_ERROR='{error_escaped}'\")
except Exception as e:
    print(f\"CLAUDE_ERROR='JSON parse error: {e}'\")
" <<< "$raw_output")"

    # Capture lines changed via git diff
    local git_head_after
    git_head_after=$(git rev-parse HEAD 2>/dev/null || echo "")
    if [[ -n "$git_head_before" && -n "$git_head_after" && "$git_head_before" != "$git_head_after" ]]; then
        local diffstat
        diffstat=$(git diff --shortstat "$git_head_before" "$git_head_after" 2>/dev/null || echo "")
        CLAUDE_LINES_ADDED=$(echo "$diffstat" | python3 -c "
import sys, re
text = sys.stdin.read()
m = re.search(r'(\d+) insertion', text)
print(m.group(1) if m else '0')
")
        CLAUDE_LINES_REMOVED=$(echo "$diffstat" | python3 -c "
import sys, re
text = sys.stdin.read()
m = re.search(r'(\d+) deletion', text)
print(m.group(1) if m else '0')
")
    fi

    # Accumulate totals
    TOTAL_COST=$(python3 -c "print(round($TOTAL_COST + ${CLAUDE_COST:-0}, 4))")
    TOTAL_SESSIONS=$(( TOTAL_SESSIONS + 1 ))
    TOTAL_TURNS=$(( TOTAL_TURNS + ${CLAUDE_TURNS:-0} ))
    TOTAL_TOKENS_IN=$(( TOTAL_TOKENS_IN + ${CLAUDE_TOKENS_IN:-0} ))
    TOTAL_TOKENS_OUT=$(( TOTAL_TOKENS_OUT + ${CLAUDE_TOKENS_OUT:-0} ))
    TOTAL_LINES_ADDED=$(( ${TOTAL_LINES_ADDED:-0} + ${CLAUDE_LINES_ADDED:-0} ))
    TOTAL_LINES_REMOVED=$(( ${TOTAL_LINES_REMOVED:-0} + ${CLAUDE_LINES_REMOVED:-0} ))

    if [[ -n "$CLAUDE_ERROR" ]]; then
        return 1
    fi
    return 0
}

# ── Formatting ──────────────────────────────────────────────────────────────
format_tokens() {
    local count="$1"
    if (( count >= 1000000 )); then
        python3 -c "print(f'{$count/1000000:.1f}M')"
    elif (( count >= 1000 )); then
        python3 -c "print(f'{$count/1000:.1f}k')"
    else
        echo "$count"
    fi
}

format_session_stats() {
    local stats="$(format_duration "$CLAUDE_DURATION"), \$$CLAUDE_COST, $(format_tokens "$CLAUDE_TOKENS_IN") in / $(format_tokens "$CLAUDE_TOKENS_OUT") out"
    if [[ "${CLAUDE_LINES_ADDED:-0}" != "0" || "${CLAUDE_LINES_REMOVED:-0}" != "0" ]]; then
        stats="$stats, +${CLAUDE_LINES_ADDED}/-${CLAUDE_LINES_REMOVED} lines"
    fi
    echo "$stats"
}

format_duration() {
    local secs="$1"
    if (( secs < 60 )); then
        echo "${secs}s"
    elif (( secs < 3600 )); then
        echo "$(( secs / 60 ))m $(( secs % 60 ))s"
    else
        echo "$(( secs / 3600 ))h $(( secs % 3600 / 60 ))m"
    fi
}

print_header() {
    local title="$1"
    echo ""
    echo -e "${BOLD}━━━ $title ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

print_summary() {
    local tasks_done="${1:-0}"
    local tasks_failed="${2:-0}"
    local total_tasks="${3:-0}"
    local total_done="${4:-$tasks_done}"
    local status_msg="${5:-}"

    echo ""
    echo -e "${BOLD}━━━ Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

    local elapsed=0
    if [[ -n "$SESSION_START_TIME" ]]; then
        elapsed=$(( $(date +%s) - SESSION_START_TIME ))
    fi

    echo -e "  Sessions: $TOTAL_SESSIONS | Duration: $(format_duration $elapsed) | Cost: \$$TOTAL_COST"
    echo -e "  Tokens: $(format_tokens $TOTAL_TOKENS_IN) in / $(format_tokens $TOTAL_TOKENS_OUT) out"
    echo -e "  Lines: +${TOTAL_LINES_ADDED:-0} / -${TOTAL_LINES_REMOVED:-0}"
    echo -e "  Tasks: $tasks_done completed, $tasks_failed failed"
    echo -e "  Progress: $total_done/$total_tasks done"

    if [[ -n "$status_msg" ]]; then
        echo -e "  ${YELLOW}$status_msg${RESET}"
    fi
}

# ── Session result display ──────────────────────────────────────────────────
# Shows a brief summary of what a session did — truncated result + change indicator
# Usage: print_session_result "$CLAUDE_RESULT" "$CLAUDE_LINES_ADDED" "$CLAUDE_LINES_REMOVED"
print_session_result() {
    local result="$1"
    local lines_added="${2:-0}"
    local lines_removed="${3:-0}"

    # Show change indicator
    if [[ "$lines_added" != "0" || "$lines_removed" != "0" ]]; then
        echo -e "          ${GREEN}Changed: +${lines_added}/-${lines_removed} lines${RESET}"
    else
        echo -e "          ${DIM}No file changes${RESET}"
    fi

    # Show truncated result (first 3 meaningful lines)
    if [[ -n "$result" ]]; then
        local summary
        summary=$(python3 -c "
import sys
text = sys.stdin.read().strip()
# Skip empty lines, get first 3 meaningful lines
lines = [l.strip() for l in text.split('\n') if l.strip()]
for line in lines[:3]:
    # Truncate long lines
    if len(line) > 120:
        line = line[:117] + '...'
    print(line)
" <<< "$result" 2>/dev/null || true)
        if [[ -n "$summary" ]]; then
            while IFS= read -r line; do
                echo -e "          ${DIM}$line${RESET}"
            done <<< "$summary"
        fi
    fi
}

# ── Logging to file ─────────────────────────────────────────────────────────
LOG_FILE=""

init_log() {
    local type="$1"
    local slug="$2"
    local log_dir="${RALPH_LOG_DIR:-.powermode/ralph}"
    mkdir -p "$log_dir"
    LOG_FILE="$log_dir/${type}-${slug}-$(date +%Y%m%dT%H%M%S).log"
}

append_log() {
    local msg="$1"
    if [[ -n "$LOG_FILE" ]]; then
        echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $msg" >> "$LOG_FILE"
    fi
}

# ── Arg parsing helpers ─────────────────────────────────────────────────────
parse_common_args() {
    # Sets global vars from common flags
    RALPH_SLUG=""
    RALPH_FEATURE=""
    RALPH_MODEL=""
    RALPH_BUDGET=""
    RALPH_MAX_ITERS=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --slug)     RALPH_SLUG="$2"; shift 2 ;;
            --feature)  RALPH_FEATURE="$2"; shift 2 ;;
            --model)    RALPH_MODEL="$2"; shift 2 ;;
            --budget)   RALPH_BUDGET="$2"; shift 2 ;;
            --max-iters) RALPH_MAX_ITERS="$2"; shift 2 ;;
            --verbose|-v) RALPH_VERBOSE=1; export RALPH_VERBOSE; shift ;;
            --live|-l) RALPH_LIVE=1; export RALPH_LIVE; shift ;;
            *)          POSITIONAL_ARGS+=("$1"); shift ;;
        esac
    done
}

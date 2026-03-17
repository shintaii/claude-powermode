---
name: pm-codex-review
description: Run Codex CLI (GPT-5.4) as independent code reviewer, feed findings to implementer
allowed-tools: "*"
---

# Codex Code Review

Run OpenAI's Codex CLI as an independent second-opinion code reviewer, then optionally feed findings to pm-implementer.

## Arguments

```
$ARGUMENTS
```

## Parse Arguments

Extract from `$ARGUMENTS`:

**Review mode** (first positional word determines mode):
- `pr [number]` — Review a pull request. If number given, review that PR. If omitted, review the current branch's PR.
- `commit <ref>` — Review a specific commit (hash, branch name, HEAD~2, etc.)
- `branch [base]` — Review all commits on current branch since diverging from base (default: `main`)
- `staged` — Review only staged (cached) changes
- `<file paths>` — Review specific files (e.g., `src/foo.py src/bar.ts`)
- *(no mode/no args)* — Review all uncommitted changes (staged + unstaged), same as before

**Flags** (can be combined with any mode):
- **--model**: Override model (default: `gpt-5.4`). MUST always be passed to codex via `-c model=`
- **--effort**: Override reasoning effort (default: `high`)

**Free-text instructions**: Any remaining text after mode and flags is treated as additional review instructions appended to the review prompt (e.g., `/pm-codex-review staged focus on error handling`).

## Step 1: Check Prerequisites

Run via Bash:
```bash
which codex
```

If `codex` is not found, stop and display:
```
Codex CLI not found. Install it:
  npm install -g @openai/codex

Then configure your API key in ~/.codex/config.toml:
  [api]
  api_key = "sk-..."
```

## Step 2: Gather Changes

Based on the detected mode:

### Mode: `pr [number]`
- If a PR number is given: `gh pr diff <number>`
- If no number: `gh pr diff` (uses current branch's PR)
- If the `gh` command fails, display the error and stop (e.g., "No PR found for current branch").
- Also run `gh pr view [number] --json title,body` to include PR context in the review prompt.

### Mode: `commit <ref>`
- Run `git diff <ref>^..<ref>` to get the diff for that commit
- Run `git log -1 --format="%H %s" <ref>` to get the commit message
- If the ref is invalid, display the error and stop.

### Mode: `branch [base]`
- Run `git diff <base>...HEAD` (default base: `main`)
- Run `git log --oneline <base>..HEAD` to list commits being reviewed
- If no commits found, display: "No commits found between `<base>` and HEAD." and stop.

### Mode: `staged`
- Run `git diff --cached --name-only` to find staged files
- If no staged changes, display: "No staged changes found. Stage files with `git add` first." and stop.
- Run `git diff --cached` to get the diff

### Mode: specific files
- Read the content of each specified file
- Also run `git diff -- <files>` and `git diff --cached -- <files>` to get diffs

### Mode: default (no args)
- Run `git diff --name-only` and `git diff --cached --name-only` to find changed files
- If no changes found, display: "No uncommitted changes found. Try: `/pm-codex-review pr`, `/pm-codex-review commit HEAD`, or pass file paths." and stop.
- Run `git diff` and `git diff --cached` to get the full diff

Store the diff content and list of changed/reviewed files.

## Step 3: Write Diff to Temp File

**IMPORTANT:** Do NOT pass the diff as a CLI argument — it gets truncated and Codex ignores it. Instead, write the diff to a temp file that Codex will read.

```bash
DIFF_FILE="/tmp/codex-diff-$(date +%s).patch"
REVIEW_FILE="/tmp/codex-review-$(date +%s).md"
```

Write the full diff content to `$DIFF_FILE` using the Write tool (or `cat <<'HEREDOC'` for large diffs).

## Step 4: Build Review Prompt

Construct this prompt — it tells Codex to read the diff file and ONLY review that:

```
Read the file <DIFF_FILE> which contains a unified diff of code changes.

IMPORTANT: ONLY review the changes shown in that diff file. Do NOT browse the repository, do NOT read other files, do NOT look for issues outside the diff. Your review scope is strictly limited to the code changes in that diff file.

For each finding, provide:
- A number
- Severity: CRITICAL, MAJOR, or MINOR
- File and line reference (from the diff headers)
- Clear description of the issue
- Suggested fix

Focus on: bugs, logic errors, security vulnerabilities, race conditions, performance issues, and code quality problems. Do NOT flag style preferences or nitpicks.

If the diff is clean and you find no issues, say: "No issues found."

<If PR mode and PR context was fetched:>
Context — PR Title: <PR title>
PR Description: <PR body>
</If>

<If commit mode:>
Context — Commit: <commit hash and message>
</If>

<If free-text instructions were provided:>
Additional review instructions: <free-text instructions>
</If>
```

## Step 5: Execute Codex Review

Run Codex via Bash. **You MUST include the `-c model=` and `-c reasoning_effort=` flags — without them, Codex uses o4-mini which is deprecated.**

```bash
codex exec \
  --sandbox read-only \
  -c model=gpt-5.4 \
  -c reasoning_effort=high \
  -o "$REVIEW_FILE" \
  "<REVIEW_PROMPT>"
```

If the user passed `--model` or `--effort` flags, use those values instead of the defaults above. The `<REVIEW_PROMPT>` is from Step 4 (properly escaped for shell).

If Codex fails or times out, display the error and stop.

## Step 6: Display Findings

Read the output file content.

Display to the user:
```
## Codex Review (GPT-5.4)

**Mode:** <mode used (pr #N / commit abc123 / branch main..HEAD / staged / files / uncommitted)>
**Files reviewed:** <list of files>
**Model:** <model used>

<contents of the review output>
```

If the review output is empty, display: "Codex returned no findings."

## Step 7: Cleanup

```bash
rm -f "$DIFF_FILE"
```

## Step 8: Implementer Integration

Ask the user:

> Feed these findings to pm-implementer for resolution? The implementer will independently verify each finding before acting.

**If user confirms:**

Fire the pm-implementer agent:
```
Agent(subagent_type="powermode:pm-implementer", prompt="
  ## External Code Review Findings

  **IMPORTANT: These are findings from an external reviewer (Codex/GPT-5.4). Verify each finding independently before acting — not all may be valid. Do NOT blindly apply fixes. For each finding:**
  1. Read the referenced code
  2. Determine if the finding is actually correct
  3. Only fix confirmed issues
  4. Skip findings that are false positives or style preferences

  ## Findings

  <review output content>

  ## Files Under Review

  <list of changed files>
")
```

**If user declines:**

Display: "Findings displayed above for manual action. No changes made."

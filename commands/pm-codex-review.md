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
- **Files**: Any file paths listed (e.g., `src/foo.py src/bar.ts`)
- **--model**: Override model (default: `gpt-5.4`)
- **--effort**: Override reasoning effort (default: `high`)

If no files and no flags, default to reviewing all uncommitted changes.

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

**If specific files were provided:**
- Read the content of each specified file
- Also run `git diff -- <files>` to get the diff for those files

**If no files provided:**
- Run `git diff --name-only` and `git diff --cached --name-only` to find changed files
- If no changes found, display: "No uncommitted changes found. Pass specific file paths to review existing files (e.g., `/pm-codex-review src/foo.py`)." and stop.
- Run `git diff` and `git diff --cached` to get the full diff

Store the diff content and list of changed files.

## Step 3: Build Review Prompt

Construct this prompt (replace `<DIFF_CONTENT>` with the actual diff):

```
Review the following code changes. For each finding, provide:
- A number
- Severity: CRITICAL, MAJOR, or MINOR
- File and line reference
- Clear description of the issue
- Suggested fix

Focus on: bugs, logic errors, security vulnerabilities, race conditions, performance issues, and code quality problems. Do NOT flag style preferences or nitpicks.

---

<DIFF_CONTENT>
```

## Step 4: Execute Codex Review

Generate a unique output file path:
```bash
REVIEW_FILE="/tmp/codex-review-$(date +%s).md"
```

Run Codex via Bash (substitute the parsed model and effort values):
```bash
codex exec \
  --sandbox read-only \
  -c model=<MODEL> \
  -c reasoning_effort=<EFFORT> \
  -o "$REVIEW_FILE" \
  "<REVIEW_PROMPT>"
```

Where:
- `<MODEL>` = parsed `--model` value or `gpt-5.4`
- `<EFFORT>` = parsed `--effort` value or `high`
- `<REVIEW_PROMPT>` = the prompt from Step 3 (properly escaped for shell)

If Codex fails or times out, display the error and stop.

## Step 5: Display Findings

Read the output file content.

Display to the user:
```
## Codex Review (GPT-5.4)

**Files reviewed:** <list of files>
**Model:** <model used>

<contents of the review output>
```

If the review output is empty, display: "Codex returned no findings."

## Step 6: Implementer Integration

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

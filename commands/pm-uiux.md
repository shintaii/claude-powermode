---
name: pm-uiux
description: "UI/UX review, audit, and implementation using the powermode workflow. Reviews existing interfaces or builds new ones with professional design discipline."
allowed-tools: "*"
---

# Power Mode UI/UX

You are performing a **UI/UX task** using the Power Mode methodology.

## Mandatory: Load the skill files first

Before doing ANYTHING, read these files in order:

1. Read `${CLAUDE_PLUGIN_ROOT}/skills/pm-uiux/SKILL.md` — this is your review + implementation framework
2. Read `${CLAUDE_PLUGIN_ROOT}/skills/pm-uiux/references/checklist.md` — this is your detailed checklist
3. Read `${CLAUDE_PLUGIN_ROOT}/skills/pm-uiux/references/color-system.md` — this is the complete color framework

**Do not proceed until you have read all three files.** Do not assume you know the contents.

## Input

```
$ARGUMENTS
```

## Mode Detection

Parse `$ARGUMENTS` to determine what the user wants:

### Review Mode (default if no clear intent)
The user wants to review/audit existing UI. Triggers: "review", "audit", "check", "how does this look", file path, URL, or screenshot.

1. Read the skill files above
2. Read the file(s) or take a screenshot of the page the user wants reviewed
3. Work through **every phase from SKILL.md in order** (Phases 1-8)
4. For Phase 2 (Color System), use the **full 4-layer framework from color-system.md**
5. For each phase, list specific findings with file paths and line numbers
6. If a phase has no issues, say "No issues found" and move on
7. After review, ask if user wants you to implement the fixes

### Build/Fix Mode
The user wants to build new UI or fix existing issues. Triggers: "build", "create", "fix", "implement", "polish", "improve".

1. Read the skill files above
2. **Explore first** — use `pm-explorer` to understand the existing codebase patterns, component library, CSS framework
3. **Plan** — propose changes with specific file paths before implementing
4. **Implement** — apply the design principles from the skill, using `pm-implementer` for focused work
5. **Verify** — take a screenshot or run the app to verify visual results

### Color-Only Mode
The user specifically wants color work. Triggers: "color", "palette", "dark mode", "theme", "color audit".

1. Read `references/color-system.md` thoroughly
2. Audit the existing color system against all 4 layers
3. Propose specific color values (hex, OKLCH) — never just say "make it darker"
4. Implement as CSS variables / design tokens

## Output Format (Review Mode)

```
## UI/UX Review: [component/page name]

### Phase 1: Icons & Visual Elements
[findings or no issues]

### Phase 2: Color System
**Layer 1 — Neutrals:** [findings]
**Layer 2 — Accent:** [findings]
**Layer 3 — Semantic:** [findings]
**Layer 4 — Theming:** [findings]

### Phase 3: Layout
[findings or no issues]

### Phase 4: Forms & Modals
[findings or no issues]

### Phase 5: Data Visualization
[findings or no issues]

### Phase 6: Billing & Pricing
[findings or N/A]

### Phase 7: Landing Page
[findings or N/A]

### Phase 8: AI Smell Check
[findings or clean]

### Priority Actions
[Numbered list of most impactful changes, ordered by importance]
```

## Rules

- **ONLY review visual design, layout, colors, and user experience** — this is NOT a code review
- **DO NOT** review code quality, performance, architecture, naming conventions, or logic
- **DO NOT** refactor or "clean up" code unless implementing approved UI fixes
- **DO NOT** skip phases — work through each one explicitly
- When proposing color changes, provide specific values (hex, OKLCH, percentage-white)
- When implementing, follow existing codebase patterns (CSS framework, component library, naming)
- Use `pm-explorer` to understand the codebase before any implementation
- Use `pm-verifier` after implementation to check visual results

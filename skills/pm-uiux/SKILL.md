---
name: pm-uiux
description: >
  Comprehensive UI/UX skill for reviewing, auditing, and building professional interfaces.
  Combines the 8-phase UI/UX review framework, 4-layer color system, and implementation patterns.
  Use when reviewing existing UI, building new interfaces, fixing color systems, implementing dark mode,
  or polishing prototype-to-production quality. Covers icons, colors, layout, forms, data visualization,
  billing/pricing pages, landing pages, and AI smell detection.
---

# Power Mode UI/UX — Review, Audit & Build

Comprehensive UI/UX skill for Power Mode. Combines review methodology, color system framework, and implementation patterns into a single reference.

## When to Use

- Reviewing or auditing existing UI/UX
- Building new frontend interfaces
- Fixing color systems, implementing dark mode
- Polishing "AI-generated" or prototype UI to production quality
- Optimizing layout, forms, data visualization, or landing pages

## Reference Files

- `references/checklist.md` — Full action-item checklist for all 8 review phases
- `references/color-system.md` — Complete 4-layer color framework (neutrals, accent, semantic, theming)

**Read these before any review or color work.** Do not assume you know the contents.

---

## Part 1: UI/UX Review Framework (8 Phases)

Follow these phases in order. Skip phases that aren't relevant, but always do a quick mental check for each one.

### Phase 1: Icons & Visual Elements

AI-generated apps almost always use emojis or decorative icons that look unprofessional.

- Replace all emojis with icons from a proper library (Phosphor, Lucide, Heroicons, Tabler)
- Remove icons that serve no functional purpose — they're visual noise
- Replace gradient letter circles (AI's favorite avatar) with proper account cards or real avatars
- When icons ARE used, they should add meaning, context, or color — not just fill space

### Phase 2: Color System

AI consistently picks bright, clashing color palettes with no structure. This phase goes deep.

**For the full 4-layer color framework, read `references/color-system.md`.**

The quick version — a professional color system has 4 layers:

1. **Neutral Foundation** — 4 background layers, 1-2 border colors, 3 text shades, button hierarchy by darkness, hover states for every interactive element
2. **Functional Accent** — A single brand color with a full ramp (100-900), with assigned roles (primary, hover, links, tint backgrounds). In dark mode: shift the ramp down, double background spacing, brighten borders
3. **Semantic Colors** — Success (green), error (red), warning (amber), info (blue). Red for destructive actions is non-negotiable. Must be visually distinct from the brand accent
4. **Theming** — Systematic color generation using OKLCH (drop lightness 0.03, increase chroma 0.02, shift hue). Works for multi-theme and dark mode variants

Common AI color mistakes to fix immediately:
- Bright saturated backgrounds instead of muted neutrals
- No defined color ramp — just random hex values
- Missing semantic colors (or using brand color for errors)
- Charts using only brand-color variations (unreadable)
- Dark mode that's just an inverted light mode
- No hover states defined

### Phase 3: Layout & Information Architecture

This is where the most time-efficient improvements live. AI is bad at complex layouts.

**Navigation & Sidebar:**
- Remove redundant links — if data lives on a dedicated page, don't repeat it in the sidebar
- Add missing key navigation items (Analytics, Settings) as proper entries
- Left-align and tighten spacing in the sidebar
- Collapse secondary items (settings, billing, usage, profile) into a popover or account menu

**Content Duplication:**
- Hunt for repeated information — KPIs and stats should appear once, not on every page
- Remove cards or components that display data but have no interactivity or purpose

**Card & List Design:**
- Collapse action buttons into a triple-dot overflow menu
- Prioritize information hierarchy — the most important data gets the most visual weight
- Collapse tag/chip lists to just icons when space is limited
- Rearrange card content: date center, primary metric right, actions hidden by default

### Phase 4: Forms & Modals

- If a flyout or drawer feels sparse, switch to a centered modal
- Collapse advanced/optional fields behind a toggle — show essentials first
- Audit for missing useful fields (descriptions, domain selectors, toggles, custom options)
- Design form layouts to be extensible — new features should slot in without a redesign

### Phase 5: Data Visualization & Analytics

- Replace generic KPI cards with meaningful visualizations (sparklines, micro charts, doughnut charts)
- Use two-column layouts for data-heavy pages instead of stacked single-column KPI rows
- Swap basic bar charts for richer alternatives where appropriate (maps with shaded regions, area charts)
- Add comparison features — toggles to split by individual items, date ranges, categories
- Pack useful information into data rows with small icons that also add color
- **For chart color palettes**, use the OKLCH spectrum method from `references/color-system.md` (Layer 3)

### Phase 6: Billing & Pricing Pages

- Simplify plan options to 3-4 tiers max — if there are 5+, drop the least useful one
- Make the price the visually largest element — nobody cares about the plan name as much
- Show discounts explicitly — don't make users do the math
- Highlight what the next plan adds over the current one
- Include billing essentials: billing email, payment method, invoices section
- Use tabs for scalability (Usage, Billing, Invoices as separate tabs)

### Phase 7: Landing Pages

This is where customers are won or lost. AI-generated landing pages destroy trust.

- Never ship an AI-generated landing page without heavy human editing
- Add real product graphics — screenshots of the actual app with slight perspective/skew
- Replace generic feature-grid icons with cropped images of real app screens
- Apply the same color and layout discipline from the app itself
- Focus on presentation over complexity — clean, trustworthy, professional

### Phase 8: AI Smell Check (Final Pass)

Do a final sweep for patterns that immediately signal "AI built this":

- Emojis used as UI icons
- Bright, mismatched color palettes with no system
- Gradient letter circles for user avatars
- Same KPIs repeated across multiple pages
- Cards that display data but have no function
- Too many visible action buttons on every card
- Flyouts/forms with too few or too many fields
- Generic bar charts where richer visualizations would work
- Five pricing tiers when three would do
- Landing pages with stock-icon feature grids
- No hover states on interactive elements
- Dark mode that's just inverted light mode

---

## Part 2: Implementation Patterns

When building or fixing UI, apply these patterns.

### Design Philosophy

**1. Bold, Not Bland**
- Use confident color choices, not safe grays everywhere
- Embrace whitespace - let elements breathe
- Create visual hierarchy with size, weight, and spacing

**2. Distinctive Typography**
- Choose fonts that have character
- Use font weight and size to create hierarchy
- Line height matters - 1.5-1.7 for body text

**3. Intentional Spacing**
- Use a spacing scale (4, 8, 12, 16, 24, 32, 48, 64)
- Consistent padding and margins
- Group related elements, separate unrelated ones

**4. Subtle Animations**
- Transitions on hover/focus (150-300ms)
- Micro-interactions that feel natural
- Don't animate everything - be intentional

### Accessibility (Non-Negotiable)

- Always include focus states
- Use semantic HTML elements
- Provide aria-labels for icon buttons
- Ensure sufficient color contrast (4.5:1 minimum)
- Support keyboard navigation
- Minimum 44x44px touch targets

### States to Always Handle

- **Loading** — Skeleton screens or pulse animations, never just "Loading..."
- **Empty** — Guide the user with icon, message, and CTA
- **Error** — Clear messaging with icons and semantic color (red)
- **Hover/Focus** — Every interactive element needs feedback

### Design Tokens Reference

**Spacing Scale:**
| Token | Value | Use Case |
|-------|-------|----------|
| xs | 4px | Tight spacing, icons |
| sm | 8px | Between related elements |
| md | 16px | Standard padding |
| lg | 24px | Section spacing |
| xl | 32px | Major sections |
| 2xl | 48px | Page sections |

**Typography Scale:**
| Size | Use Case |
|------|----------|
| text-xs | Labels, captions |
| text-sm | Secondary text |
| text-base | Body text |
| text-lg | Subheadings |
| text-xl | Section headings |
| text-2xl+ | Page titles |

---

## Key Principles

- **Color through data, not decoration** — Charts and status indicators > colored backgrounds
- **Color needs structure** — 4-layer system beats random hex values
- **Information should appear once** — If it's on the dashboard, not in the sidebar
- **Hide complexity by default** — Advanced options and secondary nav should be tucked away
- **Layout is the highest-leverage fix** — Changing arrangement beats changing appearance
- **Dark mode is not inverted light mode** — Requires its own deliberately designed palette
- **The more important the action, the darker the button**

## Quick Impact Guide

When time is limited, prioritize:

| Priority | Phase | Why |
|----------|-------|-----|
| 1 | Phase 3: Layout | Highest leverage — restructuring creates the biggest visual change |
| 2 | Phase 2: Colors | Fast wins — a proper color system instantly elevates quality |
| 3 | Phase 1: Icons | Quick — emoji-to-icon swap is low effort, high impact |
| 4 | Phase 8: Smell Check | Safety net — catches anything you missed |

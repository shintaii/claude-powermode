# UI/UX Review Checklist — Detailed Reference

Use this as a hands-on checklist when performing a UI/UX review. Each item is a concrete action.

---

## Phase 1: Icons & Visual Elements

- [ ] Replace all emojis with professional icons (Phosphor, Lucide, Heroicons, Tabler)
- [ ] Remove icons that don't serve a functional purpose
- [ ] Replace gradient profile circles with proper account cards or avatars
- [ ] Ensure remaining icons add context, meaning, or color — not just decoration

## Phase 2: Color System

For the full framework, read `color-system.md`. This is the condensed checklist version.

### Layer 1: Neutral Foundation
- [ ] Main background close to pure white (98-100% lightness)
- [ ] 4 distinct background layers defined (frame, main, card, elevated)
- [ ] Card strategy chosen and applied consistently (dark bg + light cards, or vice versa)
- [ ] Borders use light gray (~85% white), not black or shadow-only
- [ ] 3 text color variants defined (heading ~11%, body 15-20%, sub 30-40%)
- [ ] Button hierarchy follows darkness = importance (ghost > secondary > primary)
- [ ] Every interactive element has a hover state

### Layer 2: Accent Color
- [ ] Single brand color with full ramp (100-900) generated
- [ ] Ramp roles assigned (primary 500/600, hover 700, links 400/500, tints 100/200)
- [ ] Dark mode: background steps doubled, brand shifted to 300/400, borders brightened
- [ ] Dark mode: all 4 background layers still distinguishable

### Layer 3: Semantic Colors
- [ ] Success (green), error (red), warning (amber), info (blue) defined
- [ ] All destructive actions use red — no exceptions
- [ ] Semantic colors visually distinct from brand accent
- [ ] Chart palette generated via OKLCH (consistent lightness/chroma, hue increments of 25-30 degrees)

### Layer 4: Theming
- [ ] Themed variants generated via OKLCH (lightness -0.03, chroma +0.02, hue shift)
- [ ] All colors stored as design tokens / CSS variables
- [ ] Accessibility: text/background combos meet WCAG contrast ratios

## Phase 3: Layout & Information Architecture

### Navigation
- [ ] Remove redundant sidebar links (data that lives on a dedicated page)
- [ ] Add missing navigation items (e.g., Analytics, Settings)
- [ ] Left-align and tighten sidebar spacing
- [ ] Collapse secondary links (settings, billing, profile) into popover or account menu

### Duplication
- [ ] Identify KPIs or stats that appear on multiple pages — consolidate to one location
- [ ] Remove cards/components that display data but have no interactivity

### Cards & Lists
- [ ] Collapse multiple action buttons into overflow menus
- [ ] Set clear visual hierarchy — important data gets the most prominence
- [ ] Collapse chip/tag lists to icons where space is tight
- [ ] Rearrange card content: date center, primary metric right, actions hidden

## Phase 4: Forms & Modals

- [ ] Replace sparse flyouts/drawers with centered modals where appropriate
- [ ] Collapse advanced options behind a toggle (show essentials by default)
- [ ] Audit for missing useful fields (descriptions, toggles, domain selectors)
- [ ] Ensure form layout is extensible for future features

## Phase 5: Data Visualization & Analytics

- [ ] Replace generic KPI cards with sparklines, micro charts, or doughnut charts
- [ ] Use two-column layouts for data-heavy pages
- [ ] Swap basic bar charts for richer alternatives (maps, area charts) where appropriate
- [ ] Add comparison features (toggle split by link, category, date range)
- [ ] Add helpful icons to data rows for visual context and color
- [ ] Chart colors use OKLCH perceptual spectrum (see `color-system.md` Layer 3)

## Phase 6: Billing & Pricing

- [ ] Reduce plan tiers to 3-4 max
- [ ] Make price the largest visual element per plan
- [ ] Show discounts explicitly (don't make users calculate)
- [ ] Highlight what the next plan adds over the current one
- [ ] Include billing email, payment method, and invoices section
- [ ] Use tabs for scalable organization (Usage / Billing / Invoices)

## Phase 7: Landing Page

- [ ] Remove or heavily edit any AI-generated landing page content
- [ ] Add real product screenshots with perspective/skew
- [ ] Replace feature-grid icons with cropped images of actual app screens
- [ ] Apply consistent color and layout principles from the app
- [ ] Prioritize clean presentation over feature complexity

## Phase 8: AI Smell Check

Final pass — flag and fix any of these patterns:

- [ ] Emojis as icons
- [ ] Bright, clashing color palette with no system
- [ ] Gradient letter circles for avatars
- [ ] Same KPIs on multiple pages
- [ ] Non-functional decorative cards
- [ ] Excessive visible action buttons per card
- [ ] Sparse or bloated forms
- [ ] Generic bar charts that should be richer visualizations
- [ ] 5+ pricing tiers
- [ ] Stock-icon feature grids on landing page
- [ ] No hover states on interactive elements
- [ ] Dark mode that's just inverted light mode

---

## Quick Impact Guide

When time is limited, focus on these phases in priority order:

| Priority | Phase | Why |
|----------|-------|-----|
| 1 | Phase 3: Layout | Highest leverage — restructuring creates the biggest visual change |
| 2 | Phase 2: Colors | Fast wins — a proper color system instantly elevates quality |
| 3 | Phase 1: Icons | Quick — emoji-to-icon swap is low effort, high impact |
| 4 | Phase 8: Smell Check | Safety net — catches anything you missed |
| 5 | Phase 5: Data Viz | Medium effort — richer charts add perceived value |
| 6 | Phase 7: Landing Page | High impact for conversion but requires more design work |
| 7 | Phase 4: Forms | Important for usability but less visually dramatic |
| 8 | Phase 6: Billing | Only relevant if the app has pricing/billing pages |

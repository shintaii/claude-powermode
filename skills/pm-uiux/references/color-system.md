# Color System — 4-Layer Framework Reference

This is the complete color framework for building professional, systematic color palettes.
Read this whenever a review involves color, theming, dark mode, or chart palettes.

---

## Layer 1: Neutral Foundation

The neutral layer is the skeleton of your interface. Get this right and everything else falls into place.

### Backgrounds (4 distinct layers required)

Define 4 background levels that create visual depth:

1. **Frame / Sidebar** — Slightly darker than main background. Consider adding 1-2% of a tint (e.g. blue) for subtle warmth or coolness
2. **Main background** — Close to pure white (98-100% lightness). Slight off-whites are fine
3. **Card surface** — Sits on top of the main background
4. **Elevated surface** — Modals, popovers, dropdowns

Pick a card strategy and apply it consistently:
- **Dark background + lighter cards** (Vercel style)
- **Light background + darker cards** (Notion style)
- **Monochromatic layering** (Supabase style)

If using lighter cards, don't use pure white as main background — reserve white for the cards themselves.

### Borders & Edges

- Replace any thin black borders with ~85% white (light gray) — define edges without overpowering
- Define at least 1-2 stroke/border colors in your system
- Avoid relying on drop shadows alone to separate cards — they look washed out

### Text (exactly 3 variants)

- **Headings** — ~11% white (near black, not pure black)
- **Body text** — 15-20% white
- **Subtext / secondary** — 30-40% white

### Button Hierarchy (by darkness)

The more important the action, the darker the button:
- **Ghost / tertiary** — lightest (90-95% white background)
- **Secondary** — mid-range
- **Primary / CTA** — darkest (black with white text)

### Hover & Interactive States

Every interactive element must have a defined hover state. This is not optional and should not be an afterthought.

---

## Layer 2: Functional Accent Color

### Brand Color Ramp

1. Pick your primary accent color (blue, green, purple, etc.)
2. Generate a full ramp (100-900) using a tool like [UI Colors](https://uicolors.app)
3. Assign roles across the ramp:
   - **Primary / default** — 500 or 600
   - **Hover state** — 700
   - **Links** — 400 or 500
   - **Light tint backgrounds** — 100 or 200

### Dark Mode Conversion

Dark mode is NOT inverted light mode. It needs its own deliberate palette:

- **Double the distance** between neutral background colors. If light mode uses ~2% steps, dark mode needs 4-6% steps
- **Shift the primary brand color down the ramp:**
  - Primary on dark — 300 or 400
  - Hover on dark — 400 or 500
- **Dim text colors** slightly — don't use pure white for body text
- **Brighten borders** to maintain visible separation
- **Enforce the elevation rule:** surfaces get lighter as they elevate. Raised cards must be lighter than the background or use a visible border

### Dark Mode Audit

After building dark mode, verify:
- Can you still distinguish all 4 background layers?
- Do cards and elevated elements clearly "lift" off the background?
- Is the accent color comfortable on dark backgrounds (not too saturated)?

---

## Layer 3: Semantic Colors

### Status Colors (minimum set)

- **Success** — green
- **Error / destructive** — red (non-negotiable, regardless of brand color)
- **Warning** — yellow / amber
- **Info / in-progress** — blue

All destructive actions (delete, remove, cancel) must be red. Semantic colors must be visually distinct from your brand accent.

### Chart & Data Visualization Palette

Don't use neutral-only palettes (unreadable) or brand-color-only ramps (values look too similar).

Generate a perceptually uniform spectrum using OKLCH:

1. Go to [oklch.com](https://oklch.com)
2. Set a consistent lightness and chroma value
3. Increment hue by 25-30 degrees to generate each chart color
4. Verify all generated colors feel equally bright and saturated

Test chart colors for accessibility — ensure sufficient contrast and consider colorblind-safe palettes.

---

## Layer 4: Theming

### Generating Themed Variants from Neutrals

For every neutral in your palette:

1. Plug the hex value into an OKLCH converter
2. Drop lightness by **0.03**
3. Increase chroma by **0.02**
4. Adjust hue to match the desired theme color

This technique works for any theme variant (red, green, blue, etc.) and works equally well — or better — in dark mode.

Verify themed versions maintain contrast and readability across all text and background layers.

---

## Final Color Audit Checklist

- [ ] All colors defined as design tokens / CSS variables (not hardcoded hex)
- [ ] Light mode and dark mode both have complete, distinct palettes
- [ ] Neutral foundation has: 4 backgrounds, 1-2 strokes, 3 text variants
- [ ] Accent color has a full ramp (100-900) with assigned roles
- [ ] Semantic colors exist for success, error, warning, info
- [ ] Semantic colors are used consistently across all components
- [ ] Charts use a perceptually balanced OKLCH spectrum
- [ ] Themed variants generated systematically via OKLCH, not guessed
- [ ] Accessibility: all text/background combinations meet WCAG contrast ratios
- [ ] Every interactive element has a hover state
- [ ] Dark mode is deliberately designed, not auto-inverted

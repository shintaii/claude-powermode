---
name: frontend-ui-ux
description: Designer-turned-developer persona for crafting stunning UI/UX. Use when building frontend interfaces, styling components, or implementing designs. Creates distinctive, polished interfaces even without design mockups.
---

# Frontend UI/UX - Designer-Developer Mindset

You are now operating as a designer-turned-developer. Your code should produce interfaces that are visually distinctive and user-friendly, not generic Bootstrap-looking UIs.

## Design Philosophy

### Visual Principles

**1. Bold, Not Bland**
- Use confident color choices, not safe grays everywhere
- Embrace whitespace - let elements breathe
- Create visual hierarchy with size, weight, and spacing

**2. Distinctive Typography**
- Choose fonts that have character
- Use font weight and size to create hierarchy
- Line height matters - 1.5-1.7 for body text

**3. Cohesive Color System**
- Define a primary, secondary, and accent color
- Use consistent shades (light/dark variants)
- Background colors should support, not compete

**4. Intentional Spacing**
- Use a spacing scale (4, 8, 12, 16, 24, 32, 48, 64)
- Consistent padding and margins
- Group related elements, separate unrelated ones

**5. Subtle Animations**
- Transitions on hover/focus (150-300ms)
- Micro-interactions that feel natural
- Don't animate everything - be intentional

## Implementation Patterns

### Component Structure

```tsx
// Good: Semantic, accessible, styled
<button
  className="px-4 py-2 bg-indigo-600 text-white rounded-lg
             hover:bg-indigo-700 transition-colors duration-200
             focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
  onClick={handleClick}
>
  {children}
</button>

// Bad: Generic, unstyled
<button onClick={handleClick}>{children}</button>
```

### Responsive Design

```tsx
// Mobile-first responsive classes
<div className="
  grid grid-cols-1 gap-4
  md:grid-cols-2 md:gap-6
  lg:grid-cols-3 lg:gap-8
">
```

### Accessibility (Non-Negotiable)

- Always include focus states
- Use semantic HTML elements
- Provide aria-labels for icon buttons
- Ensure sufficient color contrast (4.5:1 minimum)
- Support keyboard navigation

```tsx
// Accessible icon button
<button
  aria-label="Close modal"
  className="p-2 rounded-full hover:bg-gray-100 focus:ring-2"
>
  <XIcon className="w-5 h-5" />
</button>
```

### Loading & Empty States

Always handle these states with care:

```tsx
// Loading state - don't just show "Loading..."
<div className="animate-pulse space-y-4">
  <div className="h-4 bg-gray-200 rounded w-3/4" />
  <div className="h-4 bg-gray-200 rounded w-1/2" />
</div>

// Empty state - guide the user
<div className="text-center py-12">
  <EmptyIcon className="mx-auto h-12 w-12 text-gray-400" />
  <h3 className="mt-2 text-sm font-medium text-gray-900">No projects</h3>
  <p className="mt-1 text-sm text-gray-500">Get started by creating a new project.</p>
  <button className="mt-4 ...">Create Project</button>
</div>
```

### Form Design

```tsx
// Well-designed form field
<div className="space-y-1">
  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
    Email address
  </label>
  <input
    type="email"
    id="email"
    className="block w-full px-3 py-2 border border-gray-300 rounded-lg
               shadow-sm placeholder-gray-400
               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
               transition-shadow duration-200"
    placeholder="you@example.com"
  />
  {error && (
    <p className="text-sm text-red-600">{error}</p>
  )}
</div>
```

## Design Tokens Reference

### Spacing Scale
| Token | Value | Use Case |
|-------|-------|----------|
| xs | 4px | Tight spacing, icons |
| sm | 8px | Between related elements |
| md | 16px | Standard padding |
| lg | 24px | Section spacing |
| xl | 32px | Major sections |
| 2xl | 48px | Page sections |

### Typography Scale
| Size | Use Case |
|------|----------|
| text-xs | Labels, captions |
| text-sm | Secondary text |
| text-base | Body text |
| text-lg | Subheadings |
| text-xl | Section headings |
| text-2xl+ | Page titles |

### Common Color Patterns
```tsx
// Semantic colors
const colors = {
  primary: 'indigo-600',    // Main actions
  secondary: 'gray-600',    // Secondary actions
  success: 'green-600',     // Success states
  warning: 'amber-500',     // Warnings
  error: 'red-600',         // Errors
  info: 'blue-600',         // Information
}
```

## Anti-Patterns to Avoid

| Don't | Do Instead |
|-------|------------|
| Generic gray everything | Use intentional color palette |
| No hover/focus states | Add transitions and feedback |
| Tiny click targets | Minimum 44x44px touch targets |
| Text-only error messages | Add icons and color |
| Walls of text | Break up with whitespace and hierarchy |
| Missing loading states | Always show loading feedback |
| Ignoring mobile | Design mobile-first |

## Before Submitting UI Code

Checklist:
- [ ] Responsive on mobile, tablet, desktop
- [ ] Hover and focus states on interactive elements
- [ ] Loading states implemented
- [ ] Empty states implemented
- [ ] Error states with clear messaging
- [ ] Accessible (keyboard nav, aria labels, contrast)
- [ ] Consistent with existing design system
- [ ] Animations are subtle and purposeful

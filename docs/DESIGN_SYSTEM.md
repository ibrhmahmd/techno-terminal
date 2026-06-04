# Precision Engine — Design Constitution

## Philosophy

Precision Engine is a high-density operational design language inspired by flight decks, engineering workstations, and professional control systems.

The UI should feel:

* Engineered
* Precise
* Efficient
* Technical
* Sophisticated

Avoid generic SaaS dashboards, excessive cards, playful interactions, and decorative UI.

---

## Core Principles

### Depth Over Borders

Never use visible borders for layout structure.

Prefer:

* Tonal layering
* Surface nesting
* Whitespace
* Elevation

Use borders only when accessibility requires them.

---

### Information First

Every visual decision must improve:

* Scanning
* Decision making
* Workflow speed

Decoration without function should be removed.

---

### Precision Over Playfulness

Avoid:

* Bounce animations
* Oversized radii
* Cartoon-like visuals
* Bright marketing gradients

Interactions should feel mechanical and intentional.

---

## Colors

### Primary Architecture

```yaml
primary: "#000000"
primary_container: "#131b2e"
```

Used for structure and authority.

### Action Color

```yaml
secondary: "#006a61"
secondary_fixed: "#89f5e7"
```

Used for:

* Primary actions
* Success states
* Progress indicators

### Accent Color

```yaml
tertiary_container: "#7671ff"
```

Used for:

* Analytics
* Educational content
* Data visualization

---

## Surface Hierarchy

```yaml
surface: "#f8f9ff"
surface_low: "#eff4ff"
surface_container: "#e5eeff"
surface_card: "#ffffff"
```

Hierarchy is created through surface changes, not borders.

---

## Typography

### Headlines

Font: Space Grotesk

Use for:

* Metrics
* Section titles
* Dashboard headings

### Body

Font: Inter

Use for:

* Tables
* Forms
* Operational content

### Rules

* Prefer scale over boldness.
* Avoid pure black text.
* Use strong hierarchy through size.

---

## Layout

### Spacing Scale

```yaml
4 8 12 16 24 32 40 48 64
```

Prefer large spacing at layout level.

### Rules

* Maximum 3 visual hierarchy levels.
* Avoid card-inside-card layouts.
* Use asymmetry when appropriate.
* Favor whitespace over dividers.

---

## Elevation

Primary hierarchy method:

```text
Surface Layering
```

Shadow only when necessary:

```css
box-shadow: 0 12px 40px rgba(11,28,48,0.06);
```

---

## Motion

Purpose:

* State change
* Navigation
* Focus shift

Timing:

```yaml
hover: 120ms
press: 80ms
expand: 180ms
modal: 240ms
page: 300ms
```

Easing:

```css
cubic-bezier(0.2,0,0,1)
```

Never use bounce or elastic effects.

---

## Components

### Buttons

Primary:

```yaml
background: secondary
radius: 6px
```

### Inputs

Transparent background.

Bottom border only.

### Status Chips

Success:

```yaml
secondary_container
```

Error:

```yaml
error_container
```

---

## Tables

High density by default.

Rules:

* No row dividers
* Alternate row surfaces
* Compact spacing
* Fast scanning prioritized

---

## Data Visualization

Charts should resemble instrumentation.

Rules:

* No 3D charts
* No decorative effects
* Prefer line and bar charts
* Use tertiary for analytics

---

## Robotics-Specific Patterns

### Logic Node

Educational modules use:

```yaml
left-accent: tertiary_container
```

### Student Journey

```text
Candidate
→ Enrolled
→ Active
→ Advanced
→ Competition Ready
→ Alumni
```

---

## Accessibility

Minimum contrast:

```text
4.5:1
```

Minimum touch target:

```text
40px
```

All workflows must support keyboard navigation.

---

## Content Style

Tone:

* Direct
* Technical
* Helpful
* Confident

Prefer:

```text
Payment recorded.
Enrollment completed.
Schedule conflict detected.
```

Avoid:

```text
Awesome!
Great job!
Amazing!
```

---

## Final Rule

The interface should feel like a professional control system, not a marketing website.

When unsure, choose the solution that improves clarity, density, and operational efficiency.

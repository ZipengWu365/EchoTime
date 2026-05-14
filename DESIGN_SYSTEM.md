# EchoTime Ecosystem Design System

This document defines a reusable bright scientific design language for the EchoTime ecosystem and adjacent repositories around time series, benchmarks, symbolic regression, and agent-driven research tools.

## 1. Design rationale

### Why this style fits scientific open-source tools

- White-first layouts improve scan speed for documentation, plots, notebooks, and code snippets.
- Warm yellow creates energy and optimism without making the product feel consumerish or childish.
- Restrained blue keeps the product technically credible and supports charts, links, and focus states.
- Soft grays create structure without making the interface feel corporate or lifeless.
- Inter plus JetBrains Mono gives the repo family a modern technical tone with strong readability.

### Why this is better than dark AI styles

- Dark AI landing pages hide information density and make tables, plots, and code feel heavier.
- Cross-disciplinary researchers trust white-background scientific tools more than cyberpunk branding.
- GitHub screenshots, README images, papers, and docs previews all blend more naturally with bright surfaces.
- The product wants to communicate clarity and evidence, not secrecy or hype.

### Why this supports brand consistency

- A fixed token system lets docs, Pages, README assets, dashboards, and notebooks feel related immediately.
- The yellow plus blue palette is distinctive enough to build recognition across repos without requiring complex illustration work.
- Shared section templates reduce drift between repos and make the ecosystem easier to browse and remember.

## 2. Design tokens

### Colors

```yaml
color:
  page:
    default: "#FFFFFF"
    subtle: "#FFFDF4"
  surface:
    card: "#FAFAFA"
    elevated: "#FFFFFF"
    sun: "#FFF4C2"
    sunStrong: "#FFF9E4"
  accent:
    primary: "#FFC83D"
    primarySoft: "#FFE27A"
    primaryDeep: "#C7950A"
    scientificBlue: "#2F6BFF"
    scientificBlueDeep: "#2554CC"
  text:
    primary: "#1F2937"
    secondary: "#6B7280"
    inverse: "#FFFFFF"
  border:
    default: "#E5E7EB"
    subtle: "rgba(229, 231, 235, 0.72)"
    blue: "rgba(47, 107, 255, 0.18)"
    yellow: "rgba(255, 200, 61, 0.42)"
  state:
    infoBg: "rgba(47, 107, 255, 0.06)"
    infoBorder: "rgba(47, 107, 255, 0.18)"
    warnBg: "rgba(255, 244, 194, 0.72)"
    warnBorder: "rgba(255, 200, 61, 0.46)"
    successBg: "#EEF9F2"
    successBorder: "#CFE9D7"
```

### Typography

```yaml
fontFamily:
  sans: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
  mono: "'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"

fontSize:
  xs: "0.78rem"
  sm: "0.86rem"
  base: "1rem"
  md: "1.08rem"
  lg: "1.12rem"
  xl: "1.45rem"
  2xl: "2.1rem"
  3xl: "2.6rem"
  4xl: "4.5rem"

lineHeight:
  tight: 1.0
  heading: 1.05
  body: 1.6
  relaxed: 1.72
```

### Spacing, radius, shadows, borders

```yaml
spacing:
  2: "0.5rem"
  3: "0.75rem"
  4: "1rem"
  5: "1.25rem"
  6: "1.5rem"
  8: "2rem"
  10: "2.5rem"
  12: "3rem"
  16: "4rem"

radius:
  sm: "14px"
  md: "20px"
  lg: "28px"
  full: "999px"

shadow:
  sm: "0 10px 30px rgba(31, 41, 55, 0.06)"
  md: "0 18px 50px rgba(31, 41, 55, 0.08)"
  inset: "inset 0 1px 0 rgba(255,255,255,0.7)"

border:
  width: "1px"
  color: "#E5E7EB"
```

## 3. Component specification

### Primary button
- Background: `linear-gradient(180deg, #FFD65F 0%, #FFC83D 100%)`
- Text: `#1F2937`
- Border: `1px solid rgba(255, 200, 61, 0.48)`
- Radius: `999px`
- Padding: `0 16px`, min height `46px`
- Hover: lift `translateY(-1px)` and medium shadow
- Use for the one main action per section

### Secondary button
- Background: `rgba(47, 107, 255, 0.08)`
- Text: `#2554CC`
- Border: `1px solid rgba(47, 107, 255, 0.18)`
- Radius: `999px`
- Padding: `0 16px`
- Hover: same lift, slightly stronger blue text
- Use for important but non-primary actions

### Tertiary text button
- Background: transparent
- Text: `#2554CC`
- Border: none
- Radius: none
- Padding: `0`
- Hover: darker blue text, underline optional
- Use inside dense cards or footers only

### Standard card
- Background: `#FFFFFF`
- Text: `#1F2937`
- Border: `1px solid #E5E7EB`
- Radius: `20px`
- Padding: `22px 24px`
- Hover: optional shadow increase, no dramatic motion
- Use for most content blocks

### Feature card
- Background: `#FFFFFF` or subtle sun gradient for highlighted items
- Text: same as standard card
- Border: default or yellow border for emphasis
- Radius: `20px`
- Padding: `22px 24px`
- Hover: minimal lift only
- Use for key product surfaces and demo cards

### Badges
- Background: soft neutral, soft yellow, or soft blue
- Text: secondary gray, deep yellow, or deep blue
- Border: matching subtle border
- Radius: `999px`
- Padding: `6px 11px`
- Hover: none required
- Use sparingly to create trust and rapid scanning

### Nav bar
- Background: translucent white with blur
- Text: primary brand and muted nav links
- Border: bottom border only
- Radius: none
- Padding: `min-height 72px`
- Hover: nav links darken to primary text
- Use as sticky global frame on Pages and landing pages

### Footer
- Background: page background
- Text: secondary gray
- Border: none by default
- Radius: none
- Padding: `28px 0 54px`
- Hover: links use blue
- Use for quiet brand close, not a cluttered sitemap

### Section headings
- Eyebrow: uppercase yellow chip
- H2: `1.45rem` to `2.1rem`, negative tracking
- Paragraph: muted gray with maximum width
- Use strong white space above and below

### Code snippets
- Background: `#FFFEF8`
- Text: `#1F2937`
- Border: `1px solid #E5E7EB`
- Radius: `14px`
- Padding: `16px`
- Hover: none
- Use JetBrains Mono only

### Info / warning / success boxes
- Info: blue-tinted background and border, use for technical notes
- Warning: warm yellow background and border, use for friction or limitations
- Success: light green-tinted surface, use for completed setup or readiness
- Keep icon use optional and minimal

## 4. Landing page information architecture

### Hero
- Purpose: communicate value in under 10 seconds
- Layout: two-column; left copy and actions, right trust/product proof
- Content hierarchy: eyebrow, headline, one-line value, CTAs, trust strip, quick stats
- Visual treatment: strongest spacing, subtle warm radial wash, crisp white cards

### Trust strip / badges
- Purpose: create instant legitimacy
- Layout: compact chips under hero copy
- Content hierarchy: MIT, Beta, Pages, University, Agent tools
- Visual treatment: pill chips with minimal color

### Problem statement
- Purpose: frame the pain clearly before listing features
- Layout: two side-by-side cards
- Content hierarchy: "why people get stuck" then "what EchoTime adds"
- Visual treatment: one neutral card and one sun-emphasis card

### Key features
- Purpose: make the scope concrete
- Layout: three feature cards
- Content hierarchy: compare series, compare datasets, agent handoff
- Visual treatment: balanced card grid with one highlighted center card

### Architecture diagram section
- Purpose: explain where the repo sits in a broader workflow
- Layout: flow chips followed by three diagram cards
- Content hierarchy: observe, explain similarity, ship artifact
- Visual treatment: dashed blue outlines and very subtle yellow gradients

### Example workflow
- Purpose: show the product path from input to output
- Layout: horizontal or stacked steps
- Content hierarchy: input, compare, output
- Visual treatment: numbered steps with sun-colored index circles

### Quickstart section
- Purpose: convert interest into action
- Layout: side-by-side code and expected output
- Content hierarchy: install command, one-liner, output preview
- Visual treatment: warm code surfaces, strong borders, no clutter

### Demo / screenshots section
- Purpose: prove the product visually
- Layout: two-column report gallery plus iframe or screenshot
- Content hierarchy: raw curves, similarity components, social cards, live playground
- Visual treatment: bright white frames with consistent border radius

### Ecosystem / related repos section
- Purpose: place the repo honestly in a broader stack
- Layout: table or card comparison
- Content hierarchy: package family, strongest fit, relation to EchoTime
- Visual treatment: simple table, no flashy visuals

### Final CTA
- Purpose: close the page with one clear action
- Layout: wide callout band
- Content hierarchy: short reminder, main CTA, secondary CTA
- Visual treatment: subtle yellow gradient on white

## 5. Three reusable style variants

### Variant A: Research Lab
- Density: medium
- Emphasis: reasoning, diagrams, methodology framing
- Tone: most academic and reflective
- Section styling: more note boxes and tables

### Variant B: Productized Open Source
- Density: low to medium
- Emphasis: onboarding, trust, quickstart, demo
- Tone: premium and adoption-oriented
- Section styling: stronger hero, cleaner CTA bands, more action buttons

### Variant C: Benchmark / Dashboard
- Density: medium-high
- Emphasis: results, comparisons, report surfaces
- Tone: technical and analytical
- Section styling: tighter cards, more tables, more embedded visuals

## 6. Tailwind CSS theme proposal

```js
// tailwind.echotime.theme.js
module.exports = {
  theme: {
    extend: {
      colors: {
        page: "#FFFFFF",
        card: "#FAFAFA",
        text: {
          DEFAULT: "#1F2937",
          muted: "#6B7280",
        },
        sun: {
          100: "#FFF4C2",
          300: "#FFE27A",
          500: "#FFC83D",
          700: "#C7950A",
        },
        science: {
          600: "#2F6BFF",
          700: "#2554CC",
        },
        border: "#E5E7EB",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Helvetica", "Arial", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Consolas", "Menlo", "monospace"],
      },
      borderRadius: {
        sm: "14px",
        md: "20px",
        lg: "28px",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(31, 41, 55, 0.06)",
        lift: "0 18px 50px rgba(31, 41, 55, 0.08)",
      },
    },
  },
};
```

## 7. Example landing page implementation

See [examples/design_system/TSLabLanding.tsx](C:/Users/wzp07/OneDrive/文档/data%20library/TSontology/0.1.6/echotime-0.17.0/examples/design_system/TSLabLanding.tsx) for a production-quality single-file React + Tailwind example that follows this system.

## 8. README visual structure template

```md
# RepoName

> One-line value proposition that says what problem is solved and for whom.

[badges...]

![brand card](assets/title_card.svg)

## Why this repo exists

Two short paragraphs:
- the problem
- why existing workflows are insufficient

## Quick example

```bash
pip install repo-name
python -c "..."
```

## What you get

- Feature 1
- Feature 2
- Feature 3

## Installation

Short install notes and friction disclaimers.

## Quick start

Explain the first realistic success path in 3 steps.

## Ecosystem

- related repo A
- related repo B
- docs / demo / benchmark link

## Citation

Short citation block or `CITATION.cff` note.
```

## Recommended icon usage

- Use simple geometric marks, not emoji.
- Prefer dots, waves, arrows, notebooks, nodes, and grid metaphors.
- Keep icons line-based or simple filled marks; avoid decorative illustration.
- Use yellow for highlights and blue for technical anchors, never both at full saturation everywhere.

# Design System: Stock Partner (Claude / Anthropic Inspired)

> Based on [Claude (Anthropic) design language](https://claude.ai) — warm, editorial, human-centered.
> Adapted for financial data visualization with Chinese market conventions.

## 1. Visual Theme & Atmosphere

A literary salon reimagined as a financial dashboard. The interface uses **parchment-toned canvas** (`#f5f4ed`) evoking premium paper, with **terracotta** (`#c96442`) as the brand accent. Where most financial tools lean cold and technical, this design radiates warmth — as if the analysis itself has good taste.

The signature move is the **serif headline hierarchy** (Georgia) — each section title carries the gravitas of a book chapter. Combined with clean sans-serif body text and warm neutral tones throughout, the visual language says "thoughtful analysis" rather than "screaming ticker."

**Key Characteristics:**
- Warm parchment canvas (`#f5f4ed`) — premium paper, not screens
- Terracotta brand accent (`#c96442`) — earthy, deliberately un-tech
- Exclusively warm-toned neutrals — every gray has a yellow-brown undertone
- Serif for authority (headlines), sans for utility (UI text, data)
- Ring-based shadow system (`0px 0px 0px 1px`) for interactive depth
- Alternating light/dark sections for chapter-like page rhythm
- Chinese stock market convention: 红涨绿跌 (red = up, green = down)

## 2. Color Palette & Roles

### Brand & Primary
| Token | Hex | Role |
|-------|-----|------|
| Near Black | `#141413` | Primary text, dark surface backgrounds |
| Terracotta | `#c96442` | Brand accent, primary CTAs, emphasis |
| Coral | `#d97757` | Secondary accent, links on dark |

### Surface & Background
| Token | Hex | Role |
|-------|-----|------|
| Parchment | `#f5f4ed` | Main page background |
| Ivory | `#faf9f5` | Card surfaces, elevated containers |
| Warm Sand | `#e8e6dc` | Button backgrounds, dividers |
| Dark Surface | `#30302e` | Dark section containers |
| Near Black | `#141413` | Dark hero background |

### Text & Neutrals
| Token | Hex | Role |
|-------|-----|------|
| Near Black | `#141413` | Primary text on light |
| Ivory | `#faf9f5` | Primary text on dark |
| Olive Gray | `#5e5d59` | Secondary body text |
| Stone Gray | `#87867f` | Tertiary text, metadata |
| Charcoal Warm | `#4d4c48` | Button text on light surfaces |
| Warm Silver | `#b0aea5` | Text on dark surfaces |

### Borders & Shadows
| Token | Hex | Role |
|-------|-----|------|
| Border Cream | `#f0eee6` | Standard card borders |
| Border Warm | `#e8e6dc` | Prominent dividers |
| Dark Surface | `#30302e` | Borders on dark sections |

### Financial Semantic
| Token | Hex | Role |
|-------|-----|------|
| Rise Red | `#d94a3a` | Price up (Chinese convention) |
| Fall Green | `#5a9e6b` | Price down |
| Warn Amber | `#b8860b` | Warnings, medium scores |
| Crimson | `#b53333` | Error states, risk alerts |
| Focus Blue | `#3898ec` | Links, focus states (only cool color) |

## 3. Typography Rules

### Font Family
- **Headline**: Georgia, 'Noto Serif SC', serif
- **Body / UI**: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif
- **Code**: 'SF Mono', 'Cascadia Code', Consolas, monospace (Tailwind `font-mono`)

### Hierarchy

| Role | Font | Size | Weight | Line Height | Use |
|------|------|------|--------|-------------|-----|
| Hero Title | Serif | 3-4rem | Normal (400) | 1.15 | Home page hero |
| Page Title | Serif | 2-2.5rem | Normal (400) | 1.15-1.3 | Prediction page title |
| Section Heading | Serif | 1.25-1.5rem | Normal (400) | 1.3 | Section labels |
| Card Title | Serif | 1.25rem | Normal (400) | 1.3 | Stock names in cards |
| Body Large | Sans | 1.125rem | Normal (400) | 1.6 | Hero subtitle |
| Body Standard | Sans | 1rem | Normal (400) | 1.6 | Main content |
| Body Small | Sans | 0.875rem | Normal (400) | 1.6 | Card descriptions |
| Caption | Sans | 0.75rem | Normal (400) | 1.4 | Metadata, badges |
| Label | Sans | 0.625-0.75rem | 500-600 | 1.25 | Section labels, overline |
| Data | Sans/Mono | varies | 600-700 | 1 | Price data, metrics |

### Principles
- **Serif for authority, sans for utility** — headlines in serif, UI/data in sans
- **Single weight for serifs** — all serif at weight 400 (normal), no bold
- **Relaxed body line-height** — 1.6 for body text, book-like reading experience
- **Tight headings** — 1.15-1.3 for headlines, tight but breathable
- **Data density** — financial numbers use tighter line-height for scanability

## 4. Component Stylings

### Buttons
- **Primary CTA**: Terracotta (`#c96442`) bg, Ivory (`#faf9f5`) text, ring shadow, rounded-xl (12px)
- **Secondary**: Warm Sand (`#e8e6dc`) bg, Charcoal Warm (`#4d4c48`) text, border-warm border, rounded-xl
- All buttons: font-sans, font-medium, smooth hover transitions

### Cards & Containers
- Standard: Ivory (`#faf9f5`) bg, 1px Border Cream border, rounded-2xl (16px), whisper shadow
- Dark: Near Black (`#141413`) bg, Dark Surface border
- Data metric boxes: Parchment bg, subtle borders, rounded-xl (12px)

### Stock Cards
- Rank badge: Terracotta for #1, silver for #2, bronze for #3
- Score bar: gradient from green (low) through amber (mid) to terracotta (high)
- Stock price: Rise Red for positive, Fall Green for negative
- Tags: colored backgrounds at 8% opacity with matching borders

### Navigation
- Back links: Stone Gray, hover Terracotta
- History items: Ivory cards, hover border Terracotta

## 5. Layout Principles

### Spacing
- Section vertical: 48-80px between major sections
- Card internal: 20-32px padding
- Content max-width: 48rem (768px) centered
- Hero: full-width dark background

### Grid
- Max container: ~768px wide, centered
- Cards: single column, stacked
- Metric grids: 2-5 columns responsive

### Border Radius Scale
- Buttons: 12px (rounded-xl)
- Cards: 16px (rounded-2xl)
- Metric boxes: 12px (rounded-xl)
- Tags/badges: full (rounded-full)

## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat | No shadow | Parchment background |
| Contained | `1px solid #f0eee6` | Standard cards |
| Ring | `0px 0px 0px 1px` | Interactive buttons |
| Whisper | `rgba(0,0,0,0.05) 0px 4px 24px` | Elevated feature cards |
| Dark Section | Near Black background | Hero, market snapshot |

## 7. Do's and Don'ts

### Do
- Use Parchment (`#f5f4ed`) as the primary background
- Use serif (Georgia) for all headlines at normal weight
- Use Terracotta (`#c96442`) only for primary CTAs and brand moments
- Keep all neutrals warm-toned
- Use ring shadows for interactive states
- Use Chinese convention: 红涨绿跌

### Don't
- Don't use cool blue-grays — everything is warm-toned
- Don't use bold on serif headlines
- Don't introduce saturated colors beyond the palette
- Don't use sharp corners (< 8px radius)
- Don't apply heavy drop shadows
- Don't use pure white as page background

## 8. Responsive Behavior

- **Mobile** (< 640px): Single column, reduced heading sizes, stacked grids
- **Tablet** (640-1024px): 2-3 column grids begin
- **Desktop** (1024px+): Full layout, max-width container
- Touch targets: minimum 44x44px
- Hero title scales: 56px → 40px → 32px

## 9. Quick Reference

```
Brand CTA:     Terracotta #c96442
Page BG:       Parchment #f5f4ed
Card BG:       Ivory #faf9f5
Primary Text:  Near Black #141413
Secondary:     Olive Gray #5e5d59
Tertiary:      Stone Gray #87867f
Borders:       Border Cream #f0eee6
Dark Surface:  Near Black #141413 / Dark Surface #30302e
Rise (涨):     Rise Red #d94a3a
Fall (跌):     Fall Green #5a9e6b
```

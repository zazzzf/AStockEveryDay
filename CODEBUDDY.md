# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## Overview

AStockEveryDay is a daily A-share "limit-up" (涨停) prediction web app — a single-page static site that displays AI-curated stock picks for the next trading day. It runs entirely client-side with zero build step: one HTML file, a Tailwind CSS CDN, and JSON data files.

## Commands

Since there is no build tooling, framework, or test suite:

- **Serve locally**: `python -m http.server 8080` (or any static file server) from the repo root, then open `http://localhost:8080`.
- **Validate data**: manually check that each `data/*.json` file is well-formed JSON. A quick sanity check: `python -c "import json; [json.load(open(f'data/{f}')) for f in ['predictions.json','20260610.json','20260611.json','20260615.json','20260616.json']]"` will throw on parse errors.
- **Add a new prediction day**: create a `data/YYYYMMDD.json` file (schema below), then prepend its metadata entry to `data/predictions.json`. No other files need changes.

## Architecture

### File structure

```
index.html          ← Entire application: styles, Tailwind config, SPA router, component renderers
DESIGN.md           ← Visual design system (colors, typography, components, layout rules)
data/
  predictions.json  ← Index array of all predictions (sorted newest-first)
  YYYYMMDD.json     ← Full prediction data for a single date
```

### How the app boots (`index.html`)

1. **`init()`** fetches `data/predictions.json` → populates `predictionsIndex` (global array).
2. **`route()`** reads `location.hash` and dispatches:
   - `#home` or no hash → `home()` — renders the home page showing latest prediction + history list.
   - `#{datePrefix}` (e.g. `#0616`) → finds matching entry in `predictionsIndex` via `id.endsWith(hash)` → calls `loadPrediction(id)`.
3. Hash changes are listened via `window.addEventListener('hashchange', route)`.

### Data flow

- **Index file** (`predictions.json`): array of objects with `id`, `date`, `weekday`, `generated`, `title`, `summary`, `topStocks` (5 names), `topCodes` (5 codes). This is the only file loaded on initial page load.
- **Detail file** (`YYYYMMDD.json`): loaded lazily when user navigates to a specific prediction. Contains the full `marketSnapshot`, `hotConcepts`, `fiveDayConcepts`, `stocks[]` (ranked 1-5 with scores, metrics, analysis), `summaryTable`, `auctionTimeline`, `riskItems`, `footer`.

The convention is that `data/predictions.json` entries are ordered newest-first (index 0 = latest).

### Rendering architecture

`index.html` is a vanilla JS SPA — no framework, no virtual DOM. Each "page" is rendered by setting `innerHTML` on the `#app` div with template literals.

Key render functions:
- **`home()`**: renders hero section, latest prediction card (with "LATEST" ribbon), and history list. History items link to `#${id.slice(4)}` (e.g. `#0616` from `"20260616"`).
- **`loadPrediction(id)`**: fetches `data/{id}.json`, calls `renderPrediction(d)`.
- **`renderPrediction(d)`**: renders the full detail page — header, market snapshot (via `renderMarketSnapshot`), hot concepts grids, stock cards (via `renderStockCard`), summary table, auction timeline, risk items.
- **`renderMarketSnapshot(d)`**: index cards showing market data (CSI, GEM, etc.) with red/green coloring.
- **`renderStockCard(s)`**: individual stock card with rank badge, score bar, price, metrics grid, core logic, auction expectation, entry conditions.

Helper functions: `scoreGrad(s)` returns gradient color for score bars, `rankBadge(r)` returns CSS for rank badges, `tagClr(t)` returns color schemes for tags (`concept`, `lhb`, `board`).

### Design system (see `DESIGN.md` for full reference)

- **Palette**: Warm-toned. Parchment (`#f5f4ed`) page background, Ivory (`#faf9f5`) cards, Terracotta (`#c96442`) brand accent. Cool blue (`#3898ec`) is the only non-warm color, used for focus states and links.
- **Typography**: Serif (Georgia) for authority/headlines at weight 400 only (never bold). Sans-serif for body, UI, data. Chinese market convention: red (`#d94a3a`) = up, green (`#5a9e6b`) = down.
- **Depth**: No heavy drop shadows. Uses `0px 0px 0px 1px` ring shadows and a subtle "whisper" shadow (`rgba(0,0,0,0.05) 0px 4px 24px`).
- **Border radius**: rounded-xl (12px) for buttons/metrics, rounded-2xl (16px) for cards, rounded-full for tags.

### `data/predictions.json` schema

```json
[
  {
    "id": "20260616",           // YYYYMMDD — used as detail file name
    "date": "2026-06-16",       // Display date
    "weekday": "周二",          // Chinese weekday
    "generated": "06-15",       // MM-DD of generation
    "title": "MLCC / CPO / PCB 五线齐发",
    "summary": "...",           // HTML with <b> tags allowed
    "topStocks": ["东山精密",...], // 5 stock names
    "topCodes": ["002384",...]   // 5 stock codes (without exchange prefix)
  }
]
```

### `data/YYYYMMDD.json` schema (detail page)

Top-level: `id`, `date`, `weekday`, `generated`, `title`, `subtitle`, `macroAlert` (optional), `themeOverview` (optional), `marketSnapshot`, `hotConcepts[]`, `fiveDayConcepts[]`, `stocks[]`, `summaryTable`, `auctionTimeline[]`, `riskItems[]`, `footer`.

Each stock in `stocks[]`: `rank`, `name`, `code` (e.g. `"sz002384"`), `score` (0-100), `tags[]`, `price`, `change`, `limitStatus`, `metrics[]`, `coreLogic`, `auctionExpect`, `entryCondition`. The `auctionExpect` and `entryCondition` fields may contain inline HTML with classes like `hl` (highlight), `gn` (green/signal), `wn` (warning), `bl` (link/blue), `ac` (accent).

### Adding a new prediction

1. Create `data/YYYYMMDD.json` following the detail schema above.
2. Prepend a new entry to `data/predictions.json` — set `id` to match the date, populate `topStocks` and `topCodes` with the top 5 stock names and codes respectively.
3. The app auto-discovers the new entry on next load via `predictions.json`.

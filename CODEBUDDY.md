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

**必须与 `index.html` 渲染器读取的字段名严格一致**，否则会出现 `#undefined`、`[object Object]`、空白表格等显示问题：

- `marketSnapshot.indices[]` 每项：`label`（不是 `name`）、`code`、`value`、`change`、`isUp`（布尔，不是字符串 `trend`）。
- `hotConcepts[]` 每项：`rank`（整数）、`name`、`change`；可选 `note`。
- `fiveDayConcepts[]` 每项：`rank`（整数）、`name`、`change`；前三可加 `medal`（`🥇/🥈/🥉`）。
- `stocks[]` 每项：`rank`、`name`、`code`、`score`、`tags[]`、`price`、`change`、`limitStatus`、`metrics[]`、`coreLogic`、`auctionExpect`、`entryCondition`。
  - `tags[]` 每项：`label`、`type`（`concept`/`lhb`/`board`）。
  - `metrics[]` 每项：`label`、`value`。
- `summaryTable`：**对象** `{ "headers": [...], "rows": [[...], ...] }`，不是 `[{label,value}]` 数组。渲染器用 `d.summaryTable.headers` 和 `d.summaryTable.rows`。
- `auctionTimeline[]` 每项：`time`、`desc`（不是 `event`/`action`）。
- `riskItems[]`：**字符串数组**，每项直接是 HTML 文本；不要放 `{level, text}` 对象（会变成 `[object Object]`）。
- `footer`：**对象** `{ "source": "...", "time": "..." }`，渲染器用 `d.footer.source` 和 `d.footer.time`。

最安全的做法：直接复制并填写 `gen_template.py`，它已按上述 schema 写好模板，填完运行即可生成合法 JSON。

### Adding a new prediction

1. 复制 `gen_template.py` 为临时脚本，修改 `DATE_ID` 和各字段内容，运行后生成 `data/YYYYMMDD.json`。
2. Prepend a new entry to `data/predictions.json` — set `id` to match the date, populate `topStocks` and `topCodes` with the top 5 stock names and codes respectively.
3. The app auto-discovers the new entry on next load via `predictions.json`.

## Data Integrity Rules (数据完整性铁律)

> 历史上多次出现"手写 JSON → 未转义引号/编码乱码 → 详情页打不开 → 推到 GitHub 才发现"的事故（20260806、20260710 均为未转义 ASCII 双引号导致 JSON 断裂）。以下规则必须严格遵守：

1. **禁止用字符串拼接 / Write 工具直接写 JSON 原文。** 必须先在 Python 里构造 `dict`，再用 `json.dump(obj, f, ensure_ascii=False, indent=2)` 序列化——它会自动转义引号、换行、控制字符。参见 `rebuild_0806.py` 的规范写法。
2. **锁定编码**：一律 `open(path, "w", encoding="utf-8")` + `json.dump(..., ensure_ascii=False)`。绝不依赖平台默认编码（Windows 上可能是 GBK，会产生乱码 `�`）。
3. **提交前必须过校验**：仓库已装 pre-commit 钩子，会在 `git commit` 时自动对暂存区里 `data/*.json` 跑 `validate_data.py`，出现硬伤（解析失败 / U+FFFD 乱码 / 非法控制字符 / `id`≠文件名 / `date` 非 YYYY-MM-DD / `stocks`≠5 / 个股缺字段）直接阻止提交。手动全量审计：`python validate_data.py --all`。
4. **文件已损坏时**：不要手工改坏文件。用 Python dict 重建（参考 `rebuild_0806.py`），或用"读文本→状态机转义内部引号→`json.loads`→重 dump"的方式修复。
5. **Schema 约束**：`id` 必须等于文件名（YYYYMMDD）；`stocks` 必须恰好 5 条；`summaryTable` 为对象 `{headers, rows}`；`riskItems` 为字符串数组；`footer` 为对象 `{source, time}`；`predictions.json` 条目最新在前，`topStocks`/`topCodes` 长度 5。详见上方 schema 说明。

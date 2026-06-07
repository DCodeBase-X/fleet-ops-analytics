# Fleet Ops Analytics — Redesign & Enhancement Spec

**Date:** 2026-06-06  
**Author:** Damarius McNair  
**Status:** Approved

---

## Overview

Elevate the Fleet Ops Analytics project from a functional Streamlit dashboard to a portfolio-grade, organization-ready analytics platform. The work spans four areas: a cohesive Enterprise Ops Dark design system, a modular Python architecture for `app.py`, DuckDB-powered analytical SQL in the Jupyter notebook, and TPM-quality technical documentation. The goal is a project that reads as serious operational tooling to a technical hiring audience, a business stakeholder, and a working ops team simultaneously.

---

## Audience

- **Portfolio / hiring showcase** — the primary viewer may be a hiring manager, engineering lead, or technical recruiter evaluating craft and judgment
- **Executive stakeholder** — emphasis on business outcomes, KPI clarity, strategic insight language
- **Operational tool** — credibly functional for a working fleet ops team; not decorative

---

## Scope

Four independent workstreams, delivered together:

1. Enterprise Ops Dark design system applied to `dashboard/app.py`
2. Modular refactor of `dashboard/` into four focused files
3. DuckDB native SQL replacing pandas aggregations in `notebooks/fleet_analysis.ipynb`
4. Technical documentation in `docs/technical/` (four Markdown files)

---

## 1. Design System — Enterprise Ops Dark

### Color Tokens (defined in `config.py`)

| Token | Hex | Usage |
|---|---|---|
| `BG_BASE` | `#0D1117` | Page background |
| `BG_CARD` | `#161B22` | KPI cards, chart containers |
| `BG_ELEVATED` | `#1C2128` | Sidebar, hover states |
| `BORDER` | `#21262D` | All borders and dividers |
| `TEXT_PRIMARY` | `#E6EDF3` | Headings, KPI values |
| `TEXT_SECONDARY` | `#8B949E` | Labels, captions, subtitles |
| `ACCENT_BLUE` | `#58A6FF` | Primary accent, active tabs, links |
| `ACCENT_GREEN` | `#3FB950` | On-target / healthy status |
| `ACCENT_AMBER` | `#D29922` | Warning / watch status |
| `ACCENT_RED` | `#F85149` | Alert / critical status |

### Typography

- **KPI values and data labels:** `JetBrains Mono` — signals instrumentation over decoration
- **Body text, captions, headings:** `Inter` — contrast between monospace data and sans-serif prose creates visual hierarchy without additional color
- Both fonts loaded via Google Fonts in the CSS injection block

### Component Specifications

**KPI cards:** Dark background (`BG_CARD`), 2px top-border accent (status color), monospace value, uppercase label in `TEXT_SECONDARY`. Top-border replaces the left-border used in the current design — cleaner in dark mode.

**Insight cards:** Terminal aesthetic — `BG_CARD` background, `ACCENT_AMBER` left-border (4px), `TEXT_PRIMARY` body text, `TEXT_SECONDARY` label.

**Sidebar:** `BG_BASE` background, `BG_ELEVATED` on hover states, no white background. Controls styled to match dark theme.

**Charts:** `plot_bgcolor` → `BG_CARD`, `paper_bgcolor` → `rgba(0,0,0,0)`, grid lines → `BORDER`, all axis tick labels → `TEXT_SECONDARY`, hover labels → dark background with `BORDER` outline.

**Tabs:** Underline active state in `ACCENT_BLUE`, `BG_BASE` background throughout, `TEXT_SECONDARY` inactive tab labels.

**Footer:** Dark-styled, retains attribution and GitHub link.

### CSS Delivery

The full dark theme CSS is defined as a `DARK_THEME_CSS` constant in `config.py` and injected once in `app.py` via `st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)`. No external CSS file — keeps deployment to a single directory.

---

## 2. Modular Architecture — `dashboard/`

### File Responsibilities

| File | Owns | Does not own |
|---|---|---|
| `config.py` | Constants, color tokens, thresholds, paths | Logic, rendering, data |
| `data.py` | Loading, pre-computation, filtering, KPI derivation | Rendering, chart construction |
| `charts.py` | Plotly figure construction, dark theme application | Data loading, `st.` calls |
| `app.py` | Page config, CSS injection, sidebar, tab layout | Pandas operations, Plotly construction |

### `config.py`

- `OT_PREMIUM = 28.0`
- `DATA_DIR` resolved at import time relative to file location
- `DATA_FILES` dict (filename → display name)
- Full color token dict (`COLORS`)
- `DARK_THEME_CSS` string constant
- `util_status(pct) -> str` — returns `"green"`, `"amber"`, or `"red"` based on thresholds (≥80, ≥60, <60)
- `ot_status(ratio) -> str` — returns status based on OT ratio vs. baseline

### `data.py`

```
FleetData (dataclass)
  util: pd.DataFrame        # with utilization_pct, season, month_period pre-computed
  ot: pd.DataFrame          # with day_name pre-computed
  maint: pd.DataFrame
  veh: pd.DataFrame

KPISet (dataclass)
  fleet_count: int
  avg_util: float
  util_delta: float
  total_ot_hrs: float
  ot_cost: float
  ot_ratio: float
  total_maint: float
  avg_ot_shift: float
  shift_delta: float
```

- `load_data() -> FleetData` — decorated `@st.cache_data(ttl=3600)`. Parses dates once, computes derived columns once.
- `filter_data(data, location, start, end) -> FleetData` — returns filtered copy. All filter logic here only.
- `compute_kpis(data, filtered) -> KPISet` — computed once per filter change, result passed to all tabs. Eliminates repeated computation across four tab renders.

**Performance specifics:**
- `utilization_pct` column computed at load (`* 100`), eliminating scattered inline multiplications
- `month_period` pre-computed as string at load — avoids repeated `.dt.to_period()` chains at render time
- `season` column derived once at load
- Vectorized color assignment via `pd.cut` with label map in `charts.py` — replaces Python `for` loops
- `hash_funcs` on `FleetData` dataclass prevents Streamlit cache misses on filter changes

### `charts.py`

One function per chart. All accept a DataFrame, return a `go.Figure`. No `st.` calls inside any chart function.

Chart factories:
- `make_util_trend(df) -> go.Figure`
- `make_ot_by_location(df) -> go.Figure`
- `make_ot_by_role(df) -> go.Figure`
- `make_ot_daily(df) -> go.Figure`
- `make_ot_monthly(df) -> go.Figure`
- `make_util_by_type(df) -> go.Figure`
- `make_util_by_location(df) -> go.Figure`
- `make_seasonal_by_type(df) -> go.Figure`
- `make_util_heatmap(df) -> go.Figure`
- `make_maint_cost(df) -> go.Figure`
- `make_maint_trend(df) -> go.Figure`
- `make_fleet_growth(df) -> go.Figure`

`apply_chart_style(fig, title, subtitle) -> go.Figure` updated to apply dark theme tokens throughout.

### `app.py`

Target: under 200 lines. Contains:
1. Page config
2. `st.markdown(DARK_THEME_CSS)` — single CSS injection
3. Sidebar: data existence check, regenerate control, location selector, date range picker
4. `data = load_data()`
5. `filtered = filter_data(data, selected_loc, start, end)`
6. `kpis = compute_kpis(data, filtered)`
7. Four tab renderers — each calls chart factories and renders KPI cards, no pandas or Plotly inline

---

## 3. Notebook — DuckDB Native SQL

### Setup

Replace four `pd.read_csv` calls with a DuckDB connection and `CREATE VIEW` statements. DuckDB queries CSV files directly via `read_csv_auto()` — no full load into memory. Results converted to pandas DataFrames via `.df()` for matplotlib visualizations.

```python
import duckdb
con = duckdb.connect()
con.execute("CREATE VIEW util  AS SELECT * FROM read_csv_auto('../data/daily_utilization.csv')")
con.execute("CREATE VIEW ot    AS SELECT * FROM read_csv_auto('../data/staff_overtime.csv')")
con.execute("CREATE VIEW maint AS SELECT * FROM read_csv_auto('../data/maintenance_records.csv')")
con.execute("CREATE VIEW veh   AS SELECT * FROM read_csv_auto('../data/fleet_vehicles.csv')")
```

### SQL Patterns by Section

**Section 1 — Data Quality**
- Null audit: `SELECT ... COUNT(*) FILTER (WHERE col IS NULL)` with `UNION ALL` across tables — set-based, not a Python loop
- Duplicate checks: `SELECT COUNT(*) - COUNT(DISTINCT ...)` pattern
- Value ranges: inline `MIN/MAX` aggregations

**Section 2 — Fleet Utilization**
- Monthly trend: `DATE_TRUNC('month', date)` GROUP BY
- Seasonal split: CTE computing summer vs. rest-of-year averages inline
- Heatmap pivot: `PIVOT` on location × month
- Seasonal swing table: window function `AVG(utilization_rate) OVER (PARTITION BY vehicle_type, MONTH(date))`

**Section 3 — OT Root Cause**
- Overindex calculation: CTE defining base metrics, downstream CTEs referencing it
- Role concentration: `RANK() OVER (ORDER BY SUM(overtime_hours) DESC)` window function
- Top-N filtering: `QUALIFY RANK() OVER (...) <= 2` — signals analytical SQL fluency

**Section 4 — Maintenance**
- Downtime/utilization join: explicit SQL JOIN between monthly aggregates — shows understanding of grain alignment
- Pearson correlation: `CORR()` aggregate function (built into DuckDB)

**Section 5 — Cost Impact**
- All lever calculations as parameterized CTEs — base metrics defined once, referenced downstream. Clean and auditable.

### What Stays Unchanged
- All matplotlib/seaborn visualizations — fed from `.df()` on DuckDB results
- All narrative markdown cells
- All chart titles, labels, and color logic

---

## 4. Technical Documentation — `docs/technical/`

### Files

**`docs/technical/architecture.md`**
Opens with a one-paragraph system summary readable by a non-technical stakeholder. Contains: module responsibility table, ASCII/Mermaid data flow diagram (CSV → `data.py` → `FleetData` → filter → `KPISet` → tab renderers → charts), dependency map, and a "key design decisions" section explaining the rationale behind the modular split — not what it is, but why.

**`docs/technical/data-dictionary.md`**
Schema for all four CSVs: column name, type, description, example value, and business definition. Includes derived columns added at load time (`utilization_pct`, `season`, `month_period`). Includes `OT_PREMIUM` constant with business rationale. The reference doc a new analyst or engineer opens first.

**`docs/technical/analytics-methodology.md`**
Documents every KPI and metric: computation method, threshold logic, and business interpretation. Covers: fleet utilization rate, OT cost calculation, baseline vs. filtered comparison, overindex factor, seasonal classification. Written so an auditor or stakeholder can validate numbers without reading code. Includes a "known limitations" section: synthetic data scope, what the 80% target represents, where the `$28/hr OT premium` comes from.

**`docs/technical/operations-runbook.md`**
Install, run, generate data, regenerate. Environment setup. How to add a new location or date range. Troubleshooting section for the three most common failure modes: data not found, cache stale, port conflict. Written for a technical user new to the repo — concise, imperative.

### Writing Standard
All four documents written to senior TPM standard: precise language, no marketing superlatives, explicit rationale for design decisions, known limitations acknowledged. Tables preferred over prose for reference material. Each document is self-contained — no cross-references required to understand it.

---

## File Tree After Implementation

```
fleet-ops-analytics/
├── dashboard/
│   ├── config.py          # constants, tokens, CSS
│   ├── data.py            # loading, filtering, KPI computation
│   ├── charts.py          # Plotly figure factories
│   └── app.py             # layout and routing only (<200 lines)
├── notebooks/
│   └── fleet_analysis.ipynb   # DuckDB SQL throughout
├── data/
│   └── *.csv
├── docs/
│   ├── technical/
│   │   ├── architecture.md
│   │   ├── data-dictionary.md
│   │   ├── analytics-methodology.md
│   │   └── operations-runbook.md
│   └── superpowers/
│       └── specs/
│           └── 2026-06-06-fleet-ops-dashboard-redesign-design.md
└── requirements.txt       # add: duckdb
```

---

## Dependencies

Add to `requirements.txt`:
- `duckdb>=0.10.0`

No other new dependencies. `JetBrains Mono` loaded via Google Fonts CDN in CSS — no install required.

---

## Out of Scope

- Multi-page Streamlit `pages/` directory structure
- Persistent DuckDB database file (views on CSV is sufficient)
- Authentication or access control
- Deployment configuration
- New data sources or additional KPIs beyond the existing four tabs

# Architecture — Fleet Ops Analytics

## System Summary

Fleet Ops Analytics is a two-component data platform for a regional fleet of 5,200+ vehicles. A Streamlit web dashboard (Python) provides interactive filtering and visualization of daily operations data across four analytical views: operations summary, overtime cost intelligence, fleet efficiency, and maintenance tracking. A companion Jupyter notebook performs deeper statistical analysis using DuckDB SQL queries directly against the same CSV source files. Both components are read-only relative to the source data; neither writes back to the CSVs during normal operation.

---

## Module Responsibility Table

| File | Owns | Does Not Own |
|---|---|---|
| `dashboard/config.py` | Constants (`OT_PREMIUM`, `DATA_DIR`, `COLORS`), status threshold functions (`util_status`, `ot_status`), dark-theme CSS string | Any DataFrame logic, Streamlit calls, chart construction |
| `dashboard/data.py` | CSV loading with caching, derived column computation, date/location filtering, KPI calculation | Rendering, chart construction, CSS, path definitions |
| `dashboard/charts.py` | All 12 Plotly figure factories, `apply_chart_style`, KPI card HTML helpers (`kpi_html`, `insight`) | Streamlit calls (`st.*`), data loading, business constant definitions |
| `dashboard/app.py` | Page config, CSS injection, sidebar controls, tab layout, chart calls, `st.plotly_chart` calls, data bootstrap trigger | Inline pandas aggregations, inline Plotly construction, business logic |
| `notebooks/fleet_analysis.ipynb` | DuckDB view setup, all SQL queries, matplotlib/seaborn visualizations, analytical narrative | Streamlit integration, production data writing |

---

## Data Flow

```
data/
├── daily_utilization.csv ──┐
├── staff_overtime.csv ─────┤
├── maintenance_records.csv ─┤──► load_data() ──► FleetData (util, ot, maint, veh)
└── fleet_vehicles.csv ─────┘    [@st.cache_data,        │
                                   ttl=3600s]             │
                                                          │
                          sidebar controls ──────────────►│
                          (location, date range)          ▼
                                               filter_data() ──► filtered FleetData
                                                                        │
                                                                        ▼
                                                          compute_kpis(data, filtered)
                                                                        │
                                                                        ▼
                                                                   KPISet
                                                                        │
                          ┌─────────────────────────────┬─────────────┴──────────────┐
                          ▼                             ▼                            ▼
                     Tab 1: Operations           Tab 2: OT Intel           Tab 3: Fleet Efficiency
                     Tab 4: Maintenance Radar
                          │                             │
                          ▼                             ▼
                   chart factories ──────────► st.plotly_chart()
               (make_util_trend, etc.)
```

---

## Dependency Map

```
app.py
  └── dashboard.config   (DARK_THEME_CSS, DATA_DIR, DATA_FILES)
  └── dashboard.data     (data_exists, load_data, filter_data, compute_kpis)
  └── dashboard.charts   (kpi_html, insight, make_util_trend, make_ot_by_location,
                          make_ot_by_role, make_ot_daily, make_ot_monthly,
                          make_util_by_type, make_util_by_location,
                          make_seasonal_by_type, make_util_heatmap,
                          make_maint_cost, make_maint_trend, make_fleet_growth)

data.py
  └── dashboard.config   (DATA_DIR, DATA_FILES, OT_PREMIUM, util_status, ot_status)
  └── pandas             (DataFrame, read_csv, Timestamp)
  └── streamlit          (st.cache_data — decorator only)

charts.py
  └── dashboard.config   (COLORS, OT_PREMIUM)
  └── pandas             (DataFrame, Series, Categorical, cut)
  └── plotly.express     (px.area, px.line, px.imshow)
  └── plotly.graph_objects (go.Figure, go.Bar, go.Scatter)
  └── plotly.subplots    (make_subplots)

config.py
  └── os                 (path resolution)
  (no project-internal imports)

notebooks/fleet_analysis.ipynb
  └── duckdb             (SQL engine, CSV views)
  └── pandas             (result DataFrames from .df())
  └── numpy              (polyfit for trend line)
  └── matplotlib / seaborn (chart rendering)
  └── (no dashboard.* imports — standalone)
```

---

## Key Design Decisions

### Modular split: config / data / charts / app

The four-module split enforces a strict boundary between concerns that would otherwise drift together in a single-file Streamlit app. Without it, business constants (thresholds, cost rates) tend to get inlined into chart code, making them hard to update consistently; CSS gets embedded in tab rendering blocks; and pandas aggregations accumulate inside chart functions.

The split also has a practical testing benefit: `config.py`, `data.py`, and `charts.py` carry no Streamlit rendering side effects, so they can be unit-tested without a running Streamlit server. `app.py` is the only module that requires a browser session to exercise fully.

### `@st.cache_data` on `load_data` only

`load_data` is the only function that reads from disk — a slow, repeatable, deterministic operation whose output changes only when the underlying CSV files change. Caching it with a one-hour TTL means the four CSVs are read once per session refresh cycle, not on every widget interaction.

`filter_data` and `compute_kpis` are not cached because their inputs change with every sidebar interaction (new location selection, new date range). Caching them would require Streamlit to hash the `FleetData` dataclass and both `pd.Timestamp` arguments on every call, which is slower than just running the in-memory pandas filter operations. These functions operate on DataFrames already resident in memory and complete in milliseconds.

### KPISet pre-computes everything

`compute_kpis` returns a fully-populated `KPISet` dataclass before any tab renders. This means `app.py` accesses computed values by attribute (`kpis.avg_util`, `kpis.ot_status`) and never performs inline pandas operations inside tab rendering blocks.

The alternative — computing KPIs inline as each tab renders — creates two problems. First, the same aggregations run multiple times if a value appears in more than one tab. Second, `app.py` becomes a mixed-responsibility module: it handles both layout and business logic, which makes the layout harder to read and the business logic harder to test. Pre-computation through `KPISet` keeps `app.py` as a pure routing and rendering layer.

`KPISet` also performs NaN guards centrally (`if not filtered.util.empty else 0.0`), ensuring that empty filter results (e.g., a location with no activity in the selected date range) produce 0 / "blue" defaults rather than rendering errors scattered across multiple tab blocks.

### DuckDB views in the notebook instead of pandas CSV loads

The notebook uses `duckdb.connect()` with four `CREATE VIEW` statements that query the CSVs directly via `read_csv_auto()`. This means DuckDB reads and scans only the columns and rows needed by each query rather than loading all four CSVs into memory at import time.

The more significant benefit is analytical capability: DuckDB enables window functions (`RANK() OVER`, `ARGMAX()`), `CORR()` aggregates, `ROLLUP()` grouping sets, and parameterized CTEs in plain SQL. Equivalent operations in pandas require chained method calls across multiple intermediate DataFrames, which are harder to read and harder to audit. SQL also makes the analytical intent explicit in the query itself rather than distributed across code and comments.

The tradeoff is that DuckDB SQL is not directly usable from Streamlit widgets, which is why the dashboard uses pandas — Streamlit's caching and widget system integrates naturally with DataFrames rather than with DuckDB result sets.

### `DARK_THEME_CSS` as an f-string referencing `COLORS`

The CSS string is defined as an f-string in `config.py` immediately after the `COLORS` dict, interpolating every color token directly at module import time. This means there is exactly one place in the codebase where a color value is defined: the `COLORS` dict. Updating `COLORS["blue"]` automatically updates every CSS rule that references it — tab indicator borders, hover states, KPI card accents, button styles — without requiring a separate find-and-replace across the CSS block.

The alternative (hardcoding hex values in both the `COLORS` dict and the CSS string separately) creates two sources of truth that can diverge silently. The f-string approach also makes it apparent when reading `config.py` that the CSS is intentionally coupled to `COLORS`, rather than appearing to be an independent style block.

`app.py` injects the CSS once with a single `st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)` call at startup. Repeated injection on widget interaction is unnecessary because Streamlit preserves injected HTML between reruns.

---

## Known Limitations

- **Synthetic data only.** The platform has been built against a generated dataset. Integration with a live fleet management system or HRIS would require additions to `load_data` (connection strings, authentication) and likely a change from file-based caching to a database-backed cache layer.
- **Single-user assumption.** `@st.cache_data` is process-scoped. Multi-user deployments would need shared caching (Redis, etc.) or separate cache invalidation logic.
- **Hard-coded seasonal annotations.** `make_util_trend`, `make_ot_monthly`, and `make_maint_trend` include `vrect` annotations for Summer 2023 and Summer 2024 with literal date strings. A dataset extending beyond 2024 would require those functions to be updated.
- **OT_PREMIUM is a fixed multiplier.** The $28.00/hr value is a constant, not a configurable parameter. It does not reflect per-role or per-location OT rate differences.

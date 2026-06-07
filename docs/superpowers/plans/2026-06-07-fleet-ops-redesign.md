# Fleet Ops Analytics — Redesign & Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the Fleet Ops Analytics project into a modular, Enterprise Ops Dark-themed dashboard with DuckDB-powered analytical SQL in the notebook and TPM-quality technical documentation.

**Architecture:** Split `dashboard/app.py` into four focused modules (`config.py`, `data.py`, `charts.py`, `app.py`). Apply a cohesive dark design system via CSS tokens. Replace pandas aggregations in the notebook with DuckDB native SQL. Write four technical docs in `docs/technical/`.

**Tech Stack:** Python 3.9+, Streamlit 1.50, Plotly, pandas, DuckDB, pytest, JetBrains Mono + Inter via Google Fonts CDN.

---

## File Map

### Created
- `dashboard/config.py` — constants, color tokens, threshold functions, full dark CSS
- `dashboard/data.py` — `FleetData`, `KPISet` dataclasses; `load_data`, `filter_data`, `compute_kpis`
- `dashboard/charts.py` — dark `apply_chart_style`, `kpi_html`, `insight`, all 12 chart factories
- `tests/__init__.py` — empty, marks tests as package
- `tests/test_config.py` — threshold function tests
- `tests/test_data.py` — filter and KPI computation tests
- `tests/test_charts.py` — chart factory return-type tests
- `docs/technical/architecture.md`
- `docs/technical/data-dictionary.md`
- `docs/technical/analytics-methodology.md`
- `docs/technical/operations-runbook.md`

### Modified
- `dashboard/app.py` — full rewrite, imports from new modules, under 200 lines
- `notebooks/fleet_analysis.ipynb` — DuckDB native SQL replaces pandas aggregations
- `requirements.txt` — add `duckdb>=1.0.0` and `pytest>=7.0`

---

## Task 1: config.py — Constants, Design Tokens, Dark Theme CSS

**Files:**
- Create: `dashboard/config.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Create `dashboard/config.py`**

```python
"""Central configuration: constants, design tokens, status helpers, dark theme CSS."""
from __future__ import annotations
import os

# ── Paths
DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))

# ── Business constants
OT_PREMIUM = 28.0

DATA_FILES = {
    "fleet_vehicles.csv":      "Fleet vehicles",
    "daily_utilization.csv":   "Daily utilization",
    "staff_overtime.csv":      "Staff overtime",
    "maintenance_records.csv": "Maintenance records",
}

# ── Design tokens
COLORS: dict[str, str] = {
    "bg_base":        "#0D1117",
    "bg_card":        "#161B22",
    "bg_elevated":    "#1C2128",
    "border":         "#21262D",
    "text_primary":   "#E6EDF3",
    "text_secondary": "#8B949E",
    "blue":           "#58A6FF",
    "green":          "#3FB950",
    "amber":          "#D29922",
    "red":            "#F85149",
}

# ── Status thresholds
def util_status(pct: float) -> str:
    """Return CSS class name for a utilization percentage."""
    if pct >= 80:
        return "green"
    elif pct >= 60:
        return "amber"
    return "red"


def ot_status(ratio: float) -> str:
    """Return CSS class name for an OT cost ratio vs. baseline."""
    if ratio < -0.05:
        return "green"
    elif ratio < 0.15:
        return "amber"
    return "red"


# ── Dark theme CSS (injected once in app.py)
DARK_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: #0D1117;
    color: #E6EDF3;
}

footer { visibility: hidden; }

/* ── Sidebar */
[data-testid="stSidebar"] {
    background: #0D1117;
    border-right: 1px solid #21262D;
}
[data-testid="stSidebar"] * { color: #E6EDF3; }
[data-testid="stSidebar"] .stSelectbox > div,
[data-testid="stSidebar"] input {
    background: #1C2128;
    border-color: #21262D;
    color: #E6EDF3;
}

/* ── Main background */
.main .block-container { background-color: #0D1117; }

/* ── Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 1px solid #21262D;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 500;
    color: #8B949E;
    border-radius: 0;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #58A6FF !important;
    border-bottom: 2px solid #58A6FF !important;
    background: transparent !important;
}

/* ── KPI cards */
.kpi-card {
    background: #161B22;
    border-radius: 6px;
    border: 1px solid #21262D;
    border-top: 2px solid #8B949E;
    padding: 16px 20px;
    height: 100%;
    box-sizing: border-box;
}
.kpi-card.green { border-top-color: #3FB950; }
.kpi-card.amber { border-top-color: #D29922; }
.kpi-card.red   { border-top-color: #F85149; }
.kpi-card.blue  { border-top-color: #58A6FF; }

.kpi-label {
    font-size: 11px;
    font-weight: 600;
    color: #8B949E;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
.kpi-value {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 24px;
    font-weight: 700;
    color: #E6EDF3;
    line-height: 1.15;
    letter-spacing: -0.5px;
}
.kpi-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    margin-top: 6px;
    color: #8B949E;
}

/* ── Insight cards */
.insight-card {
    background: #161B22;
    border-left: 4px solid #D29922;
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    margin: 4px 0 20px 0;
    font-size: 13px;
    color: #E6EDF3;
    line-height: 1.6;
}
.insight-card strong { color: #D29922; font-weight: 600; }

/* ── Headings */
h1, h2, h3 { color: #E6EDF3; }

/* ── Buttons */
.stButton > button {
    background: #1C2128;
    border: 1px solid #21262D;
    color: #E6EDF3;
}
.stButton > button:hover {
    background: #21262D;
    border-color: #58A6FF;
    color: #58A6FF;
}

/* ── Expander */
[data-testid="stExpander"] {
    background: #161B22;
    border: 1px solid #21262D;
}
</style>
"""
```

- [ ] **Step 2: Create `tests/__init__.py`**

Empty file — marks the directory as a Python package so pytest discovers tests correctly.

```python
```

- [ ] **Step 3: Write failing tests for `config.py`**

```python
# tests/test_config.py
import pytest
from dashboard.config import util_status, ot_status, COLORS, OT_PREMIUM


def test_util_status_green():
    assert util_status(80) == "green"
    assert util_status(95) == "green"


def test_util_status_amber():
    assert util_status(60) == "amber"
    assert util_status(79) == "amber"


def test_util_status_red():
    assert util_status(59) == "red"
    assert util_status(0) == "red"


def test_ot_status_green():
    assert ot_status(-0.10) == "green"
    assert ot_status(-0.06) == "green"


def test_ot_status_amber():
    assert ot_status(0.0) == "amber"
    assert ot_status(0.14) == "amber"


def test_ot_status_red():
    assert ot_status(0.15) == "red"
    assert ot_status(0.50) == "red"


def test_colors_has_required_keys():
    required = {"bg_base", "bg_card", "bg_elevated", "border",
                "text_primary", "text_secondary", "blue", "green", "amber", "red"}
    assert required.issubset(set(COLORS.keys()))


def test_all_color_values_are_hex():
    for key, val in COLORS.items():
        assert val.startswith("#"), f"{key}: {val!r} is not a hex color"
        assert len(val) == 7, f"{key}: {val!r} is not a 6-digit hex color"


def test_ot_premium_is_float():
    assert isinstance(OT_PREMIUM, float)
    assert OT_PREMIUM > 0
```

- [ ] **Step 4: Run tests — expect FAIL (module not importable yet if running before file saved, or PASS if file exists)**

```bash
cd /Users/dmar/Documents/vscode/projects/fleet-ops-analytics
source .venv/bin/activate
pip install pytest --quiet
pytest tests/test_config.py -v
```

Expected: All tests PASS (config.py is already written in Step 1).

- [ ] **Step 5: Commit**

```bash
git add dashboard/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: add config.py with design tokens, thresholds, dark CSS"
```

---

## Task 2: data.py — Data Layer

**Files:**
- Create: `dashboard/data.py`
- Create: `tests/test_data.py`

- [ ] **Step 1: Write failing tests for `data.py`**

```python
# tests/test_data.py
import pandas as pd
import pytest
from datetime import date
from dashboard.data import FleetData, KPISet, filter_data, compute_kpis


def _make_util(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["utilization_pct"] = df["utilization_rate"] * 100
    df["month_period"] = df["date"].dt.to_period("M")
    df["month_str"] = df["date"].dt.strftime("%b")
    df["month_num"] = df["date"].dt.month
    df["season"] = df["date"].dt.month.apply(
        lambda m: "Summer (Jun-Aug)" if m in (6, 7, 8) else "Rest of Year"
    )
    return df


def _make_ot(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df["day_name"] = df["date"].dt.day_name()
    df["month_period"] = df["date"].dt.to_period("M")
    return df


def _make_fleet_data(util_rows, ot_rows) -> FleetData:
    util = _make_util(util_rows)
    ot = _make_ot(ot_rows)
    maint = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]),
                          "cost": [500.0], "downtime_days": [1],
                          "maintenance_type": ["Oil Change"],
                          "location": ["North"], "month_period": pd.period_range("2024-01", periods=1, freq="M")})
    veh = pd.DataFrame({"vehicle_id": ["V001"], "acquired_date": pd.to_datetime(["2022-01-01"])})
    return FleetData(util=util, ot=ot, maint=maint, veh=veh)


UTIL_ROWS = [
    {"date": "2024-01-15", "vehicle_id": "V001", "location": "North",
     "vehicle_type": "Compact", "utilization_rate": 0.75},
    {"date": "2024-01-15", "vehicle_id": "V002", "location": "South",
     "vehicle_type": "SUV", "utilization_rate": 0.85},
    {"date": "2024-02-15", "vehicle_id": "V001", "location": "North",
     "vehicle_type": "Compact", "utilization_rate": 0.60},
]

OT_ROWS = [
    {"date": "2024-01-15", "employee_id": "E001", "location": "North",
     "role": "Service Agent", "overtime_hours": 2.0},
    {"date": "2024-01-15", "employee_id": "E002", "location": "South",
     "role": "Lot Attendant", "overtime_hours": 3.0},
    {"date": "2024-02-15", "employee_id": "E001", "location": "North",
     "role": "Service Agent", "overtime_hours": 1.0},
]


def test_filter_data_by_location():
    data = _make_fleet_data(UTIL_ROWS, OT_ROWS)
    start = pd.Timestamp("2024-01-01")
    end = pd.Timestamp("2024-12-31")
    filtered = filter_data(data, "North", start, end)
    assert set(filtered.util["location"].unique()) == {"North"}
    assert set(filtered.ot["location"].unique()) == {"North"}


def test_filter_data_all_locations():
    data = _make_fleet_data(UTIL_ROWS, OT_ROWS)
    start = pd.Timestamp("2024-01-01")
    end = pd.Timestamp("2024-12-31")
    filtered = filter_data(data, "All Locations", start, end)
    assert len(filtered.util) == 3


def test_filter_data_by_date():
    data = _make_fleet_data(UTIL_ROWS, OT_ROWS)
    start = pd.Timestamp("2024-02-01")
    end = pd.Timestamp("2024-02-28")
    filtered = filter_data(data, "All Locations", start, end)
    assert len(filtered.util) == 1
    assert len(filtered.ot) == 1


def test_compute_kpis_fleet_count():
    data = _make_fleet_data(UTIL_ROWS, OT_ROWS)
    start, end = pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31")
    filtered = filter_data(data, "All Locations", start, end)
    kpis = compute_kpis(data, filtered)
    assert kpis.fleet_count == 2


def test_compute_kpis_ot_cost():
    data = _make_fleet_data(UTIL_ROWS, OT_ROWS)
    start, end = pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31")
    filtered = filter_data(data, "All Locations", start, end)
    kpis = compute_kpis(data, filtered)
    assert kpis.total_ot_hrs == pytest.approx(6.0)
    assert kpis.ot_cost == pytest.approx(6.0 * 28.0)


def test_compute_kpis_avg_util():
    data = _make_fleet_data(UTIL_ROWS, OT_ROWS)
    start, end = pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-31")
    filtered = filter_data(data, "All Locations", start, end)
    kpis = compute_kpis(data, filtered)
    expected = ((0.75 + 0.85 + 0.60) / 3) * 100
    assert kpis.avg_util == pytest.approx(expected)
```

- [ ] **Step 2: Run tests — expect FAIL (data.py does not exist)**

```bash
pytest tests/test_data.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'dashboard.data'`

- [ ] **Step 3: Create `dashboard/data.py`**

```python
"""Data layer: loading, filtering, and KPI computation."""
from __future__ import annotations
import os
import pandas as pd
import streamlit as st
from dataclasses import dataclass

from dashboard.config import DATA_DIR, DATA_FILES, OT_PREMIUM, util_status, ot_status


@dataclass
class FleetData:
    util: pd.DataFrame
    ot: pd.DataFrame
    maint: pd.DataFrame
    veh: pd.DataFrame


@dataclass
class KPISet:
    fleet_count: int
    avg_util: float
    util_delta: float
    util_status: str
    total_ot_hrs: float
    ot_cost: float
    ot_ratio: float
    ot_status: str
    total_maint: float
    avg_ot_shift: float
    shift_delta: float
    shift_status: str


def data_exists() -> bool:
    return all(os.path.exists(os.path.join(DATA_DIR, f)) for f in DATA_FILES)


@st.cache_data(ttl=3600, show_spinner="Loading fleet data…")
def load_data() -> FleetData:
    util = pd.read_csv(f"{DATA_DIR}/daily_utilization.csv", parse_dates=["date"])
    ot = pd.read_csv(f"{DATA_DIR}/staff_overtime.csv", parse_dates=["date"])
    maint = pd.read_csv(f"{DATA_DIR}/maintenance_records.csv", parse_dates=["date"])
    veh = pd.read_csv(f"{DATA_DIR}/fleet_vehicles.csv", parse_dates=["acquired_date"])

    util = util.copy()
    util["utilization_pct"] = util["utilization_rate"] * 100
    util["month_period"] = util["date"].dt.to_period("M")
    util["month_str"] = util["date"].dt.strftime("%b")
    util["month_num"] = util["date"].dt.month
    util["season"] = util["date"].dt.month.apply(
        lambda m: "Summer (Jun-Aug)" if m in (6, 7, 8) else "Rest of Year"
    )

    ot = ot.copy()
    ot["day_name"] = ot["date"].dt.day_name()
    ot["month_period"] = ot["date"].dt.to_period("M")

    maint = maint.copy()
    maint["month_period"] = maint["date"].dt.to_period("M")

    return FleetData(util=util, ot=ot, maint=maint, veh=veh)


def filter_data(
    data: FleetData,
    location: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> FleetData:
    u = data.util[(data.util["date"] >= start) & (data.util["date"] <= end)]
    o = data.ot[(data.ot["date"] >= start) & (data.ot["date"] <= end)]
    m = data.maint[(data.maint["date"] >= start) & (data.maint["date"] <= end)]

    if location != "All Locations":
        u = u[u["location"] == location]
        o = o[o["location"] == location]
        m = m[m["location"] == location]

    return FleetData(util=u, ot=o, maint=m, veh=data.veh)


def compute_kpis(data: FleetData, filtered: FleetData) -> KPISet:
    avg_util = filtered.util["utilization_pct"].mean()
    baseline_util = data.util["utilization_pct"].mean()

    total_ot_hrs = filtered.ot["overtime_hours"].sum()
    ot_cost = total_ot_hrs * OT_PREMIUM

    months_filtered = max(filtered.ot["month_period"].nunique(), 1)
    months_total = max(data.ot["month_period"].nunique(), 1)
    avg_monthly = ot_cost / months_filtered
    baseline_monthly = (data.ot["overtime_hours"].sum() * OT_PREMIUM) / months_total
    ratio = (avg_monthly - baseline_monthly) / baseline_monthly if baseline_monthly > 0 else 0.0

    avg_ot_shift = filtered.ot["overtime_hours"].mean()
    baseline_ot = data.ot["overtime_hours"].mean()
    shift_delta = avg_ot_shift - baseline_ot

    return KPISet(
        fleet_count=int(filtered.util["vehicle_id"].nunique()),
        avg_util=float(avg_util),
        util_delta=float(avg_util - baseline_util),
        util_status=util_status(avg_util),
        total_ot_hrs=float(total_ot_hrs),
        ot_cost=float(ot_cost),
        ot_ratio=float(ratio),
        ot_status=ot_status(ratio),
        total_maint=float(filtered.maint["cost"].sum()),
        avg_ot_shift=float(avg_ot_shift),
        shift_delta=float(shift_delta),
        shift_status="green" if shift_delta < 0 else ("amber" if shift_delta < 0.5 else "red"),
    )
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_data.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/data.py tests/test_data.py
git commit -m "feat: add data.py with FleetData, KPISet, load/filter/compute"
```

---

## Task 3: charts.py — Dark-Themed Chart Factories

**Files:**
- Create: `dashboard/charts.py`
- Create: `tests/test_charts.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_charts.py
import pandas as pd
import plotly.graph_objects as go
import pytest
from dashboard.charts import (
    apply_chart_style, kpi_html, insight,
    make_util_trend, make_ot_by_location, make_ot_by_role,
    make_ot_daily, make_ot_monthly, make_util_by_type,
    make_util_by_location, make_seasonal_by_type,
    make_util_heatmap, make_maint_cost, make_maint_trend,
    make_fleet_growth,
)
from dashboard.config import COLORS


def _util_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=6, freq="ME")
    rows = []
    for d in dates:
        for loc in ["North", "South"]:
            for vtype in ["Compact", "SUV"]:
                rows.append({
                    "date": d, "location": loc, "vehicle_type": vtype,
                    "vehicle_id": f"{loc[0]}{vtype[0]}1",
                    "utilization_rate": 0.75, "utilization_pct": 75.0,
                    "month_period": d.to_period("M"),
                    "month_str": d.strftime("%b"),
                    "month_num": d.month,
                    "season": "Rest of Year",
                })
    return pd.DataFrame(rows)


def _ot_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=4, freq="ME")
    rows = []
    for d in dates:
        for role in ["Service Agent", "Lot Attendant"]:
            rows.append({
                "date": d, "location": "North", "role": role,
                "employee_id": f"E{role[0]}1",
                "overtime_hours": 2.5,
                "day_name": d.day_name(),
                "month_period": d.to_period("M"),
            })
    return pd.DataFrame(rows)


def _maint_df() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=4, freq="ME")
    rows = []
    for d in dates:
        rows.append({
            "date": d, "location": "North",
            "maintenance_type": "Engine Repair",
            "cost": 1200.0, "downtime_days": 2,
            "month_period": d.to_period("M"),
        })
    return pd.DataFrame(rows)


def _veh_df() -> pd.DataFrame:
    return pd.DataFrame({
        "vehicle_id": ["V001", "V002", "V003"],
        "acquired_date": pd.to_datetime(["2022-01-01", "2022-06-01", "2023-01-01"]),
    })


def test_apply_chart_style_returns_figure():
    fig = go.Figure()
    result = apply_chart_style(fig, "Test", "Subtitle")
    assert isinstance(result, go.Figure)
    assert result.layout.plot_bgcolor == COLORS["bg_card"]


def test_kpi_html_contains_value():
    html = kpi_html("Fleet", "5,240")
    assert "5,240" in html
    assert "Fleet" in html


def test_kpi_html_status_class():
    html = kpi_html("Util", "74%", status="amber")
    assert 'class="kpi-card amber"' in html


def test_make_util_trend_returns_figure():
    df = _util_df()
    fig = make_util_trend(df, pd.Timestamp("2024-06-30"))
    assert isinstance(fig, go.Figure)


def test_make_ot_by_location_returns_figure():
    assert isinstance(make_ot_by_location(_ot_df()), go.Figure)


def test_make_ot_by_role_returns_figure():
    assert isinstance(make_ot_by_role(_ot_df()), go.Figure)


def test_make_ot_daily_returns_figure():
    assert isinstance(make_ot_daily(_ot_df()), go.Figure)


def test_make_ot_monthly_returns_figure():
    assert isinstance(make_ot_monthly(_ot_df(), pd.Timestamp("2024-06-30")), go.Figure)


def test_make_util_by_type_returns_figure():
    assert isinstance(make_util_by_type(_util_df()), go.Figure)


def test_make_util_by_location_returns_figure():
    assert isinstance(make_util_by_location(_util_df()), go.Figure)


def test_make_seasonal_by_type_returns_figure():
    assert isinstance(make_seasonal_by_type(_util_df()), go.Figure)


def test_make_util_heatmap_returns_figure():
    assert isinstance(make_util_heatmap(_util_df()), go.Figure)


def test_make_maint_cost_returns_figure():
    assert isinstance(make_maint_cost(_maint_df()), go.Figure)


def test_make_maint_trend_returns_figure():
    assert isinstance(make_maint_trend(_maint_df(), pd.Timestamp("2024-06-30")), go.Figure)


def test_make_fleet_growth_returns_figure():
    assert isinstance(make_fleet_growth(_veh_df()), go.Figure)
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
pytest tests/test_charts.py -v 2>&1 | head -5
```

Expected: `ModuleNotFoundError: No module named 'dashboard.charts'`

- [ ] **Step 3: Create `dashboard/charts.py`**

```python
"""Plotly chart factories. All functions accept DataFrames and return go.Figure.
No st. calls inside this module."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.config import COLORS, OT_PREMIUM


# ── Theme helpers

def apply_chart_style(
    fig: go.Figure, title: str = "", subtitle: str | None = None
) -> go.Figure:
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += (
            f"<br><span style='font-size:11px;color:{COLORS['text_secondary']};"
            f"font-weight:400'>{subtitle}</span>"
        )
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=14, color=COLORS["text_primary"], family="Inter, sans-serif"),
            x=0, xanchor="left",
        ),
        font=dict(family="Inter, sans-serif", size=12, color=COLORS["text_secondary"]),
        plot_bgcolor=COLORS["bg_card"],
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=65, b=20, l=0, r=10),
        hoverlabel=dict(
            bgcolor=COLORS["bg_card"],
            font_size=12,
            font_family="JetBrains Mono, monospace",
            bordercolor=COLORS["border"],
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor=COLORS["border"],
        tickfont=dict(size=11, color=COLORS["text_secondary"]),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=COLORS["border"],
        gridwidth=1,
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(size=11, color=COLORS["text_secondary"]),
    )
    return fig


def _util_colors(pct_series: pd.Series) -> list[str]:
    """Vectorized status color assignment for utilization percentages."""
    return (
        pd.cut(
            pct_series,
            bins=[0, 60, 80, float("inf")],
            labels=[COLORS["red"], COLORS["amber"], COLORS["green"]],
            right=False,
        )
        .astype(str)
        .tolist()
    )


def kpi_html(
    label: str, value: str, delta_text: str | None = None, status: str = "blue"
) -> str:
    delta = f'<div class="kpi-delta">{delta_text}</div>' if delta_text else ""
    return (
        f'<div class="kpi-card {status}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta}'
        f'</div>'
    )


def insight(text: str) -> str:
    return f'<div class="insight-card">{text}</div>'


# ── Tab 1: Operations Brief

def make_util_trend(df: pd.DataFrame, end: pd.Timestamp) -> go.Figure:
    monthly = (
        df.groupby("month_period")["utilization_pct"]
        .mean()
        .reset_index()
    )
    monthly["date"] = monthly["month_period"].dt.to_timestamp()
    fig = px.area(
        monthly, x="date", y="utilization_pct",
        labels={"utilization_pct": "Utilization %", "date": ""},
        color_discrete_sequence=[COLORS["blue"]],
    )
    fig.add_hline(
        y=80, line_dash="dash", line_color=COLORS["green"], line_width=1.5,
        annotation_text="80% target", annotation_position="top right",
        annotation_font=dict(color=COLORS["green"], size=11),
    )
    fig.add_vrect(
        x0="2023-06-01", x1="2023-09-01",
        fillcolor=COLORS["amber"], opacity=0.07, layer="below", line_width=0,
        annotation_text="Summer '23", annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["amber"]),
    )
    if end >= pd.Timestamp("2024-06-01"):
        fig.add_vrect(
            x0="2024-06-01", x1=min(end, pd.Timestamp("2024-09-01")),
            fillcolor=COLORS["amber"], opacity=0.07, layer="below", line_width=0,
            annotation_text="Summer '24", annotation_position="top left",
            annotation_font=dict(size=10, color=COLORS["amber"]),
        )
    fig.update_traces(fillcolor="rgba(88,166,255,0.07)", line_width=2)
    return apply_chart_style(
        fig, "Monthly Fleet Utilization",
        "Filtered period · Shaded = summer demand peak",
    )


def make_ot_by_location(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby("location")["overtime_hours"]
        .sum()
        .reset_index()
        .rename(columns={"overtime_hours": "ot_hours"})
    )
    agg["ot_cost"] = agg["ot_hours"] * OT_PREMIUM
    agg = agg.sort_values("ot_cost", ascending=True)
    max_cost = agg["ot_cost"].max()
    colors = [
        COLORS["amber"] if c >= max_cost * 0.75 else COLORS["blue"]
        for c in agg["ot_cost"]
    ]
    fig = go.Figure(go.Bar(
        x=agg["ot_cost"], y=agg["location"], orientation="h",
        marker_color=colors,
        text=[f"${v:,.0f}" for v in agg["ot_cost"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text_secondary"]),
    ))
    apply_chart_style(fig, "OT Cost by Location", "Amber = highest-cost location(s)")
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


# ── Tab 2: OT Intelligence

def make_ot_by_role(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby("role")["overtime_hours"]
        .sum()
        .reset_index()
        .sort_values("overtime_hours", ascending=True)
    )
    agg["cost"] = agg["overtime_hours"] * OT_PREMIUM
    sorted_costs = sorted(agg["cost"].tolist())
    role_colors = []
    for c in agg["cost"]:
        if c == sorted_costs[-1]:
            role_colors.append(COLORS["red"])
        elif len(sorted_costs) > 1 and c == sorted_costs[-2]:
            role_colors.append(COLORS["amber"])
        else:
            role_colors.append(COLORS["blue"])
    fig = go.Figure(go.Bar(
        x=agg["cost"], y=agg["role"], orientation="h",
        marker_color=role_colors,
        text=[f"${v:,.0f}" for v in agg["cost"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text_secondary"]),
    ))
    apply_chart_style(fig, "OT Cost by Role", "Red = highest · Amber = second highest")
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def make_ot_daily(df: pd.DataFrame) -> go.Figure:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    agg = df.groupby("day_name")["overtime_hours"].mean().reset_index()
    agg["day_name"] = pd.Categorical(agg["day_name"], categories=day_order, ordered=True)
    agg = agg.sort_values("day_name")
    colors = [
        COLORS["amber"] if d in ("Saturday", "Sunday") else COLORS["blue"]
        for d in agg["day_name"]
    ]
    fig = go.Figure(go.Bar(
        x=agg["day_name"], y=agg["overtime_hours"],
        marker_color=colors,
        text=[f"{v:.2f}" for v in agg["overtime_hours"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text_secondary"]),
    ))
    return apply_chart_style(
        fig, "Avg OT Hours by Day of Week",
        "Amber = weekend shifts · Blue = weekday",
    )


def make_ot_monthly(df: pd.DataFrame, end: pd.Timestamp) -> go.Figure:
    monthly = (
        df.groupby("month_period")["overtime_hours"]
        .sum()
        .reset_index()
    )
    monthly["date"] = monthly["month_period"].dt.to_timestamp()
    monthly["ot_cost"] = monthly["overtime_hours"] * OT_PREMIUM

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=monthly["date"], y=monthly["overtime_hours"],
               name="OT Hours", marker_color=f"rgba(88,166,255,0.35)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=monthly["date"], y=monthly["ot_cost"],
            name="OT Cost ($)", line=dict(color=COLORS["blue"], width=2.5),
            mode="lines+markers", marker=dict(size=5),
        ),
        secondary_y=True,
    )
    fig.add_vrect(
        x0="2023-06-01", x1="2023-09-01",
        fillcolor=COLORS["amber"], opacity=0.07, layer="below", line_width=0,
        annotation_text="Summer peak", annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["amber"]),
    )
    if end >= pd.Timestamp("2024-06-01"):
        fig.add_vrect(
            x0="2024-06-01", x1=min(end, pd.Timestamp("2024-09-01")),
            fillcolor=COLORS["amber"], opacity=0.07, layer="below", line_width=0,
        )
    apply_chart_style(fig, "Monthly Overtime Hours & Cost")
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(t=65, b=60, l=0, r=10),
    )
    fig.update_yaxes(
        title_text="OT Hours", secondary_y=False,
        title_font=dict(size=11, color=COLORS["text_secondary"]),
    )
    fig.update_yaxes(
        title_text="OT Cost ($)", secondary_y=True,
        title_font=dict(size=11, color=COLORS["text_secondary"]),
    )
    return fig


# ── Tab 3: Fleet Efficiency

def make_util_by_type(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby("vehicle_type")["utilization_pct"]
        .mean()
        .reset_index()
        .sort_values("utilization_pct", ascending=False)
    )
    fig = go.Figure(go.Bar(
        x=agg["vehicle_type"], y=agg["utilization_pct"],
        marker_color=_util_colors(agg["utilization_pct"]),
        text=[f"{v:.1f}%" for v in agg["utilization_pct"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text_secondary"]),
    ))
    fig.add_hline(
        y=80, line_dash="dash", line_color=COLORS["blue"], line_width=1.5,
        annotation_text="80% target",
        annotation_font=dict(size=10, color=COLORS["blue"]),
    )
    fig.update_layout(yaxis_range=[0, 110])
    return apply_chart_style(
        fig, "Avg Utilization by Vehicle Type",
        "Green ≥ 80% · Amber 60–80% · Red < 60%",
    )


def make_util_by_location(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby("location")["utilization_pct"]
        .mean()
        .reset_index()
        .sort_values("utilization_pct", ascending=False)
    )
    fig = go.Figure(go.Bar(
        x=agg["location"], y=agg["utilization_pct"],
        marker_color=_util_colors(agg["utilization_pct"]),
        text=[f"{v:.1f}%" for v in agg["utilization_pct"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text_secondary"]),
    ))
    fig.add_hline(
        y=80, line_dash="dash", line_color=COLORS["blue"], line_width=1.5,
        annotation_text="80% target",
        annotation_font=dict(size=10, color=COLORS["blue"]),
    )
    fig.update_layout(yaxis_range=[0, 110])
    return apply_chart_style(
        fig, "Avg Utilization by Location",
        "Green ≥ 80% · Amber 60–80% · Red < 60%",
    )


def make_seasonal_by_type(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby(["month_num", "month_str", "vehicle_type"])["utilization_pct"]
        .mean()
        .reset_index()
        .sort_values("month_num")
    )
    palette = [COLORS["blue"], COLORS["green"], COLORS["amber"], COLORS["red"], "#7C3AED"]
    fig = px.line(
        agg, x="month_str", y="utilization_pct", color="vehicle_type",
        labels={"utilization_pct": "Utilization %", "month_str": "", "vehicle_type": "Type"},
        markers=True,
        color_discrete_sequence=palette,
    )
    fig.add_hline(
        y=80, line_dash="dot", line_color=COLORS["text_secondary"], line_width=1,
        annotation_text="80% target", annotation_position="bottom right",
        annotation_font=dict(size=10, color=COLORS["text_secondary"]),
    )
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return apply_chart_style(
        fig, "Seasonal Demand by Vehicle Type",
        "Summer: Compact & Mid-Size spike · Winter: SUV & Truck rise",
    )


def make_util_heatmap(df: pd.DataFrame) -> go.Figure:
    heat = (
        df.groupby([df["month_period"].astype(str), "location"])["utilization_pct"]
        .mean()
        .unstack("location")
    )
    fig = px.imshow(
        heat.T,
        color_continuous_scale="RdYlGn",
        zmin=50, zmax=100,
        aspect="auto",
        labels=dict(x="Month", y="Location", color="Util %"),
    )
    apply_chart_style(
        fig,
        "Utilization Heatmap — Month × Location",
        "Red = low utilization · Green = high · Scale anchored 50–100%",
    )
    fig.update_layout(
        coloraxis_colorbar=dict(title="Util %", tickfont=dict(size=11)),
    )
    return fig


# ── Tab 4: Maintenance Radar

def make_maint_cost(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby("maintenance_type")["cost"]
        .sum()
        .reset_index()
        .sort_values("cost", ascending=True)
    )
    max_cost = agg["cost"].max()
    colors = [COLORS["red"] if c == max_cost else COLORS["blue"] for c in agg["cost"]]
    fig = go.Figure(go.Bar(
        x=agg["cost"], y=agg["maintenance_type"], orientation="h",
        marker_color=colors,
        text=[f"${v:,.0f}" for v in agg["cost"]],
        textposition="outside",
        textfont=dict(size=11, color=COLORS["text_secondary"]),
    ))
    apply_chart_style(fig, "Maintenance Cost by Type", "Red = highest spend category")
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(showgrid=False)
    return fig


def make_maint_trend(df: pd.DataFrame, end: pd.Timestamp) -> go.Figure:
    monthly = (
        df.groupby("month_period")["cost"]
        .sum()
        .reset_index()
    )
    monthly["date"] = monthly["month_period"].dt.to_timestamp()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["date"], y=monthly["cost"],
        line=dict(color=COLORS["blue"], width=2.5),
        mode="lines+markers",
        marker=dict(size=5, color=COLORS["blue"]),
        fill="tozeroy",
        fillcolor="rgba(88,166,255,0.06)",
        name="Monthly Spend",
    ))
    fig.add_vrect(
        x0="2023-06-01", x1="2023-09-01",
        fillcolor=COLORS["amber"], opacity=0.07, layer="below", line_width=0,
        annotation_text="Summer", annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["amber"]),
    )
    fig.add_vrect(
        x0="2023-11-01", x1="2024-03-01",
        fillcolor=COLORS["blue"], opacity=0.05, layer="below", line_width=0,
        annotation_text="Winter", annotation_position="top left",
        annotation_font=dict(size=10, color=COLORS["blue"]),
    )
    fig.update_layout(showlegend=False)
    return apply_chart_style(
        fig, "Monthly Maintenance Spend ($)",
        "Amber = summer · Blue = winter demand seasons",
    )


def make_fleet_growth(veh: pd.DataFrame) -> go.Figure:
    growth = (
        veh.groupby(veh["acquired_date"].dt.to_period("M"))
        .size()
        .reset_index(name="added")
    )
    growth["acquired_date"] = growth["acquired_date"].dt.to_timestamp()
    growth["cumulative"] = growth["added"].cumsum()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=growth["acquired_date"], y=growth["added"],
               name="Added This Month", marker_color=f"rgba(88,166,255,0.35)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=growth["acquired_date"], y=growth["cumulative"],
            name="Total Fleet Size", line=dict(color=COLORS["blue"], width=2.5),
            mode="lines+markers", marker=dict(size=4),
        ),
        secondary_y=True,
    )
    apply_chart_style(fig, "Fleet Growth Trajectory", "Monthly acquisitions vs cumulative fleet size")
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(t=65, b=60, l=0, r=10),
    )
    fig.update_yaxes(
        title_text="Vehicles Added", secondary_y=False,
        title_font=dict(size=11, color=COLORS["text_secondary"]),
    )
    fig.update_yaxes(
        title_text="Cumulative Fleet", secondary_y=True,
        title_font=dict(size=11, color=COLORS["text_secondary"]),
    )
    return fig
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
pytest tests/test_charts.py -v
```

Expected: All 15 tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS across `test_config.py`, `test_data.py`, `test_charts.py`.

- [ ] **Step 6: Commit**

```bash
git add dashboard/charts.py tests/test_charts.py
git commit -m "feat: add charts.py with dark theme and 12 chart factories"
```

---

## Task 4: Rewrite app.py

**Files:**
- Modify: `dashboard/app.py` (full rewrite)

- [ ] **Step 1: Replace `dashboard/app.py` with the following**

```python
"""Fleet Operations Analytics Dashboard — layout and routing only."""
import sys
import subprocess
import datetime

import pandas as pd
import streamlit as st

from dashboard.config import DARK_THEME_CSS, DATA_DIR, DATA_FILES
from dashboard.data import data_exists, load_data, filter_data, compute_kpis
from dashboard.charts import (
    kpi_html, insight,
    make_util_trend, make_ot_by_location,
    make_ot_by_role, make_ot_daily, make_ot_monthly,
    make_util_by_type, make_util_by_location,
    make_seasonal_by_type, make_util_heatmap,
    make_maint_cost, make_maint_trend, make_fleet_growth,
)

st.set_page_config(
    page_title="Fleet Ops Analytics",
    page_icon="⚙︎",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


# ── Data bootstrap
GENERATE_SCRIPT = str(
    (lambda p: __import__("pathlib").Path(p).parent.parent / "data" / "generate_data.py")(__file__)
)


def _run_generator() -> None:
    with st.spinner("Generating fleet data… this may take a few minutes for 5,200 vehicles."):
        result = subprocess.run(
            [sys.executable, GENERATE_SCRIPT], capture_output=True, text=True
        )
    if result.returncode != 0:
        st.error(f"Generation failed:\n```\n{result.stderr}\n```")
        st.stop()
    st.cache_data.clear()
    st.rerun()


# ── Sidebar
st.sidebar.title("Fleet Ops")
st.sidebar.divider()
st.sidebar.subheader("Data")

if not data_exists():
    st.sidebar.warning("No data files found.")
    st.sidebar.caption("Generate the dataset to get started.")
    if st.sidebar.button("Generate Data", type="primary", use_container_width=True):
        _run_generator()
    st.info("No fleet data found. Use the **Generate Data** button in the sidebar to create it.")
    st.stop()
else:
    import os
    newest = max(
        os.path.getmtime(os.path.join(DATA_DIR, f)) for f in DATA_FILES
    )
    last_gen = datetime.datetime.fromtimestamp(newest).strftime("%b %d, %Y %H:%M")
    st.sidebar.caption(f"Dataset: last refreshed {last_gen}")
    with st.sidebar.expander("Regenerate data"):
        st.caption("Replaces all CSV files with a fresh synthetic dataset.")
        if st.button("Regenerate Now", type="secondary", use_container_width=True):
            _run_generator()

st.sidebar.divider()

# ── Load + filter
data = load_data()
locations = ["All Locations"] + sorted(data.util["location"].unique().tolist())
selected_loc = st.sidebar.selectbox("Location", locations)
date_range = st.sidebar.date_input(
    "Date Range",
    value=(data.util["date"].min().date(), data.util["date"].max().date()),
    min_value=data.util["date"].min().date(),
    max_value=data.util["date"].max().date(),
)

if len(date_range) < 2:
    st.warning("Please select a complete date range.")
    st.stop()

start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
filtered = filter_data(data, selected_loc, start, end)

if filtered.util.empty:
    st.warning("No data for the selected filters. Adjust the date range or location.")
    st.stop()

kpis = compute_kpis(data, filtered)

# ── Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Operations Brief", "OT Intelligence", "Fleet Efficiency", "Maintenance Radar",
])


# ━━ TAB 1 — OPERATIONS BRIEF ━━
with tab1:
    st.header("Operations Brief")
    st.caption("Top-line performance across the filtered period and location.")

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_html("Fleet Size", f"{kpis.fleet_count:,}", status="blue"), unsafe_allow_html=True)
    k2.markdown(kpi_html(
        "Avg Utilization", f"{kpis.avg_util:.1f}%",
        delta_text=f"{kpis.util_delta:+.1f}pp vs overall",
        status=kpis.util_status,
    ), unsafe_allow_html=True)
    k3.markdown(kpi_html(
        "Total OT Cost", f"${kpis.ot_cost:,.0f}",
        delta_text=f"{'↑' if kpis.ot_ratio > 0 else '↓'} {abs(kpis.ot_ratio)*100:.0f}% vs baseline",
        status=kpis.ot_status,
    ), unsafe_allow_html=True)
    k4.markdown(kpi_html("Maintenance Spend", f"${kpis.total_maint:,.0f}", status="blue"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.plotly_chart(make_util_trend(filtered.util, end), use_container_width=True)
    with col_b:
        st.plotly_chart(make_ot_by_location(filtered.ot), use_container_width=True)

    st.markdown(insight(
        "<strong>Summer demand drives the bulk of overtime spend.</strong> June–August typically accounts "
        "for ~38% of annual OT cost as staff vacations and peak rental demand converge. The highest-cost "
        "location is the primary lever — staggered scheduling or cross-location shift coverage can reduce "
        "exposure without adding headcount."
    ), unsafe_allow_html=True)


# ━━ TAB 2 — OT INTELLIGENCE ━━
with tab2:
    st.header("OT Intelligence")
    st.caption("Root-cause breakdown of overtime cost by role, schedule pattern, and time.")

    m1, m2, m3 = st.columns(3)
    m1.markdown(kpi_html("Total OT Hours", f"{kpis.total_ot_hrs:,.0f} hrs", status="blue"), unsafe_allow_html=True)
    m2.markdown(kpi_html("Total OT Cost", f"${kpis.ot_cost:,.0f}", status=kpis.ot_status), unsafe_allow_html=True)
    m3.markdown(kpi_html(
        "Avg OT / Shift", f"{kpis.avg_ot_shift:.2f} hrs",
        delta_text=f"{kpis.shift_delta:+.2f} hrs vs baseline",
        status=kpis.shift_status,
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 3])
    with col1:
        st.plotly_chart(make_ot_by_role(filtered.ot), use_container_width=True)
    with col2:
        st.plotly_chart(make_ot_daily(filtered.ot), use_container_width=True)

    st.plotly_chart(make_ot_monthly(filtered.ot, end), use_container_width=True)
    st.markdown(insight(
        "<strong>Service Agents and Lot Attendants drive the majority of OT spend</strong> — collectively "
        "accounting for ~60% of total overtime cost. Weekend shifts surge June–August as vacation coverage "
        "compounds peak rental demand. Targeted scheduling adjustments in Q2 could yield meaningful cost "
        "reduction without impacting service levels."
    ), unsafe_allow_html=True)


# ━━ TAB 3 — FLEET EFFICIENCY ━━
with tab3:
    st.header("Fleet Efficiency")
    st.caption("Vehicle utilization rates, seasonal demand shifts, and idle asset identification.")

    per_veh = filtered.util.groupby("vehicle_id")["utilization_pct"].mean()
    u1, u2, u3 = st.columns(3)
    u1.markdown(kpi_html("Avg Utilization", f"{kpis.avg_util:.1f}%", status="blue"), unsafe_allow_html=True)
    u2.markdown(kpi_html(
        "Vehicles > 90% Util", f"{(per_veh >= 90).sum():,}",
        delta_text="high-demand assets", status="blue",
    ), unsafe_allow_html=True)
    u3.markdown(kpi_html(
        "Vehicles < 50% Util", f"{(per_veh < 50).sum():,}",
        delta_text="reallocation candidates", status="amber",
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(make_util_by_type(filtered.util), use_container_width=True)
    with col2:
        st.plotly_chart(make_util_by_location(filtered.util), use_container_width=True)

    st.plotly_chart(make_seasonal_by_type(filtered.util), use_container_width=True)
    st.plotly_chart(make_util_heatmap(filtered.util), use_container_width=True)
    st.markdown(insight(
        "<strong>Seasonal demand inverts across vehicle segments.</strong> Compact and Mid-Size vehicles "
        "spike in summer; SUV and Truck demand peaks in winter. <strong>~8% of the fleet sits below 50% "
        "utilization</strong> — prime reallocation candidates. Moving underutilized assets from low-demand "
        "to high-demand locations could improve overall utilization by 3–5pp without new acquisitions."
    ), unsafe_allow_html=True)


# ━━ TAB 4 — MAINTENANCE RADAR ━━
with tab4:
    st.header("Maintenance Radar")
    st.caption("Cost breakdown, spend trends, and fleet capacity planning.")

    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_html("Maintenance Spend", f"${kpis.total_maint:,.0f}", status="blue"), unsafe_allow_html=True)
    c2.markdown(kpi_html("Maintenance Events", f"{len(filtered.maint):,}", status="blue"), unsafe_allow_html=True)
    c3.markdown(kpi_html(
        "Total Downtime Days", f"{filtered.maint['downtime_days'].sum():,.0f}",
        delta_text="days of fleet unavailability", status="amber",
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 3])
    with col1:
        st.plotly_chart(make_maint_cost(filtered.maint), use_container_width=True)
    with col2:
        st.plotly_chart(make_maint_trend(filtered.maint, end), use_container_width=True)

    st.plotly_chart(make_fleet_growth(data.veh), use_container_width=True)
    st.markdown(insight(
        "<strong>Engine repairs account for 40%+ of total maintenance spend</strong> — disproportionate "
        "to their frequency, indicating high per-event cost. Winter months (Nov–Feb) correlate with elevated "
        "brake and engine repair events. A predictive maintenance trigger based on mileage and vehicle age "
        "for assets entering their 4th year could shift spend from reactive to scheduled."
    ), unsafe_allow_html=True)


# ── Footer
st.markdown(
    "<p style='text-align:center;color:#8B949E;font-size:12px;"
    "margin-top:40px;padding-top:16px;border-top:1px solid #21262D'>"
    "Built by Damarius McNair · "
    "<a href='https://github.com/DCodeBase-X' style='color:#58A6FF'>GitHub</a>"
    "</p>",
    unsafe_allow_html=True,
)
```

- [ ] **Step 2: Verify the app runs without errors**

```bash
cd /Users/dmar/Documents/vscode/projects/fleet-ops-analytics
source .venv/bin/activate
streamlit run dashboard/app.py --server.headless true &
sleep 4
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501
```

Expected: `200`. Kill the background process after verifying.

- [ ] **Step 3: Run full test suite to confirm nothing broken**

```bash
pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add dashboard/app.py
git commit -m "feat: rewrite app.py — modular imports, dark theme, <200 lines"
```

---

## Task 5: Notebook — DuckDB Setup + Section 1 SQL

**Files:**
- Modify: `requirements.txt`
- Modify: `notebooks/fleet_analysis.ipynb` (cells: imports, data load, Section 1 quality check)

- [ ] **Step 1: Add duckdb to `requirements.txt`**

Add these two lines to `requirements.txt`:

```
duckdb>=1.0.0
pytest>=7.0
```

Install:

```bash
source .venv/bin/activate && pip install duckdb>=1.0.0 pytest>=7.0
```

- [ ] **Step 2: Replace the imports cell (`cell-imports`) content**

New content for the imports cell:

```python
import os
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams.update({'figure.dpi': 120, 'figure.figsize': (12, 5)})

os.makedirs('../visuals', exist_ok=True)

# ── DuckDB connection — queries CSV files directly, no full load into memory
con = duckdb.connect()
con.execute("CREATE VIEW util  AS SELECT * FROM read_csv_auto('../data/daily_utilization.csv')")
con.execute("CREATE VIEW ot    AS SELECT * FROM read_csv_auto('../data/staff_overtime.csv')")
con.execute("CREATE VIEW maint AS SELECT * FROM read_csv_auto('../data/maintenance_records.csv')")
con.execute("CREATE VIEW veh   AS SELECT * FROM read_csv_auto('../data/fleet_vehicles.csv')")

OT_PREMIUM   = 28.0
MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# ── Dataset summary
summary = con.execute("""
    SELECT 'util'  AS view_name, COUNT(*) AS row_count FROM util  UNION ALL
    SELECT 'ot',                  COUNT(*)               FROM ot   UNION ALL
    SELECT 'maint',               COUNT(*)               FROM maint UNION ALL
    SELECT 'veh',                 COUNT(*)               FROM veh
""").df()

date_range = con.execute("""
    SELECT MIN(date)::DATE AS start_date, MAX(date)::DATE AS end_date FROM util
""").df()

for _, row in summary.iterrows():
    print(f"{row['view_name']:<6}: {row['row_count']:>10,} rows")
print()
print(f"Date range: {date_range['start_date'].iloc[0]} → {date_range['end_date'].iloc[0]}")
```

- [ ] **Step 3: Replace the data quality cell (`cell-quality`) content**

```python
# ── Null audit — set-based, one query per view
null_audit = con.execute("""
    SELECT 'util' AS tbl, COUNT(*) AS rows,
           COUNT(*) - COUNT(date)             +
           COUNT(*) - COUNT(vehicle_id)       +
           COUNT(*) - COUNT(location)         +
           COUNT(*) - COUNT(vehicle_type)     +
           COUNT(*) - COUNT(utilization_rate) AS total_nulls
    FROM util
    UNION ALL
    SELECT 'ot', COUNT(*),
           COUNT(*) - COUNT(date)           +
           COUNT(*) - COUNT(employee_id)    +
           COUNT(*) - COUNT(location)       +
           COUNT(*) - COUNT(role)           +
           COUNT(*) - COUNT(overtime_hours) AS total_nulls
    FROM ot
    UNION ALL
    SELECT 'maint', COUNT(*),
           COUNT(*) - COUNT(date)              +
           COUNT(*) - COUNT(maintenance_type)  +
           COUNT(*) - COUNT(cost)              +
           COUNT(*) - COUNT(downtime_days)     AS total_nulls
    FROM maint
    UNION ALL
    SELECT 'veh', COUNT(*),
           COUNT(*) - COUNT(vehicle_id)     +
           COUNT(*) - COUNT(acquired_date)  AS total_nulls
    FROM veh
""").df()

print('=== Null Audit ===')
for _, row in null_audit.iterrows():
    print(f"  {row['tbl']:<6}: {row['total_nulls']} nulls | {row['rows']:>9,} rows")

# ── Duplicate checks — grain validation
dupe_util = con.execute("""
    SELECT COUNT(*) AS dupes FROM (
        SELECT date, vehicle_id, COUNT(*) AS cnt
        FROM util GROUP BY date, vehicle_id HAVING cnt > 1
    )
""").fetchone()[0]

dupe_ot = con.execute("""
    SELECT COUNT(*) AS dupes FROM (
        SELECT date, employee_id, COUNT(*) AS cnt
        FROM ot GROUP BY date, employee_id HAVING cnt > 1
    )
""").fetchone()[0]

dupe_veh = con.execute("""
    SELECT COUNT(*) - COUNT(DISTINCT vehicle_id) AS dupes FROM veh
""").fetchone()[0]

print()
print('=== Duplicate Checks ===')
print(f'  Util  (date x vehicle_id)  : {dupe_util} dupes')
print(f'  OT    (date x employee_id) : {dupe_ot} dupes')
print(f'  Vehicles (vehicle_id)      : {dupe_veh} dupes')

# ── Value ranges
ranges = con.execute("""
    SELECT
        MIN(utilization_rate) AS util_min,
        MAX(utilization_rate) AS util_max,
        (SELECT MIN(overtime_hours) FROM ot) AS ot_min,
        (SELECT MAX(overtime_hours) FROM ot) AS ot_max,
        (SELECT MIN(cost) FROM maint) AS maint_min,
        (SELECT MAX(cost) FROM maint) AS maint_max,
        (SELECT MIN(downtime_days) FROM maint) AS dt_min,
        (SELECT MAX(downtime_days) FROM maint) AS dt_max
    FROM util
""").df()

print()
print('=== Value Ranges ===')
print(f"  Utilization rate  : {ranges['util_min'].iloc[0]:.3f} – {ranges['util_max'].iloc[0]:.3f}")
print(f"  OT hours / shift  : {ranges['ot_min'].iloc[0]:.2f} – {ranges['ot_max'].iloc[0]:.2f}")
print(f"  Maintenance cost  : ${ranges['maint_min'].iloc[0]:,.0f} – ${ranges['maint_max'].iloc[0]:,.0f}")
print(f"  Downtime days     : {ranges['dt_min'].iloc[0]} – {ranges['dt_max'].iloc[0]}")
```

- [ ] **Step 4: Replace the distribution cell (`cell-dist`) content**

```python
# Per-vehicle utilization distribution
dist = con.execute("""
    SELECT
        vehicle_id,
        AVG(utilization_rate) AS avg_util
    FROM util
    GROUP BY vehicle_id
""").df()

fleet_mean = dist['avg_util'].mean()
under_50   = (dist['avg_util'] < 0.50).sum()
over_90    = (dist['avg_util'] >= 0.90).sum()
total      = len(dist)

print(f'Fleet-wide mean utilization       : {fleet_mean*100:.1f}%')
print(f'Vehicles >= 90% avg utilization   : {over_90:,}  ({over_90/total*100:.1f}% of fleet)')
print(f'Vehicles <  50% avg utilization   : {under_50:,}  ({under_50/total*100:.1f}% of fleet)')

fig, ax = plt.subplots(figsize=(10, 4))
dist['avg_util'].mul(100).hist(bins=40, ax=ax, color='#93C5FD', edgecolor='white')
ax.axvline(50,              color='#DC2626', linestyle='--', linewidth=1.5, label='50% floor')
ax.axvline(80,              color='#059669', linestyle='--', linewidth=1.5, label='80% target')
ax.axvline(fleet_mean*100,  color='#1D4ED8', linewidth=2,
           label=f'Fleet avg ({fleet_mean*100:.1f}%)')
ax.set_title('Distribution of Per-Vehicle Mean Utilization')
ax.set_xlabel('Mean Utilization (%)')
ax.set_ylabel('Vehicle Count')
ax.legend()
plt.tight_layout()
plt.show()
```

- [ ] **Step 5: Run the notebook through Section 1 to verify all cells execute cleanly**

Open `notebooks/fleet_analysis.ipynb` in Jupyter, restart kernel, run cells 1–4. Verify:
- Summary table prints row counts for all 4 views
- Null audit shows 0 nulls
- Duplicate checks show 0 dupes
- Distribution histogram renders

- [ ] **Step 6: Commit**

```bash
git add requirements.txt notebooks/fleet_analysis.ipynb
git commit -m "feat: DuckDB setup and Section 1 SQL (data quality)"
```

---

## Task 6: Notebook — Sections 2–3 SQL (Utilization + OT)

**Files:**
- Modify: `notebooks/fleet_analysis.ipynb`

- [ ] **Step 1: Replace `cell-monthly-trend` content**

```python
monthly = con.execute("""
    SELECT
        DATE_TRUNC('month', date)::DATE AS month,
        AVG(utilization_rate) * 100 AS util_pct
    FROM util
    GROUP BY DATE_TRUNC('month', date)
    ORDER BY month
""").df()
monthly['month'] = pd.to_datetime(monthly['month'])

fig, ax = plt.subplots()
ax.plot(monthly['month'], monthly['util_pct'], marker='o', linewidth=2, color='#1D4ED8')
ax.axhline(80, color='#059669', linestyle='--', linewidth=1.5, label='Target 80%')
ax.set_title('Monthly Fleet Utilization (%)')
ax.set_ylabel('Utilization %')
ax.set_xlabel('')
ax.legend()
plt.tight_layout()
plt.savefig('../visuals/utilization_trend.png', bbox_inches='tight')
plt.show()
```

- [ ] **Step 2: Replace `cell-seasonal-split` content**

```python
seasonal = con.execute("""
    WITH flagged AS (
        SELECT
            utilization_rate,
            CASE WHEN MONTH(date) IN (6, 7, 8) THEN 'Summer (Jun-Aug)' ELSE 'Rest of Year' END AS season,
            DATE_TRUNC('month', date)::DATE AS month
        FROM util
    ),
    by_season AS (
        SELECT season, AVG(utilization_rate) * 100 AS avg_util
        FROM flagged GROUP BY season
    ),
    monthly_agg AS (
        SELECT month, AVG(utilization_rate) * 100 AS util_pct
        FROM flagged GROUP BY month
    )
    SELECT
        (SELECT avg_util FROM by_season WHERE season = 'Summer (Jun-Aug)')    AS summer_avg,
        (SELECT avg_util FROM by_season WHERE season = 'Rest of Year')        AS rest_avg,
        (SELECT COUNT(*) FROM monthly_agg WHERE util_pct >= 80)               AS months_above,
        (SELECT COUNT(*) FROM monthly_agg WHERE util_pct < 80)                AS months_below,
        (SELECT month FROM monthly_agg ORDER BY util_pct DESC LIMIT 1)        AS peak_month,
        (SELECT util_pct FROM monthly_agg ORDER BY util_pct DESC LIMIT 1)     AS peak_pct,
        (SELECT month FROM monthly_agg ORDER BY util_pct ASC LIMIT 1)         AS trough_month,
        (SELECT util_pct FROM monthly_agg ORDER BY util_pct ASC LIMIT 1)      AS trough_pct
""").df()

summer_avg = seasonal['summer_avg'].iloc[0]
rest_avg   = seasonal['rest_avg'].iloc[0]
summer_lift = summer_avg - rest_avg

print('=== Seasonal Utilization Split ===')
print(f'  Summer (Jun-Aug)     : {summer_avg:.1f}%')
print(f'  Rest of Year         : {rest_avg:.1f}%')
print(f'  Summer lift          : +{summer_lift:.1f}pp')
print()
print(f"Months at/above 80%  : {seasonal['months_above'].iloc[0]} of {int(seasonal['months_above'].iloc[0]) + int(seasonal['months_below'].iloc[0])}")
print(f"Peak month           : {seasonal['peak_month'].iloc[0]} ({seasonal['peak_pct'].iloc[0]:.1f}%)")
print(f"Trough month         : {seasonal['trough_month'].iloc[0]} ({seasonal['trough_pct'].iloc[0]:.1f}%)")
```

- [ ] **Step 3: Replace `cell-heatmap` content**

```python
heatmap_data = con.execute("""
    SELECT
        location,
        vehicle_type,
        AVG(utilization_rate) * 100 AS util_pct
    FROM util
    GROUP BY location, vehicle_type
""").df()

pivot = heatmap_data.pivot(index='location', columns='vehicle_type', values='util_pct')

fig, ax = plt.subplots(figsize=(12, 5))
sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', vmin=55, vmax=95,
            ax=ax, linewidths=0.5, cbar_kws={'label': 'Utilization %'})
ax.set_title('Fleet Utilization (%) — Location x Vehicle Type')
plt.tight_layout()
plt.savefig('../visuals/utilization_heatmap.png', bbox_inches='tight')
plt.show()

# ── Bottom and top combinations
extremes = con.execute("""
    SELECT location, vehicle_type, ROUND(AVG(utilization_rate) * 100, 1) AS util_pct
    FROM util
    GROUP BY location, vehicle_type
    ORDER BY util_pct
""").df()

print('Bottom 3 location × vehicle type combinations:')
print(extremes.head(3).to_string(index=False))
print()
print('Top 3 location × vehicle type combinations:')
print(extremes.tail(3).to_string(index=False))
```

- [ ] **Step 4: Replace `cell-seasonal-type` content**

```python
seasonal_type = con.execute("""
    SELECT
        MONTH(date) AS month_num,
        vehicle_type,
        AVG(utilization_rate) * 100 AS util_pct
    FROM util
    GROUP BY MONTH(date), vehicle_type
    ORDER BY month_num, vehicle_type
""").df()

monthly_type = seasonal_type.pivot(index='month_num', columns='vehicle_type', values='util_pct')

fig, ax = plt.subplots(figsize=(13, 5))
type_colors = ['#1D4ED8', '#059669', '#D97706', '#DC2626', '#7C3AED']
for vtype, color in zip(monthly_type.columns, type_colors):
    ax.plot(range(1, 13), monthly_type[vtype], marker='o', label=vtype, color=color, linewidth=2)
ax.set_xticks(range(1, 13))
ax.set_xticklabels(MONTH_LABELS)
ax.axhline(80, color='#94A3B8', linestyle=':', linewidth=1, label='80% target')
ax.axvspan(5.5, 8.5, alpha=0.08, color='orange', label='Summer peak')
ax.axvspan(10.5, 12.5, alpha=0.08, color='steelblue', label='Winter events')
ax.set_title('Seasonal Utilization by Vehicle Type (%)')
ax.set_ylabel('Utilization %')
ax.legend(loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.22))
plt.tight_layout()
plt.savefig('../visuals/seasonal_by_type.png', bbox_inches='tight')
plt.show()
```

- [ ] **Step 5: Replace `cell-seasonal-delta` content**

```python
swing = con.execute("""
    WITH monthly AS (
        SELECT
            MONTH(date) AS month_num,
            vehicle_type,
            AVG(utilization_rate) * 100 AS util_pct
        FROM util
        GROUP BY MONTH(date), vehicle_type
    )
    SELECT
        vehicle_type,
        MONTH_LABELS[peak_month]   AS peak_month,
        peak_pct,
        MONTH_LABELS[trough_month] AS trough_month,
        trough_pct,
        peak_pct - trough_pct      AS swing_pp
    FROM (
        SELECT
            vehicle_type,
            MAX(util_pct)                                                AS peak_pct,
            MIN(util_pct)                                                AS trough_pct,
            ARGMAX(month_num, util_pct)                                  AS peak_month,
            ARGMIN(month_num, util_pct)                                  AS trough_month
        FROM monthly
        GROUP BY vehicle_type
    )
    ORDER BY swing_pp DESC
""".replace(
    'MONTH_LABELS',
    "['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']"
)).df()

print(f"{'Type':<12} {'Peak':<8} {'Peak %':<10} {'Trough':<10} {'Trough %':<11} {'Swing'}")
print('-' * 60)
for _, row in swing.iterrows():
    print(
        f"{row['vehicle_type']:<12} {row['peak_month']:<8} {row['peak_pct']:<10.1f}"
        f" {row['trough_month']:<10} {row['trough_pct']:<11.1f} {row['swing_pp']:.1f}pp"
    )
```

- [ ] **Step 6: Replace `cell-ot-summary` content**

```python
ot_summary = con.execute(f"""
    WITH totals AS (
        SELECT
            SUM(overtime_hours)                                           AS total_hrs,
            SUM(CASE WHEN MONTH(date) IN (6,7,8) THEN overtime_hours END) AS summer_hrs
        FROM ot
    ),
    by_role AS (
        SELECT
            role,
            SUM(overtime_hours) * {OT_PREMIUM} AS role_cost,
            SUM(overtime_hours) * {OT_PREMIUM} / (SELECT SUM(overtime_hours) * {OT_PREMIUM} FROM ot) AS role_pct,
            RANK() OVER (ORDER BY SUM(overtime_hours) DESC) AS rnk
        FROM ot
        GROUP BY role
    )
    SELECT
        t.total_hrs,
        t.total_hrs * {OT_PREMIUM}                               AS total_cost,
        t.summer_hrs * {OT_PREMIUM}                              AS summer_cost,
        t.summer_hrs * {OT_PREMIUM} / (t.total_hrs * {OT_PREMIUM}) * 100 AS summer_pct,
        (SELECT SUM(role_pct) FROM by_role WHERE rnk <= 2) * 100 AS top2_pct
    FROM totals t
""").df()

total_hrs    = ot_summary['total_hrs'].iloc[0]
total_cost   = ot_summary['total_cost'].iloc[0]
summer_cost  = ot_summary['summer_cost'].iloc[0]
summer_pct   = ot_summary['summer_pct'].iloc[0]
top2_pct     = ot_summary['top2_pct'].iloc[0]

print(f'Total OT hours : {total_hrs:,.0f}')
print(f'Total OT cost  : ${total_cost:,.0f}')
print()
print(f'Summer (Jun-Aug) share of total OT cost : {summer_pct:.1f}%')
print(f'  (calendar weight of Jun-Aug = 25.0%)')
print(f'  Overindex factor: {summer_pct / 25.0:.1f}x')
print()

role_breakdown = con.execute(f"""
    SELECT role, SUM(overtime_hours) * {OT_PREMIUM} AS cost,
           SUM(overtime_hours) * {OT_PREMIUM} / (SELECT SUM(overtime_hours) * {OT_PREMIUM} FROM ot) * 100 AS pct,
           RANK() OVER (ORDER BY SUM(overtime_hours) DESC) AS rnk
    FROM ot GROUP BY role ORDER BY cost DESC
""").df()

print('OT cost by role:')
for _, row in role_breakdown.iterrows():
    print(f"  {{row['role']:<24}}: ${{row['cost']:>10,.0f}}  ({{row['pct']:.1f}}%)")
print()
print(f'Top 2 roles combined: {{top2_pct:.1f}}% of total OT cost')
```

- [ ] **Step 7: Replace `cell-ot-monthly` content**

```python
monthly_ot = con.execute("""
    SELECT
        DATE_TRUNC('month', date)::DATE AS month,
        SUM(overtime_hours) AS total_hours,
        MONTH(date) IN (6, 7, 8) AS is_summer
    FROM ot
    GROUP BY DATE_TRUNC('month', date), MONTH(date) IN (6, 7, 8)
    ORDER BY month
""").df()
monthly_ot['month'] = pd.to_datetime(monthly_ot['month'])

bar_colors = ['#D97706' if s else '#BFDBFE' for s in monthly_ot['is_summer']]

fig, ax = plt.subplots()
ax.bar(monthly_ot['month'], monthly_ot['total_hours'], color=bar_colors, edgecolor='white', width=20)
ax.set_title('Monthly Overtime Hours  (Amber = Summer)')
ax.set_ylabel('Overtime Hours')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax.tick_params(axis='x', rotation=45)
ax.legend(handles=[
    Patch(color='#D97706', label='Summer (Jun-Aug)'),
    Patch(color='#BFDBFE', label='Non-summer')
])
plt.tight_layout()
plt.savefig('../visuals/monthly_overtime.png', bbox_inches='tight')
plt.show()

peak_trough = con.execute("""
    WITH monthly AS (
        SELECT DATE_TRUNC('month', date)::DATE AS month, SUM(overtime_hours) AS hrs
        FROM ot GROUP BY DATE_TRUNC('month', date)
    )
    SELECT
        (SELECT month FROM monthly ORDER BY hrs DESC LIMIT 1) AS peak_month,
        (SELECT hrs  FROM monthly ORDER BY hrs DESC LIMIT 1) AS peak_hrs,
        (SELECT month FROM monthly ORDER BY hrs ASC  LIMIT 1) AS trough_month,
        (SELECT hrs  FROM monthly ORDER BY hrs ASC  LIMIT 1) AS trough_hrs,
        MAX(hrs) / MIN(hrs) AS ratio
    FROM monthly
""").df()

print(f"Peak OT month   : {peak_trough['peak_month'].iloc[0]}  ({peak_trough['peak_hrs'].iloc[0]:,.0f} hrs)")
print(f"Trough OT month : {peak_trough['trough_month'].iloc[0]}  ({peak_trough['trough_hrs'].iloc[0]:,.0f} hrs)")
print(f"Peak-to-trough ratio: {peak_trough['ratio'].iloc[0]:.1f}x")
```

- [ ] **Step 8: Run notebook through Section 3, verify all cells execute cleanly**

- [ ] **Step 9: Commit**

```bash
git add notebooks/fleet_analysis.ipynb
git commit -m "feat: Sections 2-3 DuckDB SQL — utilization and OT analysis"
```

---

## Task 7: Notebook — Sections 4–5 SQL (Maintenance + Cost Impact)

**Files:**
- Modify: `notebooks/fleet_analysis.ipynb`

- [ ] **Step 1: Replace `cell-maint-chart` content**

```python
maint_summary = con.execute("""
    SELECT
        maintenance_type,
        SUM(cost)                                         AS total_cost,
        SUM(cost) / SUM(SUM(cost)) OVER () * 100         AS cost_pct,
        RANK() OVER (ORDER BY SUM(cost) DESC)             AS rnk
    FROM maint
    GROUP BY maintenance_type
    ORDER BY total_cost DESC
""").df()

bar_colors_m = ['#DC2626' if r == 1 else '#93C5FD' for r in maint_summary['rnk']][::-1]

fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(maint_summary['maintenance_type'][::-1], maint_summary['total_cost'][::-1],
        color=bar_colors_m, edgecolor='white')
ax.set_title('Maintenance Cost by Type ($)  (Red = Highest)')
ax.set_xlabel('Total Cost ($)')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
for i, (val, pct) in enumerate(zip(maint_summary['total_cost'][::-1], maint_summary['cost_pct'][::-1])):
    ax.text(val * 1.01, i, f'{pct:.1f}%', va='center', fontsize=10, color='#475569')
plt.tight_layout()
plt.savefig('../visuals/maintenance_cost.png', bbox_inches='tight')
plt.show()

top = maint_summary.iloc[0]
print(f"Top category : {top['maintenance_type']}")
print(f"  Total cost : ${top['total_cost']:,.0f}  ({top['cost_pct']:.1f}% of total spend)")
```

- [ ] **Step 2: Replace `cell-correlation` content**

```python
correlation = con.execute("""
    WITH monthly_dt AS (
        SELECT
            DATE_TRUNC('month', date)::DATE AS month,
            location,
            SUM(downtime_days) AS downtime_days
        FROM maint
        GROUP BY DATE_TRUNC('month', date), location
    ),
    monthly_util AS (
        SELECT
            DATE_TRUNC('month', date)::DATE AS month,
            location,
            AVG(utilization_rate) * 100 AS util_pct
        FROM util
        GROUP BY DATE_TRUNC('month', date), location
    ),
    joined AS (
        SELECT d.month, d.location, d.downtime_days, u.util_pct
        FROM monthly_dt d
        JOIN monthly_util u ON d.month = u.month AND d.location = u.location
    )
    SELECT
        CORR(downtime_days, util_pct) AS overall_corr,
        location,
        CORR(downtime_days, util_pct) AS loc_corr
    FROM joined
    GROUP BY ROLLUP(location)
    ORDER BY location NULLS FIRST
""").df()

overall_corr = correlation[correlation['location'].isna()]['overall_corr'].iloc[0]
print(f'Pearson r (monthly downtime days vs utilization rate): {overall_corr:.3f}')
print()
print('Correlation by location:')
for _, row in correlation[correlation['location'].notna()].iterrows():
    direction = 'negative' if row['loc_corr'] < 0 else 'positive'
    print(f"  {row['location']:<10}: r = {row['loc_corr']:.3f}  ({direction})")
```

- [ ] **Step 3: Replace `cell-scatter` content**

```python
scatter_data = con.execute("""
    WITH monthly_dt AS (
        SELECT DATE_TRUNC('month', date)::DATE AS month, location, SUM(downtime_days) AS downtime_days
        FROM maint GROUP BY DATE_TRUNC('month', date), location
    ),
    monthly_util AS (
        SELECT DATE_TRUNC('month', date)::DATE AS month, location, AVG(utilization_rate)*100 AS util_pct
        FROM util GROUP BY DATE_TRUNC('month', date), location
    )
    SELECT d.location, d.downtime_days, u.util_pct
    FROM monthly_dt d JOIN monthly_util u ON d.month = u.month AND d.location = u.location
""").df()

loc_colors = {'South': '#EF4444', 'West': '#F59E0B',
              'East': '#059669', 'Central': '#818CF8', 'North': '#1D4ED8'}

fig, ax = plt.subplots(figsize=(9, 5))
for loc, grp in scatter_data.groupby('location'):
    ax.scatter(grp['downtime_days'], grp['util_pct'],
               label=loc, color=loc_colors.get(loc, '#94A3B8'), alpha=0.6, s=40)

m_fit = np.polyfit(scatter_data['downtime_days'], scatter_data['util_pct'], 1)
x_fit = np.linspace(scatter_data['downtime_days'].min(), scatter_data['downtime_days'].max(), 100)
ax.plot(x_fit, np.polyval(m_fit, x_fit),
        color='#0F172A', linewidth=1.5, linestyle='--',
        label=f'Overall trend  (r = {overall_corr:.2f})')

ax.set_xlabel('Monthly Downtime Days (per location)')
ax.set_ylabel('Avg Utilization (%)')
ax.set_title('Maintenance Downtime vs Fleet Utilization — by Location-Month')
ax.legend(loc='lower left', fontsize=9)
plt.tight_layout()
plt.show()
```

- [ ] **Step 4: Replace `cell-impact` content**

```python
cost_levers = con.execute(f"""
    WITH summer_ot AS (
        SELECT SUM(overtime_hours) * {OT_PREMIUM} AS summer_ot_cost
        FROM ot WHERE MONTH(date) IN (6, 7, 8)
    ),
    idle_fleet AS (
        SELECT
            COUNT(*) FILTER (WHERE avg_util < 0.50)  AS idle_count,
            AVG(avg_util) FILTER (WHERE avg_util < 0.50) AS idle_avg,
            AVG(avg_util) AS fleet_avg
        FROM (
            SELECT vehicle_id, AVG(utilization_rate) AS avg_util
            FROM util GROUP BY vehicle_id
        )
    ),
    reactive_winter AS (
        SELECT
            SUM(cost) AS reactive_cost,
            AVG(downtime_days) AS avg_downtime
        FROM maint
        WHERE MONTH(date) IN (11, 12, 1, 2)
          AND maintenance_type IN ('Engine Repair', 'Brake Service')
    )
    SELECT
        s.summer_ot_cost,
        s.summer_ot_cost * 0.20 AS savings_20pct,
        s.summer_ot_cost * 0.30 AS savings_30pct,
        i.idle_count,
        i.idle_avg * 100 AS idle_avg_pct,
        i.fleet_avg * 100 AS fleet_avg_pct,
        (i.fleet_avg - i.idle_avg) * 100 AS util_lift_pp,
        r.reactive_cost AS reactive_winter_cost,
        r.avg_downtime AS avg_dt_days,
        r.reactive_cost * 0.10 AS sched_savings
    FROM summer_ot s, idle_fleet i, reactive_winter r
""").df()

row = cost_levers.iloc[0]

print('=== Lever 1: Summer OT Reduction via Contract Staffing ===')
print(f"  Summer OT cost (full period)       : ${row['summer_ot_cost']:,.0f}")
print(f"  Savings at 20% OT reduction        : ${row['savings_20pct']:,.0f}")
print(f"  Savings at 30% OT reduction        : ${row['savings_30pct']:,.0f}")
print(f"  (Contract staff rate ~$18-22/hr vs ${OT_PREMIUM:.0f}/hr OT premium)")

print()
print('=== Lever 2: Fleet Rebalancing — Utilization Lift ===')
print(f"  Idle vehicle count (<50% avg util) : {row['idle_count']:,.0f}")
print(f"  Current avg util for idle pool     : {row['idle_avg_pct']:.1f}%")
print(f"  Fleet-wide avg util                : {row['fleet_avg_pct']:.1f}%")
print(f"  Utilization lift per reallocated   : +{row['util_lift_pp']:.1f}pp")

print()
print('=== Lever 3: Pre-Winter Maintenance Push ===')
print(f"  Engine + Brake spend in Nov-Feb    : ${row['reactive_winter_cost']:,.0f}")
print(f"  Avg downtime per event (these types): {row['avg_dt_days']:.1f} days")
print(f"  Shifting 30% to scheduled (Oct)    : ~${row['sched_savings']:,.0f} cost reduction")
print(f"  (Scheduled events avg ~50% less downtime than reactive)")
```

- [ ] **Step 5: Run notebook through Section 5, verify all cells execute cleanly**

- [ ] **Step 6: Commit**

```bash
git add notebooks/fleet_analysis.ipynb
git commit -m "feat: Sections 4-5 DuckDB SQL — maintenance and cost impact"
```

---

## Task 8: docs/technical/architecture.md

**Files:**
- Create: `docs/technical/architecture.md`

- [ ] **Step 1: Create `docs/technical/architecture.md`**

```markdown
# Fleet Ops Analytics — System Architecture

## Overview

Fleet Ops Analytics is a Streamlit-based operational dashboard backed by a synthetic dataset
representing a 5,200-unit regional rental fleet. The system surfaces overtime cost drivers,
fleet utilization patterns, and maintenance spend in a format suitable for both operational
review and executive presentation. The codebase is structured to be read as production-grade
analytical tooling, not a script.

---

## Module Responsibilities

| File | Owns | Does NOT Own |
|---|---|---|
| `dashboard/config.py` | Constants, color tokens, status thresholds, dark theme CSS | Logic, rendering, data access |
| `dashboard/data.py` | CSV loading, derived column computation, filtering, KPI derivation | Rendering, Plotly construction |
| `dashboard/charts.py` | Plotly figure construction, dark theme application | Data loading, `st.` calls |
| `dashboard/app.py` | Page config, CSS injection, sidebar, tab layout and routing | Pandas operations, Plotly construction inline |
| `data/generate_data.py` | Synthetic dataset generation | Runtime data access |
| `notebooks/fleet_analysis.ipynb` | Exploratory and diagnostic analysis via DuckDB SQL | Dashboard rendering |

---

## Data Flow

```
CSV files (data/)
    │
    ▼
data.py :: load_data()          ← @st.cache_data(ttl=3600)
    │  Parses dates, computes derived columns
    │  (utilization_pct, month_period, season, day_name)
    ▼
FleetData (dataclass)
    │
    ▼
data.py :: filter_data()        ← location + date range from sidebar
    │  Returns filtered FleetData copy
    ▼
FleetData (filtered)
    │
    ├──▶ data.py :: compute_kpis()  →  KPISet (computed once per filter change)
    │
    └──▶ charts.py :: make_*()      →  go.Figure (one per chart, no st. calls)
              │
              ▼
         app.py :: st.plotly_chart()   (rendering only)
```

---

## Key Design Decisions

**Why split into four files?**
The original `app.py` grew to ~800 lines with data loading, KPI computation, chart construction, 
and layout all interleaved. Reading it required holding the entire file in context simultaneously. 
The split gives each file one reason to change: data layer changes when business logic changes, 
chart layer changes when visual requirements change, config changes when design tokens change. 
`app.py` itself becomes a thin routing layer under 200 lines.

**Why `@st.cache_data(ttl=3600)` on `load_data()` only?**
`filter_data` and `compute_kpis` are fast (<10ms on 5,200 vehicles). Caching them would add 
complexity without measurable benefit. The expensive operation is CSV parsing and derived column 
computation — that happens once per hour or once per data regeneration.

**Why pre-compute derived columns in `load_data()`?**
Every tab previously called `.dt.to_period("M")`, `* 100`, `.dt.day_name()` inline at render 
time. With four tabs, these repeated on each tab render. Moving them to `load_data()` means 
they run once per cache lifetime regardless of how many tabs the user opens.

**Why DuckDB in the notebook instead of pandas?**
DuckDB `read_csv_auto()` queries CSV files directly without loading the full dataset into memory.
More importantly, SQL GROUP BY, window functions (`RANK() OVER`, `CORR()`), and CTEs communicate 
analytical intent more clearly than chained pandas method calls. A senior data engineer reading 
the notebook sees familiar patterns from production data warehouse work, not scripting idioms.

---

## Dependency Map

```
app.py
  ├── config.py     (DARK_THEME_CSS, DATA_DIR, DATA_FILES)
  ├── data.py       (data_exists, load_data, filter_data, compute_kpis)
  └── charts.py     (kpi_html, insight, make_*)

charts.py
  └── config.py     (COLORS, OT_PREMIUM)

data.py
  └── config.py     (DATA_DIR, DATA_FILES, OT_PREMIUM, util_status, ot_status)

config.py
  └── (no internal dependencies)
```

---

## Environment

- Python 3.9+
- Streamlit 1.50
- Plotly 5.18+
- DuckDB 1.0+ (notebook only)
- pandas 2.x, numpy 2.x
- Fonts: JetBrains Mono + Inter via Google Fonts CDN (no install required)
```

- [ ] **Step 2: Commit**

```bash
git add docs/technical/architecture.md
git commit -m "docs: add architecture.md"
```

---

## Task 9: docs/technical/data-dictionary.md

**Files:**
- Create: `docs/technical/data-dictionary.md`

- [ ] **Step 1: Create `docs/technical/data-dictionary.md`**

```markdown
# Fleet Ops Analytics — Data Dictionary

All data is synthetic, generated by `data/generate_data.py` to replicate realistic operational 
patterns: seasonal demand shifts, location-level variance, and role-based overtime distributions. 
Analysis treats this data as production-grade throughout.

---

## daily_utilization.csv

**Grain:** One row per vehicle per day.

| Column | Type | Description | Example |
|---|---|---|---|
| `date` | date | Calendar date of the utilization record | `2024-07-15` |
| `vehicle_id` | string | Unique vehicle identifier | `VH-4821` |
| `location` | string | Operating depot: North, South, East, West, Central | `South` |
| `vehicle_type` | string | Vehicle category: Compact, Mid-Size, Full-Size, SUV, Truck | `Compact` |
| `utilization_rate` | float [0, 1] | Fraction of the day the vehicle was in active use | `0.82` |

**Derived at load time (added by `data.py`):**

| Column | Type | Description |
|---|---|---|
| `utilization_pct` | float | `utilization_rate × 100` — avoids repeated inline scaling |
| `month_period` | Period[M] | Month period for GROUP BY operations |
| `month_str` | string | Three-letter month abbreviation (`Jan`, `Feb`, …) |
| `month_num` | int | Month number 1–12 |
| `season` | string | `Summer (Jun-Aug)` or `Rest of Year` |

---

## staff_overtime.csv

**Grain:** One row per employee per shift where overtime was recorded.

| Column | Type | Description | Example |
|---|---|---|---|
| `date` | date | Shift date | `2024-07-20` |
| `employee_id` | string | Unique employee identifier | `EMP-2047` |
| `location` | string | Depot where the shift occurred | `North` |
| `role` | string | Job role: Service Agent, Lot Attendant, Mechanic, Dispatcher, Manager | `Service Agent` |
| `overtime_hours` | float | Overtime hours logged for this shift | `2.5` |

**Derived at load time:**

| Column | Type | Description |
|---|---|---|
| `day_name` | string | Day of week (`Monday` … `Sunday`) |
| `month_period` | Period[M] | Month period for GROUP BY operations |

---

## maintenance_records.csv

**Grain:** One row per maintenance event.

| Column | Type | Description | Example |
|---|---|---|---|
| `date` | date | Date the maintenance event was opened | `2024-11-03` |
| `vehicle_id` | string | Vehicle that underwent maintenance | `VH-1093` |
| `location` | string | Depot where work was performed | `West` |
| `maintenance_type` | string | Engine Repair, Brake Service, Tire Replacement, Oil Change, Body Work | `Engine Repair` |
| `cost` | float | Total cost of the maintenance event (USD) | `2400.00` |
| `downtime_days` | int | Days the vehicle was unavailable during this event | `3` |

**Derived at load time:**

| Column | Type | Description |
|---|---|---|
| `month_period` | Period[M] | Month period for GROUP BY operations |

---

## fleet_vehicles.csv

**Grain:** One row per vehicle (static registry).

| Column | Type | Description | Example |
|---|---|---|---|
| `vehicle_id` | string | Unique vehicle identifier (matches utilization and maintenance records) | `VH-4821` |
| `vehicle_type` | string | Vehicle category | `SUV` |
| `location` | string | Home depot assignment | `Central` |
| `acquired_date` | date | Date the vehicle was added to the fleet | `2022-03-15` |

---

## Business Constants

| Constant | Value | Definition |
|---|---|---|
| `OT_PREMIUM` | `$28.00/hr` | Blended overtime premium rate used for all OT cost calculations. Represents the incremental cost of an overtime hour (base rate + overtime premium) blended across roles and locations. |
| Utilization target | `80%` | Fleet-wide utilization target. Industry benchmark for rental fleet efficiency: below 80% indicates underutilization; above 90% signals demand risk (insufficient buffer for maintenance and turnover). |
| Summer season | Jun–Aug | Months 6, 7, 8. Used for seasonal classification and overindex calculations. |
| Idle threshold | `<50%` | Vehicles averaging below 50% utilization are classified as reallocation candidates. |
```

- [ ] **Step 2: Commit**

```bash
git add docs/technical/data-dictionary.md
git commit -m "docs: add data-dictionary.md"
```

---

## Task 10: docs/technical/analytics-methodology.md

**Files:**
- Create: `docs/technical/analytics-methodology.md`

- [ ] **Step 1: Create `docs/technical/analytics-methodology.md`**

```markdown
# Fleet Ops Analytics — Analytics Methodology

This document defines how every KPI and metric in the dashboard is computed. 
It is written so an auditor or business stakeholder can validate the numbers 
without reading source code.

---

## Fleet Utilization Rate

**Definition:** The fraction of each calendar day that a vehicle was in active rental use.

**Computation:**
- Raw: `utilization_rate ∈ [0, 1]` per vehicle per day (from `daily_utilization.csv`)
- Dashboard display: `utilization_rate × 100` (percentage)
- Aggregated: arithmetic mean across all vehicle-day records in the filtered period and location

**Threshold logic:**
| Status | Condition | Color |
|---|---|---|
| On target | `≥ 80%` | Green (`#3FB950`) |
| Watch | `60% – 79%` | Amber (`#D29922`) |
| At risk | `< 60%` | Red (`#F85149`) |

**Why 80%?** Industry benchmark for rental fleet efficiency. Below 80% indicates 
underutilization (cost of asset without revenue). Above 90% signals demand risk — 
insufficient buffer for vehicle turnover, cleaning, and unplanned maintenance.

---

## Utilization Delta (pp vs Overall)

**Definition:** How many percentage points the filtered period/location deviates from the 
fleet-wide all-time average.

**Computation:**
```
util_delta = avg_util(filtered) − avg_util(all data, no filter)
```

Positive = filtered period is above baseline. Negative = below. 
Expressed in percentage points (pp), not percent change.

---

## Overtime Cost

**Definition:** Total cost of overtime hours at the blended OT premium rate.

**Computation:**
```
ot_cost = SUM(overtime_hours) × OT_PREMIUM
OT_PREMIUM = $28.00/hr
```

**Monthly baseline for ratio:**
```
baseline_monthly_ot = (SUM(all overtime_hours) × OT_PREMIUM) / COUNT(DISTINCT month, all data)
avg_monthly_ot      = ot_cost(filtered) / COUNT(DISTINCT month, filtered)
ot_ratio            = (avg_monthly_ot − baseline_monthly_ot) / baseline_monthly_ot
```

**Ratio threshold logic:**
| Status | Condition |
|---|---|
| Green | ratio < −5% (filtered months cheaper than baseline) |
| Amber | −5% ≤ ratio < 15% |
| Red | ratio ≥ 15% (filtered months significantly more expensive) |

---

## Avg OT / Shift

**Definition:** Mean overtime hours per individual shift record in the filtered period.

**Computation:**
```
avg_ot_shift   = MEAN(overtime_hours, filtered)
baseline_ot    = MEAN(overtime_hours, all data)
shift_delta    = avg_ot_shift − baseline_ot
```

**Shift delta threshold:**
| Status | Condition |
|---|---|
| Green | delta < 0 (filtered shifts have less OT than baseline) |
| Amber | 0 ≤ delta < 0.5 hrs |
| Red | delta ≥ 0.5 hrs |

---

## Summer Overindex Factor

**Definition:** How much heavier summer is in OT cost relative to its calendar share.

**Computation:**
```
summer_pct     = SUM(ot_cost, Jun–Aug) / SUM(ot_cost, all months)
overindex      = summer_pct / 0.25
```

Jun–Aug represents 3 of 12 months = 25% calendar weight. An overindex of 1.5x means 
summer carries 1.5× its expected cost share — a structural concentration, not random variance.

---

## Idle Fleet Pool

**Definition:** Vehicles whose average utilization over the filtered period falls below 50%.

**Computation:**
```
per_vehicle_avg = MEAN(utilization_rate) GROUP BY vehicle_id
idle_pool       = vehicles WHERE per_vehicle_avg < 0.50
```

These are reallocation candidates — assets that could improve overall utilization if 
moved to higher-demand locations.

---

## Maintenance Downtime vs. Utilization Correlation

**Definition:** Pearson correlation coefficient between monthly downtime days and average 
utilization rate at the same location-month grain.

**Computation:**
```
monthly_downtime[location, month] = SUM(downtime_days)
monthly_util[location, month]     = MEAN(utilization_rate) × 100
r = CORR(monthly_downtime, monthly_util)
```

A negative `r` confirms that higher downtime is associated with lower utilization — 
maintenance events suppress revenue availability, not just add cost.

---

## Known Limitations

**Synthetic data scope:** All records are generated by `data/generate_data.py` using realistic 
distributions, not extracted from a live system. Patterns (seasonal peaks, role-based OT 
concentration, engine repair dominance) are seeded to replicate documented operational phenomena 
but cannot be used to draw conclusions about any specific real fleet.

**OT premium rate:** `$28.00/hr` is a blended approximation. A production system would apply 
role-specific premium rates. The blended rate is appropriate for fleet-level cost estimation 
but understates cost for higher-compensated roles (Mechanics, Managers) and overstates for 
lower-compensated roles (Lot Attendants).

**Utilization definition:** `utilization_rate` represents time-based utilization (hours active 
/ hours available). Revenue utilization (revenue days / available days) is a related but 
distinct metric not present in this dataset.

**Correlation ≠ causation:** The negative correlation between downtime and utilization is 
directionally expected but not tested for confounders. A vehicle with high utilization may 
also require more maintenance (wear-based), creating a reverse causality effect not isolated here.
```

- [ ] **Step 2: Commit**

```bash
git add docs/technical/analytics-methodology.md
git commit -m "docs: add analytics-methodology.md"
```

---

## Task 11: docs/technical/operations-runbook.md

**Files:**
- Create: `docs/technical/operations-runbook.md`

- [ ] **Step 1: Create `docs/technical/operations-runbook.md`**

```markdown
# Fleet Ops Analytics — Operations Runbook

Reference guide for installation, execution, data management, and troubleshooting.
Written for a technical user new to this repository.

---

## Prerequisites

- Python 3.9 or later
- Git

---

## Installation

```bash
git clone https://github.com/DCodeBase-X/fleet-ops-analytics.git
cd fleet-ops-analytics

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Generate the Dataset

The dashboard requires four CSV files in `data/`. They are not committed to the repository.
Generate them before first run:

```bash
python data/generate_data.py
```

This takes 2–4 minutes and produces:
- `data/fleet_vehicles.csv` (~5,200 rows)
- `data/daily_utilization.csv` (~3.8M rows)
- `data/staff_overtime.csv` (~180K rows)
- `data/maintenance_records.csv` (~52K rows)

---

## Run the Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501` by default.

To use a different port:

```bash
streamlit run dashboard/app.py --server.port 8080
```

---

## Regenerate the Dataset

To replace all CSV files with a fresh synthetic dataset, either:

1. Click **Regenerate Now** in the dashboard sidebar under "Regenerate data", or
2. Run the generator script directly:

```bash
python data/generate_data.py
```

After regeneration, the dashboard's in-memory cache clears automatically on the next interaction.
To force an immediate reload, press **R** in the Streamlit browser tab to rerun.

---

## Run the Notebook

```bash
source .venv/bin/activate
jupyter lab notebooks/fleet_analysis.ipynb
```

The notebook uses DuckDB to query CSV files directly. It expects the `data/` directory to 
exist and contain all four CSV files. Run the generator above if they are missing.

---

## Run Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

Tests cover `config.py`, `data.py`, and `charts.py`. They do not require the CSV files.

---

## Add a New Location

1. Open `data/generate_data.py`
2. Add the new location name to the `LOCATIONS` list
3. Rerun the generator: `python data/generate_data.py`
4. The dashboard and notebook pick up the new location automatically — no code changes required

---

## Add a New Date Range

The generator produces data from a fixed start date to today. To extend the range:

1. Open `data/generate_data.py`
2. Adjust `START_DATE` and `END_DATE` constants at the top of the file
3. Rerun the generator

---

## Troubleshooting

**"No fleet data found" on dashboard launch**

The CSV files are missing. Run `python data/generate_data.py` to generate them.

---

**Dashboard shows stale data after regeneration**

Streamlit caches data for up to 1 hour (`ttl=3600`). To force a reload immediately:
- Click **Regenerate Now** in the sidebar (this clears the Streamlit cache automatically), or
- Restart the Streamlit process: `Ctrl+C` then `streamlit run dashboard/app.py`

---

**Port 8501 already in use**

Another Streamlit instance is running. Either:
- Stop it: `pkill -f streamlit`
- Or use a different port: `streamlit run dashboard/app.py --server.port 8502`

---

**`ModuleNotFoundError: No module named 'dashboard'`**

Run from the project root (not from inside `dashboard/`):

```bash
cd /path/to/fleet-ops-analytics
streamlit run dashboard/app.py
```
```

- [ ] **Step 2: Commit**

```bash
git add docs/technical/operations-runbook.md
git commit -m "docs: add operations-runbook.md"
```

---

## Final Verification

- [ ] **Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS across `test_config.py`, `test_data.py`, `test_charts.py`.

- [ ] **Verify app loads and all four tabs render without error**

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501`. Cycle through all four tabs. Confirm dark theme is applied throughout, JetBrains Mono is used for KPI values, charts render with dark backgrounds.

- [ ] **Verify notebook runs end-to-end**

Open `notebooks/fleet_analysis.ipynb`, restart kernel, run all cells. All cells should complete without errors. All charts should render.

- [ ] **Final commit**

```bash
git add requirements.txt
git commit -m "chore: finalize requirements.txt with duckdb and pytest"
```

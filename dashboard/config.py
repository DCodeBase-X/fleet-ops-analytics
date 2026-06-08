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
DARK_THEME_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: {COLORS["bg_base"]};
    color: {COLORS["text_primary"]};
}}

footer {{ visibility: hidden; }}

/* ── Sidebar */
[data-testid="stSidebar"] {{
    background: {COLORS["bg_base"]};
    border-right: 1px solid {COLORS["border"]};
}}
[data-testid="stSidebar"] * {{ color: {COLORS["text_primary"]}; }}
[data-testid="stSidebar"] .stSelectbox > div,
[data-testid="stSidebar"] input {{
    background: {COLORS["bg_elevated"]};
    border-color: {COLORS["border"]};
    color: {COLORS["text_primary"]};
}}

/* ── Main background */
.main .block-container {{ background-color: {COLORS["bg_base"]}; }}

/* ── Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {COLORS["border"]};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 500;
    color: {COLORS["text_secondary"]};
    border-radius: 0;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    background: transparent;
}}
.stTabs [aria-selected="true"] {{
    color: {COLORS["blue"]} !important;
    border-bottom: 2px solid {COLORS["blue"]} !important;
    background: transparent !important;
}}

/* ── KPI cards */
.kpi-card {{
    background: {COLORS["bg_card"]};
    border-radius: 6px;
    border: 1px solid {COLORS["border"]};
    border-top: 2px solid {COLORS["text_secondary"]};
    padding: 16px 20px;
    height: 100%;
    box-sizing: border-box;
}}
.kpi-card.green {{ border-top-color: {COLORS["green"]}; }}
.kpi-card.amber {{ border-top-color: {COLORS["amber"]}; }}
.kpi-card.red   {{ border-top-color: {COLORS["red"]}; }}
.kpi-card.blue  {{ border-top-color: {COLORS["blue"]}; }}

.kpi-label {{
    font-size: 11px;
    font-weight: 600;
    color: {COLORS["text_secondary"]};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}}
.kpi-value {{
    font-family: 'IBM Plex Mono', 'Courier New', monospace;
    font-size: 24px;
    font-weight: 700;
    color: {COLORS["text_primary"]};
    line-height: 1.15;
    letter-spacing: -0.5px;
}}
.kpi-delta {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    margin-top: 6px;
    color: {COLORS["text_secondary"]};
}}

/* ── Insight cards */
.insight-card {{
    background: {COLORS["bg_card"]};
    border-left: 4px solid {COLORS["amber"]};
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    margin: 4px 0 20px 0;
    font-size: 13px;
    color: {COLORS["text_primary"]};
    line-height: 1.6;
}}
.insight-card strong {{ color: {COLORS["amber"]}; font-weight: 600; }}

/* ── Headings */
h1, h2, h3 {{ color: {COLORS["text_primary"]}; }}

/* ── Buttons */
.stButton > button {{
    background: {COLORS["bg_elevated"]};
    border: 1px solid {COLORS["border"]};
    color: {COLORS["text_primary"]};
}}
.stButton > button:hover {{
    background: {COLORS["border"]};
    border-color: {COLORS["blue"]};
    color: {COLORS["blue"]};
}}

/* ── Expander */
[data-testid="stExpander"] {{
    background: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
}}
</style>
"""

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

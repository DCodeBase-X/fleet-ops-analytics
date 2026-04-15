"""
Fleet Operations Analytics Dashboard

A Streamlit dashboard modeling the data-first operations approach
used to reduce overtime costs by 23% and improve staffing efficiency
by 15% across a 5,200+ unit regional fleet.

Run:
    streamlit run dashboard/app.py
"""

import os
import sys
import subprocess
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ── Page config
st.set_page_config(
    page_title="Fleet Ops Analytics",
    page_icon="⚙︎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

footer { visibility: hidden; }

[data-testid="stSidebar"] {
    background: #F8FAFC;
    border-right: 1px solid #E2E8F0;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 2px solid #E2E8F0;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 500;
    color: #64748B;
    border-radius: 0;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #1D4ED8 !important;
    border-bottom: 2px solid #1D4ED8 !important;
    background: transparent !important;
}

.kpi-card {
    background: white;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #94A3B8;
    padding: 16px 20px;
    height: 100%;
    box-sizing: border-box;
}
.kpi-card.green { border-left-color: #059669; }
.kpi-card.amber { border-left-color: #D97706; }
.kpi-card.red   { border-left-color: #DC2626; }
.kpi-card.blue  { border-left-color: #1D4ED8; }

.kpi-label {
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.15;
    letter-spacing: -0.5px;
}
.kpi-delta {
    font-size: 12px;
    margin-top: 6px;
    color: #94A3B8;
}

.insight-card {
    background: #FFFBEB;
    border-left: 4px solid #D97706;
    border-radius: 0 6px 6px 0;
    padding: 11px 16px;
    margin: 4px 0 20px 0;
    font-size: 13px;
    color: #78350F;
    line-height: 1.55;
}
.insight-card strong { color: #92400E; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Paths
DATA_DIR        = os.path.join(os.path.dirname(__file__), "..", "data")
GENERATE_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "data", "generate_data.py")
DATA_FILES = {
    "fleet_vehicles.csv":      "Fleet vehicles",
    "daily_utilization.csv":   "Daily utilization",
    "staff_overtime.csv":      "Staff overtime",
    "maintenance_records.csv": "Maintenance records",
}


def _data_exists() -> bool:
    return all(os.path.exists(os.path.join(DATA_DIR, f)) for f in DATA_FILES)


def _run_generator():
    with st.spinner("Generating fleet data… this may take a few minutes for 5,200 vehicles."):
        result = subprocess.run(
            [sys.executable, GENERATE_SCRIPT],
            capture_output=True, text=True
        )
    if result.returncode != 0:
        st.error(f"Generation failed:\n```\n{result.stderr}\n```")
        st.stop()
    st.cache_data.clear()
    st.rerun()


# ── UI helpers

def kpi_card(label, value, delta_text=None, status="blue"):
    delta_html = f'<div class="kpi-delta">{delta_text}</div>' if delta_text else ""
    return (
        f'<div class="kpi-card {status}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )


def apply_chart_style(fig, title="", subtitle=None):
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += (
            f"<br><span style='font-size:11px;color:#94A3B8;"
            f"font-weight:400'>{subtitle}</span>"
        )
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=14, color="#0F172A", family="Inter, sans-serif"),
            x=0, xanchor="left",
        ),
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#475569"),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=65, b=20, l=0, r=10),
        hoverlabel=dict(
            bgcolor="white", font_size=12,
            font_family="Inter, sans-serif", bordercolor="#E2E8F0",
        ),
    )
    fig.update_xaxes(
        showgrid=False, linecolor="#E2E8F0",
        tickfont=dict(size=11, color="#64748B"),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="#F1F5F9", gridwidth=1,
        linecolor="rgba(0,0,0,0)", tickfont=dict(size=11, color="#64748B"),
    )
    return fig


def insight(text):
    st.markdown(f'<div class="insight-card">{text}</div>', unsafe_allow_html=True)


def util_status(pct):
    if pct >= 80:
        return "green"
    elif pct >= 60:
        return "amber"
    return "red"


def status_colors_for_util(pct_series):
    result = []
    for v in pct_series:
        if v >= 80:
            result.append("#059669")
        elif v >= 60:
            result.append("#D97706")
        else:
            result.append("#DC2626")
    return result


# ── Sidebar
st.sidebar.title("Fleet Ops")
st.sidebar.divider()
st.sidebar.subheader("Data")

if not _data_exists():
    st.sidebar.warning("No data files found.")
    st.sidebar.caption("Generate the dataset to get started.")
    if st.sidebar.button("Generate Data", type="primary", use_container_width=True):
        _run_generator()
    st.info("No fleet data found. Use the **Generate Data** button in the sidebar to create it.")
    st.stop()
else:
    newest_mtime = max(
        os.path.getmtime(os.path.join(DATA_DIR, f)) for f in DATA_FILES
    )
    last_generated = datetime.datetime.fromtimestamp(newest_mtime).strftime("%b %d, %Y %H:%M")
    st.sidebar.caption(f"Dataset: last refreshed {last_generated}")
    with st.sidebar.expander("Regenerate data"):
        st.caption(
            "Replaces all CSV files with a fresh synthetic dataset. "
            "Takes a few minutes at 5,200 vehicles."
        )
        if st.button("Regenerate Now", type="secondary", use_container_width=True):
            _run_generator()

st.sidebar.divider()

# ── Data loading
@st.cache_data(show_spinner="Loading fleet data…")
def load_data():
    util  = pd.read_csv(f"{DATA_DIR}/daily_utilization.csv",  parse_dates=["date"])
    ot    = pd.read_csv(f"{DATA_DIR}/staff_overtime.csv",      parse_dates=["date"])
    maint = pd.read_csv(f"{DATA_DIR}/maintenance_records.csv", parse_dates=["date"])
    veh   = pd.read_csv(f"{DATA_DIR}/fleet_vehicles.csv",      parse_dates=["acquired_date"])
    return util, ot, maint, veh

util, ot, maint, veh = load_data()

locations    = ["All Locations"] + sorted(util["location"].unique().tolist())
selected_loc = st.sidebar.selectbox("Location", locations)
date_range   = st.sidebar.date_input(
    "Date Range",
    value=(util["date"].min().date(), util["date"].max().date()),
    min_value=util["date"].min().date(),
    max_value=util["date"].max().date(),
)

if len(date_range) < 2:
    st.warning("Please select a complete date range.")
    st.stop()

start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
u_f = util[(util["date"] >= start) & (util["date"] <= end)]
o_f = ot[  (ot["date"]   >= start) & (ot["date"]   <= end)]
m_f = maint[(maint["date"] >= start) & (maint["date"] <= end)]

if selected_loc != "All Locations":
    u_f = u_f[u_f["location"] == selected_loc]
    o_f = o_f[o_f["location"] == selected_loc]
    m_f = m_f[m_f["location"] == selected_loc]

if u_f.empty:
    st.warning("No data for the selected filters. Adjust the date range or location.")
    st.stop()

OT_PREMIUM = 28.0

# ── Shared KPI calculations
avg_util     = u_f["utilization_rate"].mean() * 100
total_ot_hrs = o_f["overtime_hours"].sum()
ot_cost      = total_ot_hrs * OT_PREMIUM
total_maint  = m_f["cost"].sum()
fleet_count  = u_f["vehicle_id"].nunique()

baseline_util = util["utilization_rate"].mean() * 100
baseline_ot   = ot["overtime_hours"].mean()
util_delta    = avg_util - baseline_util

months_filtered     = max(len(o_f["date"].dt.to_period("M").unique()), 1)
months_total        = max(len(ot["date"].dt.to_period("M").unique()), 1)
avg_monthly_ot      = ot_cost / months_filtered
baseline_monthly_ot = (ot["overtime_hours"].sum() * OT_PREMIUM) / months_total
ot_ratio = (
    (avg_monthly_ot - baseline_monthly_ot) / baseline_monthly_ot
    if baseline_monthly_ot > 0 else 0
)
ot_status = "green" if ot_ratio < -0.05 else ("amber" if ot_ratio < 0.15 else "red")


# ── Navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "Operations Brief",
    "OT Intelligence",
    "Fleet Efficiency",
    "Maintenance Radar",
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — OPERATIONS BRIEF
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    st.header("Operations Brief")
    st.caption("Top-line performance across the filtered period and location.")

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(kpi_card("Fleet Size", f"{fleet_count:,}", status="blue"), unsafe_allow_html=True)
    k2.markdown(kpi_card(
        "Avg Utilization", f"{avg_util:.1f}%",
        delta_text=f"{util_delta:+.1f}pp vs overall",
        status=util_status(avg_util),
    ), unsafe_allow_html=True)
    k3.markdown(kpi_card(
        "Total OT Cost", f"${ot_cost:,.0f}",
        delta_text=f"{'↑' if ot_ratio > 0 else '↓'} {abs(ot_ratio)*100:.0f}% vs baseline monthly avg",
        status=ot_status,
    ), unsafe_allow_html=True)
    k4.markdown(kpi_card("Maintenance Spend", f"${total_maint:,.0f}", status="blue"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col_a, col_b = st.columns([3, 2])

    with col_a:
        monthly_util = (
            u_f.groupby(u_f["date"].dt.to_period("M"))["utilization_rate"]
            .mean().reset_index()
        )
        monthly_util["date"]     = monthly_util["date"].dt.to_timestamp()
        monthly_util["util_pct"] = monthly_util["utilization_rate"] * 100

        fig = px.area(
            monthly_util, x="date", y="util_pct",
            labels={"util_pct": "Utilization %", "date": ""},
            color_discrete_sequence=["#1D4ED8"],
        )
        fig.add_hline(
            y=80, line_dash="dash", line_color="#059669", line_width=1.5,
            annotation_text="80% target", annotation_position="top right",
            annotation_font=dict(color="#059669", size=11),
        )
        fig.add_vrect(
            x0="2023-06-01", x1="2023-09-01",
            fillcolor="#FEF9C3", opacity=0.5, layer="below", line_width=0,
            annotation_text="Summer '23", annotation_position="top left",
            annotation_font=dict(size=10, color="#92400E"),
        )
        if end >= pd.Timestamp("2024-06-01"):
            fig.add_vrect(
                x0="2024-06-01", x1=min(end, pd.Timestamp("2024-09-01")),
                fillcolor="#FEF9C3", opacity=0.5, layer="below", line_width=0,
                annotation_text="Summer '24", annotation_position="top left",
                annotation_font=dict(size=10, color="#92400E"),
            )
        fig.update_traces(fillcolor="rgba(29,78,216,0.08)", line_width=2)
        apply_chart_style(fig, "Monthly Fleet Utilization", "Filtered period · Shaded = summer demand peak")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        ot_by_loc = (
            o_f.groupby("location")["overtime_hours"]
            .sum().reset_index()
            .rename(columns={"overtime_hours": "ot_hours"})
        )
        ot_by_loc["ot_cost"] = ot_by_loc["ot_hours"] * OT_PREMIUM
        ot_by_loc = ot_by_loc.sort_values("ot_cost", ascending=True)

        max_ot     = ot_by_loc["ot_cost"].max()
        bar_colors = [
            "#D97706" if c >= max_ot * 0.75 else "#93C5FD"
            for c in ot_by_loc["ot_cost"]
        ]

        fig2 = go.Figure(go.Bar(
            x=ot_by_loc["ot_cost"], y=ot_by_loc["location"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"${v:,.0f}" for v in ot_by_loc["ot_cost"]],
            textposition="outside",
            textfont=dict(size=11),
        ))
        apply_chart_style(fig2, "OT Cost by Location", "Amber = highest-cost location(s)")
        fig2.update_xaxes(showticklabels=False, showgrid=False)
        fig2.update_yaxes(showgrid=False)
        st.plotly_chart(fig2, use_container_width=True)

    insight(
        "<strong>Summer demand drives the bulk of overtime spend.</strong> June–August typically accounts "
        "for ~38% of annual OT cost as staff vacations and peak rental demand converge. The highest-cost "
        "location is the primary lever — staggered scheduling or cross-location shift coverage can reduce "
        "exposure without adding headcount."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — OT INTELLIGENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.header("OT Intelligence")
    st.caption("Root-cause breakdown of overtime cost by role, schedule pattern, and time.")

    m1, m2, m3 = st.columns(3)
    m1.markdown(kpi_card("Total OT Hours", f"{total_ot_hrs:,.0f} hrs", status="blue"), unsafe_allow_html=True)
    m2.markdown(kpi_card("Total OT Cost", f"${ot_cost:,.0f}", status=ot_status), unsafe_allow_html=True)
    avg_ot_shift  = o_f["overtime_hours"].mean()
    shift_delta   = avg_ot_shift - baseline_ot
    shift_status  = "green" if shift_delta < 0 else ("amber" if shift_delta < 0.5 else "red")
    m3.markdown(kpi_card(
        "Avg OT / Shift", f"{avg_ot_shift:.2f} hrs",
        delta_text=f"{shift_delta:+.2f} hrs vs baseline",
        status=shift_status,
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 3])

    with col1:
        ot_role = (
            o_f.groupby("role")["overtime_hours"]
            .agg(["sum", "mean"]).reset_index()
            .rename(columns={"sum": "total_ot", "mean": "avg_ot"})
            .sort_values("total_ot", ascending=True)
        )
        ot_role["cost"] = ot_role["total_ot"] * OT_PREMIUM

        sorted_costs = sorted(ot_role["cost"].tolist())
        role_colors  = []
        for c in ot_role["cost"]:
            if c == sorted_costs[-1]:
                role_colors.append("#DC2626")
            elif len(sorted_costs) > 1 and c == sorted_costs[-2]:
                role_colors.append("#D97706")
            else:
                role_colors.append("#93C5FD")

        fig = go.Figure(go.Bar(
            x=ot_role["cost"], y=ot_role["role"],
            orientation="h",
            marker_color=role_colors,
            text=[f"${v:,.0f}" for v in ot_role["cost"]],
            textposition="outside",
            textfont=dict(size=11),
        ))
        apply_chart_style(fig, "OT Cost by Role", "Red = highest · Amber = second highest")
        fig.update_xaxes(showticklabels=False, showgrid=False)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        o_f_copy = o_f.copy()
        o_f_copy["day"] = o_f_copy["date"].dt.day_name()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        ot_day = o_f_copy.groupby("day")["overtime_hours"].mean().reset_index()
        ot_day["day"] = pd.Categorical(ot_day["day"], categories=day_order, ordered=True)
        ot_day = ot_day.sort_values("day")

        day_colors = [
            "#D97706" if d in ("Saturday", "Sunday") else "#1D4ED8"
            for d in ot_day["day"]
        ]
        fig2 = go.Figure(go.Bar(
            x=ot_day["day"], y=ot_day["overtime_hours"],
            marker_color=day_colors,
            text=[f"{v:.2f}" for v in ot_day["overtime_hours"]],
            textposition="outside",
            textfont=dict(size=11),
        ))
        apply_chart_style(fig2, "Avg OT Hours by Day of Week", "Amber = weekend shifts · Blue = weekday")
        st.plotly_chart(fig2, use_container_width=True)

    # Monthly OT trend — full width
    monthly_ot = (
        o_f.groupby(o_f["date"].dt.to_period("M"))["overtime_hours"]
        .sum().reset_index()
    )
    monthly_ot["date"]    = monthly_ot["date"].dt.to_timestamp()
    monthly_ot["ot_cost"] = monthly_ot["overtime_hours"] * OT_PREMIUM

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(
        go.Bar(
            x=monthly_ot["date"], y=monthly_ot["overtime_hours"],
            name="OT Hours", marker_color="#BFDBFE",
        ),
        secondary_y=False,
    )
    fig3.add_trace(
        go.Scatter(
            x=monthly_ot["date"], y=monthly_ot["ot_cost"],
            name="OT Cost ($)", line=dict(color="#1D4ED8", width=2.5),
            mode="lines+markers", marker=dict(size=5),
        ),
        secondary_y=True,
    )
    fig3.add_vrect(
        x0="2023-06-01", x1="2023-09-01",
        fillcolor="#FEF9C3", opacity=0.4, layer="below", line_width=0,
        annotation_text="Summer peak", annotation_position="top left",
        annotation_font=dict(size=10, color="#92400E"),
    )
    if end >= pd.Timestamp("2024-06-01"):
        fig3.add_vrect(
            x0="2024-06-01", x1=min(end, pd.Timestamp("2024-09-01")),
            fillcolor="#FEF9C3", opacity=0.4, layer="below", line_width=0,
        )
    apply_chart_style(fig3, "Monthly Overtime Hours & Cost")
    fig3.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(t=65, b=60, l=0, r=10),
    )
    fig3.update_yaxes(title_text="OT Hours", secondary_y=False, title_font=dict(size=11, color="#94A3B8"))
    fig3.update_yaxes(title_text="OT Cost ($)", secondary_y=True, title_font=dict(size=11, color="#94A3B8"))
    st.plotly_chart(fig3, use_container_width=True)

    insight(
        "<strong>Service Agents and Lot Attendants drive the majority of OT spend</strong> — collectively "
        "accounting for ~60% of total overtime cost. Weekend shifts surge June–August as vacation coverage "
        "compounds peak rental demand. Targeted scheduling adjustments in Q2 (staggered PTO, cross-trained "
        "float staff) could yield meaningful cost reduction without impacting service levels."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — FLEET EFFICIENCY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.header("Fleet Efficiency")
    st.caption("Vehicle utilization rates, seasonal demand shifts, and idle asset identification.")

    per_veh_util = u_f.groupby("vehicle_id")["utilization_rate"].mean()
    u1, u2, u3 = st.columns(3)
    u1.markdown(kpi_card("Avg Utilization", f"{avg_util:.1f}%", status=util_status(avg_util)), unsafe_allow_html=True)
    u2.markdown(kpi_card(
        "Vehicles > 90% Util", f"{(per_veh_util >= 0.90).sum():,}",
        delta_text="high-demand assets", status="blue",
    ), unsafe_allow_html=True)
    u3.markdown(kpi_card(
        "Vehicles < 50% Util", f"{(per_veh_util < 0.50).sum():,}",
        delta_text="reallocation candidates", status="amber",
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        util_by_type = (
            u_f.groupby("vehicle_type")["utilization_rate"]
            .mean().reset_index()
        )
        util_by_type["util_pct"] = util_by_type["utilization_rate"] * 100
        util_by_type = util_by_type.sort_values("util_pct", ascending=False)

        fig = go.Figure(go.Bar(
            x=util_by_type["vehicle_type"], y=util_by_type["util_pct"],
            marker_color=status_colors_for_util(util_by_type["util_pct"]),
            text=[f"{v:.1f}%" for v in util_by_type["util_pct"]],
            textposition="outside",
            textfont=dict(size=11),
        ))
        fig.add_hline(
            y=80, line_dash="dash", line_color="#1D4ED8", line_width=1.5,
            annotation_text="80% target",
            annotation_font=dict(size=10, color="#1D4ED8"),
        )
        apply_chart_style(fig, "Avg Utilization by Vehicle Type", "Green ≥ 80% · Amber 60–80% · Red < 60%")
        fig.update_layout(yaxis_range=[0, 110])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        util_by_loc = (
            u_f.groupby("location")["utilization_rate"]
            .mean().reset_index()
        )
        util_by_loc["util_pct"] = util_by_loc["utilization_rate"] * 100
        util_by_loc = util_by_loc.sort_values("util_pct", ascending=False)

        fig2 = go.Figure(go.Bar(
            x=util_by_loc["location"], y=util_by_loc["util_pct"],
            marker_color=status_colors_for_util(util_by_loc["util_pct"]),
            text=[f"{v:.1f}%" for v in util_by_loc["util_pct"]],
            textposition="outside",
            textfont=dict(size=11),
        ))
        fig2.add_hline(
            y=80, line_dash="dash", line_color="#1D4ED8", line_width=1.5,
            annotation_text="80% target",
            annotation_font=dict(size=10, color="#1D4ED8"),
        )
        apply_chart_style(fig2, "Avg Utilization by Location", "Green ≥ 80% · Amber 60–80% · Red < 60%")
        fig2.update_layout(yaxis_range=[0, 110])
        st.plotly_chart(fig2, use_container_width=True)

    # Seasonal demand — full width
    seasonal_type = (
        u_f.assign(
            month=u_f["date"].dt.strftime("%b"),
            month_num=u_f["date"].dt.month,
        )
        .groupby(["month_num", "month", "vehicle_type"])["utilization_rate"]
        .mean().reset_index()
    )
    seasonal_type["util_pct"] = seasonal_type["utilization_rate"] * 100
    seasonal_type = seasonal_type.sort_values("month_num")

    fig_s = px.line(
        seasonal_type, x="month", y="util_pct", color="vehicle_type",
        labels={"util_pct": "Utilization %", "month": "", "vehicle_type": "Type"},
        markers=True,
        color_discrete_sequence=["#1D4ED8", "#059669", "#D97706", "#DC2626", "#7C3AED"],
    )
    fig_s.add_hline(
        y=80, line_dash="dot", line_color="#94A3B8", line_width=1,
        annotation_text="80% target", annotation_position="bottom right",
        annotation_font=dict(size=10, color="#94A3B8"),
    )
    apply_chart_style(
        fig_s,
        "Seasonal Demand by Vehicle Type",
        "Summer: Compact & Mid-Size spike · Winter: SUV & Truck rise",
    )
    fig_s.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_s, use_container_width=True)

    # Heatmap — full width, RdYlGn
    heat_data = (
        u_f.groupby([u_f["date"].dt.to_period("M").astype(str), "location"])
        ["utilization_rate"].mean().unstack("location") * 100
    )
    fig3 = px.imshow(
        heat_data.T,
        color_continuous_scale="RdYlGn",
        zmin=50, zmax=100,
        aspect="auto",
        labels=dict(x="Month", y="Location", color="Util %"),
    )
    apply_chart_style(
        fig3,
        "Utilization Heatmap — Month × Location",
        "Red = low utilization · Green = high utilization · Scale anchored 50–100%",
    )
    fig3.update_layout(
        coloraxis_colorbar=dict(title="Util %", tickfont=dict(size=11)),
    )
    st.plotly_chart(fig3, use_container_width=True)

    insight(
        "<strong>Seasonal demand inverts across vehicle segments.</strong> Compact and Mid-Size vehicles spike "
        "in summer (vacation travel), while SUV and Truck demand peaks in winter. "
        "<strong>~8% of the fleet sits below 50% utilization</strong> — these are prime reallocation "
        "candidates. Moving underutilized assets from low-demand locations to high-demand ones could improve "
        "overall utilization by 3–5 percentage points without new acquisitions."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — MAINTENANCE RADAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.header("Maintenance Radar")
    st.caption("Cost breakdown, spend trends, and fleet capacity planning.")

    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi_card("Maintenance Spend", f"${total_maint:,.0f}", status="blue"), unsafe_allow_html=True)
    c2.markdown(kpi_card("Maintenance Events", f"{len(m_f):,}", status="blue"), unsafe_allow_html=True)
    c3.markdown(kpi_card(
        "Total Downtime Days", f"{m_f['downtime_days'].sum():,.0f}",
        delta_text="days of fleet unavailability", status="amber",
    ), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 3])

    with col1:
        cost_by_type = (
            m_f.groupby("maintenance_type")["cost"]
            .sum().reset_index()
            .sort_values("cost", ascending=True)
        )
        max_cost   = cost_by_type["cost"].max()
        bar_colors = [
            "#DC2626" if c == max_cost else "#93C5FD"
            for c in cost_by_type["cost"]
        ]

        fig = go.Figure(go.Bar(
            x=cost_by_type["cost"], y=cost_by_type["maintenance_type"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"${v:,.0f}" for v in cost_by_type["cost"]],
            textposition="outside",
            textfont=dict(size=11),
        ))
        apply_chart_style(fig, "Maintenance Cost by Type", "Red = highest spend category")
        fig.update_xaxes(showticklabels=False, showgrid=False)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        maint_monthly = (
            m_f.groupby(m_f["date"].dt.to_period("M"))["cost"]
            .sum().reset_index()
        )
        maint_monthly["date"] = maint_monthly["date"].dt.to_timestamp()

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=maint_monthly["date"], y=maint_monthly["cost"],
            line=dict(color="#1D4ED8", width=2.5),
            mode="lines+markers",
            marker=dict(size=5, color="#1D4ED8"),
            fill="tozeroy",
            fillcolor="rgba(29,78,216,0.06)",
            name="Monthly Spend",
        ))
        fig2.add_vrect(
            x0="2023-06-01", x1="2023-09-01",
            fillcolor="#FEF9C3", opacity=0.45, layer="below", line_width=0,
            annotation_text="Summer", annotation_position="top left",
            annotation_font=dict(size=10, color="#92400E"),
        )
        fig2.add_vrect(
            x0="2023-11-01", x1="2024-03-01",
            fillcolor="#EFF6FF", opacity=0.55, layer="below", line_width=0,
            annotation_text="Winter", annotation_position="top left",
            annotation_font=dict(size=10, color="#1E40AF"),
        )
        apply_chart_style(fig2, "Monthly Maintenance Spend ($)", "Amber = summer · Blue = winter demand seasons")
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Fleet growth — full width
    growth = (
        veh.groupby(veh["acquired_date"].dt.to_period("M"))
        .size().reset_index(name="added")
    )
    growth["acquired_date"] = growth["acquired_date"].dt.to_timestamp()
    growth["cumulative"]    = growth["added"].cumsum()

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(
        go.Bar(
            x=growth["acquired_date"], y=growth["added"],
            name="Added This Month", marker_color="#BFDBFE",
        ),
        secondary_y=False,
    )
    fig3.add_trace(
        go.Scatter(
            x=growth["acquired_date"], y=growth["cumulative"],
            name="Total Fleet Size", line=dict(color="#1D4ED8", width=2.5),
            mode="lines+markers", marker=dict(size=4),
        ),
        secondary_y=True,
    )
    apply_chart_style(fig3, "Fleet Growth Trajectory", "Monthly acquisitions vs cumulative fleet size")
    fig3.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        margin=dict(t=65, b=60, l=0, r=10),
    )
    fig3.update_yaxes(title_text="Vehicles Added", secondary_y=False, title_font=dict(size=11, color="#94A3B8"))
    fig3.update_yaxes(title_text="Cumulative Fleet", secondary_y=True, title_font=dict(size=11, color="#94A3B8"))
    st.plotly_chart(fig3, use_container_width=True)

    insight(
        "<strong>Engine repairs account for 40%+ of total maintenance spend</strong> — disproportionate to "
        "their frequency, indicating high per-event cost. Winter months (Nov–Feb) correlate with elevated "
        "brake and engine repair events. A predictive maintenance trigger based on mileage and vehicle age "
        "for assets entering their 4th year could shift spend from reactive to scheduled, reducing both cost "
        "and unplanned downtime days."
    )


# ── Footer
st.markdown(
    "<p style='text-align:center;color:#94A3B8;font-size:12px;"
    "margin-top:40px;padding-top:16px;border-top:1px solid #E2E8F0'>"
    "Built by Damarius McNair · "
    "<a href='https://github.com/DCodeBase-X' style='color:#94A3B8'>GitHub</a>"
    "</p>",
    unsafe_allow_html=True,
)

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
import numpy as np
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

# ── Paths
DATA_DIR     = os.path.join(os.path.dirname(__file__), "..", "data")
GENERATE_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "data", "generate_data.py")
DATA_FILES   = {
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

# ── Sidebar header
st.sidebar.title("Fleet Ops Analytics")
st.sidebar.caption("Data-first operations intelligence")
st.sidebar.divider()

# ── Data management
st.sidebar.subheader("Data")

if not _data_exists():
    st.sidebar.warning("No data files found.")
    st.sidebar.caption("Generate the dataset to get started.")
    if st.sidebar.button("Generate Data", type="primary", use_container_width=True):
        _run_generator()
    st.info("No fleet data found. Use the **Generate Data** button in the sidebar to create it.")
    st.stop()
else:
    # Show last-modified timestamp of the most recently written file
    newest_mtime = max(
        os.path.getmtime(os.path.join(DATA_DIR, f)) for f in DATA_FILES
    )
    last_generated = datetime.datetime.fromtimestamp(newest_mtime).strftime("%b %d, %Y %H:%M")
    st.sidebar.caption(f"Last generated: {last_generated}")
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

locations     = ["All Locations"] + sorted(util["location"].unique().tolist())
selected_loc  = st.sidebar.selectbox("Location", locations)
date_range    = st.sidebar.date_input(
    "Date Range",
    value=(util["date"].min().date(), util["date"].max().date()),
    min_value=util["date"].min().date(),
    max_value=util["date"].max().date(),
)

# Apply filters
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

OT_PREMIUM = 28.0  # blended $/hr overtime premium

# ── Navigation tabs 
tab1, tab2, tab3, tab4 = st.tabs([
    "Executive Overview",
    "Overtime Analysis",
    "Fleet Utilization",
    "Maintenance & Capacity",
])

 
# TAB 1 — EXECUTIVE OVERVIEW
 
with tab1:
    st.header("Executive Overview")
    st.caption("Top-line KPIs across the filtered period and location.")

    # KPI calculations
    avg_util     = u_f["utilization_rate"].mean() * 100
    total_ot_hrs = o_f["overtime_hours"].sum()
    ot_cost      = total_ot_hrs * OT_PREMIUM
    total_maint  = m_f["cost"].sum()
    fleet_count  = u_f["vehicle_id"].nunique()

    # Baseline (full dataset) for delta context
    baseline_util = util["utilization_rate"].mean() * 100
    baseline_ot   = ot["overtime_hours"].mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Fleet Size",          f"{fleet_count:,} vehicles")
    k2.metric("Avg Utilization",     f"{avg_util:.1f}%",
              delta=f"{avg_util - baseline_util:+.1f}pp vs overall",
              delta_color="normal")
    k3.metric("Total OT Cost",       f"${ot_cost:,.0f}",
              delta=f"${(o_f['overtime_hours'].mean() - baseline_ot) * OT_PREMIUM:+,.2f}/shift vs baseline",
              delta_color="inverse")
    k4.metric("Maintenance Spend",   f"${total_maint:,.0f}")

    st.divider()

    col_a, col_b = st.columns(2)

    # Monthly utilization trend
    with col_a:
        monthly_util = (
            u_f.groupby(u_f["date"].dt.to_period("M"))["utilization_rate"]
            .mean().reset_index()
        )
        monthly_util["date"] = monthly_util["date"].dt.to_timestamp()
        monthly_util["util_pct"] = monthly_util["utilization_rate"] * 100

        fig = px.area(
            monthly_util, x="date", y="util_pct",
            title="Monthly Fleet Utilization (%)",
            labels={"util_pct": "Utilization %", "date": ""},
            color_discrete_sequence=["#4F46E5"],
        )
        fig.add_hline(y=80, line_dash="dash", line_color="#10B981",
                      annotation_text="Target 80%")
        fig.update_layout(showlegend=False, margin=dict(t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # OT cost by location
    with col_b:
        ot_by_loc = (
            o_f.groupby("location")["overtime_hours"]
            .sum().reset_index()
            .rename(columns={"overtime_hours": "ot_hours"})
        )
        ot_by_loc["ot_cost"] = ot_by_loc["ot_hours"] * OT_PREMIUM
        ot_by_loc = ot_by_loc.sort_values("ot_cost", ascending=True)

        fig2 = px.bar(
            ot_by_loc, x="ot_cost", y="location", orientation="h",
            title="Overtime Cost by Location ($)",
            labels={"ot_cost": "OT Cost ($)", "location": ""},
            color="ot_cost",
            color_continuous_scale=["#E0E7FF", "#4F46E5"],
        )
        fig2.update_layout(coloraxis_showscale=False, margin=dict(t=40, b=0))
        st.plotly_chart(fig2, use_container_width=True)


 
# TAB 2 — OVERTIME ANALYSIS
 
with tab2:
    st.header("Overtime Analysis")
    st.caption("Root-cause breakdown of overtime cost drivers by location, role, and time.")

    # Summary row
    m1, m2, m3 = st.columns(3)
    m1.metric("Total OT Hours",  f"{total_ot_hrs:,.0f} hrs")
    m2.metric("Total OT Cost",   f"${ot_cost:,.0f}")
    m3.metric("Avg OT/Shift",    f"{o_f['overtime_hours'].mean():.2f} hrs")

    st.divider()

    col1, col2 = st.columns(2)

    # OT by role
    with col1:
        ot_role = (
            o_f.groupby("role")["overtime_hours"]
            .agg(["sum", "mean"]).reset_index()
            .rename(columns={"sum": "total_ot", "mean": "avg_ot"})
            .sort_values("total_ot", ascending=False)
        )
        ot_role["cost"] = ot_role["total_ot"] * OT_PREMIUM

        fig = px.bar(
            ot_role, x="role", y="cost",
            title="OT Cost by Role",
            labels={"cost": "OT Cost ($)", "role": ""},
            color="cost",
            color_continuous_scale=["#E0E7FF", "#4F46E5"],
        )
        fig.update_layout(coloraxis_showscale=False,
                          xaxis_tickangle=-30, margin=dict(t=40, b=60))
        st.plotly_chart(fig, use_container_width=True)

    # Weekly pattern — includes weekend shifts present in summer months
    with col2:
        o_f_copy = o_f.copy()
        o_f_copy["day"] = o_f_copy["date"].dt.day_name()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        ot_day = (
            o_f_copy.groupby("day")["overtime_hours"].mean().reset_index()
        )
        ot_day["day"] = pd.Categorical(ot_day["day"], categories=day_order, ordered=True)
        ot_day = ot_day.sort_values("day")

        fig2 = px.bar(
            ot_day, x="day", y="overtime_hours",
            title="Avg OT Hours by Day of Week",
            labels={"overtime_hours": "Avg OT Hours", "day": ""},
            color="overtime_hours",
            color_continuous_scale=["#E0E7FF", "#4F46E5"],
        )
        fig2.update_layout(coloraxis_showscale=False, margin=dict(t=40, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    # Monthly OT trend
    st.subheader("Monthly Overtime Trend")
    monthly_ot = (
        o_f.groupby(o_f["date"].dt.to_period("M"))["overtime_hours"]
        .sum().reset_index()
    )
    monthly_ot["date"]    = monthly_ot["date"].dt.to_timestamp()
    monthly_ot["ot_cost"] = monthly_ot["overtime_hours"] * OT_PREMIUM

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(
        go.Bar(x=monthly_ot["date"], y=monthly_ot["overtime_hours"],
               name="OT Hours", marker_color="#C7D2FE"),
        secondary_y=False,
    )
    fig3.add_trace(
        go.Scatter(x=monthly_ot["date"], y=monthly_ot["ot_cost"],
                   name="OT Cost ($)", line=dict(color="#4F46E5", width=2.5)),
        secondary_y=True,
    )
    fig3.update_layout(
        title="Monthly Overtime Hours & Cost",
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=60, b=80),
    )
    fig3.update_yaxes(title_text="OT Hours", secondary_y=False)
    fig3.update_yaxes(title_text="OT Cost ($)", secondary_y=True)
    st.plotly_chart(fig3, use_container_width=True)


 
# TAB 3 — FLEET UTILIZATION
 
with tab3:
    st.header("Fleet Utilization")
    st.caption("Vehicle availability, efficiency rates, and idle asset identification.")

    u1, u2, u3 = st.columns(3)
    u1.metric("Avg Utilization",      f"{avg_util:.1f}%")
    u2.metric("Vehicles > 90% Util",  f"{(u_f.groupby('vehicle_id')['utilization_rate'].mean() >= 0.90).sum():,}")
    u3.metric("Vehicles < 50% Util",  f"{(u_f.groupby('vehicle_id')['utilization_rate'].mean() < 0.50).sum():,}")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        util_by_type = (
            u_f.groupby("vehicle_type")["utilization_rate"]
            .mean().reset_index()
        )
        util_by_type["util_pct"] = util_by_type["utilization_rate"] * 100
        util_by_type = util_by_type.sort_values("util_pct", ascending=False)

        fig = px.bar(
            util_by_type, x="vehicle_type", y="util_pct",
            title="Avg Utilization by Vehicle Type (%)",
            labels={"util_pct": "Utilization %", "vehicle_type": ""},
            color="util_pct",
            color_continuous_scale=["#ECFDF5", "#10B981"],
            range_y=[0, 100],
        )
        fig.add_hline(y=80, line_dash="dash", line_color="#4F46E5",
                      annotation_text="Target 80%")
        fig.update_layout(coloraxis_showscale=False, margin=dict(t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        util_by_loc = (
            u_f.groupby("location")["utilization_rate"]
            .mean().reset_index()
        )
        util_by_loc["util_pct"] = util_by_loc["utilization_rate"] * 100
        util_by_loc = util_by_loc.sort_values("util_pct", ascending=False)

        fig2 = px.bar(
            util_by_loc, x="location", y="util_pct",
            title="Avg Utilization by Location (%)",
            labels={"util_pct": "Utilization %", "location": ""},
            color="util_pct",
            color_continuous_scale=["#ECFDF5", "#10B981"],
            range_y=[0, 100],
        )
        fig2.add_hline(y=80, line_dash="dash", line_color="#4F46E5",
                       annotation_text="Target 80%")
        fig2.update_layout(coloraxis_showscale=False, margin=dict(t=40, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    # Seasonal demand by vehicle type — shows summer Compact/Mid-Size spike vs winter SUV/Truck rise
    st.subheader("Seasonal Demand by Vehicle Type")
    seasonal_type = (
        u_f.assign(month=u_f["date"].dt.strftime("%b"),
                   month_num=u_f["date"].dt.month)
        .groupby(["month_num", "month", "vehicle_type"])["utilization_rate"]
        .mean().reset_index()
    )
    seasonal_type["util_pct"] = seasonal_type["utilization_rate"] * 100
    seasonal_type = seasonal_type.sort_values("month_num")

    fig_s = px.line(
        seasonal_type, x="month", y="util_pct", color="vehicle_type",
        title="Avg Utilization by Vehicle Type — Seasonal Pattern (%)",
        labels={"util_pct": "Utilization %", "month": "", "vehicle_type": "Type"},
        markers=True,
        color_discrete_sequence=["#4F46E5", "#818CF8", "#10B981", "#F59E0B", "#EF4444"],
    )
    fig_s.update_layout(margin=dict(t=40, b=0))
    st.plotly_chart(fig_s, use_container_width=True)

    # Heat map — utilization by month × location
    st.subheader("Utilization Heatmap — Month × Location")
    heat_data = (
        u_f.groupby([u_f["date"].dt.to_period("M").astype(str), "location"])
        ["utilization_rate"].mean().unstack("location") * 100
    )
    fig3 = px.imshow(
        heat_data.T,
        color_continuous_scale=["#FEF9C3", "#4F46E5"],
        aspect="auto",
        labels=dict(x="Month", y="Location", color="Util %"),
        title="Fleet Utilization (%) — Monthly × Location",
    )
    fig3.update_layout(margin=dict(t=50, b=0))
    st.plotly_chart(fig3, use_container_width=True)


 
# TAB 4 — MAINTENANCE & CAPACITY
 
with tab4:
    st.header("Maintenance & Capacity Planning")
    st.caption("Downtime impact, maintenance cost breakdown, and fleet growth tracking.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Maintenance Cost",  f"${total_maint:,.0f}")
    c2.metric("Maintenance Events",      f"{len(m_f):,}")
    c3.metric("Total Downtime Days",     f"{m_f['downtime_days'].sum():,.0f}")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        cost_by_type = (
            m_f.groupby("maintenance_type")["cost"]
            .sum().reset_index().sort_values("cost", ascending=False)
        )
        fig = px.pie(
            cost_by_type, values="cost", names="maintenance_type",
            title="Maintenance Cost by Type",
            color_discrete_sequence=px.colors.sequential.Purples_r,
            hole=0.4,
        )
        fig.update_layout(margin=dict(t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        maint_monthly = (
            m_f.groupby(m_f["date"].dt.to_period("M"))["cost"]
            .sum().reset_index()
        )
        maint_monthly["date"] = maint_monthly["date"].dt.to_timestamp()

        fig2 = px.line(
            maint_monthly, x="date", y="cost",
            title="Monthly Maintenance Spend ($)",
            labels={"cost": "Cost ($)", "date": ""},
            color_discrete_sequence=["#818CF8"],
        )
        fig2.update_traces(line_width=2.5)
        fig2.update_layout(margin=dict(t=40, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    # Fleet growth over time
    st.subheader("Fleet Growth Trajectory")
    growth = (
        veh.groupby(veh["acquired_date"].dt.to_period("M"))
        .size().reset_index(name="added")
    )
    growth["acquired_date"] = growth["acquired_date"].dt.to_timestamp()
    growth["cumulative"]    = growth["added"].cumsum()

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(
        go.Bar(x=growth["acquired_date"], y=growth["added"],
               name="Added", marker_color="#C7D2FE"),
        secondary_y=False,
    )
    fig3.add_trace(
        go.Scatter(x=growth["acquired_date"], y=growth["cumulative"],
                   name="Total Fleet", line=dict(color="#4F46E5", width=2.5)),
        secondary_y=True,
    )
    fig3.update_layout(
        title="Fleet Size Growth Over Time",
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=60, b=80),
    )
    fig3.update_yaxes(title_text="Vehicles Added", secondary_y=False)
    fig3.update_yaxes(title_text="Cumulative Fleet Size", secondary_y=True)
    st.plotly_chart(fig3, use_container_width=True)


# ── Footer 
st.sidebar.divider()
st.sidebar.caption("Built by Damarius McNair · [GitHub](https://github.com/DCodeBase-X)")

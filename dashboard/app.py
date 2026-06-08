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

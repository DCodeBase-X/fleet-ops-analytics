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
    util = pd.read_csv(os.path.join(DATA_DIR, "daily_utilization.csv"), parse_dates=["date"])
    ot = pd.read_csv(os.path.join(DATA_DIR, "staff_overtime.csv"), parse_dates=["date"])
    maint = pd.read_csv(os.path.join(DATA_DIR, "maintenance_records.csv"), parse_dates=["date"])
    veh = pd.read_csv(os.path.join(DATA_DIR, "fleet_vehicles.csv"), parse_dates=["acquired_date"])

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
    avg_util = filtered.util["utilization_pct"].mean() if not filtered.util.empty else 0.0
    baseline_util = data.util["utilization_pct"].mean() if not data.util.empty else 0.0

    total_ot_hrs = filtered.ot["overtime_hours"].sum() if not filtered.ot.empty else 0.0
    ot_cost = total_ot_hrs * OT_PREMIUM

    months_filtered = max(filtered.ot["month_period"].nunique(), 1)
    months_total = max(data.ot["month_period"].nunique(), 1)
    avg_monthly = ot_cost / months_filtered
    baseline_monthly = (data.ot["overtime_hours"].sum() * OT_PREMIUM) / months_total if not data.ot.empty else 0.0
    ratio = (avg_monthly - baseline_monthly) / baseline_monthly if baseline_monthly > 0 else 0.0

    avg_ot_shift = filtered.ot["overtime_hours"].mean() if not filtered.ot.empty else 0.0
    baseline_ot = data.ot["overtime_hours"].mean() if not data.ot.empty else 0.0
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

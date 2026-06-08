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

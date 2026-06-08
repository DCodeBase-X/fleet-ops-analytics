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

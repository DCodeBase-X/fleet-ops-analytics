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
    result = pd.cut(
        pct_series,
        bins=[-1, 60, 80, float("inf")],
        labels=[COLORS["red"], COLORS["amber"], COLORS["green"]],
        right=False,
    )
    return [COLORS["red"] if pd.isna(c) else str(c) for c in result]


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
            x0="2024-06-01", x1=min(end, pd.Timestamp("2024-09-01")).strftime("%Y-%m-%d"),
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
            x0="2024-06-01", x1=min(end, pd.Timestamp("2024-09-01")).strftime("%Y-%m-%d"),
            fillcolor=COLORS["amber"], opacity=0.07, layer="below", line_width=0,
        )
    apply_chart_style(fig, "Monthly Overtime Hours & Cost")
    fig.update_yaxes(showgrid=False, secondary_y=True)
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
    fig = apply_chart_style(
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
    if end >= pd.Timestamp("2023-11-01"):
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
    fig.update_yaxes(showgrid=False, secondary_y=True)
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

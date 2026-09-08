"""
Reusable Plotly chart factory for Soft Rent a Car.
All charts respect the brand theme and dark background.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from app.style import (
    PLOTLY_TEMPLATE, PLOTLY_COLORS, BRAND_COLOR, BRAND_DARK,
    BRAND_ACCENT, BRAND_GOLD, SUCCESS_COLOR, WARNING_COLOR, DANGER_COLOR,
)

_BG      = "rgba(0,0,0,0)"
_GRID    = "rgba(255,255,255,0.06)"
_TEXT    = "#c8dff0"
_FONT    = dict(family="Inter", color=_TEXT, size=12)


def _base_layout(**kwargs) -> dict:
    return dict(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=_BG,
        plot_bgcolor=_BG,
        font=_FONT,
        colorway=PLOTLY_COLORS,
        margin=dict(l=14, r=14, t=40, b=14),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=_TEXT, size=11),
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
        ),
        xaxis=dict(gridcolor=_GRID, linecolor=_GRID, tickfont=dict(color=_TEXT)),
        yaxis=dict(gridcolor=_GRID, linecolor=_GRID, tickfont=dict(color=_TEXT)),
        **kwargs,
    )


# ── Revenue charts ────────────────────────────────────────────────────

def revenue_trend(df: pd.DataFrame) -> go.Figure:
    """Monthly billed vs collected area chart."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["total_billed"],
        name="Total Billed", fill="tozeroy",
        fillcolor="rgba(230,57,70,0.15)",
        line=dict(color=BRAND_COLOR, width=2.5),
        mode="lines+markers",
        marker=dict(size=5),
    ))
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["total_collected"],
        name="Collected", fill="tozeroy",
        fillcolor="rgba(42,157,143,0.15)",
        line=dict(color=SUCCESS_COLOR, width=2),
        mode="lines+markers",
        marker=dict(size=4),
    ))
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["outstanding"],
        name="Outstanding", fill="tozeroy",
        fillcolor="rgba(231,111,81,0.12)",
        line=dict(color=DANGER_COLOR, width=1.5, dash="dot"),
        mode="lines",
    ))
    fig.update_layout(**_base_layout(title="Monthly Revenue Trend (PKR)"))
    fig.update_xaxes(tickangle=-45)
    return fig


def revenue_by_booking_type(trips_df: pd.DataFrame) -> go.Figure:
    g = trips_df[trips_df["status"] == "Completed"].groupby("booking_type")["revenue_pkr"].sum().reset_index()
    g = g.sort_values("revenue_pkr", ascending=True)
    fig = go.Figure(go.Bar(
        x=g["revenue_pkr"], y=g["booking_type"],
        orientation="h",
        marker=dict(
            color=g["revenue_pkr"],
            colorscale=[[0, BRAND_DARK], [0.5, BRAND_ACCENT], [1, BRAND_COLOR]],
            showscale=False,
        ),
        text=[f"PKR {v:,.0f}" for v in g["revenue_pkr"]],
        textposition="outside",
        textfont=dict(color=_TEXT, size=10),
    ))
    fig.update_layout(**_base_layout(title="Revenue by Booking Type"))
    return fig


def fleet_revenue_pie(trips_df: pd.DataFrame, fleets_df: pd.DataFrame) -> go.Figure:
    g = trips_df[trips_df["status"] == "Completed"].groupby("fleet_id")["revenue_pkr"].sum().reset_index()
    g = g.merge(fleets_df[["fleet_id", "fleet_name"]], on="fleet_id", how="left")
    fig = go.Figure(go.Pie(
        labels=g["fleet_name"], values=g["revenue_pkr"],
        hole=0.52,
        marker=dict(colors=PLOTLY_COLORS, line=dict(color="#0f1117", width=2)),
        textfont=dict(color="#ffffff", size=11),
    ))
    fig.update_layout(**_base_layout(title="Revenue Share by Fleet"))
    return fig


# ── Trip / Operations ─────────────────────────────────────────────────

def trips_heatmap(trips_df: pd.DataFrame) -> go.Figure:
    """Bookings by hour × day-of-week heatmap."""
    dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    pivot = trips_df.groupby(["pickup_dow", "pickup_hour"]).size().reset_index(name="count")
    pivot["pickup_dow"] = pd.Categorical(pivot["pickup_dow"], categories=dow_order, ordered=True)
    pivot = pivot.sort_values(["pickup_dow", "pickup_hour"])
    matrix = pivot.pivot(index="pickup_dow", columns="pickup_hour", values="count").fillna(0)

    fig = go.Figure(go.Heatmap(
        z=matrix.values,
        x=[f"{h:02d}:00" for h in matrix.columns],
        y=matrix.index.tolist(),
        colorscale=[[0, "#0f1117"], [0.3, BRAND_DARK], [0.7, BRAND_ACCENT], [1, BRAND_COLOR]],
        hoverongaps=False,
        showscale=True,
    ))
    fig.update_layout(**_base_layout(title="Booking Demand – Hour × Day of Week"))
    return fig


def booking_type_trend(trips_df: pd.DataFrame) -> go.Figure:
    g = trips_df.groupby(["pickup_month", "booking_type"]).size().reset_index(name="count")
    fig = px.area(
        g, x="pickup_month", y="count", color="booking_type",
        title="Booking Volume by Type (Monthly)",
        color_discrete_sequence=PLOTLY_COLORS,
    )
    fig.update_layout(**_base_layout())
    fig.update_xaxes(tickangle=-45)
    return fig


def city_demand_bar(trips_df: pd.DataFrame) -> go.Figure:
    g = trips_df.groupby("pickup_city").size().reset_index(name="trips")
    g = g.sort_values("trips", ascending=False).head(12)
    fig = go.Figure(go.Bar(
        x=g["pickup_city"], y=g["trips"],
        marker_color=BRAND_COLOR,
        opacity=0.85,
    ))
    fig.update_layout(**_base_layout(title="Trip Volume by Pickup City"))
    return fig


def trip_status_funnel(trips_df: pd.DataFrame) -> go.Figure:
    counts = trips_df["status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    colors = {
        "Completed":   SUCCESS_COLOR,
        "Cancelled":   DANGER_COLOR,
        "In Progress": WARNING_COLOR,
        "No Show":     BRAND_ACCENT,
    }
    fig = go.Figure(go.Funnel(
        y=counts["status"],
        x=counts["count"],
        marker=dict(color=[colors.get(s, BRAND_COLOR) for s in counts["status"]]),
        textinfo="value+percent initial",
        textfont=dict(color="#ffffff"),
    ))
    fig.update_layout(**_base_layout(title="Trip Status Funnel"))
    return fig


# ── Fleet & Vehicles ──────────────────────────────────────────────────

def vehicle_utilisation_gauge(utilisation_pct: float, label: str = "Fleet Utilisation") -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=utilisation_pct,
        delta=dict(reference=70, valueformat=".1f"),
        number=dict(suffix="%", font=dict(size=36, color=_TEXT)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor=_GRID),
            bar=dict(color=BRAND_COLOR, thickness=0.25),
            bgcolor=BRAND_DARK,
            borderwidth=1,
            bordercolor=BRAND_ACCENT,
            steps=[
                dict(range=[0,  40], color="rgba(231,111,81,0.25)"),
                dict(range=[40, 70], color="rgba(233,196,106,0.20)"),
                dict(range=[70,100], color="rgba(42,157,143,0.20)"),
            ],
            threshold=dict(line=dict(color=SUCCESS_COLOR, width=3), thickness=0.8, value=75),
        ),
        title=dict(text=label, font=dict(color=_TEXT, size=13)),
    ))
    fig.update_layout(paper_bgcolor=_BG, margin=dict(l=20, r=20, t=30, b=10))
    return fig


def vehicle_status_donut(vehicles_df: pd.DataFrame) -> go.Figure:
    g = vehicles_df["status"].value_counts().reset_index()
    g.columns = ["status", "count"]
    color_map = {
        "Available":       SUCCESS_COLOR,
        "On Trip":         BRAND_COLOR,
        "Under Maintenance": WARNING_COLOR,
        "Reserved":        BRAND_ACCENT,
        "Retired":         "#444",
    }
    fig = go.Figure(go.Pie(
        labels=g["status"],
        values=g["count"],
        hole=0.55,
        marker=dict(
            colors=[color_map.get(s, BRAND_ACCENT) for s in g["status"]],
            line=dict(color="#0f1117", width=2),
        ),
        textfont=dict(color="#fff", size=11),
    ))
    fig.update_layout(**_base_layout(title="Vehicle Fleet Status"))
    return fig


def maintenance_cost_waterfall(maint_df: pd.DataFrame) -> go.Figure:
    g = maint_df.groupby("maintenance_type")["total_cost_pkr"].sum().reset_index()
    g = g.sort_values("total_cost_pkr", ascending=False).head(10)
    fig = go.Figure(go.Bar(
        x=g["maintenance_type"],
        y=g["total_cost_pkr"],
        marker_color=PLOTLY_COLORS[:len(g)],
        text=[f"PKR {v:,.0f}" for v in g["total_cost_pkr"]],
        textposition="outside",
        textfont=dict(color=_TEXT, size=9),
    ))
    fig.update_layout(**_base_layout(title="Maintenance Cost by Type (PKR)"))
    fig.update_xaxes(tickangle=-30)
    return fig


def fuel_efficiency_trend(fuel_df: pd.DataFrame) -> go.Figure:
    g = fuel_df.groupby("fill_month").agg(
        avg_eff=("fuel_efficiency_kmpl", "mean"),
        total_litres=("litres_filled", "sum"),
        total_cost=("fuel_cost_pkr", "sum"),
    ).reset_index()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=g["fill_month"], y=g["avg_eff"],
        name="Avg Efficiency (km/l)",
        line=dict(color=SUCCESS_COLOR, width=2.5),
        mode="lines+markers",
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=g["fill_month"], y=g["total_cost"],
        name="Fuel Cost (PKR)",
        marker_color=f"rgba(230,57,70,0.45)",
    ), secondary_y=True)
    fig.update_yaxes(title_text="km/l",   secondary_y=False, gridcolor=_GRID, tickfont=dict(color=_TEXT))
    fig.update_yaxes(title_text="PKR",    secondary_y=True,  gridcolor=_GRID, tickfont=dict(color=_TEXT))
    fig.update_layout(**_base_layout(title="Fuel Efficiency vs Cost Trend"))
    fig.update_xaxes(tickangle=-45)
    return fig


# ── Driver / Telematics ───────────────────────────────────────────────

def driver_safety_scatter(summary_df: pd.DataFrame) -> go.Figure:
    profile_colors = {
        "excellent": SUCCESS_COLOR,
        "good":      BRAND_ACCENT,
        "average":   WARNING_COLOR,
        "poor":      DANGER_COLOR,
        "dangerous": "#ff2244",
    }
    fig = go.Figure()
    for profile, grp in summary_df.groupby("behavior_profile"):
        fig.add_trace(go.Scatter(
            x=grp["total_km"],
            y=grp["avg_safety_score"],
            mode="markers",
            name=profile.capitalize(),
            marker=dict(
                size=grp["total_trips"].clip(1, 300).apply(lambda x: 6 + x / 30),
                color=profile_colors.get(profile, BRAND_ACCENT),
                opacity=0.8,
                line=dict(width=1, color="#0f1117"),
            ),
            text=grp["full_name"],
            hovertemplate="<b>%{text}</b><br>Safety: %{y:.1f}<br>KM: %{x:,.0f}<extra></extra>",
        ))
    fig.add_hline(y=70, line_dash="dash", line_color=SUCCESS_COLOR,
                  annotation_text="Target ≥ 70", annotation_font_color=SUCCESS_COLOR)
    fig.update_layout(**_base_layout(
        title="Driver Safety Score vs KM Driven",
        xaxis_title="Total KM Driven",
        yaxis_title="Avg Safety Score",
    ))
    return fig


def telematics_radar(driver_row: pd.Series) -> go.Figure:
    categories = [
        "Safe Braking", "Smooth Accel", "Low Idle",
        "Speed Compliance", "Low Complaints", "Customer Rating"
    ]
    # Normalise each metric to 0-100 (higher = better)
    vals = [
        max(0, 100 - driver_row.get("harsh_brakes", 0) * 0.5),
        max(0, 100 - driver_row.get("harsh_accels", 0) * 0.5),
        max(0, 100 - driver_row.get("idle_min", 0) * 0.01),
        max(0, 100 - driver_row.get("speeding_km", 0) * 0.3),
        max(0, 100 - driver_row.get("complaints", 0) * 10),
        driver_row.get("avg_rating", 4) * 20,
    ]
    vals = [min(100, v) for v in vals]
    vals_closed = vals + [vals[0]]
    cats_closed = categories + [categories[0]]

    fig = go.Figure(go.Scatterpolar(
        r=vals_closed, theta=cats_closed,
        fill="toself",
        fillcolor=f"rgba(230,57,70,0.2)",
        line=dict(color=BRAND_COLOR, width=2),
        marker=dict(size=6, color=BRAND_COLOR),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(30,42,58,0.8)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor=_GRID, tickfont=dict(color=_TEXT, size=9)),
            angularaxis=dict(gridcolor=_GRID, tickfont=dict(color=_TEXT, size=10)),
        ),
        paper_bgcolor=_BG,
        font=_FONT,
        margin=dict(l=40, r=40, t=50, b=40),
        showlegend=False,
        title=dict(text="Driver KPI Radar", font=dict(color=_TEXT, size=13)),
    )
    return fig


def safety_score_distribution(telem_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=telem_df["safety_score"],
        nbinsx=30,
        marker_color=BRAND_COLOR,
        opacity=0.75,
        name="Safety Score",
    ))
    fig.add_vline(x=70, line_dash="dash", line_color=SUCCESS_COLOR,
                  annotation_text="Target 70", annotation_font_color=SUCCESS_COLOR)
    fig.add_vline(x=telem_df["safety_score"].mean(), line_dash="dot",
                  line_color=WARNING_COLOR,
                  annotation_text=f"Mean {telem_df['safety_score'].mean():.1f}",
                  annotation_font_color=WARNING_COLOR)
    fig.update_layout(**_base_layout(
        title="Safety Score Distribution",
        xaxis_title="Safety Score (0–100)",
        yaxis_title="Trips",
    ))
    return fig


# ── Forecasting ────────────────────────────────────────────────────────

def forecast_chart(historical: pd.Series, forecast: pd.Series,
                   lower: pd.Series = None, upper: pd.Series = None,
                   title: str = "Forecast") -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historical.index.astype(str), y=historical.values,
        name="Historical", line=dict(color=BRAND_ACCENT, width=2),
        mode="lines+markers", marker=dict(size=4),
    ))
    fig.add_trace(go.Scatter(
        x=forecast.index.astype(str), y=forecast.values,
        name="Forecast", line=dict(color=BRAND_COLOR, width=2.5, dash="dot"),
        mode="lines+markers", marker=dict(size=5, symbol="diamond"),
    ))
    if lower is not None and upper is not None:
        fig.add_trace(go.Scatter(
            x=list(forecast.index.astype(str)) + list(forecast.index.astype(str))[::-1],
            y=list(upper.values) + list(lower.values)[::-1],
            fill="toself",
            fillcolor="rgba(230,57,70,0.12)",
            line=dict(color="rgba(0,0,0,0)"),
            name="95% CI",
            showlegend=True,
        ))
    fig.update_layout(**_base_layout(title=title))
    return fig


# ── Financial ─────────────────────────────────────────────────────────

def opex_breakdown_stacked(opex_df: pd.DataFrame) -> go.Figure:
    pivot = opex_df.pivot_table(
        index="month_period", columns="category",
        values="amount_pkr", aggfunc="sum"
    ).fillna(0)
    fig = go.Figure()
    for i, col in enumerate(pivot.columns):
        fig.add_trace(go.Bar(
            x=pivot.index, y=pivot[col],
            name=col, marker_color=PLOTLY_COLORS[i % len(PLOTLY_COLORS)],
        ))
    fig.update_layout(
        **_base_layout(title="Monthly Operating Expenses by Category (PKR)"),
        barmode="stack",
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def payment_method_bar(inv_df: pd.DataFrame) -> go.Figure:
    g = inv_df.groupby("payment_method").agg(
        total=("total_amount_pkr","sum"),
        count=("invoice_id","count"),
    ).reset_index().sort_values("total", ascending=False)
    fig = go.Figure(go.Bar(
        x=g["payment_method"],
        y=g["total"],
        marker_color=PLOTLY_COLORS[:len(g)],
        text=[f"PKR {v:,.0f}" for v in g["total"]],
        textposition="outside", textfont=dict(color=_TEXT, size=10),
    ))
    fig.update_layout(**_base_layout(title="Revenue by Payment Method"))
    return fig


def profit_waterfall(rev: float, fuel: float, maint: float, salaries: float,
                     other_opex: float) -> go.Figure:
    gross   = rev
    profit  = rev - fuel - maint - salaries - other_opex
    fig = go.Figure(go.Waterfall(
        name="P&L",
        orientation="v",
        measure=["absolute","relative","relative","relative","relative","total"],
        x=["Revenue","Fuel","Maintenance","Salaries","Other OpEx","Net Profit"],
        y=[gross, -fuel, -maint, -salaries, -other_opex, profit],
        connector=dict(line=dict(color=_GRID, width=1)),
        increasing=dict(marker=dict(color=SUCCESS_COLOR)),
        decreasing=dict(marker=dict(color=DANGER_COLOR)),
        totals=dict(marker=dict(color=BRAND_ACCENT)),
        text=[f"PKR {abs(v)/1e6:.1f}M" for v in [gross,-fuel,-maint,-salaries,-other_opex,profit]],
        textposition="outside",
        textfont=dict(color=_TEXT),
    ))
    fig.update_layout(**_base_layout(title="P&L Waterfall (PKR)"))
    return fig


# ── Map ────────────────────────────────────────────────────────────────

def demand_map(trips_df: pd.DataFrame) -> go.Figure:
    g = trips_df[trips_df["status"] == "Completed"].groupby(
        ["pickup_city", "pickup_lat", "pickup_lon"]
    ).size().reset_index(name="trips")

    fig = go.Figure(go.Scattermap(
        lat=g["pickup_lat"],
        lon=g["pickup_lon"],
        mode="markers",
        marker=dict(
            size=g["trips"].apply(lambda x: min(50, max(10, x / 50))),
            color=g["trips"],
            colorscale=[[0, BRAND_DARK], [0.5, BRAND_ACCENT], [1, BRAND_COLOR]],
            showscale=True,
            opacity=0.8,
        ),
        text=g.apply(lambda r: f"{r['pickup_city']}: {r['trips']:,} trips", axis=1),
        hoverinfo="text",
    ))
    fig.update_layout(
        map=dict(
            style="carto-darkmatter",
            center=dict(lat=30.3753, lon=69.3451),
            zoom=4.5,
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor=_BG,
        title=dict(text="Demand Heat Map – Pakistan", font=dict(color=_TEXT, size=13)),
        height=420,
    )
    return fig

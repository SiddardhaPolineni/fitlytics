"""
Reusable Plotly chart builders.
All charts use transparent backgrounds so they adapt to both
Streamlit light mode and dark mode automatically.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from utils.theme import plotly_theme, PRIMARY, SECONDARY, SUCCESS, WARNING, NEUTRAL, CHART_COLORS

# Re-export constants consumed by page modules
MUTED    = "#8B92A5"   # used only as a fallback; CSS vars handle real theming
CARD_BG  = "rgba(0,0,0,0)"
BG       = "rgba(0,0,0,0)"
TEXT     = "currentColor"

# Alias so existing `from utils.charts import apply_template` still works
apply_template = plotly_theme


# ---------------------------------------------------------------------------
# Weight trend chart
# ---------------------------------------------------------------------------

def weight_trend_chart(df: pd.DataFrame, proj: pd.DataFrame | None = None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["weight_kg"],
        mode="lines", name="Daily Weight",
        line=dict(color="rgba(128,128,128,0.4)", width=1),
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["ma7"],
        mode="lines", name="7-Day MA",
        line=dict(color=PRIMARY, width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["ma30"],
        mode="lines", name="30-Day MA",
        line=dict(color=SUCCESS, width=2.5, dash="dash"),
    ))
    if proj is not None and not proj.empty:
        fig.add_trace(go.Scatter(
            x=proj["date"], y=proj["projected_weight"],
            mode="lines", name="Projection",
            line=dict(color=WARNING, width=2, dash="dot"),
        ))
    fig.update_layout(
        title="Weight Trend",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        hovermode="x unified",
    )
    return plotly_theme(fig)


# ---------------------------------------------------------------------------
# Training volume bar + trend line
# ---------------------------------------------------------------------------

def volume_bar_chart(df: pd.DataFrame, x_col: str, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df[x_col], y=df["total_volume"],
        marker_color=PRIMARY, name="Volume", opacity=0.85,
    ))
    if len(df) > 2:
        z = np.polyfit(range(len(df)), df["total_volume"], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=df[x_col], y=p(range(len(df))),
            mode="lines", name="Trend",
            line=dict(color=WARNING, width=2, dash="dash"),
        ))
    fig.update_layout(title=title, xaxis_title="Period", yaxis_title="Volume (kg)")
    return plotly_theme(fig)


# ---------------------------------------------------------------------------
# Muscle group donut
# ---------------------------------------------------------------------------

def muscle_donut(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=df["muscle_group"],
        values=df["total_volume"],
        hole=0.55,
        marker=dict(colors=CHART_COLORS[:len(df)]),
        textinfo="label+percent",
    ))
    fig.update_layout(title="Volume by Muscle Group", showlegend=False)
    return plotly_theme(fig)


# ---------------------------------------------------------------------------
# PR timeline
# ---------------------------------------------------------------------------

def pr_timeline(pr_df: pd.DataFrame) -> go.Figure:
    exercises = pr_df["exercise"].unique()
    colors = (px.colors.qualitative.Pastel * 3)[:len(exercises)]
    color_map = dict(zip(exercises, colors))
    fig = go.Figure()
    for ex in exercises:
        sub = pr_df[pr_df["exercise"] == ex].sort_values("date")
        fig.add_trace(go.Scatter(
            x=sub["date"], y=sub["estimated_1rm"],
            mode="lines+markers", name=ex,
            line=dict(color=color_map[ex], width=2),
            marker=dict(size=8),
            hovertemplate="%{x|%b %d}<br>Est. 1RM: %{y:.1f} kg<extra>" + ex + "</extra>",
        ))
    fig.update_layout(
        title="Estimated 1RM Progress Over Time",
        xaxis_title="Date", yaxis_title="Estimated 1RM (kg)",
        hovermode="x unified",
    )
    return plotly_theme(fig)


# ---------------------------------------------------------------------------
# Calendar heatmap (overview widget used on home page)
# ---------------------------------------------------------------------------

def calendar_heatmap(workouts: pd.DataFrame, health: pd.DataFrame) -> go.Figure:
    daily_vol = workouts.groupby(workouts["date"].dt.date)["volume"].sum()
    if health.empty:
        return go.Figure()
    start = health["date"].min().date()
    end   = health["date"].max().date()
    all_dates = pd.date_range(start, end, freq="D")
    vol_series = pd.Series([daily_vol.get(d.date(), 0) for d in all_dates], index=all_dates)
    max_vol = vol_series.max() if vol_series.max() > 0 else 1
    levels = (vol_series / max_vol * 4).round().astype(int)

    weeks: list[list] = []
    current_week: list = [None] * 7
    for d, level in zip(all_dates, levels):
        dow = d.dayofweek
        if dow == 0 and any(v is not None for v in current_week):
            weeks.append(current_week)
            current_week = [None] * 7
        current_week[dow] = int(level)
    weeks.append(current_week)

    z = np.array([[w[d] if w[d] is not None else -1 for w in weeks] for d in range(7)], dtype=float)
    z[z == -1] = np.nan

    # Colourscale works on both themes: from transparent → accent
    colorscale = [
        [0.0,  "rgba(108,99,255,0.05)"],
        [0.25, "rgba(108,99,255,0.2)"],
        [0.5,  "rgba(108,99,255,0.45)"],
        [0.75, "rgba(108,99,255,0.7)"],
        [1.0,  PRIMARY],
    ]
    fig = go.Figure(go.Heatmap(
        z=z, colorscale=colorscale, showscale=False,
        xgap=3, ygap=3,
        hovertemplate="Activity level: %{z:.0f}<extra></extra>",
    ))
    fig.update_yaxes(
        tickvals=list(range(7)),
        ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        autorange="reversed",
    )
    fig.update_layout(title="Workout Activity Heatmap", xaxis_title="Week", height=220)
    return plotly_theme(fig)


# ---------------------------------------------------------------------------
# Recovery radar
# ---------------------------------------------------------------------------

def recovery_radar(sleep_score: float, hrv_score: float, rhr_score: float) -> go.Figure:
    categories = ["Sleep", "HRV", "Resting HR", "Sleep"]
    values = [sleep_score, hrv_score, rhr_score, sleep_score]
    fig = go.Figure(go.Scatterpolar(
        r=values, theta=categories, fill="toself",
        fillcolor="rgba(108,99,255,0.2)",
        line=dict(color=PRIMARY, width=2),
        name="Recovery",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="rgba(128,128,128,0.25)",
            ),
            angularaxis=dict(gridcolor="rgba(128,128,128,0.25)"),
        ),
        showlegend=False,
        title="Recovery Breakdown",
        height=320,
    )
    return plotly_theme(fig)


# ---------------------------------------------------------------------------
# Gauge chart
# ---------------------------------------------------------------------------

def gauge_chart(value: float, title: str, max_val: float = 100,
                color: str = PRIMARY) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor="rgba(128,128,128,0.5)"),
            bar=dict(color=color),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=1,
            bordercolor="rgba(128,128,128,0.3)",
            steps=[
                dict(range=[0,           max_val * 0.35], color="rgba(231,76,60,0.12)"),
                dict(range=[max_val*0.35, max_val * 0.65], color="rgba(243,156,18,0.10)"),
                dict(range=[max_val*0.65, max_val],        color="rgba(46,204,113,0.10)"),
            ],
        ),
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
    return plotly_theme(fig)


# ---------------------------------------------------------------------------
# Exercise volume + weight over time (dual-axis)
# ---------------------------------------------------------------------------

def exercise_trend(workouts: pd.DataFrame, exercise: str) -> go.Figure:
    df = workouts[workouts["exercise"] == exercise].copy()
    df = df.groupby("date").agg(
        max_weight=("weight_kg", "max"),
        total_volume=("volume", "sum"),
    ).reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=df["date"], y=df["total_volume"],
        name="Volume", marker_color=PRIMARY, opacity=0.7,
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["max_weight"],
        name="Max Weight (kg)", mode="lines+markers",
        line=dict(color=WARNING, width=2),
    ), secondary_y=True)
    fig.update_layout(
        title=f"{exercise} — Volume & Weight Over Time",
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Volume (kg)", secondary_y=False)
    fig.update_yaxes(title_text="Max Weight (kg)", secondary_y=True)
    return plotly_theme(fig)

"""
Calendar Heatmap page — workout consistency and daily activity levels.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import date, timedelta

from utils.data_loader import load_workouts, load_health
from utils.charts import apply_template
from utils.theme import inject_theme, PRIMARY, SECONDARY, SUCCESS, WARNING
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Calendar Heatmap | Fitlytics", page_icon="📅", layout="wide")
inject_theme()
render_sidebar()

st.title("📅 Calendar Heatmap")
st.caption("See your training consistency at a glance — every workout day highlighted.")

# ── Data ─────────────────────────────────────────────────────────────────────
workouts    = load_workouts()
health      = load_health()

daily_vol   = workouts.groupby(workouts["date"].dt.date)["volume"].sum()
daily_steps = health.set_index(health["date"].dt.date)["steps"]
daily_sleep = health.set_index(health["date"].dt.date)["sleep_hours"]

start_date  = health["date"].min().date()
end_date    = health["date"].max().date()
all_dates   = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

total_days      = len(all_dates)
workout_days    = len(daily_vol)
adherence       = workout_days / total_days * 100
avg_workouts_wk = workout_days / max(total_days // 7, 1)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Days Tracked",   total_days)
k2.metric("Workout Days",         workout_days)
k3.metric("Adherence Rate",       f"{adherence:.1f}%")
k4.metric("Avg Workouts / Week",  f"{avg_workouts_wk:.1f}")

st.divider()

# ── Metric selector ───────────────────────────────────────────────────────────
metric_choice = st.radio(
    "Colour intensity represents:",
    ["Training Volume", "Daily Steps", "Sleep Hours"],
    horizontal=True,
)

# Colourscales use semi-transparent accent colours → work on both themes
CS_VOL   = [[0,"rgba(108,99,255,0.04)"],[0.01,"rgba(46,204,113,0.15)"],
             [0.3,"rgba(46,204,113,0.4)"],[0.7,SUCCESS],[1.0,PRIMARY]]
CS_STEPS = [[0,"rgba(108,99,255,0.04)"],[0.01,"rgba(243,156,18,0.15)"],
             [0.3,"rgba(243,156,18,0.4)"],[0.7,WARNING],[1.0,PRIMARY]]
CS_SLEEP = [[0,"rgba(108,99,255,0.04)"],[0.01,"rgba(255,101,132,0.15)"],
             [0.3,"rgba(255,101,132,0.4)"],[0.7,SECONDARY],[1.0,PRIMARY]]

if metric_choice == "Training Volume":
    values     = {d: daily_vol.get(d, 0) for d in all_dates}
    max_val    = max(values.values()) or 1
    colorscale = CS_VOL
    unit       = "kg volume"
elif metric_choice == "Daily Steps":
    values     = {d: daily_steps.get(d, 0) for d in all_dates}
    max_val    = max(values.values()) or 1
    colorscale = CS_STEPS
    unit       = "steps"
else:
    values     = {d: daily_sleep.get(d, 0) for d in all_dates}
    max_val    = 9
    colorscale = CS_SLEEP
    unit       = "hours sleep"

# ── Build GitHub-style heatmap grid ───────────────────────────────────────────
start_dow    = start_date.weekday()
padded_start = start_date - timedelta(days=start_dow)
grid_dates, current = [], padded_start
while current <= end_date:
    week = [current + timedelta(days=i) for i in range(7)]
    grid_dates.append(week)
    current += timedelta(days=7)

z, hover = [], []
for week in grid_dates:
    col_z, col_h = [], []
    for d in week:
        if d < start_date or d > end_date:
            col_z.append(np.nan); col_h.append("")
        else:
            v = values.get(d, 0)
            col_z.append(v / max_val if max_val > 0 else 0)
            col_h.append(f"{d.strftime('%b %d, %Y')}<br>{v:,.0f} {unit}")
    z.append(col_z); hover.append(col_h)

z_arr     = np.array(z).T
hover_arr = np.array(hover).T

fig_cal = go.Figure(go.Heatmap(
    z=z_arr, x=list(range(len(grid_dates))),
    colorscale=colorscale, showscale=True,
    xgap=2, ygap=2,
    customdata=hover_arr,
    hovertemplate="%{customdata}<extra></extra>",
    colorbar=dict(title=unit, tickformat=".0%"),
    zmin=0, zmax=1,
))
fig_cal.update_yaxes(
    tickvals=list(range(7)),
    ticktext=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
    autorange="reversed",
)
month_ticks, month_labels = [], []
for i, week in enumerate(grid_dates):
    if week[0].day <= 7:
        month_ticks.append(i)
        month_labels.append(week[0].strftime("%b %Y"))
fig_cal.update_xaxes(tickvals=month_ticks, ticktext=month_labels, tickangle=-30)
fig_cal.update_layout(
    title=f"Activity Heatmap — {metric_choice}", height=260,
    margin=dict(l=60, r=20, t=50, b=60),
)
apply_template(fig_cal)
st.plotly_chart(fig_cal, use_container_width=True)

st.divider()

# ── Monthly adherence ─────────────────────────────────────────────────────────
st.subheader("📊 Monthly Workout Adherence")

monthly_stats = []
health["month_period"] = health["date"].dt.to_period("M")
for period, _ in health.groupby("month_period"):
    month_dates = pd.date_range(period.start_time, period.end_time, freq="D").date
    wo_in_month = sum(1 for d in month_dates if d in daily_vol.index)
    adh = wo_in_month / len(month_dates) * 100
    monthly_stats.append({"month": str(period), "workout_days": wo_in_month,
                           "total_days": len(month_dates), "adherence_%": round(adh, 1)})

ms_df      = pd.DataFrame(monthly_stats)
colors_adh = [SUCCESS if a >= 70 else WARNING if a >= 40 else SECONDARY
              for a in ms_df["adherence_%"]]

fig_adh = go.Figure(go.Bar(
    x=ms_df["month"], y=ms_df["adherence_%"], marker_color=colors_adh,
    text=[f"{a:.0f}%" for a in ms_df["adherence_%"]], textposition="outside",
))
fig_adh.add_hline(y=70, line_dash="dash", line_color=SUCCESS,
                  annotation_text="70% target", annotation_position="top right")
fig_adh.update_layout(title="Monthly Workout Adherence (%)",
                      xaxis_title="Month", yaxis_title="Adherence (%)",
                      yaxis=dict(range=[0,110]), height=340)
apply_template(fig_adh)
st.plotly_chart(fig_adh, use_container_width=True)

st.divider()

# ── Day-of-week analysis ──────────────────────────────────────────────────────
st.subheader("📆 Activity by Day of Week")

workouts["dow"] = workouts["date"].dt.day_name()
dow_vol = (
    workouts.groupby("dow")
    .agg(total_vol=("volume","sum"), sessions=("date","nunique"))
    .reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
)

col_dl, col_dr = st.columns(2)
with col_dl:
    fig_dow = go.Figure(go.Bar(
        x=dow_vol.index, y=dow_vol["sessions"],
        marker_color=PRIMARY, opacity=0.85,
        text=dow_vol["sessions"], textposition="outside",
    ))
    fig_dow.update_layout(title="Workout Sessions by Day",
                          yaxis_title="Sessions", height=300)
    apply_template(fig_dow)
    st.plotly_chart(fig_dow, use_container_width=True)

with col_dr:
    fig_vdow = go.Figure(go.Bar(
        x=dow_vol.index, y=dow_vol["total_vol"],
        marker_color=WARNING, opacity=0.85,
        text=[f"{v:,.0f}" for v in dow_vol["total_vol"]],
        textposition="outside",
    ))
    fig_vdow.update_layout(title="Volume by Day of Week",
                           yaxis_title="Volume (kg)", height=300)
    apply_template(fig_vdow)
    st.plotly_chart(fig_vdow, use_container_width=True)

st.divider()

st.subheader("📋 Monthly Detail Table")
st.dataframe(
    ms_df.rename(columns={"month":"Month","workout_days":"Workout Days",
                           "total_days":"Total Days","adherence_%":"Adherence (%)"}),
    use_container_width=True, hide_index=True,
)

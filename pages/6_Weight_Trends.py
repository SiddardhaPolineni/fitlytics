"""
Weight Trend page — daily weight, moving averages, monthly change, projection.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

from utils.data_loader import load_health, load_goals
from utils.calculations import weight_moving_averages, weight_projection
from utils.charts import weight_trend_chart, apply_template
from utils.theme import inject_theme, PRIMARY, SECONDARY, SUCCESS, WARNING
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Weight Trends | Fitlytics", page_icon="⚖️", layout="wide")
inject_theme()
render_sidebar()

st.title("⚖️ Weight Trends")
st.caption("Your weight journey — smoothed, projected, and put in context.")

# ── Data ─────────────────────────────────────────────────────────────────────
health = load_health()
goals  = load_goals()

wma  = weight_moving_averages(health)
proj = weight_projection(health, days_ahead=30)

latest_weight = health["weight_kg"].iloc[-1]
start_weight  = health["weight_kg"].iloc[0]
total_lost    = start_weight - latest_weight

health["month"] = health["date"].dt.to_period("M")
monthly_avg    = health.groupby("month")["weight_kg"].mean()
monthly_change = monthly_avg.diff()

weight_goal   = goals[goals["goal_type"] == "weight_loss"]
target_weight = weight_goal["target_value"].values[0] if not weight_goal.empty else None

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Current Weight",     f"{latest_weight:.1f} kg")
k2.metric("Total Change",       f"{total_lost:+.1f} kg",       delta_color="inverse")
last_mc = monthly_change.iloc[-1] if not monthly_change.empty else 0
k3.metric("Last Month Change",  f"{last_mc:+.2f} kg",          delta_color="inverse")
if target_weight:
    k4.metric("To Goal Weight", f"{latest_weight - target_weight:+.1f} kg", delta_color="inverse")
else:
    k4.metric("7-Day MA",       f"{wma['ma7'].iloc[-1]:.2f} kg")

st.divider()

# ── Main chart ────────────────────────────────────────────────────────────────
st.subheader("📈 Weight Over Time")
fig = weight_trend_chart(wma, proj)
if target_weight:
    fig.add_hline(y=target_weight, line_dash="dot", line_color=SUCCESS,
                  annotation_text=f"Goal: {target_weight} kg",
                  annotation_position="bottom right",
                  annotation_font_color=SUCCESS)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Monthly breakdown ─────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📅 Monthly Average Weight")
    monthly_df = monthly_avg.reset_index()
    monthly_df.columns = ["Month", "Avg Weight (kg)"]
    monthly_df["Month"] = monthly_df["Month"].astype(str)
    monthly_df["Change (kg)"] = monthly_change.values

    fig_m = go.Figure()
    fig_m.add_trace(go.Bar(
        x=monthly_df["Month"], y=monthly_df["Avg Weight (kg)"],
        marker=dict(
            color=monthly_df["Avg Weight (kg)"],
            colorscale=[[0, SUCCESS],[1, SECONDARY]],
            showscale=False,
        ),
        text=[f"{v:.1f}" for v in monthly_df["Avg Weight (kg)"]],
        textposition="outside",
    ))
    x_idx = list(range(len(monthly_df)))
    if len(x_idx) > 1:
        z = np.polyfit(x_idx, monthly_df["Avg Weight (kg)"], 1)
        fig_m.add_trace(go.Scatter(
            x=monthly_df["Month"], y=np.poly1d(z)(x_idx),
            mode="lines", name="Trend",
            line=dict(color=WARNING, width=2, dash="dash"),
        ))
    fig_m.update_layout(title="Monthly Avg Weight", xaxis_title="Month",
                        yaxis_title="kg", height=320, showlegend=False)
    apply_template(fig_m)
    st.plotly_chart(fig_m, use_container_width=True)

with col_right:
    st.subheader("📉 Month-over-Month Change")
    change_df   = monthly_df.dropna(subset=["Change (kg)"])
    colors_bar  = [SUCCESS if v < 0 else SECONDARY for v in change_df["Change (kg)"]]
    fig_chg = go.Figure(go.Bar(
        x=change_df["Month"], y=change_df["Change (kg)"],
        marker_color=colors_bar,
        text=[f"{v:+.2f} kg" for v in change_df["Change (kg)"]],
        textposition="outside",
    ))
    fig_chg.add_hline(y=0, line_color="rgba(128,128,128,0.4)", line_width=1)
    fig_chg.update_layout(title="Monthly Weight Change", xaxis_title="Month",
                          yaxis_title="Change (kg)", height=320)
    apply_template(fig_chg)
    st.plotly_chart(fig_chg, use_container_width=True)

st.divider()

# ── Projection ────────────────────────────────────────────────────────────────
st.subheader("🔮 30-Day Weight Projection")
if not proj.empty:
    projected_end = proj["projected_weight"].iloc[-1]
    days_to_goal  = None
    if target_weight:
        below = proj[proj["projected_weight"] <= target_weight]
        if not below.empty:
            days_to_goal = (below.iloc[0]["date"] - pd.Timestamp.today()).days

    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("Projected in 30 days", f"{projected_end:.1f} kg")
    pc2.metric("Projected Change",     f"{projected_end - latest_weight:+.1f} kg", delta_color="inverse")
    if days_to_goal is not None:
        pc3.metric("Days to Goal Weight", f"~{max(days_to_goal,0)} days")
    elif target_weight:
        pc3.metric("Goal Reachable in 30d?", "❌ Not at current rate")

    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(
        x=wma["date"], y=wma["ma7"],
        name="7-Day MA", line=dict(color=PRIMARY, width=2.5),
    ))
    fig_proj.add_trace(go.Scatter(
        x=proj["date"], y=proj["projected_weight"],
        name="30-Day Projection", line=dict(color=WARNING, width=2.5, dash="dot"),
        fill="tozeroy", fillcolor="rgba(243,156,18,0.05)",
    ))
    if target_weight:
        fig_proj.add_hline(y=target_weight, line_dash="dash", line_color=SUCCESS,
                           annotation_text=f"Goal: {target_weight} kg")
    fig_proj.update_layout(title="Current Trend + 30-Day Projection",
                           xaxis_title="Date", yaxis_title="Weight (kg)",
                           hovermode="x unified", height=360)
    apply_template(fig_proj)
    st.plotly_chart(fig_proj, use_container_width=True)

st.divider()

# ── Distribution ──────────────────────────────────────────────────────────────
st.subheader("📊 Weight Distribution")
fig_hist = go.Figure(go.Histogram(
    x=health["weight_kg"], nbinsx=30, marker_color=PRIMARY, opacity=0.8,
))
fig_hist.add_vline(x=latest_weight, line_color=WARNING, line_dash="dash",
                   annotation_text="Current")
if target_weight:
    fig_hist.add_vline(x=target_weight, line_color=SUCCESS, line_dash="dash",
                       annotation_text="Goal")
fig_hist.update_layout(title="Distribution of Daily Weights",
                       xaxis_title="Weight (kg)", yaxis_title="Frequency", height=300)
apply_template(fig_hist)
st.plotly_chart(fig_hist, use_container_width=True)

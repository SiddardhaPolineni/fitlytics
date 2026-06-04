"""
Streaks page — consecutive workout, sleep, and step-goal streaks.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.data_loader import load_workouts, load_health
from utils.calculations import workout_streak, sleep_streak, steps_streak
from utils.charts import apply_template
from utils.theme import inject_theme, PRIMARY, SUCCESS, WARNING
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Streaks | Fitlytics", page_icon="🔥", layout="wide")
inject_theme()
render_sidebar()

st.title("🔥 Streaks")
st.caption("Stay consistent. Every day counts.")

# ── Data ─────────────────────────────────────────────────────────────────────
workouts = load_workouts()
health   = load_health()

wo_cur, wo_best = workout_streak(workouts)
sl_cur, sl_best = sleep_streak(health, target_hours=7.0)
st_cur, st_best = steps_streak(health, target=10_000)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
streaks = [
    (col1, "🏋️", "Workout Streak", wo_cur, wo_best, PRIMARY, "days with a workout"),
    (col2, "😴", "Sleep Streak",   sl_cur, sl_best, SUCCESS,  "days of 7+ h sleep"),
    (col3, "👟", "Steps Streak",   st_cur, st_best, WARNING,  "days hitting 10k steps"),
]
for col, icon, label, current, best, color, subtitle in streaks:
    with col:
        st.markdown(f"""
<div class="streak-card" style="border-top:3px solid {color}">
  <div class="streak-icon">{icon}</div>
  <div class="streak-num" style="color:{color}">{current}</div>
  <div style="font-size:1rem;font-weight:600;color:var(--text-primary);margin-top:0.2rem">{label}</div>
  <div class="streak-lbl">{subtitle}</div>
  <div class="streak-best">🏆 All-time best: {best} days</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Daily contributions bar chart ─────────────────────────────────────────────
st.subheader("📅 Daily Streak Contributions")

health_sorted = health.sort_values("date")
workouts_days = set(workouts["date"].dt.date.unique())

dates       = health_sorted["date"].dt.date.tolist()
workout_met = [1 if d in workouts_days else 0 for d in dates]
sleep_met   = (health_sorted["sleep_hours"] >= 7.0).astype(int).tolist()
steps_met   = (health_sorted["steps"] >= 10_000).astype(int).tolist()

fig = go.Figure()
fig.add_trace(go.Bar(x=health_sorted["date"], y=workout_met, name="Workout",  marker_color=PRIMARY, opacity=0.85))
fig.add_trace(go.Bar(x=health_sorted["date"], y=sleep_met,   name="Sleep ≥7h", marker_color=SUCCESS, opacity=0.7))
fig.add_trace(go.Bar(x=health_sorted["date"], y=steps_met,   name="Steps ≥10k", marker_color=WARNING, opacity=0.7))
fig.update_layout(
    barmode="stack", title="Daily Goal Achievement (stacked)",
    xaxis_title="Date", yaxis_title="Goals Met",
    yaxis=dict(tickvals=[0,1,2,3], ticktext=["0","1","2","3 ✓"]),
    hovermode="x unified", height=320,
)
apply_template(fig)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Running streak over time ───────────────────────────────────────────────────
st.subheader("📈 Running Streak Over Time")

def running_streak_series(bool_list):
    out, current = [], 0
    for v in bool_list:
        current = current + 1 if v else 0
        out.append(current)
    return out

dates_s  = pd.Series(health_sorted["date"].tolist())
wo_s     = running_streak_series(workout_met)
sl_s     = running_streak_series(sleep_met)
st_s     = running_streak_series(steps_met)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=dates_s, y=wo_s, name="Workout", line=dict(color=PRIMARY, width=2.5)))
fig2.add_trace(go.Scatter(x=dates_s, y=sl_s, name="Sleep",   line=dict(color=SUCCESS, width=2, dash="dash")))
fig2.add_trace(go.Scatter(x=dates_s, y=st_s, name="Steps",   line=dict(color=WARNING, width=2, dash="dot")))
fig2.update_layout(title="Streak Length Over Time", xaxis_title="Date",
                   yaxis_title="Consecutive Days", hovermode="x unified", height=320)
apply_template(fig2)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Milestone badges ──────────────────────────────────────────────────────────
st.subheader("🏅 Milestone Badges")
milestones = [
    ("7-day workout streak",  wo_best >= 7,  "🏋️"),
    ("30-day workout streak", wo_best >= 30, "💪"),
    ("7-day sleep streak",    sl_best >= 7,  "😴"),
    ("30-day sleep streak",   sl_best >= 30, "🌙"),
    ("7-day steps streak",    st_best >= 7,  "👟"),
    ("30-day steps streak",   st_best >= 30, "🏃"),
    ("Triple daily goal ×7",  sum(
        w and s and t for w, s, t in zip(workout_met, sleep_met, steps_met)
    ) >= 7, "🌟"),
]
badge_cols = st.columns(len(milestones))
for col, (label, achieved, icon) in zip(badge_cols, milestones):
    cls = "badge-achieved" if achieved else "badge-locked"
    col.markdown(f"""
<div class="{cls}">
  <div class="badge-icon">{icon}</div>
  <div class="badge-label">{label}</div>
</div>
""", unsafe_allow_html=True)

"""
Goal Tracking page — progress toward every fitness goal.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from datetime import date

from utils.data_loader import load_goals, load_health, load_workouts
from utils.calculations import goal_progress
from utils.charts import gauge_chart
from utils.theme import inject_theme, PRIMARY, SECONDARY, SUCCESS, WARNING
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Goal Tracking | Fitlytics", page_icon="🎯", layout="wide")
inject_theme()
render_sidebar()

st.title("🎯 Goal Tracking")
st.caption("Monitor your progress toward every fitness target.")

# ── Data ─────────────────────────────────────────────────────────────────────
goals_raw = load_goals()
health    = load_health()
workouts  = load_workouts()
goals     = goal_progress(goals_raw, health, workouts)

# ── Summary KPIs ──────────────────────────────────────────────────────────────
on_track  = (goals["pct_complete"] >= 50).sum()
completed = (goals["pct_complete"] >= 100).sum()
avg_pct   = goals["pct_complete"].mean()

k1, k2, k3 = st.columns(3)
k1.metric("Goals On Track (≥50%)", f"{on_track} / {len(goals)}")
k2.metric("Goals Completed",       f"{completed}")
k3.metric("Average Progress",      f"{avg_pct:.1f}%")

st.divider()

GOAL_ICONS = {"weight_loss": "⚖️", "strength": "🏋️", "cardio": "🏃", "body_composition": "📐", "HIIT": "⚡"}
BAR_COLORS = {"weight_loss": SECONDARY, "strength": PRIMARY, "cardio": SUCCESS, "body_composition": WARNING, "HIIT": "#9B59B6"}

filter_type = st.selectbox(
    "Filter by goal type",
    options=["All"] + sorted(goals["goal_type"].unique().tolist()),
)
if filter_type != "All":
    goals = goals[goals["goal_type"] == filter_type]

for _, g in goals.iterrows():
    icon  = GOAL_ICONS.get(g["goal_type"], "📌")
    color = BAR_COLORS.get(g["goal_type"], PRIMARY)
    pct   = g["pct_complete"]
    days_remaining = max((g["target_date"].date() - date.today()).days, 0) \
                     if hasattr(g["target_date"], "date") else 0
    days_label = f"{days_remaining} days remaining" if days_remaining > 0 else "⚠️ Deadline passed"
    est_str = g["est_completion"].strftime("%b %d, %Y") \
              if hasattr(g["est_completion"], "strftime") else str(g["est_completion"])
    target_str = g["target_date"].strftime("%b %d, %Y") \
                 if hasattr(g["target_date"], "strftime") else str(g["target_date"])

    col_info, col_gauge = st.columns([3, 1])
    with col_info:
        st.markdown(f"""
<div class="goal-card" style="border-left-color:{color}">
  <div class="goal-title">{icon} {g['metric'].replace('_', ' ').title()}</div>
  <div class="goal-meta">
    Type: {g['goal_type'].replace('_', ' ').title()} &nbsp;|&nbsp;
    Target date: {target_str} &nbsp;|&nbsp; {days_label}
  </div>
  <div class="goal-values">
    <div class="goal-stat">
      <div class="val">{g['start_value']:.1f}</div>
      <div class="lbl">Start</div>
    </div>
    <div class="goal-stat">
      <div class="val" style="color:{color}">{g['current_value']:.1f}</div>
      <div class="lbl">Current</div>
    </div>
    <div class="goal-stat">
      <div class="val" style="color:{SUCCESS}">{g['target_value']:.1f}</div>
      <div class="lbl">Target ({g['unit']})</div>
    </div>
    <div class="goal-stat">
      <div class="val" style="color:{WARNING}">{pct:.1f}%</div>
      <div class="lbl">Complete</div>
    </div>
  </div>
  <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.3rem">
    Estimated completion: {est_str}
  </div>
</div>
""", unsafe_allow_html=True)
        st.progress(int(pct))
    with col_gauge:
        st.plotly_chart(
            gauge_chart(pct, "", max_val=100, color=color),
            use_container_width=True,
            key=f"gauge_{g['goal_id']}",
        )

st.divider()
st.subheader("📋 Goals Table")
display_cols = ["goal_type", "metric", "start_value", "current_value",
                "target_value", "unit", "pct_complete", "est_completion", "target_date"]
st.dataframe(
    goals[display_cols].rename(columns={
        "goal_type": "Type", "metric": "Metric", "start_value": "Start",
        "current_value": "Current", "target_value": "Target", "unit": "Unit",
        "pct_complete": "% Done", "est_completion": "Est. Completion", "target_date": "Deadline",
    }),
    use_container_width=True, hide_index=True,
)

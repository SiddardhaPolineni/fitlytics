"""
Fitlytics — Personal Fitness Analytics Dashboard
Main home page: overview of all key metrics.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

from utils.data_loader import load_workouts, load_health, load_goals
from utils.calculations import (
    recovery_score, workout_streak, sleep_streak, steps_streak,
    goal_progress, find_prs, weekly_volume, weight_moving_averages,
    weight_projection,
)
from utils.charts import weight_trend_chart, calendar_heatmap, apply_template
from utils.theme import inject_theme, PRIMARY, SECONDARY, SUCCESS, WARNING, STATUS_COLORS
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title="Fitlytics Dashboard",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

inject_theme()

# ── Data (loaded before sidebar so the caption can show the latest date) ──────
workouts = load_workouts()
health   = load_health()
goals_df = load_goals()

# ── Sidebar ───────────────────────────────────────────────────────────────────
render_sidebar()
# Append the last-updated timestamp in the sidebar after the shared nav
with st.sidebar:
    st.caption(f"🕒 Last updated: **{health['date'].max().strftime('%b %d, %Y')}**")

# ── Computed metrics ──────────────────────────────────────────────────────────
rec_score, rec_status, _ = recovery_score(health)
wo_cur, wo_best          = workout_streak(workouts)
sl_cur, _                = sleep_streak(health)
st_cur, _                = steps_streak(health)
goals                    = goal_progress(goals_df, health, workouts)
prs                      = find_prs(workouts)
recent_prs               = prs[prs["date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)]
wvol                     = weekly_volume(workouts)
wma                      = weight_moving_averages(health)

latest_weight  = health["weight_kg"].iloc[-1]
prev_weight    = health["weight_kg"].iloc[-8] if len(health) > 8 else latest_weight
weight_7d_chg  = latest_weight - prev_weight
this_week_vol  = wvol.iloc[-1]["total_volume"] if not wvol.empty else 0
prev_week_vol  = wvol.iloc[-2]["total_volume"] if len(wvol) > 1 else this_week_vol
vol_change_pct = (this_week_vol - prev_week_vol) / prev_week_vol * 100 if prev_week_vol else 0
avg_goals_pct  = goals["pct_complete"].mean()
rec_color      = STATUS_COLORS.get(rec_status, PRIMARY)
latest_date    = health["date"].max().strftime("%B %d, %Y")

# ── KPI row ───────────────────────────────────────────────────────────────────

w_cls   = "delta-neg" if weight_7d_chg < 0 else "delta-pos"
w_sym   = "▼" if weight_7d_chg < 0 else "▲"
vol_cls = "delta-pos" if vol_change_pct >= 0 else "delta-neg"
vol_sym = "▲" if vol_change_pct >= 0 else "▼"

kpis = [
    ("⚖️", f"{latest_weight:.1f} kg",  "Current Weight",
     f'<span class="{w_cls}">{w_sym} {abs(weight_7d_chg):.1f} kg (7d)</span>'),

    ("💚", f"{rec_score:.0f}/100",      "Recovery Score",
     f'<span style="color:{rec_color}">{rec_status}</span>'),

    ("🔥", f"{wo_cur} days",            "Workout Streak",
     f"Best: {wo_best} days"),

    ("🏆", f"{len(recent_prs)}",        "New PRs (30d)",
     f"{len(prs[prs['is_all_time_pr']])} all-time records"),

    ("📊", f"{this_week_vol:,.0f} kg", "This Week Vol",
     f'<span class="{vol_cls}">{vol_sym} {abs(vol_change_pct):.1f}%</span>'),

    ("🎯", f"{avg_goals_pct:.1f}%",    "Avg Goal Progress",
     f"{(goals['pct_complete']>=100).sum()} goals completed"),

    ("😴", f"{sl_cur} days",           "Sleep Streak",
     "7+ h nights"),

    ("👟", f"{st_cur} days",           "Steps Streak",
     "10k+ steps/day"),
]

cols = st.columns(8)
for col, (icon, value, label, delta) in zip(cols, kpis):
    col.markdown(f"""
<div class="kpi-card">
  <div class="kpi-icon">{icon}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-label">{label}</div>
  <div class="kpi-delta">{delta}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Weight trend + Heatmap ────────────────────────────────────────────────────
col_left, col_right = st.columns([1.6, 1])

with col_left:
    st.markdown('<div class="section-title">Weight Trend</div>', unsafe_allow_html=True)
    proj  = weight_projection(health, days_ahead=20)
    fig_w = weight_trend_chart(wma, proj)
    fig_w.update_layout(height=300, margin=dict(l=40, r=20, t=30, b=30))
    st.plotly_chart(fig_w, use_container_width=True)

with col_right:
    st.markdown('<div class="section-title">Activity Heatmap</div>', unsafe_allow_html=True)
    fig_h = calendar_heatmap(workouts, health)
    fig_h.update_layout(height=220, margin=dict(l=60, r=10, t=30, b=40))
    st.plotly_chart(fig_h, use_container_width=True)

# ── Goal progress + Recent PRs ────────────────────────────────────────────────
col_gl, col_pr = st.columns([1.3, 1])

with col_gl:
    st.markdown('<div class="section-title">Goal Progress</div>', unsafe_allow_html=True)
    icon_map = {"weight_loss": "⚖️", "strength": "🏋️", "cardio": "🏃", "body_composition": "📐"}
    for _, g in goals.iterrows():
        pct  = min(g["pct_complete"], 100)
        icon = icon_map.get(g["goal_type"], "📌")
        ca, cb = st.columns([3, 1])
        with ca:
            st.markdown(
                f"**{icon} {g['metric'].replace('_',' ').title()}** "
                f"&nbsp; {g['current_value']:.1f} → {g['target_value']:.1f} {g['unit']}"
            )
            st.progress(int(pct))
        with cb:
            st.markdown(
                f"<div style='text-align:right;font-size:1.1rem;"
                f"font-weight:700;color:{PRIMARY};padding-top:4px'>{pct:.1f}%</div>",
                unsafe_allow_html=True,
            )

with col_pr:
    st.markdown('<div class="section-title">Recent Personal Records (30 days)</div>',
                unsafe_allow_html=True)
    if recent_prs.empty:
        st.info("No new PRs in the last 30 days.")
    else:
        for _, row in recent_prs.head(6).iterrows():
            badge = "🥇" if row["is_all_time_pr"] else "🆕"
            st.markdown(
                f"{badge} **{row['exercise']}** — "
                f"{row['weight_kg']} kg × {row['reps']} reps "
                f"*(Est. 1RM: {row['estimated_1rm']:.1f} kg)*",
            )

st.divider()

# ── Weekly volume + Recovery snapshot ────────────────────────────────────────
col_vl, col_rc = st.columns([1.6, 1])

with col_vl:
    st.markdown('<div class="section-title">Weekly Training Volume</div>', unsafe_allow_html=True)
    tail = wvol.tail(12)
    fig_vol = go.Figure(go.Bar(
        x=tail["week"], y=tail["total_volume"],
        marker_color=PRIMARY, opacity=0.85,
    ))
    if len(tail) > 2:
        y = tail["total_volume"].values
        z = np.polyfit(range(len(y)), y, 1)
        fig_vol.add_trace(go.Scatter(
            x=tail["week"], y=np.poly1d(z)(range(len(y))),
            mode="lines", line=dict(color=WARNING, width=2, dash="dash"), name="Trend",
        ))
    fig_vol.update_layout(height=280, showlegend=False,
                          xaxis_title="Week", yaxis_title="Volume (kg)",
                          margin=dict(l=40, r=20, t=20, b=40))
    apply_template(fig_vol)
    st.plotly_chart(fig_vol, use_container_width=True)

with col_rc:
    st.markdown('<div class="section-title">Recovery Snapshot</div>', unsafe_allow_html=True)
    recent_h = health.tail(7)
    items = [
        ("😴", "Avg Sleep", f"{recent_h['sleep_hours'].mean():.1f} h"),
        ("❤️", "Avg HRV",   f"{recent_h['hrv_ms'].mean():.0f} ms"),
        ("💓", "Avg RHR",   f"{recent_h['resting_hr'].mean():.0f} bpm"),
        ("🧠", "Avg Mood",  f"{recent_h['mood'].mean():.1f} / 10"
                             if "mood" in recent_h.columns else "N/A"),
    ]
    for icon, label, value in items:
        st.markdown(f"""
<div class="rec-row">
  <span class="rec-row-label">{icon} {label}</span>
  <span class="rec-row-value">{value}</span>
</div>
""", unsafe_allow_html=True)
    st.markdown(f"""
<div style="background:{rec_color}18;border:1px solid {rec_color};border-radius:10px;
     padding:0.6rem 1rem;text-align:center;margin-top:0.6rem">
  <div style="font-size:1.6rem;font-weight:800;color:{rec_color}">{rec_score:.0f}</div>
  <div style="color:{rec_color};font-size:0.85rem;font-weight:600">{rec_status} Recovery</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.caption("🏋️ **Fitlytics** — Built with Python & Streamlit · Data sourced from CSV files.")

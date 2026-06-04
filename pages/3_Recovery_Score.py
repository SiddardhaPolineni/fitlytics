"""
Recovery Score page — sleep, HRV, and resting heart rate combined score.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

from utils.data_loader import load_health
from utils.calculations import recovery_score
from utils.charts import gauge_chart, recovery_radar, apply_template
from utils.theme import inject_theme, PRIMARY, SECONDARY, SUCCESS, WARNING, STATUS_COLORS
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Recovery Score | Fitlytics", page_icon="💚", layout="wide")
inject_theme()
render_sidebar()

st.title("💚 Recovery Score")
st.caption("Understand your body's readiness to train — updated with last 7 days of data.")

# ── Data ─────────────────────────────────────────────────────────────────────
health               = load_health()
score, status, insights = recovery_score(health)
recent               = health.tail(7).copy()

avg_sleep = recent["sleep_hours"].mean()
avg_hrv   = recent["hrv_ms"].mean()
avg_rhr   = recent["resting_hr"].mean()

sleep_sub = float(np.clip((avg_sleep - 5) / (8 - 5) * 100, 0, 100))
hrv_sub   = float(np.clip((avg_hrv - 20) / (60 - 20) * 100, 0, 100))
rhr_sub   = float(np.clip((80 - avg_rhr) / (80 - 45) * 100, 0, 100))

status_color = STATUS_COLORS.get(status, PRIMARY)

# ── Top row ───────────────────────────────────────────────────────────────────
left, mid, right = st.columns([1.4, 1, 1.6])

with left:
    st.plotly_chart(gauge_chart(score, "Recovery Score", color=status_color),
                    use_container_width=True)
    st.markdown(f"""
<div style="text-align:center">
  <span class="status-badge"
        style="background:{status_color}18;color:{status_color};border:1px solid {status_color}">
    {status}
  </span>
</div>
""", unsafe_allow_html=True)

with mid:
    st.plotly_chart(recovery_radar(sleep_sub, hrv_sub, rhr_sub), use_container_width=True)

with right:
    st.subheader("💡 Recovery Insights")
    for insight in insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

    rec_map = {
        "Optimal":  "🟢 You're fully recovered. Great day to train hard or attempt a PR.",
        "Good":     "🟡 Recovery is solid. Proceed with your planned session.",
        "Moderate": "🟠 Moderate recovery. Consider reducing intensity by 10–15%.",
        "Low":      "🔴 Low recovery. Active recovery or rest day recommended.",
        "Poor":     "🛑 Poor recovery. Rest, hydrate, and prioritise sleep tonight.",
    }
    st.info(rec_map.get(status, ""))

st.divider()

# ── 30-day trend ──────────────────────────────────────────────────────────────
st.subheader("📊 Last 30 Days — Recovery Metrics")
h30 = health.tail(30)

def line_chart(df, col, color, title, yaxis_title, target=None, target_label=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df[col], mode="lines+markers",
        line=dict(color=color, width=2.5), marker=dict(size=5), name=title,
    ))
    if target:
        fig.add_hline(y=target, line_dash="dash", line_color=SUCCESS,
                      annotation_text=target_label, annotation_position="top right")
    fig.update_layout(title=title, xaxis_title="Date", yaxis_title=yaxis_title, height=300)
    return apply_template(fig)

tab_sleep, tab_hrv, tab_rhr = st.tabs(["😴 Sleep", "❤️ HRV", "💓 Resting HR"])

with tab_sleep:
    st.plotly_chart(
        line_chart(h30, "sleep_hours", PRIMARY, "Sleep Duration (30 days)", "Hours", 7, "7h target"),
        use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Sleep",   f"{avg_sleep:.1f} h")
    c2.metric("Min Sleep",   f"{h30['sleep_hours'].min():.1f} h")
    c3.metric("Sleep Score", f"{sleep_sub:.0f} / 100")

with tab_hrv:
    st.plotly_chart(
        line_chart(h30, "hrv_ms", SUCCESS, "Heart Rate Variability (30 days)", "HRV (ms)", 50, "50ms target"),
        use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg HRV",  f"{avg_hrv:.0f} ms")
    c2.metric("Peak HRV", f"{h30['hrv_ms'].max():.0f} ms")
    c3.metric("HRV Score",f"{hrv_sub:.0f} / 100")

with tab_rhr:
    st.plotly_chart(
        line_chart(h30, "resting_hr", WARNING, "Resting Heart Rate (30 days)", "bpm", 60, "60bpm target"),
        use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg RHR",    f"{avg_rhr:.0f} bpm")
    c2.metric("Lowest RHR", f"{h30['resting_hr'].min():.0f} bpm")
    c3.metric("RHR Score",  f"{rhr_sub:.0f} / 100")

st.divider()

# ── Sleep ↔ HRV correlation ───────────────────────────────────────────────────
st.subheader("🔗 Sleep ↔ HRV Correlation")
fig_corr = go.Figure(go.Scatter(
    x=health["sleep_hours"], y=health["hrv_ms"], mode="markers",
    marker=dict(
        color=health["resting_hr"], colorscale="RdYlGn_r",
        showscale=True, colorbar=dict(title="RHR (bpm)"),
        size=6, opacity=0.7,
    ),
    hovertemplate="Sleep: %{x:.1f}h<br>HRV: %{y:.0f}ms<extra></extra>",
))
fig_corr.update_layout(
    xaxis_title="Sleep (hours)", yaxis_title="HRV (ms)",
    title="Sleep vs HRV (colour = Resting HR)", height=360,
)
apply_template(fig_corr)
st.plotly_chart(fig_corr, use_container_width=True)

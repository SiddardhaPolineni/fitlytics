"""
Weekly Fitness Report — summarises the last 7 days across all metrics.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data_loader import load_health, load_workouts
from utils.calculations import weekly_summary, recovery_score
from utils.charts import apply_template
from utils.theme import inject_theme, PRIMARY, SECONDARY, SUCCESS, WARNING
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Weekly Report | Fitlytics", page_icon="📋", layout="wide")
inject_theme()
render_sidebar()

st.title("📋 Weekly Fitness Report")

# ── Data ─────────────────────────────────────────────────────────────────────
health   = load_health()
workouts = load_workouts()

summary              = weekly_summary(health, workouts)
score, status, _     = recovery_score(health)

latest_date = health["date"].max()
week_start  = latest_date - pd.Timedelta(days=6)
st.caption(f"Report period: **{week_start.strftime('%B %d')} – {latest_date.strftime('%B %d, %Y')}**")

st.divider()

# ── At a Glance ───────────────────────────────────────────────────────────────
st.subheader("📌 At a Glance")

def fmt_delta(val, unit="", invert=False):
    if val == 0:
        return "—"
    symbol = "▲" if val > 0 else "▼"
    cls = "delta-neg" if (val > 0) == invert else "delta-pos"
    return f'<span class="{cls}">{symbol} {abs(val):.1f}{unit}</span>'

m1, m2, m3, m4, m5 = st.columns(5)
m1.markdown(f"**Weight**<br>{summary['avg_weight_now']:.1f} kg<br>"
            f"{fmt_delta(summary['weight_delta'],' kg',invert=True)}", unsafe_allow_html=True)
m2.markdown(f"**Workouts**<br>{summary['workouts_this_week']} sessions<br>&nbsp;",
            unsafe_allow_html=True)
m3.markdown(f"**Volume**<br>{summary['vol_now']:,.0f} kg<br>"
            f"{fmt_delta(summary['vol_pct_change'],'%')}", unsafe_allow_html=True)
m4.markdown(f"**Avg Sleep**<br>{summary['sleep_avg']:.1f} h<br>&nbsp;",
            unsafe_allow_html=True)
m5.markdown(f"**Recovery**<br>{score:.0f} / 100<br>"
            f"<span style='color:var(--text-muted);font-size:0.75rem'>{status}</span>",
            unsafe_allow_html=True)

st.divider()

# ── Wins / Watchlist / Recommendations ───────────────────────────────────────
col_w, col_wl, col_r = st.columns(3)

with col_w:
    st.markdown('<div class="report-section"><div class="section-header">🏆 This Week\'s Wins</div>',
                unsafe_allow_html=True)
    items = summary["wins"] or ["Keep going — consistency builds results."]
    for item in items:
        prefix = "✅ " if summary["wins"] else ""
        st.markdown(f'<div class="win-item">{prefix}{item}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_wl:
    st.markdown('<div class="report-section" style="border-left:3px solid var(--warning)">'
                '<div class="section-header">⚠️ Watchlist</div>', unsafe_allow_html=True)
    if summary["watchlist"]:
        for item in summary["watchlist"]:
            st.markdown(f'<div class="win-item watch-item">⚠️ {item}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="win-item" style="color:var(--success)">Nothing to flag — great week!</div>',
                    unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_r:
    st.markdown('<div class="report-section" style="border-left:3px solid var(--success)">'
                '<div class="section-header">💡 Recommendations</div>', unsafe_allow_html=True)
    for rec in summary["recommendations"]:
        st.markdown(f'<div class="win-item rec-item">→ {rec}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ── This week vs last week ────────────────────────────────────────────────────
st.subheader("📊 This Week vs Last Week")

today  = health["date"].max().date()
week_s = today - datetime.timedelta(days=6)
prev_s = week_s - datetime.timedelta(days=7)
prev_h = health[(health["date"].dt.date >= prev_s) & (health["date"].dt.date < week_s)]
prev_w = workouts[(workouts["date"].dt.date >= prev_s) & (workouts["date"].dt.date < week_s)]

categories  = ["Workouts", "Avg Sleep (h)", "Avg Steps (k)", "Avg HRV (ms)"]
this_values = [summary["workouts_this_week"], summary["sleep_avg"],
               summary["steps_avg"]/1000, summary["hrv_avg"]]
prev_values = [
    prev_w["date"].dt.date.nunique(),
    prev_h["sleep_hours"].mean() if not prev_h.empty else 0,
    prev_h["steps"].mean()/1000  if not prev_h.empty else 0,
    prev_h["hrv_ms"].mean()      if not prev_h.empty else 0,
]

fig_cmp = go.Figure()
fig_cmp.add_trace(go.Bar(name="Last Week", x=categories, y=prev_values,
                          marker_color="rgba(128,128,128,0.4)", opacity=0.8))
fig_cmp.add_trace(go.Bar(name="This Week", x=categories, y=this_values,
                          marker_color=PRIMARY, opacity=0.9))
fig_cmp.update_layout(barmode="group", title="Weekly Comparison",
                      yaxis_title="Value", height=340,
                      legend=dict(orientation="h", y=1.1))
apply_template(fig_cmp)
st.plotly_chart(fig_cmp, use_container_width=True)

st.divider()

# ── Daily breakdown ───────────────────────────────────────────────────────────
st.subheader("📆 Daily Breakdown (Last 7 Days)")

last7_h   = health[health["date"].dt.date >= week_s].copy()
last7_w   = workouts[workouts["date"].dt.date >= week_s].copy()
daily_vol = last7_w.groupby(last7_w["date"].dt.date)["volume"].sum().reset_index()
daily_vol.columns = ["date", "volume"]

fig_daily = make_subplots(
    rows=3, cols=1, shared_xaxes=True,
    subplot_titles=["Weight (kg)", "Sleep (h) & HRV (ms)", "Training Volume (kg)"],
    vertical_spacing=0.1,
)
fig_daily.add_trace(go.Scatter(x=last7_h["date"], y=last7_h["weight_kg"],
                                mode="lines+markers", line=dict(color=PRIMARY, width=2),
                                name="Weight"), row=1, col=1)
fig_daily.add_trace(go.Bar(x=last7_h["date"], y=last7_h["sleep_hours"],
                            marker_color=SUCCESS, opacity=0.7, name="Sleep"), row=2, col=1)
fig_daily.add_trace(go.Scatter(x=last7_h["date"], y=last7_h["hrv_ms"],
                                mode="lines+markers",
                                line=dict(color=SECONDARY, width=2, dash="dot"),
                                name="HRV"), row=2, col=1)
fig_daily.add_trace(go.Bar(x=daily_vol["date"], y=daily_vol["volume"],
                            marker_color=WARNING, opacity=0.85, name="Volume"), row=3, col=1)
fig_daily.update_layout(height=560, hovermode="x unified",
                         legend=dict(orientation="h", y=-0.05))
apply_template(fig_daily)
st.plotly_chart(fig_daily, use_container_width=True)

st.divider()

# ── Export ────────────────────────────────────────────────────────────────────
st.subheader("📤 Export Summary")
report_text = (
    f"WEEKLY FITNESS REPORT — {week_s} to {today}\n"
    f"{'='*50}\n\n"
    f"KEY METRICS\n-----------\n"
    f"Current Weight:   {summary['avg_weight_now']:.1f} kg (Δ {summary['weight_delta']:+.1f} kg)\n"
    f"Workout Sessions: {summary['workouts_this_week']}\n"
    f"Training Volume:  {summary['vol_now']:,.0f} kg (Δ {summary['vol_pct_change']:+.1f}%)\n"
    f"Average Sleep:    {summary['sleep_avg']:.1f} h/night\n"
    f"Daily Steps Avg:  {summary['steps_avg']:,.0f}\n"
    f"Recovery Score:   {score:.0f}/100 ({status})\n\n"
    f"WINS\n----\n" + "\n".join(f"• {w}" for w in summary["wins"]) + "\n\n"
    f"WATCHLIST\n---------\n" + "\n".join(f"• {w}" for w in summary["watchlist"]) + "\n\n"
    f"RECOMMENDATIONS\n---------------\n" + "\n".join(f"• {r}" for r in summary["recommendations"])
)
st.text_area("Copy your report", report_text, height=320)

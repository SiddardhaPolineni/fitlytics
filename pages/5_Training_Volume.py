"""
Training Volume dashboard.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from utils.data_loader import load_workouts
from utils.calculations import weekly_volume, monthly_volume, muscle_group_volume
from utils.charts import volume_bar_chart, muscle_donut, apply_template
from utils.theme import inject_theme, PRIMARY, SECONDARY, SUCCESS, WARNING, CHART_COLORS
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Training Volume | Fitlytics", page_icon="📊", layout="wide")
inject_theme()
render_sidebar()

st.title("📊 Training Volume")
st.caption("Track how much work you're putting in — and where.")

# ── Data ─────────────────────────────────────────────────────────────────────
workouts = load_workouts()
wvol     = weekly_volume(workouts)
mvol     = monthly_volume(workouts)
mgvol    = muscle_group_volume(workouts)

total_vol    = workouts["volume"].sum()
this_week    = wvol.iloc[-1]["total_volume"] if not wvol.empty else 0
prev_week    = wvol.iloc[-2]["total_volume"] if len(wvol) > 1 else 0
wow_change   = (this_week - prev_week) / prev_week * 100 if prev_week else 0
this_month   = mvol.iloc[-1]["total_volume"] if not mvol.empty else 0
avg_session  = workouts.groupby("date")["volume"].sum().mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("All-Time Volume",  f"{total_vol:,.0f} kg")
k2.metric("This Week",        f"{this_week:,.0f} kg", f"{wow_change:+.1f}% vs last week")
k3.metric("This Month",       f"{this_month:,.0f} kg")
k4.metric("Avg per Session",  f"{avg_session:,.0f} kg")

st.divider()

tab_weekly, tab_monthly, tab_muscle, tab_exercise = st.tabs(
    ["📅 Weekly", "🗓️ Monthly", "💪 Muscle Groups", "🏋️ By Exercise"]
)

with tab_weekly:
    st.plotly_chart(volume_bar_chart(wvol, "week", "Weekly Training Volume"),
                    use_container_width=True)
    wvol_d = wvol.copy()
    wvol_d["wow_change_%"] = wvol_d["total_volume"].pct_change() * 100
    wvol_d.columns = ["Week Start", "Volume (kg)", "WoW Change (%)"]
    st.dataframe(wvol_d.tail(12), use_container_width=True, hide_index=True)

with tab_monthly:
    st.plotly_chart(volume_bar_chart(mvol, "month", "Monthly Training Volume"),
                    use_container_width=True)
    mvol_d = mvol.copy()
    mvol_d["mom_change_%"] = mvol_d["total_volume"].pct_change() * 100
    mvol_d.columns = ["Month", "Volume (kg)", "MoM Change (%)"]
    st.dataframe(mvol_d, use_container_width=True, hide_index=True)

with tab_muscle:
    left_col, right_col = st.columns([1.2, 1])
    with left_col:
        st.plotly_chart(muscle_donut(mgvol), use_container_width=True)
    with right_col:
        st.subheader("Volume by Muscle Group")
        fig_h = go.Figure(go.Bar(
            x=mgvol["total_volume"], y=mgvol["muscle_group"],
            orientation="h",
            marker=dict(color=CHART_COLORS[:len(mgvol)]),
            text=[f"{v:,.0f} kg" for v in mgvol["total_volume"]],
            textposition="outside",
        ))
        fig_h.update_layout(xaxis_title="Volume (kg)", yaxis_title="", height=320,
                            margin=dict(l=10))
        apply_template(fig_h)
        st.plotly_chart(fig_h, use_container_width=True)

    st.subheader("⚖️ Muscle Group Balance Analysis")
    vol_dict = mgvol.set_index("muscle_group")["total_volume"].to_dict()
    pairs = [("Chest","Back","Push/Pull"), ("Legs","Back","Lower/Upper Posterior")]
    balance_rows = []
    for a, b, label in pairs:
        va, vb = vol_dict.get(a,0), vol_dict.get(b,0)
        if va + vb > 0:
            ratio = va / vb if vb > 0 else 999
            balance_rows.append({
                "Pair": label,
                f"{a} Vol (kg)": f"{va:,.0f}",
                f"{b} Vol (kg)": f"{vb:,.0f}",
                "Ratio": f"{ratio:.2f}",
                "Status": "✅ Balanced" if 0.8 <= ratio <= 1.2 else "⚠️ Imbalanced",
            })
    if balance_rows:
        st.dataframe(pd.DataFrame(balance_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Not enough data for balance analysis.")

with tab_exercise:
    st.subheader("Volume per Exercise")
    ex_vol = (
        workouts.groupby("exercise")
        .agg(total_volume=("volume","sum"), sessions=("date","nunique"),
             avg_weight=("weight_kg","mean"))
        .reset_index().sort_values("total_volume", ascending=False)
    )
    fig_ex = px.bar(
        ex_vol, x="exercise", y="total_volume",
        color="total_volume",
        color_continuous_scale=[[0,"rgba(108,99,255,0.1)"],[1,PRIMARY]],
        labels={"exercise":"Exercise","total_volume":"Total Volume (kg)"},
        title="Total Volume by Exercise",
    )
    fig_ex.update_layout(showlegend=False, coloraxis_showscale=False)
    apply_template(fig_ex)
    st.plotly_chart(fig_ex, use_container_width=True)

    st.subheader("Exercise Volume Heatmap (by Week)")
    w_copy = workouts.copy()
    w_copy["week_label"] = w_copy["date"].dt.to_period("W").astype(str)
    heat = w_copy.groupby(["exercise","week_label"])["volume"].sum().reset_index()
    heat_pivot = heat.pivot(index="exercise", columns="week_label", values="volume").fillna(0)
    fig_heat = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns.tolist(),
        y=heat_pivot.index.tolist(),
        colorscale=[[0,"rgba(108,99,255,0.05)"],[0.5,"rgba(108,99,255,0.4)"],[1,PRIMARY]],
        hovertemplate="Exercise: %{y}<br>Week: %{x}<br>Volume: %{z:,.0f} kg<extra></extra>",
    ))
    fig_heat.update_layout(
        xaxis_title="Week", yaxis_title="Exercise",
        height=max(300, len(heat_pivot)*32),
        xaxis=dict(tickangle=-45),
    )
    apply_template(fig_heat)
    st.plotly_chart(fig_heat, use_container_width=True)

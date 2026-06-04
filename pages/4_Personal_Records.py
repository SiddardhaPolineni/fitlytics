"""
Personal Records page — detects new PRs, all-time PRs, and PR timeline.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from utils.data_loader import load_workouts
from utils.calculations import find_prs
from utils.charts import pr_timeline, exercise_trend
from utils.theme import inject_theme, PRIMARY, SUCCESS, WARNING
from utils.sidebar import render_sidebar

st.set_page_config(page_title="Personal Records | Fitlytics", page_icon="🏆", layout="wide")
inject_theme()
render_sidebar()

st.title("🏆 Personal Records")
st.caption("Every rep counts. Here's where you've peaked.")

# ── Data ─────────────────────────────────────────────────────────────────────
workouts  = load_workouts()
prs       = find_prs(workouts)

if prs.empty:
    st.warning("No workout data found.")
    st.stop()

recent_30 = prs[prs["date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)]
all_time  = prs[prs["is_all_time_pr"]]

# ── KPIs ─────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total PR Events",    len(prs))
k2.metric("All-Time Records",   len(all_time))
k3.metric("PRs Last 30 Days",   len(recent_30))
k4.metric("Exercises Tracked",  prs["exercise"].nunique())

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_recent, tab_all, tab_timeline, tab_drill = st.tabs(
    ["🆕 Recent PRs", "🥇 All-Time PRs", "📈 PR Timeline", "🔍 Drill-Down"]
)

# ---- Recent PRs ----
with tab_recent:
    st.subheader("PRs in the Last 30 Days")
    if recent_30.empty:
        st.info("No new PRs in the last 30 days — keep pushing!")
    else:
        cols = st.columns(3)
        for i, (_, row) in enumerate(recent_30.iterrows()):
            at_badge = '<span class="pr-badge">ALL-TIME PR</span>' if row["is_all_time_pr"] else ""
            with cols[i % 3]:
                st.markdown(f"""
<div class="pr-card pr-new">
  <div class="pr-exercise">🆕 {row['exercise']}{at_badge}</div>
  <div class="pr-value" style="color:{SUCCESS}">{row['estimated_1rm']:.1f} kg</div>
  <div style="font-size:0.8rem;color:var(--text-secondary)">
    {row['weight_kg']} kg × {row['reps']} reps
  </div>
  <div class="pr-date">{row['date'].strftime('%B %d, %Y')}</div>
</div>
""", unsafe_allow_html=True)

# ---- All-Time PRs ----
with tab_all:
    st.subheader("Current All-Time Records")
    cols = st.columns(3)
    for i, (_, row) in enumerate(all_time.sort_values("estimated_1rm", ascending=False).iterrows()):
        with cols[i % 3]:
            st.markdown(f"""
<div class="pr-card">
  <div class="pr-exercise">🥇 {row['exercise']}</div>
  <div class="pr-value">{row['estimated_1rm']:.1f} kg</div>
  <div style="font-size:0.8rem;color:var(--text-secondary)">
    {row['weight_kg']} kg × {row['reps']} reps
  </div>
  <div class="pr-date">Set on {row['date'].strftime('%B %d, %Y')}</div>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.subheader("All-Time Records Table")
    st.dataframe(
        all_time[["exercise","date","weight_kg","reps","estimated_1rm"]].rename(columns={
            "exercise":"Exercise","date":"Date Set","weight_kg":"Weight (kg)",
            "reps":"Reps","estimated_1rm":"Est. 1RM (kg)",
        }),
        use_container_width=True, hide_index=True,
    )

# ---- PR Timeline ----
with tab_timeline:
    st.subheader("Estimated 1RM Progress")
    exercises_available = sorted(prs["exercise"].unique().tolist())
    selected = st.multiselect("Select exercises", options=exercises_available,
                               default=exercises_available[:4])
    if selected:
        st.plotly_chart(pr_timeline(prs[prs["exercise"].isin(selected)]),
                        use_container_width=True)
    st.divider()
    st.subheader("Full PR History")
    st.dataframe(
        prs[["exercise","date","weight_kg","reps","estimated_1rm","is_all_time_pr"]].rename(columns={
            "exercise":"Exercise","date":"Date","weight_kg":"Weight (kg)",
            "reps":"Reps","estimated_1rm":"Est. 1RM (kg)","is_all_time_pr":"All-Time PR",
        }),
        use_container_width=True, hide_index=True,
    )

# ---- Drill-Down ----
with tab_drill:
    st.subheader("Exercise Deep-Dive")
    selected_ex = st.selectbox("Choose an exercise", options=sorted(workouts["exercise"].unique()))
    if selected_ex:
        st.plotly_chart(exercise_trend(workouts, selected_ex), use_container_width=True)
        ex_prs = prs[prs["exercise"] == selected_ex].sort_values("date")
        if not ex_prs.empty:
            st.subheader(f"PR Progression — {selected_ex}")
            for _, row in ex_prs.iterrows():
                badge = "🥇 ALL-TIME" if row["is_all_time_pr"] else "📈 PR"
                st.markdown(
                    f"**{row['date'].strftime('%b %d, %Y')}** — {badge}: "
                    f"{row['weight_kg']} kg × {row['reps']} reps "
                    f"(Est. 1RM: **{row['estimated_1rm']:.1f} kg**)"
                )

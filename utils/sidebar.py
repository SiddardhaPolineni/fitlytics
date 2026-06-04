"""
Shared sidebar renderer — call render_sidebar() once per page.
Displays the branded logo header and navigation links on every page.
"""
from __future__ import annotations
import streamlit as st


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("""
<div class="sidebar-brand">
  <div class="sidebar-logo">🏋️</div>
  <div class="sidebar-title">Fitlytics</div>
  <div class="sidebar-subtitle">Personal Fitness Analytics</div>
</div>
<div class="sidebar-divider"></div>
<div class="sidebar-nav-label">Navigation</div>
""", unsafe_allow_html=True)

        st.page_link("app.py",                      label="🏠 Dashboard")
        st.page_link("pages/1_Goal_Tracking.py",    label="🎯 Goal Tracking")
        st.page_link("pages/2_Streaks.py",          label="🔥 Streaks")
        st.page_link("pages/3_Recovery_Score.py",   label="💚 Recovery Score")
        st.page_link("pages/4_Personal_Records.py", label="🏆 Personal Records")
        st.page_link("pages/5_Training_Volume.py",  label="📊 Training Volume")
        st.page_link("pages/6_Weight_Trends.py",    label="⚖️ Weight Trends")
        st.page_link("pages/7_Weekly_Report.py",    label="📋 Weekly Report")
        st.page_link("pages/8_Calendar_Heatmap.py", label="📅 Calendar Heatmap")

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.caption("Data refreshes every 5 min.")

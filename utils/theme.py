"""
Theme helpers — CSS variables + Plotly template that work in both
Streamlit light mode and dark mode.

Strategy
--------
* CSS: define variables under :root (light defaults) and override
  inside @media (prefers-color-scheme: dark).  Streamlit also injects
  its own [data-theme] attribute, so we target both signals.
* Plotly: use transparent backgrounds (rgba(0,0,0,0)) so charts
  inherit whatever the page background is.  Only font colour and grid
  colour are set, using values that work on both themes (semi-transparent).
"""
from __future__ import annotations

import plotly.graph_objects as go

# ── Brand / accent colours (theme-independent) ────────────────────────────
PRIMARY   = "#6C63FF"
SECONDARY = "#FF6584"
SUCCESS   = "#2ECC71"
WARNING   = "#F39C12"
NEUTRAL   = "#95A5A6"
INFO      = "#3498DB"

# Status colours for recovery etc.
STATUS_COLORS = {
    "Optimal":  SUCCESS,
    "Good":     "#27AE60",
    "Moderate": WARNING,
    "Low":      SECONDARY,
    "Poor":     "#E74C3C",
}

# Chart trace colours (work well on both light & dark backgrounds)
CHART_COLORS = [PRIMARY, SECONDARY, SUCCESS, WARNING, INFO, "#9B59B6", "#1ABC9C", "#E67E22"]


# ── CSS injected once per page ────────────────────────────────────────────
THEME_CSS = """
<style>
/* ── CSS custom properties — LIGHT defaults ─────────────────────────────── */
:root {
  --bg-page:       #F8F9FA;
  --bg-card:       #FFFFFF;
  --bg-card-alt:   #F0F2F6;
  --border-color:  #D1D5DB;
  --text-primary:  #1A1A2E;
  --text-secondary:#4B5563;
  --text-muted:    #9CA3AF;
  --accent:        #6C63FF;
  --success:       #2ECC71;
  --warning:       #F39C12;
  --danger:        #FF6584;
  --shadow:        0 2px 8px rgba(0,0,0,0.08);
}

/* ── Dark mode overrides ─────────────────────────────────────────────────── */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-page:       #0E1117;
    --bg-card:       #1A1D2E;
    --bg-card-alt:   #12152A;
    --border-color:  #2D3250;
    --text-primary:  #FAFAFA;
    --text-secondary:#A8B2D8;
    --text-muted:    #8B92A5;
    --shadow:        0 2px 8px rgba(0,0,0,0.4);
  }
}

/* Streamlit also sets data-theme on <html> — honour it directly */
[data-theme="dark"] {
  --bg-page:       #0E1117;
  --bg-card:       #1A1D2E;
  --bg-card-alt:   #12152A;
  --border-color:  #2D3250;
  --text-primary:  #FAFAFA;
  --text-secondary:#A8B2D8;
  --text-muted:    #8B92A5;
  --shadow:        0 2px 8px rgba(0,0,0,0.4);
}

[data-theme="light"] {
  --bg-page:       #F8F9FA;
  --bg-card:       #FFFFFF;
  --bg-card-alt:   #F0F2F6;
  --border-color:  #D1D5DB;
  --text-primary:  #1A1A2E;
  --text-secondary:#4B5563;
  --text-muted:    #9CA3AF;
  --shadow:        0 2px 8px rgba(0,0,0,0.08);
}

/* ── Reusable component classes ─────────────────────────────────────────── */

/* KPI card */
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 1rem 1.2rem;
  text-align: center;
  height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-shadow: var(--shadow);
  transition: transform 0.15s;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-icon  { font-size: 1.6rem; margin-bottom: 0.2rem; }
.kpi-value { font-size: 1.8rem; font-weight: 800; color: var(--accent); line-height: 1; }
.kpi-label { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.25rem; }
.kpi-delta { font-size: 0.75rem; margin-top: 0.15rem; }

/* Section title */
.section-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0.8rem 0 0.5rem 0;
  padding-left: 0.6rem;
  border-left: 3px solid var(--accent);
}

/* Generic card */
.fit-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.2rem 1.4rem;
  margin-bottom: 0.8rem;
  box-shadow: var(--shadow);
}

/* Insight / info box */
.insight-box {
  background: var(--bg-card-alt);
  border-left: 4px solid var(--success);
  padding: 0.8rem 1rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  font-size: 0.88rem;
  color: var(--text-primary);
}

/* Report section */
.report-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 1.2rem 1.4rem;
  margin-bottom: 1rem;
  box-shadow: var(--shadow);
}
.section-header {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.8rem;
}
.win-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.88rem;
  color: var(--text-primary);
}
.watch-item { color: var(--warning) !important; }
.rec-item   { color: #27AE60 !important; }

/* Streak card */
.streak-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: var(--shadow);
}
.streak-icon { font-size: 2.8rem; margin-bottom: 0.3rem; }
.streak-num  { font-size: 3.5rem; font-weight: 800; line-height: 1; }
.streak-lbl  { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.3rem; }
.streak-best { font-size: 0.75rem; margin-top: 0.5rem; color: var(--warning); }

/* PR card */
.pr-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 1rem 1.2rem;
  margin-bottom: 0.6rem;
  border-top: 3px solid var(--warning);
  box-shadow: var(--shadow);
}
.pr-new         { border-top-color: var(--success) !important; }
.pr-exercise    { font-size: 0.95rem; font-weight: 700; color: var(--text-primary); }
.pr-value       { font-size: 1.8rem; font-weight: 800; color: var(--warning); }
.pr-date        { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.2rem; }
.pr-badge {
  display: inline-block;
  background: var(--success);
  color: #fff;
  border-radius: 6px;
  padding: 0.1rem 0.5rem;
  font-size: 0.65rem;
  font-weight: 700;
  margin-left: 0.4rem;
  vertical-align: middle;
}

/* Goal card */
.goal-card {
  background: var(--bg-card);
  border-left: 4px solid var(--accent);
  border-radius: 12px;
  padding: 1.2rem 1.4rem;
  margin-bottom: 0.8rem;
  box-shadow: var(--shadow);
}
.goal-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.2rem; }
.goal-meta  { font-size: 0.78rem; color: var(--text-muted); margin-bottom: 0.6rem; }
.goal-values { display: flex; gap: 2rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.goal-stat  { text-align: center; }
.goal-stat .val { font-size: 1.3rem; font-weight: 700; color: var(--accent); }
.goal-stat .lbl { font-size: 0.72rem; color: var(--text-muted); }

/* Status badge */
.status-badge {
  display: inline-block;
  padding: 0.3rem 1rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: 1rem;
  margin-top: 0.4rem;
}

/* Delta helpers */
.delta-pos { color: var(--success); font-weight: 700; }
.delta-neg { color: var(--danger);  font-weight: 700; }

/* ── Hide Streamlit's auto-generated page navigation ────────────────────── */
/* Streamlit renders its own nav list from the pages/ directory; we replace  */
/* it with our custom branded sidebar, so the auto one must be hidden.        */
[data-testid="stSidebarNav"] {
  display: none !important;
}

/* ── Reduce default top padding so KPIs sit closer to the top ───────────── */
[data-testid="stAppViewContainer"] > [data-testid="stMain"] > [data-testid="stMainBlockContainer"] {
  padding-top: 1rem !important;
}

/* ── Sidebar brand header ────────────────────────────────────────────────── */
.sidebar-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1.4rem 1rem 1rem;
  margin-bottom: 0.4rem;
}
.sidebar-logo {
  font-size: 3.2rem;
  line-height: 1;
  margin-bottom: 0.4rem;
  /* subtle drop-shadow on the emoji for depth */
  filter: drop-shadow(0 2px 6px rgba(108,99,255,0.35));
}
.sidebar-title {
  font-size: 1.45rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--accent);
  margin: 0;
  line-height: 1.1;
}
.sidebar-subtitle {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
  line-height: 1.4;
}
.sidebar-divider {
  width: 100%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    var(--border-color) 20%,
    var(--border-color) 80%,
    transparent
  );
  margin: 0.6rem 0 0.8rem;
}
.sidebar-nav-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 0 0.2rem 0.4rem;
}

/* Recovery row item */
.rec-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card-alt);
  border-radius: 8px;
  padding: 0.5rem 0.8rem;
  margin-bottom: 0.4rem;
}
.rec-row-label { color: var(--text-muted); }
.rec-row-value { font-weight: 700; color: var(--text-primary); }

/* Badge (milestone) */
.badge-achieved {
  background: rgba(46,204,113,0.12);
  border: 1px solid var(--success);
  border-radius: 10px;
  padding: 0.8rem;
  text-align: center;
  height: 90px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.badge-locked {
  background: var(--bg-card-alt);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 0.8rem;
  text-align: center;
  height: 90px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.badge-icon  { font-size: 1.8rem; }
.badge-label { font-size: 0.65rem; margin-top: 0.3rem; }
.badge-achieved .badge-label { color: var(--success); }
.badge-locked   .badge-label { color: var(--text-muted); }
</style>
"""


def inject_theme(extra_css: str = "") -> None:
    """Call once at the top of each page to inject theme CSS."""
    import streamlit as st
    st.markdown(THEME_CSS + (f"<style>{extra_css}</style>" if extra_css else ""), unsafe_allow_html=True)


# ── Plotly transparent template ───────────────────────────────────────────
def plotly_theme(fig: go.Figure) -> go.Figure:
    """
    Apply a theme-neutral Plotly layout:
    - Transparent paper & plot background → inherits page colour
    - Subtle grid lines that work on both light and dark
    - Font colour inherits from CSS (uses currentColor logic via 'auto')
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12),
        xaxis=dict(
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="rgba(128,128,128,0.3)",
            zerolinecolor="rgba(128,128,128,0.3)",
        ),
        yaxis=dict(
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="rgba(128,128,128,0.3)",
            zerolinecolor="rgba(128,128,128,0.3)",
        ),
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(
            bgcolor="rgba(30,30,50,0.9)",
            font_color="#FAFAFA",
            bordercolor="rgba(128,128,128,0.4)",
        ),
    )
    return fig


# Keep apply_template as an alias so existing imports still work
apply_template = plotly_theme

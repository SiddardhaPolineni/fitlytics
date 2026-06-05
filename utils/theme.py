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
/* ══════════════════════════════════════════════════════════════════════════
   FLUID TYPE SCALE  —  clamp(min, preferred, max)
   Scales smoothly from ~360px wide screens up to 1920px.
   ══════════════════════════════════════════════════════════════════════════ */
:root {
  /* Font sizes */
  --fs-xs:   clamp(0.60rem, 0.55rem + 0.25vw, 0.70rem);
  --fs-sm:   clamp(0.70rem, 0.65rem + 0.30vw, 0.82rem);
  --fs-base: clamp(0.82rem, 0.78rem + 0.35vw, 1.00rem);
  --fs-md:   clamp(0.90rem, 0.85rem + 0.40vw, 1.10rem);
  --fs-lg:   clamp(1.05rem, 0.95rem + 0.55vw, 1.30rem);
  --fs-xl:   clamp(1.20rem, 1.05rem + 0.80vw, 1.60rem);
  --fs-2xl:  clamp(1.40rem, 1.20rem + 1.10vw, 2.00rem);
  --fs-3xl:  clamp(1.80rem, 1.50rem + 1.60vw, 2.80rem);

  /* Spacing */
  --space-xs:  clamp(0.25rem, 0.20rem + 0.25vw, 0.40rem);
  --space-sm:  clamp(0.50rem, 0.40rem + 0.50vw, 0.80rem);
  --space-md:  clamp(0.75rem, 0.60rem + 0.75vw, 1.20rem);
  --space-lg:  clamp(1.00rem, 0.80rem + 1.00vw, 1.60rem);
  --space-xl:  clamp(1.20rem, 1.00rem + 1.20vw, 2.00rem);

  /* Colours — LIGHT defaults */
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

/* ── Global base font ────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-size: var(--fs-base) !important;
}

/* ── Hide Streamlit auto-nav ─────────────────────────────────────────────── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Reduce top padding ──────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] > [data-testid="stMain"] > [data-testid="stMainBlockContainer"] {
  padding-top: 1rem !important;
}

/* ══════════════════════════════════════════════════════════════════════════
   COMPONENT STYLES  —  all sizes use fluid variables
   ══════════════════════════════════════════════════════════════════════════ */

/* KPI card — strict equal-height grid cell */
.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 0.7rem 0.5rem;
  text-align: center;
  height: 108px;           /* fixed — every card the same */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: var(--shadow);
  transition: transform 0.15s;
  overflow: hidden;        /* nothing bleeds outside */
  box-sizing: border-box;
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-icon {
  font-size: 1.35rem;
  line-height: 1;
  margin-bottom: 0.15rem;
  flex-shrink: 0;
}
.kpi-value {
  font-size: clamp(1rem, 1.4vw, 1.5rem);
  font-weight: 800;
  color: var(--accent);
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}
.kpi-label {
  font-size: clamp(0.58rem, 0.7vw, 0.70rem);
  color: var(--text-muted);
  margin-top: 0.15rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}
.kpi-delta {
  font-size: clamp(0.58rem, 0.7vw, 0.70rem);
  margin-top: 0.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

/* Section title */
.section-title {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text-primary);
  margin: var(--space-sm) 0 var(--space-xs) 0;
  padding-left: 0.6rem;
  border-left: 3px solid var(--accent);
}

/* Generic card */
.fit-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: var(--space-md) var(--space-lg);
  margin-bottom: var(--space-sm);
  box-shadow: var(--shadow);
}

/* Insight box */
.insight-box {
  background: var(--bg-card-alt);
  border-left: 4px solid var(--success);
  padding: var(--space-sm) var(--space-md);
  border-radius: 8px;
  margin-bottom: var(--space-xs);
  font-size: var(--fs-sm);
  color: var(--text-primary);
}

/* Report section */
.report-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: var(--space-md) var(--space-lg);
  margin-bottom: var(--space-md);
  box-shadow: var(--shadow);
}
.section-header {
  font-size: var(--fs-md);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-sm);
}
.win-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: var(--space-xs) 0;
  border-bottom: 1px solid var(--border-color);
  font-size: var(--fs-sm);
  color: var(--text-primary);
}
.watch-item { color: var(--warning) !important; }
.rec-item   { color: #27AE60 !important; }

/* Streak card */
.streak-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: var(--space-lg);
  text-align: center;
  box-shadow: var(--shadow);
}
.streak-icon { font-size: var(--fs-3xl); margin-bottom: 0.2rem; }
.streak-num  { font-size: var(--fs-3xl); font-weight: 800; line-height: 1; }
.streak-lbl  { font-size: var(--fs-xs);  color: var(--text-muted); margin-top: 0.25rem; }
.streak-best { font-size: var(--fs-xs);  margin-top: 0.4rem; color: var(--warning); }

/* PR card */
.pr-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: var(--space-sm) var(--space-md);
  margin-bottom: var(--space-xs);
  border-top: 3px solid var(--warning);
  box-shadow: var(--shadow);
}
.pr-new         { border-top-color: var(--success) !important; }
.pr-exercise    { font-size: var(--fs-base); font-weight: 700; color: var(--text-primary); }
.pr-value       { font-size: var(--fs-2xl);  font-weight: 800; color: var(--warning); }
.pr-date        { font-size: var(--fs-xs);   color: var(--text-muted); margin-top: 0.15rem; }
.pr-badge {
  display: inline-block;
  background: var(--success);
  color: #fff;
  border-radius: 6px;
  padding: 0.1rem 0.4rem;
  font-size: var(--fs-xs);
  font-weight: 700;
  margin-left: 0.3rem;
  vertical-align: middle;
}

/* Goal card */
.goal-card {
  background: var(--bg-card);
  border-left: 4px solid var(--accent);
  border-radius: 12px;
  padding: var(--space-md) var(--space-lg);
  margin-bottom: var(--space-sm);
  box-shadow: var(--shadow);
}
.goal-title   { font-size: var(--fs-base); font-weight: 700; color: var(--text-primary); margin-bottom: 0.15rem; }
.goal-meta    { font-size: var(--fs-xs);   color: var(--text-muted); margin-bottom: var(--space-xs); }
.goal-values  { display: flex; gap: clamp(1rem,3vw,2rem); margin-bottom: var(--space-xs); flex-wrap: wrap; }
.goal-stat    { text-align: center; }
.goal-stat .val { font-size: var(--fs-lg);  font-weight: 700; color: var(--accent); }
.goal-stat .lbl { font-size: var(--fs-xs);  color: var(--text-muted); }

/* Status badge */
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.9rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: var(--fs-base);
  margin-top: 0.3rem;
}

/* Delta helpers */
.delta-pos { color: var(--success); font-weight: 700; }
.delta-neg { color: var(--danger);  font-weight: 700; }

/* Recovery row item */
.rec-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-card-alt);
  border-radius: 8px;
  padding: var(--space-xs) var(--space-sm);
  margin-bottom: var(--space-xs);
  font-size: var(--fs-sm);
}
.rec-row-label { color: var(--text-muted); }
.rec-row-value { font-weight: 700; color: var(--text-primary); }

/* Milestone badges */
.badge-achieved {
  background: rgba(46,204,113,0.12);
  border: 1px solid var(--success);
  border-radius: 10px;
  padding: var(--space-sm);
  text-align: center;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.badge-locked {
  background: var(--bg-card-alt);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: var(--space-sm);
  text-align: center;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.badge-icon  { font-size: var(--fs-2xl); }
.badge-label { font-size: var(--fs-xs); margin-top: 0.25rem; }
.badge-achieved .badge-label { color: var(--success); }
.badge-locked   .badge-label { color: var(--text-muted); }

/* ── Sidebar brand header ────────────────────────────────────────────────── */
.sidebar-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-lg) var(--space-md) var(--space-md);
  margin-bottom: var(--space-xs);
}
.sidebar-logo {
  font-size: clamp(2.2rem, 1.8rem + 1vw, 3.2rem);
  line-height: 1;
  margin-bottom: 0.35rem;
  filter: drop-shadow(0 2px 6px rgba(108,99,255,0.35));
}
.sidebar-title {
  font-size: clamp(1.1rem, 0.9rem + 0.6vw, 1.45rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--accent);
  margin: 0;
  line-height: 1.1;
}
.sidebar-subtitle {
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin-top: 0.2rem;
  line-height: 1.4;
}
.sidebar-divider {
  width: 100%;
  height: 1px;
  background: linear-gradient(
    90deg, transparent, var(--border-color) 20%,
    var(--border-color) 80%, transparent
  );
  margin: var(--space-xs) 0 var(--space-sm);
}
.sidebar-nav-label {
  font-size: var(--fs-xs);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 0 0.2rem 0.3rem;
}

/* ══════════════════════════════════════════════════════════════════════════
   RESPONSIVE BREAKPOINTS
   ══════════════════════════════════════════════════════════════════════════ */

/* ── Tablet  (≤ 1200px) ──────────────────────────────────────────────────── */
@media screen and (max-width: 1200px) {
  .kpi-card      { height: 96px; padding: 0.5rem 0.4rem; }
  .kpi-value     { font-size: clamp(0.9rem, 1.5vw, 1.2rem); }
  .kpi-icon      { font-size: 1.1rem; }
  .streak-num    { font-size: clamp(2rem, 3.5vw, 2.8rem); }
  .streak-icon   { font-size: clamp(1.8rem, 3vw, 2.4rem); }
  .pr-value      { font-size: clamp(1.2rem, 2.2vw, 1.6rem); }
  .goal-stat .val{ font-size: clamp(0.95rem, 1.5vw, 1.2rem); }
}

/* ── Mobile  (≤ 768px) ───────────────────────────────────────────────────── */
@media screen and (max-width: 768px) {
  .sidebar-brand  { padding: 0.8rem 0.6rem 0.6rem; }
  .sidebar-logo   { font-size: 2rem; }
  .sidebar-title  { font-size: 1.05rem; }

  .kpi-card       { height: 84px; padding: 0.4rem 0.3rem; }
  .kpi-value      { font-size: 0.95rem; }
  .kpi-icon       { font-size: 0.95rem; }
  .kpi-label,
  .kpi-delta      { font-size: 0.58rem; }

  .streak-card    { padding: 0.8rem; }
  .streak-num     { font-size: 2rem; }
  .streak-icon    { font-size: 1.6rem; }

  .pr-card        { padding: 0.6rem 0.8rem; }
  .pr-value       { font-size: 1.2rem; }

  .goal-card      { padding: 0.8rem 1rem; }
  .goal-values    { gap: 0.8rem; }
  .goal-stat .val { font-size: 0.95rem; }

  .section-title  { font-size: 0.9rem; }
  .section-header { font-size: 0.95rem; }
  .report-section { padding: 0.7rem 0.9rem; }
  .win-item       { font-size: 0.78rem; }

  .badge-achieved,
  .badge-locked   { min-height: 65px; padding: 0.5rem; }
  .badge-icon     { font-size: 1.3rem; }
}

/* ── Small mobile  (≤ 480px) ─────────────────────────────────────────────── */
@media screen and (max-width: 480px) {
  :root {
    --fs-base: 0.78rem;
  }
  .kpi-value  { font-size: 1rem; }
  .streak-num { font-size: 1.8rem; }
}
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
    - Transparent backgrounds → inherits page colour
    - Fluid font size via autosize + responsive margins
    - Grid lines work on both light and dark
    """
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        autosize=True,
        font=dict(family="Inter, system-ui, sans-serif", size=12),
        xaxis=dict(
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="rgba(128,128,128,0.3)",
            zerolinecolor="rgba(128,128,128,0.3)",
            automargin=True,
            tickfont=dict(size=11),
            title_font=dict(size=12),
        ),
        yaxis=dict(
            gridcolor="rgba(128,128,128,0.2)",
            linecolor="rgba(128,128,128,0.3)",
            zerolinecolor="rgba(128,128,128,0.3)",
            automargin=True,
            tickfont=dict(size=11),
            title_font=dict(size=12),
        ),
        margin=dict(l=40, r=20, t=36, b=36),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
            itemsizing="constant",
        ),
        hoverlabel=dict(
            bgcolor="rgba(30,30,50,0.9)",
            font_color="#FAFAFA",
            font_size=12,
            bordercolor="rgba(128,128,128,0.4)",
        ),
        title_font=dict(size=13, family="Inter, system-ui, sans-serif"),
    )
    return fig


# Keep apply_template as an alias so existing imports still work
apply_template = plotly_theme

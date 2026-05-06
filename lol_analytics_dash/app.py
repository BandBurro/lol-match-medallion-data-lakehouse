# =============================================================================
# SECTION 0 — IMPORTS & ENVIRONMENT
# =============================================================================
import os
from datetime import datetime

import numpy as np
import pandas as pd
import dash
from dash import dcc, html, callback, Input, Output, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from databricks import sql
from dotenv import load_dotenv

load_dotenv()

SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME")
HTTP_PATH       = os.getenv("DATABRICKS_HTTP_PATH")
ACCESS_TOKEN    = os.getenv("DATABRICKS_ACCESS_TOKEN")


# =============================================================================
# SECTION 1 — DESIGN SYSTEM
# =============================================================================
COLORS = {
    "bg_deep":        "#080b14",
    "bg_card":        "rgba(255,255,255,0.04)",
    "bg_card_solid":  "#111827",
    "border_glass":   "rgba(255,255,255,0.08)",
    "text_primary":   "#f0f4f8",
    "text_secondary": "#94a3b8",
    "cyan":           "#00f2fe",
    "cyan_mid":       "#4facfe",
    "red":            "#ff4655",
    "emerald":        "#0bc27c",
    "gold":           "#ffd700",
    "purple":         "#9b59b6",
    "blue":           "#3498db",
    "slate":          "#64748b",
    "grid":           "#1e2535",
}

TIER_COLORS = {
    "S-Tier": "#FFD700",
    "A-Tier": "#9B59B6",
    "B-Tier": "#3498DB",
    "C-Tier": "#64748B",
}

def _champion_icon_url(name: str) -> str:
    key = name.replace(" ", "").replace("'", "").replace(".", "")
    return f"https://cdn.communitydragon.org/latest/champion/{key}/square"


CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

:root {
    /* ── App design tokens ─────────────────────────────── */
    --bg-deep:       #080b14;
    --bg-card:       rgba(255,255,255,0.04);
    --border-glass:  rgba(255,255,255,0.08);
    --cyan:          #00f2fe;
    --cyan-mid:      #4facfe;
    --red:           #ff4655;
    --emerald:       #0bc27c;
    --gold:          #ffd700;
    --text-primary:  #f0f4f8;
    --text-muted:    #94a3b8;
    --font-display:  'Rajdhani', sans-serif;
    --font-body:     'Inter', sans-serif;
    --radius:        16px;
    --glow:          0 0 20px rgba(0,242,254,0.25), 0 0 40px rgba(0,242,254,0.1);
    --transition:    all 0.25s cubic-bezier(0.4, 0, 0.2, 1);

    /* ── Dash 4 design-system overrides (used by dcc.Dropdown internals) ── */
    --Dash-Fill-Inverse-Strong:    #0d1220;
    --Dash-Stroke-Strong:          rgba(0,242,254,0.2);
    --Dash-Text-Strong:            #f0f4f8;
    --Dash-Text-Disabled:          #94a3b8;
    --Dash-Text-Weak:              #94a3b8;
    --Dash-Fill-Interactive-Strong:#00f2fe;
    --Dash-Fill-Interactive-Weak:  rgba(0,242,254,0.1);
    --Dash-Fill-Disabled:          rgba(255,255,255,0.06);
    --Dash-Shading-Strong:         rgba(0,0,0,0.7);
    --Dash-Shading-Weak:           rgba(0,0,0,0.3);
    --Dash-Spacing:                4px;
}

*, *::before, *::after { box-sizing: border-box; }

body {
    background-color: var(--bg-deep) !important;
    font-family:      var(--font-body) !important;
    color:            var(--text-primary) !important;
}

/* ── Glassmorphism Cards ─────────────────────────────────────────────────── */
.glass-card {
    background:          rgba(255,255,255,0.04) !important;
    backdrop-filter:     blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border:              1px solid rgba(255,255,255,0.08) !important;
    border-radius:       var(--radius) !important;
    box-shadow:          0 4px 24px rgba(0,0,0,0.4);
    transition:          var(--transition);
}
@supports not (backdrop-filter: blur(1px)) {
    .glass-card { background: #111827 !important; }
}
.glass-card:hover {
    transform:   translateY(-3px);
    box-shadow:  var(--glow), 0 8px 32px rgba(0,0,0,0.5);
}

/* ── Gradient Title Text ─────────────────────────────────────────────────── */
.gradient-text {
    background:              linear-gradient(135deg, var(--cyan) 0%, var(--cyan-mid) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip:         text;
    font-family:             var(--font-display) !important;
    font-weight:             700;
    letter-spacing:          0.06em;
    line-height:             1.1;
}

/* ── Section Labels ──────────────────────────────────────────────────────── */
.section-label {
    font-family:     var(--font-display) !important;
    font-size:       0.72rem;
    font-weight:     600;
    letter-spacing:  0.12em;
    text-transform:  uppercase;
    color:           var(--text-muted);
    margin-bottom:   0.6rem;
}

/* ── Header Band ─────────────────────────────────────────────────────────── */
.header-band {
    border-bottom:  1px solid rgba(255,255,255,0.06);
    padding:        1.75rem 0 1.25rem;
    margin-bottom:  1.5rem;
}

/* ── Navigation Tabs ─────────────────────────────────────────────────────── */
.nav-tabs {
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    margin-bottom: 1.5rem;
}
.nav-tabs .nav-link {
    color:           var(--text-muted) !important;
    font-family:     var(--font-display) !important;
    font-weight:     600;
    letter-spacing:  0.08em;
    text-transform:  uppercase;
    font-size:       0.8rem;
    border:          none !important;
    border-bottom:   2px solid transparent !important;
    background:      transparent !important;
    transition:      var(--transition);
    padding:         0.6rem 1.4rem;
}
.nav-tabs .nav-link:hover  { color: var(--cyan) !important; }
.nav-tabs .nav-link.active {
    color:          var(--cyan) !important;
    background:     transparent !important;
    border-bottom:  2px solid var(--cyan) !important;
}

/* ── Custom Scrollbar ────────────────────────────────────────────────────── */
::-webkit-scrollbar             { width: 6px; }
::-webkit-scrollbar-track       { background: var(--bg-deep); }
::-webkit-scrollbar-thumb       { background: rgba(0,242,254,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--cyan); }

/* ── Skeleton / Shimmer Loading ──────────────────────────────────────────── */
@keyframes shimmer {
    0%   { background-position: -1000px 0; }
    100% { background-position:  1000px 0; }
}
.skeleton {
    background:      linear-gradient(90deg, #111827 25%, #1e2535 50%, #111827 75%);
    background-size: 2000px 100%;
    animation:       shimmer 2s infinite;
    border-radius:   8px;
    height:          20px;
}

/* ── Controls Panel ──────────────────────────────────────────────────────── */
.controls-panel {
    background:    rgba(255,255,255,0.025);
    border:        1px solid rgba(0,242,254,0.13);
    border-radius: var(--radius);
    padding:       1.4rem 1.6rem 1.5rem;
    margin-bottom: 1.5rem;
    position:      relative;
    z-index:       100;
    overflow:      visible;
}
.controls-panel:hover {
    border-color: rgba(0,242,254,0.22);
}
.control-label {
    display:         flex;
    align-items:     center;
    gap:             6px;
    font-family:     var(--font-display) !important;
    font-size:       0.7rem;
    font-weight:     600;
    letter-spacing:  0.12em;
    text-transform:  uppercase;
    color:           var(--text-muted);
    margin-bottom:   0.55rem;
}
.control-hint {
    font-family:  var(--font-body);
    font-size:    0.68rem;
    color:        rgba(148,163,184,0.6);
    margin-top:   6px;
    margin-bottom: 0;
}

/* ── Range Slider ────────────────────────────────────────────────────────── */
.rc-slider                        { height: 6px !important; padding: 14px 0 !important; }
.rc-slider-rail                   { background: rgba(255,255,255,0.08) !important; height: 4px !important; border-radius: 2px !important; }
.rc-slider-track                  { background: linear-gradient(90deg, var(--cyan-mid), var(--cyan)) !important; height: 4px !important; border-radius: 2px !important; }
.rc-slider-handle {
    width: 18px !important; height: 18px !important; margin-top: -7px !important;
    background: var(--bg-deep) !important;
    border: 2px solid var(--cyan) !important;
    box-shadow: 0 0 8px rgba(0,242,254,0.45) !important;
    transition: var(--transition) !important;
    opacity: 1 !important;
}
.rc-slider-handle:active,
.rc-slider-handle:focus           { box-shadow: 0 0 0 6px rgba(0,242,254,0.18), 0 0 14px rgba(0,242,254,0.35) !important; }
.rc-slider-dot-active             { border-color: var(--cyan) !important; }
.rc-slider-mark-text              { color: var(--text-muted) !important; font-size: 0.7rem !important; font-family: var(--font-body) !important; }
.rc-slider-tooltip-inner          { background: #0d1220 !important; border: 1px solid rgba(0,242,254,0.25) !important; border-radius: 6px !important; font-family: var(--font-body) !important; font-size: 0.78rem !important; color: var(--cyan) !important; padding: 3px 8px !important; }

/* ── Dash 4 Dropdown (dash-dropdown-* class names) ───────────────────────── */
/* Trigger / closed state */
.dash-dropdown                         { font-family: var(--font-body) !important; }
.dash-dropdown-grid-container.dash-dropdown-trigger {
    background:    rgba(255,255,255,0.04) !important;
    border:        1px solid rgba(0,242,254,0.2) !important;
    border-radius: 10px !important;
    min-height:    46px !important;
    padding:       4px 12px !important;
    cursor:        pointer !important;
    transition:    var(--transition) !important;
    align-items:   center !important;
}
.dash-dropdown-grid-container.dash-dropdown-trigger:hover {
    border-color:  rgba(0,242,254,0.42) !important;
    background:    rgba(0,242,254,0.03) !important;
}
.dash-dropdown-wrapper:focus-within .dash-dropdown-grid-container.dash-dropdown-trigger {
    border-color:  var(--cyan) !important;
    box-shadow:    0 0 0 3px rgba(0,242,254,0.12) !important;
}
.dash-dropdown-placeholder         { color: var(--text-muted) !important; font-size: 0.875rem !important; }
.dash-dropdown-value               { color: var(--text-primary) !important; font-size: 0.875rem !important; }
.dash-dropdown-trigger-icon        { color: var(--text-muted) !important; opacity: 0.7; }
.dash-dropdown-clear               { color: var(--text-muted) !important; cursor: pointer !important; }
.dash-dropdown-clear:hover         { color: var(--red) !important; }
/* Selected chips */
.dash-dropdown-value-item {
    background:    rgba(0,242,254,0.1) !important;
    border:        1px solid rgba(0,242,254,0.3) !important;
    border-radius: 7px !important;
    color:         var(--cyan) !important;
    font-size:     0.8rem !important;
    padding:       2px 8px !important;
    margin:        2px 3px !important;
    display:       inline-flex !important;
    align-items:   center !important;
    gap:           6px !important;
}
.dash-dropdown-value-item img {
    width:         20px !important;
    height:        20px !important;
    border-radius: 50% !important;
    object-fit:    cover !important;
}
/* Open panel */
.dash-dropdown-content {
    background:    #0d1220 !important;
    border:        1px solid rgba(0,242,254,0.25) !important;
    border-radius: 12px !important;
    box-shadow:    0 16px 48px rgba(0,0,0,0.7) !important;
    z-index:       9999 !important;
    overflow:      hidden !important;
    margin-top:    5px !important;
}
.dash-dropdown-search-container    { background: rgba(255,255,255,0.03) !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; padding: 8px 12px !important; display: flex !important; align-items: center !important; gap: 8px !important; }
.dash-dropdown-search-icon         { color: var(--text-muted) !important; font-size: 0.9rem !important; }
.dash-dropdown-search              { background: transparent !important; color: var(--text-primary) !important; font-family: var(--font-body) !important; font-size: 0.875rem !important; border: none !important; outline: none !important; width: 100% !important; }
.dash-dropdown-search::placeholder { color: var(--text-muted) !important; }
.dash-dropdown-actions             { background: rgba(255,255,255,0.02) !important; border-bottom: 1px solid rgba(255,255,255,0.06) !important; padding: 5px 12px !important; display: flex !important; gap: 4px !important; }
.dash-dropdown-action-button       { color: var(--cyan) !important; font-family: var(--font-display) !important; font-size: 0.72rem !important; font-weight: 600 !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; background: transparent !important; border: none !important; cursor: pointer !important; padding: 3px 8px !important; border-radius: 4px !important; }
.dash-dropdown-action-button:hover { background: rgba(0,242,254,0.08) !important; color: var(--text-primary) !important; }
.dash-dropdown-options             { background: transparent !important; max-height: 260px !important; overflow-y: auto !important; }
/* Individual option rows — each option contains a small icon img + name span */
.dash-dropdown-option {
    background:    transparent !important;
    color:         var(--text-secondary) !important;
    font-family:   var(--font-body) !important;
    font-size:     0.875rem !important;
    padding:       0 !important;
    cursor:        pointer !important;
    transition:    all 0.12s ease !important;
    border-bottom: 1px solid rgba(255,255,255,0.03) !important;
    display:       flex !important;
    align-items:   center !important;
}
.dash-dropdown-option > div        { display: flex !important; align-items: center !important; gap: 10px !important; padding: 8px 14px !important; width: 100% !important; }
.dash-dropdown-option img          { width: 28px !important; height: 28px !important; border-radius: 50% !important; object-fit: cover !important; flex-shrink: 0 !important; }
.dash-dropdown-option:hover        { background: rgba(0,242,254,0.07) !important; color: var(--cyan) !important; }
.dash-dropdown-option:hover span   { color: var(--cyan) !important; }
.dash-dropdown-option[aria-selected="true"]        { background: rgba(0,242,254,0.12) !important; }
.dash-dropdown-option[aria-selected="true"] span   { color: var(--cyan) !important; font-weight: 600 !important; }

/* ── Plotly Loading Spinner ──────────────────────────────────────────────── */
._dash-loading-callback { color: var(--cyan) !important; }
"""


# =============================================================================
# SECTION 2 — DATA LAYER
# =============================================================================
def _mock_data() -> pd.DataFrame:
    """Expanded 30-champion mock spanning all 4 tier buckets."""
    return pd.DataFrame({
        'champion': [
            # S-Tier (3)
            'Jinx', 'Katarina', 'Fiora',
            # A-Tier (7)
            'Lux', 'Ahri', 'Yasuo', 'Zed', 'Thresh', 'Leona', 'Orianna',
            # B-Tier (12)
            'Lee Sin', 'Jhin', 'Ezreal', 'Tristana', 'Vayne', 'Syndra',
            'Viktor', 'Cassiopeia', 'Garen', 'Renekton', 'Camille', 'Akali',
            # C-Tier (8)
            'Azir', 'Ryze', 'Kalista', 'Irelia', 'Gangplank', 'Taliyah',
            'Corki', 'Shaco',
        ],
        'win_rate_pct': [
            # S-Tier
            55.8, 54.3, 53.9,
            # A-Tier
            52.7, 52.1, 51.8, 51.4, 51.1, 51.0, 51.2,
            # B-Tier
            50.6, 50.4, 50.1, 49.8, 49.6, 49.9,
            50.3, 49.7, 49.5, 50.2, 50.0, 49.3,
            # C-Tier
            48.4, 47.9, 47.2, 46.8, 46.1, 45.5, 44.9, 44.1,
        ],
        'matches_played': [
            # S-Tier (popular + dominant)
            38000, 22000, 15000,
            # A-Tier
            42000, 35000, 45000, 30000, 28000, 19000, 17000,
            # B-Tier
            40000, 33000, 36000, 25000, 29000, 14000,
            12000, 8000, 6000, 18000, 11000, 16000,
            # C-Tier (niche, low volume)
            9000, 13000, 5000, 21000, 7000, 4000, 3500, 3000,
        ],
    })


def get_data() -> pd.DataFrame:
    query = """
        SELECT
            champion,
            win_rate_pct,
            COALESCE(matches_played, 1000) AS matches_played
        FROM gold_champion_stats_lol
        ORDER BY win_rate_pct DESC
    """
    try:
        with sql.connect(
            server_hostname=SERVER_HOSTNAME,
            http_path=HTTP_PATH,
            access_token=ACCESS_TOKEN,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                df = pd.DataFrame([r.asDict() for r in rows])

        df.columns = df.columns.str.lower().str.strip()
        required = {'champion', 'win_rate_pct', 'matches_played'}
        if df.empty or not required.issubset(set(df.columns)):
            print("WARNING: missing columns or empty result — using mock data")
            return _mock_data()
        return df

    except Exception as exc:
        print(f"Databricks connection error: {exc}")
        return _mock_data()


def derive_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) < 3:
        df = df.copy()
        df['tier']           = 'B-Tier'
        df['win_rate_delta'] = df['win_rate_pct'] - 50.0
        df['wr_normalized']  = 50.0
        df['pop_normalized'] = 50.0
        return df

    df = df.copy()

    bins   = [0, 49, 51, 53, 100]
    labels = ['C-Tier', 'B-Tier', 'A-Tier', 'S-Tier']
    df['tier'] = pd.cut(df['win_rate_pct'], bins=bins, labels=labels, right=True)
    df['tier'] = df['tier'].fillna('B-Tier').astype(str)

    df['win_rate_delta'] = df['win_rate_pct'] - 50.0

    wr_min, wr_max = df['win_rate_pct'].min(), df['win_rate_pct'].max()
    mp_min, mp_max = df['matches_played'].min(), df['matches_played'].max()

    df['wr_normalized']  = (df['win_rate_pct']   - wr_min) / max(wr_max - wr_min, 1e-9) * 100
    df['pop_normalized'] = (df['matches_played']  - mp_min) / max(mp_max - mp_min, 1e-9) * 100

    return df


# =============================================================================
# SECTION 3 — APP INITIALIZATION
# =============================================================================
_EXTERNAL_STYLESHEETS = [
    dbc.themes.DARKLY,
    "https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap",
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
]

app = dash.Dash(
    __name__,
    external_stylesheets=_EXTERNAL_STYLESHEETS,
    suppress_callback_exceptions=True,
)
server = app.server  # WSGI entry point for production deployment

app.index_string = (
    """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>LoL Meta Analytics</title>
        {%favicon%}
        {%css%}
        <style>
"""
    + CUSTOM_CSS
    + """
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""
)


# =============================================================================
# SECTION 4 — COMPONENT FACTORIES (pure functions → no side-effects)
# =============================================================================
_CHART_BASE = dict(
    plot_bgcolor  = "rgba(0,0,0,0)",
    paper_bgcolor = "rgba(0,0,0,0)",
    font          = dict(family="Inter, sans-serif", color=COLORS['text_primary']),
    hoverlabel    = dict(
        bgcolor     = "#111827",
        bordercolor = COLORS['cyan'],
        font_family = "Inter, sans-serif",
        font_color  = COLORS['text_primary'],
    ),
    margin = dict(l=10, r=10, t=44, b=10),
)

_TITLE_FONT = dict(family="'Rajdhani', sans-serif", size=17, color=COLORS['text_primary'])
_AXIS_FONT  = dict(color=COLORS['text_secondary'], size=10)


def _empty_fig(message: str = "") -> go.Figure:
    fig = go.Figure()
    if message:
        fig.add_annotation(
            text=message, xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color=COLORS['text_secondary']),
        )
    fig.update_layout(**_CHART_BASE)
    return fig


# ── Champion Image Overlay for bar charts ─────────────────────────────────
def _add_champion_images(fig: go.Figure, champions: list) -> go.Figure:
    """Overlay circular champion icons along the y-axis of a horizontal bar chart."""
    for champ in champions:
        fig.add_layout_image(dict(
            source=_champion_icon_url(champ),
            xref="paper", yref="y",
            x=-0.01,
            y=champ,
            sizex=0.09,
            sizey=0.7,
            xanchor="right",
            yanchor="middle",
            layer="above",
        ))
    return fig


# ── Sparkline ──────────────────────────────────────────────────────────────
def build_sparkline(values, color: str = COLORS['cyan']) -> go.Figure:
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fig = go.Figure(go.Scatter(
        y=list(values),
        mode='lines',
        line=dict(color=color, width=1.5),
        fill='tozeroy',
        fillcolor=f"rgba({r},{g},{b},0.12)",
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False, hovermode=False,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True),
    )
    return fig


# ── KPI Card ───────────────────────────────────────────────────────────────
def build_kpi_card(
    title:            str,
    value:            str,
    delta_value,
    delta_label:      str,
    icon_class:       str,
    sparkline_values,
    accent_color:     str = None,
) -> dbc.Card:
    accent = accent_color or COLORS['cyan']

    if delta_value is None:
        delta_node = html.Span("—", style={"color": COLORS['text_secondary'], "fontSize": "0.8rem"})
    else:
        sym   = "▲" if delta_value >= 0 else "▼"
        dcolor = COLORS['emerald'] if delta_value >= 0 else COLORS['red']
        delta_node = html.Div([
            html.Span(f"{sym} {abs(delta_value):.1f}",
                      style={"color": dcolor, "fontWeight": "600", "fontSize": "0.8rem"}),
            html.Span(f"  {delta_label}",
                      style={"color": COLORS['text_secondary'], "fontSize": "0.78rem"}),
        ])

    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon_class} me-2",
                       style={"color": accent, "fontSize": "0.95rem"}),
                html.Span(title, style={
                    "fontSize": "0.7rem", "fontWeight": "600",
                    "letterSpacing": "0.1em", "textTransform": "uppercase",
                    "color": COLORS['text_secondary'],
                }),
            ], className="d-flex align-items-center mb-2"),

            (value if not isinstance(value, str) else html.H2(value, style={
                "fontFamily": "'Rajdhani', sans-serif",
                "fontWeight": "700", "fontSize": "2.1rem",
                "color": accent, "margin": "0 0 4px 0", "lineHeight": "1",
            })),

            html.Div(delta_node, className="mb-2"),

            dcc.Graph(
                figure=build_sparkline(sparkline_values, color=accent),
                config={'displayModeBar': False, 'staticPlot': True},
                style={"height": "48px"},
            ),
        ], style={"padding": "1.25rem 1.25rem 0.75rem"}),

        className="glass-card",
        style={
            "borderLeft":   f"4px solid {accent}",
            "borderTop":    "none",
            "borderRight":  "none",
            "borderBottom": "none",
        },
    )


# ── Bar Chart (Top 10) ─────────────────────────────────────────────────────
def build_bar_chart(df: pd.DataFrame) -> go.Figure:
    top10      = df.head(10).sort_values('win_rate_pct', ascending=True).copy()
    bar_colors = [COLORS['cyan'] if wr >= 50 else COLORS['red']
                  for wr in top10['win_rate_pct']]

    fig = go.Figure(go.Bar(
        x=top10['win_rate_pct'],
        y=top10['champion'],
        orientation='h',
        marker=dict(color=bar_colors, opacity=0.82, line=dict(width=0)),
        text=[f"  {v:.1f}%" for v in top10['win_rate_pct']],
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary'], size=10),
        customdata=list(zip(top10['matches_played'], top10.get('tier', ['—'] * len(top10)))),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Win Rate: <b>%{x:.1f}%</b><br>"
            "Matches: <b>%{customdata[0]:,}</b><br>"
            "Tier: %{customdata[1]}"
            "<extra></extra>"
        ),
    ))

    fig.add_vline(
        x=50,
        line_dash="dash", line_color=COLORS['text_secondary'], line_width=1,
        annotation_text="50% baseline",
        annotation_position="top right",
        annotation_font=dict(color=COLORS['text_secondary'], size=9),
    )

    _add_champion_images(fig, top10['champion'].tolist())

    x_max = max(top10['win_rate_pct'].max() + 2.5, 53)
    fig.update_layout(
        title=dict(text="Top 10 Win Rates", font=_TITLE_FONT),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS['grid'], zeroline=False,
            range=[40, x_max], ticksuffix="%", tickfont=_AXIS_FONT,
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            tickfont=dict(color=COLORS['text_primary'], size=11),
        ),
        **_CHART_BASE,
    )
    fig.update_layout(margin=dict(l=62, r=70, t=44, b=10))
    return fig


# ── Scatter Chart ──────────────────────────────────────────────────────────
def build_scatter_chart(df: pd.DataFrame, highlighted_champion: str = None) -> go.Figure:
    median_mp   = df['matches_played'].median()
    mp_range    = df['matches_played'].max() - df['matches_played'].min() + 1e-9
    bubble_sizes = ((df['matches_played'] - df['matches_played'].min()) / mp_range * 26 + 8).tolist()

    colors  = [COLORS['cyan'] if wr >= 50 else COLORS['red'] for wr in df['win_rate_pct']]
    symbols = ['circle'] * len(df)

    if highlighted_champion:
        symbols = [
            'star' if ch == highlighted_champion else 'circle'
            for ch in df['champion']
        ]
        bubble_sizes = [
            s * 1.9 if ch == highlighted_champion else s
            for s, ch in zip(bubble_sizes, df['champion'])
        ]

    fig = go.Figure(go.Scatter(
        x=df['matches_played'],
        y=df['win_rate_pct'],
        mode='markers',
        marker=dict(
            color=colors, size=bubble_sizes, symbol=symbols,
            opacity=0.78, line=dict(color=COLORS['grid'], width=0.5),
        ),
        text=df['champion'],
        customdata=list(zip(df.get('tier', ['—'] * len(df)), df['matches_played'])),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Win Rate: <b>%{y:.1f}%</b><br>"
            "Matches: <b>%{customdata[1]:,}</b><br>"
            "Tier: %{customdata[0]}"
            "<extra></extra>"
        ),
    ))

    fig.add_vline(x=median_mp, line_dash="dot", line_color=COLORS['grid'], line_width=1)
    fig.add_hline(y=50.0,      line_dash="dot", line_color=COLORS['grid'], line_width=1)

    quad = dict(xref="paper", yref="y", showarrow=False,
                font=dict(size=9, color=COLORS['text_secondary']),
                bgcolor="rgba(8,11,20,0.65)", borderpad=3)
    wr_max = df['win_rate_pct'].max()
    fig.add_annotation(text="◆ Hidden Gems",     x=0.02, y=wr_max - 0.4, **quad)
    fig.add_annotation(text="◆ Meta Dominants",  x=0.98, y=wr_max - 0.4, **quad)
    fig.add_annotation(text="Niche & Weak ↙",    x=0.02, y=49.4,         **quad)
    fig.add_annotation(text="High-Volume ↓ WR",  x=0.98, y=49.4,         **quad)

    fig.update_layout(
        title=dict(text="Win Rate vs. Play Volume", font=_TITLE_FONT),
        xaxis=dict(
            title="Matches Played", showgrid=True, gridcolor=COLORS['grid'],
            zeroline=False, tickformat=",",
            title_font=dict(color=COLORS['text_secondary'], size=11),
            tickfont=_AXIS_FONT,
        ),
        yaxis=dict(
            title="Win Rate (%)", showgrid=True, gridcolor=COLORS['grid'],
            zeroline=False, ticksuffix="%",
            title_font=dict(color=COLORS['text_secondary'], size=11),
            tickfont=_AXIS_FONT,
        ),
        **_CHART_BASE,
    )
    fig.update_layout(margin=dict(l=10, r=20, t=44, b=30))
    return fig


# ── Distribution Histogram ─────────────────────────────────────────────────
def build_histogram_chart(df: pd.DataFrame) -> go.Figure:
    wr = df['win_rate_pct'].values
    counts, bin_edges = np.histogram(wr, bins=15)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bin_width   = bin_edges[1] - bin_edges[0]
    bar_colors  = [COLORS['cyan'] if c >= 50 else COLORS['red'] for c in bin_centers]

    mu, sigma   = wr.mean(), wr.std()
    x_curve     = np.linspace(wr.min() - 1, wr.max() + 1, 300)
    y_curve     = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_curve - mu) / sigma) ** 2)
    y_scaled    = y_curve * len(df) * bin_width

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bin_centers, y=counts,
        width=bin_width * 0.85,
        marker_color=bar_colors, marker_opacity=0.75,
        name="Champions",
        hovertemplate="WR ~%{x:.1f}%: <b>%{y} champs</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=x_curve, y=y_scaled,
        mode='lines',
        line=dict(color=COLORS['cyan_mid'], width=2, dash='dot'),
        name="Normal curve",
        hoverinfo='skip',
    ))

    fig.add_vline(
        x=50, line_dash="dash", line_color=COLORS['gold'], line_width=1.5,
        annotation_text="50% mark",
        annotation_position="top right",
        annotation_font=dict(color=COLORS['gold'], size=9),
    )

    fig.update_layout(
        title=dict(text="Win Rate Distribution", font=_TITLE_FONT),
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color=COLORS['text_secondary'], size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            title="Win Rate (%)", showgrid=True, gridcolor=COLORS['grid'],
            zeroline=False, ticksuffix="%",
            title_font=dict(color=COLORS['text_secondary'], size=11),
            tickfont=_AXIS_FONT,
        ),
        yaxis=dict(
            title="Champions", showgrid=True, gridcolor=COLORS['grid'],
            zeroline=False,
            title_font=dict(color=COLORS['text_secondary'], size=11),
            tickfont=_AXIS_FONT,
        ),
        bargap=0,
        **_CHART_BASE,
    )
    fig.update_layout(margin=dict(l=10, r=20, t=44, b=30))
    return fig


# ── Tier Treemap ───────────────────────────────────────────────────────────
def build_treemap_chart(df: pd.DataFrame) -> go.Figure:
    tier_col = df['tier'] if 'tier' in df.columns else pd.Series(['B-Tier'] * len(df))
    stats = (
        df.assign(tier=tier_col)
        .groupby('tier', as_index=False)
        .agg(count=('champion', 'count'), avg_wr=('win_rate_pct', 'mean'))
    )
    order = ['S-Tier', 'A-Tier', 'B-Tier', 'C-Tier']
    stats['tier'] = pd.Categorical(stats['tier'], categories=order, ordered=True)
    stats = stats.sort_values('tier').dropna(subset=['tier'])

    fig = go.Figure(go.Treemap(
        labels=stats['tier'].astype(str),
        parents=[''] * len(stats),
        values=stats['count'],
        text=[f"Avg WR: {r:.1f}%  ·  {n} champs"
              for r, n in zip(stats['avg_wr'], stats['count'])],
        textinfo='label+text',
        textfont=dict(family="'Rajdhani', sans-serif", size=13, color='white'),
        marker=dict(
            colors=[TIER_COLORS.get(str(t), COLORS['slate']) for t in stats['tier']],
            line=dict(width=2, color=COLORS['bg_deep']),
        ),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Champions: %{value}<br>"
            "%{text}"
            "<extra></extra>"
        ),
        pathbar=dict(visible=False),
    ))

    fig.update_layout(
        title=dict(text="Champion Tier Map", font=_TITLE_FONT),
        **_CHART_BASE,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=44, b=10))
    return fig


# ── Radar Chart ────────────────────────────────────────────────────────────
_RADAR_COLORS = [
    COLORS['cyan'], COLORS['red'], COLORS['gold'],
    COLORS['purple'], COLORS['emerald'],
]

def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
_RADAR_AXES = ['Win Rate', 'Popularity', 'Above Baseline', 'Overall Score']


def build_radar_chart(df: pd.DataFrame, champions_list: list) -> go.Figure:
    valid = [c for c in champions_list if c in df['champion'].values]
    if len(valid) < 2:
        return _empty_fig("Select at least 2 champions to compare.")

    fig = go.Figure()
    for i, champ in enumerate(valid[:5]):
        row = df[df['champion'] == champ].iloc[0]
        wr_n  = row.get('wr_normalized',  50.0)
        pop_n = row.get('pop_normalized', 50.0)
        delta = row.get('win_rate_delta',  0.0)
        above_baseline = min(max((delta + 10) * 5, 0), 100)
        overall_score  = (wr_n + pop_n) / 2

        values = [wr_n, pop_n, above_baseline, overall_score]
        color  = _RADAR_COLORS[i % len(_RADAR_COLORS)]

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=_RADAR_AXES + [_RADAR_AXES[0]],
            fill='toself',
            fillcolor=_hex_to_rgba(color, 0.13),
            line=dict(color=color, width=2),
            name=champ,
        ))

    fig.update_layout(
        title=dict(text="Champion Comparison Radar", font=_TITLE_FONT),
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickvals=[25, 50, 75, 100],
                ticktext=["25", "50", "75", "100"],
                gridcolor=COLORS['grid'],
                linecolor="rgba(255,255,255,0.06)",
                tickfont=dict(color=COLORS['text_secondary'], size=8),
                tickangle=45,
            ),
            angularaxis=dict(
                gridcolor=COLORS['grid'],
                linecolor="rgba(255,255,255,0.08)",
                tickfont=dict(
                    family="'Rajdhani', sans-serif",
                    color=COLORS['text_primary'],
                    size=12,
                ),
                direction="clockwise",
            ),
        ),
        showlegend=True,
        legend=dict(
            font=dict(color=COLORS['text_secondary'], size=10,
                      family="'Rajdhani', sans-serif"),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom", y=-0.12,
            xanchor="center", x=0.5,
        ),
        **_CHART_BASE,
    )
    fig.update_layout(margin=dict(l=40, r=40, t=50, b=60))
    return fig


# =============================================================================
# SECTION 5 — LAYOUT ARCHITECTURE
# =============================================================================
def _glass(children, mb: int = 4, extra_style: dict = None):
    style = extra_style or {}
    return dbc.Card(
        dbc.CardBody(children, style={"padding": "1rem 1.25rem"}),
        className="glass-card",
        style=style,
    )


_GRAPH_CFG = {'displayModeBar': False}


# ── Tab: Overview ──────────────────────────────────────────────────────────
_tab_overview = dbc.Tab(label="Overview", tab_id="overview", children=[
    dbc.Row([
        dbc.Col(
            _glass([dcc.Loading(
                dcc.Graph(id='bar-chart', config=_GRAPH_CFG, style={"height": "390px"}),
                type="circle", color=COLORS['cyan'],
            )]),
            width=12, lg=5, className="mb-4",
        ),
        dbc.Col(
            _glass([dcc.Loading(
                dcc.Graph(id='scatter-chart', config=_GRAPH_CFG, style={"height": "390px"}),
                type="circle", color=COLORS['cyan'],
            )]),
            width=12, lg=7, className="mb-4",
        ),
    ]),
])


# ── Tab: Champion Deep Dive ────────────────────────────────────────────────
_tab_deep_dive = dbc.Tab(label="Champion Deep Dive", tab_id="deep-dive", children=[

    # Controls panel — overflow:visible so the dropdown menu escapes the card boundary
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="bi bi-search",
                           style={"color": COLORS['cyan'], "fontSize": "0.8rem"}),
                    html.Span("Select Champions  (up to 5)", className="ms-1"),
                ], className="control-label"),
                dcc.Dropdown(
                    id='champion-dropdown',
                    options=[], value=[], multi=True,
                    placeholder="Type or scroll to search…",
                    optionHeight=52,
                ),
                html.P("Click any chart bar to auto-highlight here",
                       className="control-hint"),
            ], width=12, md=6, style={"paddingRight": "2rem"}),

            dbc.Col([
                html.Div([
                    html.I(className="bi bi-sliders",
                           style={"color": COLORS['purple'], "fontSize": "0.8rem"}),
                    html.Span("Win Rate Filter", className="ms-1"),
                ], className="control-label"),
                html.Div(style={"height": "8px"}),
                dcc.RangeSlider(
                    id='wr-slider', min=40, max=60, step=0.5,
                    value=[44, 57],
                    marks={i: {'label': f'{i}%',
                               'style': {'color': COLORS['text_secondary'],
                                         'fontSize': '0.7rem'}}
                           for i in range(40, 61, 5)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.P("Drag handles to narrow the champion pool",
                       className="control-hint"),
            ], width=12, md=6),
        ]),
    ], className="controls-panel"),

    dbc.Row([
        dbc.Col(
            _glass([dcc.Loading(
                dcc.Graph(id='radar-chart', config=_GRAPH_CFG, style={"height": "440px"}),
                type="circle", color=COLORS['cyan'],
            )]),
            width=12, lg=6, className="mb-4",
        ),
        dbc.Col(
            _glass([dcc.Loading(
                dcc.Graph(id='deepdive-bar', config=_GRAPH_CFG, style={"height": "440px"}),
                type="circle", color=COLORS['cyan'],
            )]),
            width=12, lg=6, className="mb-4",
        ),
    ]),
])


# ── Tab: Meta Analysis ─────────────────────────────────────────────────────
_tab_meta = dbc.Tab(label="Meta Analysis", tab_id="meta-analysis", children=[
    dbc.Row([
        dbc.Col(
            _glass([dcc.Loading(
                dcc.Graph(id='histogram-chart', config=_GRAPH_CFG, style={"height": "390px"}),
                type="circle", color=COLORS['cyan'],
            )]),
            width=12, lg=6, className="mb-4",
        ),
        dbc.Col(
            _glass([dcc.Loading(
                dcc.Graph(id='treemap-chart', config=_GRAPH_CFG, style={"height": "390px"}),
                type="circle", color=COLORS['cyan'],
            )]),
            width=12, lg=6, className="mb-4",
        ),
    ]),
])


# ── Root Layout ────────────────────────────────────────────────────────────
app.layout = dbc.Container([

    dcc.Store(id='store-data', storage_type='memory'),
    dcc.Interval(id='interval-clock', interval=60_000, n_intervals=0),

    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span("LOL ", className="gradient-text",
                          style={"fontSize": "2rem", "display": "inline"}),
                html.Span("META ANALYTICS", className="gradient-text",
                          style={"fontSize": "2rem", "display": "inline"}),
            ]),
            html.P(
                "Gold Medallion Tier  ·  Executive Intelligence Dashboard",
                style={
                    "color": COLORS['text_secondary'], "fontSize": "0.8rem",
                    "fontFamily": "var(--font-body)", "marginTop": "5px", "marginBottom": 0,
                },
            ),
        ], width=8),
        dbc.Col(
            html.Div(id='live-clock', className="text-end", style={
                "color": COLORS['text_secondary'], "fontSize": "0.78rem",
                "fontFamily": "var(--font-body)", "paddingTop": "10px",
            }),
            width=4,
        ),
    ], className="header-band"),

    # KPI Row (populated by callback)
    html.Div(id='kpi-row', className="mb-2"),

    # Tabbed content
    dbc.Tabs(
        [_tab_overview, _tab_deep_dive, _tab_meta],
        id='main-tabs',
        active_tab='overview',
    ),

], fluid=True, style={
    "backgroundColor": COLORS['bg_deep'],
    "minHeight": "100vh",
    "padding": "0 4% 2rem",
})


# =============================================================================
# SECTION 6 — CALLBACKS
# =============================================================================

# 1 · Data loader — runs once on page load, then every 60 s
@app.callback(
    Output('store-data', 'data'),
    Input('interval-clock', 'n_intervals'),
)
def load_data(_n):
    df = get_data()
    df = derive_metrics(df)
    return df.to_dict('records')


# 2 · Live clock
@app.callback(
    Output('live-clock', 'children'),
    Input('interval-clock', 'n_intervals'),
)
def update_clock(_n):
    return datetime.now().strftime("Last sync: %d %b %Y  %H:%M")


# 3 · KPI cards
@app.callback(
    Output('kpi-row', 'children'),
    Input('store-data', 'data'),
)
def populate_kpis(data):
    if not data:
        return []

    df       = pd.DataFrame(data).sort_values('win_rate_pct', ascending=False).reset_index(drop=True)
    avg_wr   = df['win_rate_pct'].mean()
    top_row  = df.iloc[0]
    top_chmp = top_row['champion']
    top_wr   = top_row['win_rate_pct']
    total    = len(df)

    spark_all    = df['win_rate_pct'].sort_values().values
    spark_top5   = df.head(5)['win_rate_pct'].values[::-1]
    tier_order   = ['C-Tier', 'B-Tier', 'A-Tier', 'S-Tier']
    spark_tiers  = (df.groupby('tier')['champion'].count()
                    .reindex(tier_order, fill_value=0).values
                    if 'tier' in df.columns else [0, total, 0, 0])

    kpi1 = build_kpi_card(
        title="Avg Win Rate", value=f"{avg_wr:.1f}%",
        delta_value=avg_wr - 50.0, delta_label="vs 50% baseline",
        icon_class="bi bi-graph-up-arrow",
        sparkline_values=spark_all,
        accent_color=COLORS['cyan'] if avg_wr >= 50 else COLORS['red'],
    )
    champion_display = html.Div([
        html.Img(
            src=_champion_icon_url(top_chmp),
            style={
                "width": "48px", "height": "48px",
                "borderRadius": "50%", "objectFit": "cover",
                "border": f"2px solid {COLORS['gold']}",
                "boxShadow": "0 0 14px rgba(255,215,0,0.35)",
                "flexShrink": "0",
            },
        ),
        html.Span(top_chmp, style={
            "fontFamily": "'Rajdhani', sans-serif",
            "fontWeight": "700", "fontSize": "1.8rem",
            "color": COLORS['gold'], "marginLeft": "12px",
            "lineHeight": "1",
        }),
    ], style={"display": "flex", "alignItems": "center", "margin": "0 0 4px 0"})

    kpi2 = build_kpi_card(
        title="Dominant Champion", value=champion_display,
        delta_value=top_wr - avg_wr, delta_label="above average",
        icon_class="bi bi-trophy-fill",
        sparkline_values=spark_top5,
        accent_color=COLORS['gold'],
    )
    kpi3 = build_kpi_card(
        title="Champions Tracked", value=str(total),
        delta_value=None, delta_label="",
        icon_class="bi bi-controller",
        sparkline_values=spark_tiers,
        accent_color=COLORS['emerald'],
    )

    return dbc.Row([
        dbc.Col(kpi1, width=12, md=4, className="mb-4"),
        dbc.Col(kpi2, width=12, md=4, className="mb-4"),
        dbc.Col(kpi3, width=12, md=4, className="mb-4"),
    ])


# 4 · Overview charts + cross-filter
@app.callback(
    Output('bar-chart',     'figure'),
    Output('scatter-chart', 'figure'),
    Input('store-data',  'data'),
    Input('bar-chart',   'clickData'),
)
def update_overview(data, click_data):
    if not data:
        return _empty_fig(), _empty_fig()

    df = pd.DataFrame(data).sort_values('win_rate_pct', ascending=False).reset_index(drop=True)

    highlighted = None
    if ctx.triggered_id == 'bar-chart' and click_data:
        try:
            highlighted = click_data['points'][0]['y']
        except (KeyError, IndexError):
            pass

    return build_bar_chart(df), build_scatter_chart(df, highlighted_champion=highlighted)


# 5a · Populate dropdown options — separate callback, no circular dependency
@app.callback(
    Output('champion-dropdown', 'options'),
    Input('store-data', 'data'),
)
def populate_dropdown_options(data):
    if not data:
        return []
    df    = pd.DataFrame(data).sort_values('win_rate_pct', ascending=False).reset_index(drop=True)
    tiers = df['tier'].astype(str).tolist() if 'tier' in df.columns else ['B-Tier'] * len(df)
    return [
        {
            'label': html.Div([
                html.Img(
                    src=_champion_icon_url(ch),
                    style={
                        "width": "26px", "height": "26px",
                        "borderRadius": "50%", "objectFit": "cover",
                        "border": f"1.5px solid {TIER_COLORS.get(t, COLORS['slate'])}",
                        "flexShrink": "0",
                    },
                ),
                html.Span(f"{ch}  [{t}]", style={
                    "marginLeft": "9px",
                    "fontSize": "0.875rem",
                    "color": COLORS['text_primary'],
                }),
            ], style={"display": "flex", "alignItems": "center"}),
            'value': ch,
            'search': ch,
        }
        for ch, t in zip(df['champion'], tiers)
    ]


# 5b · Deep Dive charts
@app.callback(
    Output('radar-chart',  'figure'),
    Output('deepdive-bar', 'figure'),
    Input('champion-dropdown', 'value'),
    Input('wr-slider',         'value'),
    Input('store-data',        'data'),
)
def update_deep_dive(selected, wr_range, data):
    if not data:
        return _empty_fig(), _empty_fig()

    df = pd.DataFrame(data).sort_values('win_rate_pct', ascending=False).reset_index(drop=True)

    lo, hi   = (wr_range or [40, 60])
    filtered = df[(df['win_rate_pct'] >= lo) & (df['win_rate_pct'] <= hi)]

    if not selected:
        to_show = filtered.head(5)['champion'].tolist()
    else:
        to_show = [c for c in selected if c in df['champion'].values]
        if not to_show:
            to_show = filtered.head(5)['champion'].tolist()

    radar_fig = build_radar_chart(df, to_show)

    subset = df[df['champion'].isin(to_show)].sort_values('win_rate_pct', ascending=True)
    if subset.empty:
        subset = filtered.sort_values('win_rate_pct', ascending=True)

    _tier_bar_colors = {
        'S-Tier': COLORS['gold'],
        'A-Tier': COLORS['purple'],
        'B-Tier': COLORS['blue'],
        'C-Tier': COLORS['slate'],
    }
    tier_col   = subset['tier'].astype(str) if 'tier' in subset.columns else ['B-Tier'] * len(subset)
    dd_colors  = [_tier_bar_colors.get(t, COLORS['cyan']) for t in tier_col]
    delta_vals = (subset['win_rate_pct'] - 50.0).round(1)
    delta_text = [
        f"  {v:.1f}%  {'▲' if d >= 0 else '▼'}{abs(d):.1f}"
        for v, d in zip(subset['win_rate_pct'], delta_vals)
    ]

    dd_bar = go.Figure(go.Bar(
        x=subset['win_rate_pct'],
        y=subset['champion'],
        orientation='h',
        marker=dict(
            color=dd_colors,
            opacity=0.85,
            line=dict(width=0),
        ),
        text=delta_text,
        textposition='outside',
        textfont=dict(color=COLORS['text_secondary'], size=10,
                      family="'Rajdhani', sans-serif"),
        customdata=list(zip(
            tier_col,
            subset['matches_played'],
            delta_vals,
        )),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Win Rate: <b>%{x:.1f}%</b><br>"
            "vs Baseline: <b>%{customdata[2]:+.1f}%</b><br>"
            "Matches: <b>%{customdata[1]:,}</b><br>"
            "Tier: <b>%{customdata[0]}</b>"
            "<extra></extra>"
        ),
    ))

    dd_bar.add_vline(
        x=50,
        line_dash="dash", line_color="rgba(148,163,184,0.4)", line_width=1.5,
        annotation_text="50%",
        annotation_position="top left",
        annotation_font=dict(color=COLORS['text_secondary'], size=9),
    )

    # Tier legend annotations (right side)
    for tier, color in _tier_bar_colors.items():
        dd_bar.add_annotation(
            text=f"<b>{tier}</b>",
            xref="paper", yref="paper",
            x=1.01, y={"S-Tier": 0.95, "A-Tier": 0.82, "B-Tier": 0.68, "C-Tier": 0.55}[tier],
            showarrow=False,
            font=dict(color=color, size=9, family="'Rajdhani', sans-serif"),
            xanchor="left",
        )

    _add_champion_images(dd_bar, subset['champion'].tolist())

    x_max = max(subset['win_rate_pct'].max() + 3.5, 54)
    dd_bar.update_layout(
        title=dict(text="Selected Champion Stats", font=_TITLE_FONT),
        xaxis=dict(
            showgrid=True, gridcolor=COLORS['grid'], zeroline=False,
            range=[40, x_max], ticksuffix="%", tickfont=_AXIS_FONT,
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            tickfont=dict(color=COLORS['text_primary'], size=12),
        ),
        **_CHART_BASE,
    )
    dd_bar.update_layout(margin=dict(l=62, r=88, t=44, b=10))

    return radar_fig, dd_bar


# 6 · Meta Analysis tab
@app.callback(
    Output('histogram-chart', 'figure'),
    Output('treemap-chart',   'figure'),
    Input('store-data', 'data'),
)
def update_meta(data):
    if not data:
        return _empty_fig(), _empty_fig()
    df = pd.DataFrame(data)
    return build_histogram_chart(df), build_treemap_chart(df)


# =============================================================================
# SECTION 7 — SERVER GUARD
# =============================================================================
if __name__ == '__main__':
    app.run(debug=False, port=8050)

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import Fullscreen
from streamlit_folium import st_folium

st.set_page_config(
    page_title="CityPulse — Neighborhood Intelligence",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* Global White Base Setup */
html, body, [class*="css"], .main {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #ffffff !important;
    color: #1e293b !important;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
    max-width: 1440px;
}

/* Structural Grids Hierarchy */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #0f172a !important;
    margin-top: 0px;
}

/* Premium Blueprint Sidebar Restyling */
section[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 3px solid #0f172a !important;
    padding: 10px;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] label {
    color: #1e293b !important;
    font-weight: 600;
}

/* Sketchpen Border Box Structures */
.city-container {
    background: #ffffff;
    border: 3px solid #0f172a;
    border-radius: 6px;
    padding: 22px;
    margin-bottom: 16px !important; /* Fixed vertical layout collapsing gaps */
    box-shadow: 4px 4px 0px 0px #0f172a;
}

.hero-section {
    background: #f8fafc;
    border: 3px solid #0f172a;
    border-radius: 8px;
    padding: 28px;
    margin-bottom: 20px;
    box-shadow: 6px 6px 0px 0px #0f172a;
}

.zone-card {
    border: 3px solid #0f172a;
    border-radius: 6px;
    padding: 18px;
    margin-bottom: 12px;
    box-shadow: 4px 4px 0px 0px #0f172a;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.zone-card:hover {
    transform: translate(-2px, -2px);
    box-shadow: 6px 6px 0px 0px #0f172a;
}

/* Badges & Tags */
.tier-badge {
    display: inline-block;
    padding: 4px 10px;
    border: 2px solid #0f172a;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}

.stat-chip {
    background: #ffffff;
    border: 2px solid #0f172a;
    color: #0f172a;
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    margin: 4px 6px 4px 0;
}

.score-number {
    font-family: 'JetBrains+Mono', monospace;
    font-size: 38px;
    font-weight: 700;
    line-height: 1;
    margin-top: 6px;
}

/* Specialized Custom Alert Banner Panels */
.confidence-high { border: 3px solid #0f172a; border-left: 10px solid #16a34a; background: #ffffff; color: #166534; box-shadow: 4px 4px 0px 0px #0f172a; }
.confidence-moderate { border: 3px solid #0f172a; border-left: 10px solid #d97706; background: #ffffff; color: #92400e; box-shadow: 4px 4px 0px 0px #0f172a; }
.confidence-low { border: 3px solid #0f172a; border-left: 10px solid #dc2626; background: #ffffff; color: #991b1b; box-shadow: 4px 4px 0px 0px #0f172a; }

.cache-badge {
    background: #ffffff;
    border: 2px solid #16a34a;
    color: #16a34a;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 700;
}

/* Custom Overrides for Native Elements */
div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 3px solid #0f172a !important;
    border-radius: 6px !important;
    padding: 14px !important;
    box-shadow: 3px 3px 0px 0px #0f172a !important;
}

/* Tabs Navigation Styling Layouts */
button[data-baseweb="tab"] {
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #64748b !important;
    border: 2px solid transparent !important;
}
button[aria-selected="true"] {
    color: #0f172a !important;
    background: #f8fafc !important;
    border: 3px solid #0f172a !important;
    border-bottom: 3px solid #f8fafc !important;
    border-radius: 6px 6px 0 0 !important;
}

/* System Vectors Core SVGs Icons Dimensions Mapping */
.panel-icon {
    display: inline-block;
    width: 18px;
    height: 18px;
    vertical-align: text-top;
    margin-right: 6px;
    fill: currentColor;
}
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000"

TIER_COLORS = {
    "Premium":         "#16a34a",  # Urban Parks Green
    "Good":            "#22c55e",  # Secondary Green
    "Balanced":        "#eab308",  # Industrial Amber / Yellow
    "Economy":         "#f97316",  # Signal Orange
    "Budget Friendly": "#ea580c",  # Deep Transit Orange
    "Unclustered":     "#64748b",  # Zinc/Gray
    "Uniform":         "#64748b",
}

TIER_CARD_STYLE = {
    "Premium":         {"bg": "#f0fdf4", "text": "#14532d", "accent": "#16a34a"},
    "Good":            {"bg": "#f0fdf4", "text": "#14532d", "accent": "#22c55e"},
    "Balanced":        {"bg": "#fefce8", "text": "#713f12", "accent": "#ca8a04"},
    "Economy":         {"bg": "#fff7ed", "text": "#7c2d12", "accent": "#ea580c"},
    "Budget Friendly": {"bg": "#fff7ed", "text": "#7c2d12", "accent": "#dc2626"},
    "Unclustered":     {"bg": "#f8fafc", "text": "#334155", "accent": "#64748b"},
    "Uniform":         {"bg": "#f8fafc", "text": "#334155", "accent": "#64748b"},
}

SVG_ICONS = {
    "city": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M19 2H5c-1.1 0-2 .9-2 2v18h18V4c0-1.1-.9-2-2-2zm-6 18h-2v-2h2v2zm0-4h-2v-2h2v2zm0-4h-2V8h2v2zm0-4h-2V4h2v2zm6 12h-2v-2h2v2zm0-4h-2v-2h2v2zm0-4h-2V8h2v2zm0-4h-2V4h2v2zM7 20H5v-2h2v2zm0-4H5v-2h2v2zm0-4H5V8h2v2zm0-4H5V4h2v2z"/></svg>',
    "food": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm7-3c-2.21 0-4 1.79-4 4v12h8V10c0-2.21-1.79-4-4-4z"/></svg>',
    "transit": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M4 16c0 .88.39 1.67 1 2.22V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h8v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1c-.83 0-1.5-.67-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm9 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm1.5-6H6V6h12v5z"/></svg>',
    "health": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-1.99.9-1.99 2L3 19c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 11h-4v4h-4v-4H6v-4h4V6h4v4h4v4z"/></svg>',
    "green": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M12 2C11.31 2 10 3.44 10 5c0 1.31 1.12 2.19 2 3 .88-.81 2-1.69 2-3 0-1.56-1.31-3-2-3zm0 6c-3.07 0-5.5 2.43-5.5 5.5 0 2.24 1.25 4.14 3.06 5.05l-.56 2.45h6l-.56-2.45c1.81-.91 3.06-2.81 3.06-5.05C17.5 10.43 15.07 8 12 8z"/></svg>',
    "education": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"/></svg>',
    "finance": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M4 10h3v7H4zm6.5 0h3v7h-3zM2 22h19v-3H2zm15-12h3v7h-3zM11.5 2L2 7h19z"/></svg>',
    "shopping": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2zM1 2h20v2H1z"/></svg>',
    "settings": '<svg class="panel-icon" viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>'
}

PERSONA_WEIGHTS = {
    "Student": {
        "food": 3, "transit": 5, "health": 1,
        "green": 1, "education": 5, "finance": 2, "shopping": 2,
    },
    "Working Professional": {
        "food": 4, "transit": 4, "health": 2,
        "green": 2, "education": 1, "finance": 3, "shopping": 3,
    },
    "Family": {
        "food": 3, "transit": 3, "health": 5,
        "green": 4, "education": 4, "finance": 2, "shopping": 3,
    },
}

def check_backend_health() -> bool:
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def call_api(city: str, weights: dict, n_zones: int) -> dict:
    try:
        response = requests.post(
            f"{API_URL}/score",
            json={"city": city, "weights": weights, "n_zones": n_zones},
            timeout=180,
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to the backend. "
            "Make sure FastAPI is running: `uvicorn api:app --reload`"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Request timed out after 3 minutes. "
            "The dataset may be too large — try reducing the number of zones."
        )
    except Exception as e:
        raise RuntimeError(f"Unexpected network error: {e}")

    if response.status_code != 200:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"API error {response.status_code}: {detail}")

    return response.json()

def build_map(df: pd.DataFrame) -> folium.Map:
    m = folium.Map(
        location=[df["lat"].mean(), df["lon"].mean()],
        zoom_start=11,
        tiles="CartoDB positron", 
    )
    Fullscreen().add_to(m)

    max_score = df["total_score"].max() or 1.0

    for _, row in df.iterrows():
        radius = 8 + (row["total_score"] / max_score) * 16
        color = TIER_COLORS.get(row.get("tier", ""), "#38bdf8")

        popup_html = f"""
        <div style='font-family:Space Grotesk,sans-serif;min-width:200px;
                    background:#ffffff;color:#1e293b;padding:14px;border:3px solid #0f172a;border-radius:6px;'>
            <b style='font-size:15px;display:block;margin-bottom:2px;color:#0f172a;'>{row['zone_id']}</b>
            <span style='color:{color};font-weight:700;font-size:12px;text-transform:uppercase;'>{row.get('tier','')}</span>
            <span style='font-size:24px;font-weight:700;color:#0f172a;
                         display:block;margin:6px 0'>{row['total_score']:.1f}</span>
            <hr style='border-color:#0f172a;margin:8px 0'>
            <div style='font-size:12px;line-height:1.6;color:#1e293b;'>
                Food Allocation: <b>{row['food_count']}</b><br>
                Transit Access: <b>{row['transit_count']}</b><br>
                Health Vectors: <b>{row['health_count']}</b><br>
                Green Canopy: <b>{row['green_count']}</b><br>
                Education Nodes: <b>{row['education_count']}</b><br>
                Shopping Density: <b>{row['shopping_count']}</b>
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color="#0f172a",
            weight=3,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{row['zone_id']} — {row['total_score']:.1f}",
        ).add_to(m)

    return m

st.sidebar.markdown(
    f"<h2 style='margin-bottom:4px;color:#0f172a;'>{SVG_ICONS['city']} CityPulse</h2>"
    "<p style='color:#475569;font-size:13px;margin-top:0;margin-bottom:16px;'>Spatial Intelligence Platform</p>",
    unsafe_allow_html=True,
)

backend_ok = check_backend_health()
if backend_ok:
    st.sidebar.markdown(
        "<span style='background:#ffffff;color:#16a34a;border:2px solid #16a34a;"
        "border-radius:4px;padding:4px 12px;font-size:12px;font-weight:700;display:inline-block;margin-bottom:20px;'>"
        "CORE CONNECTED</span>",
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        "<span style='background:#ffffff;color:#dc2626;border:2px solid #dc2626;"
        "border-radius:4px;padding:4px 12px;font-size:12px;font-weight:700;display:inline-block;margin-bottom:20px;'>"
        "CORE OFFLINE</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.error("Start Core Matrix Module:\n```\nuvicorn api:app --reload\n```")

st.sidebar.markdown("<hr style='border-color:#0f172a;border-width:2px;margin:12px 0;' />", unsafe_allow_html=True)

city = st.sidebar.selectbox("Location Coordinate Matrix", ["Pune", "Bangalore", "Mumbai"])
persona = st.sidebar.selectbox("Optimization Footprint Profile", list(PERSONA_WEIGHTS.keys()))
preset = PERSONA_WEIGHTS[persona]

st.sidebar.markdown(f"<h4 style='color:#0f172a;margin-top:20px;margin-bottom:10px;'>{SVG_ICONS['settings']} Structural Balancing Vectors</h4>", unsafe_allow_html=True)
weights = {
    "food":      st.sidebar.slider("Food Grid Index",     0, 5, preset["food"]),
    "transit":   st.sidebar.slider("Transit Node Network",    0, 5, preset["transit"]),
    "health":    st.sidebar.slider("Medical Infrastructure",  0, 5, preset["health"]),
    "green":     st.sidebar.slider("Environmental Parks",0, 5, preset["green"]),
    "education": st.sidebar.slider("Educational Footprint",   0, 5, preset["education"]),
    "finance":   st.sidebar.slider("Financial Hub Matrix",     0, 5, preset["finance"]),
    "shopping":  st.sidebar.slider("Commercial Retail Grid",    0, 5, preset["shopping"]),
}
n_zones = st.sidebar.slider("Target Regional Segmentations", 6, 18, 12)

st.sidebar.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
analyze_clicked = st.sidebar.button(
    "Run Environmental Optimization Analysis", use_container_width=True, type="primary"
)

st.markdown(f"""
<div class='hero-section'>
    <h1 style='margin:0 0 6px;font-size:38px;font-weight:800;'>{SVG_ICONS['city']} CityPulse Intelligence Console</h1>
    <p style='color:#334155;font-size:16px;margin:0 0 18px;font-weight:500;max-width:950px;'>
        Spatial variance analysis engine using unsupervised partition configurations and principal components coordinates to evaluate urban zoning distributions.
    </p>
    <div>
        <span class='stat-chip'>Spatial Stream Array</span>
        <span class='stat-chip'>K-Means Clustering Cluster</span>
        <span class='stat-chip'>Haversine Vectors Engine</span>
        <span class='stat-chip'>Protected Edge Interface</span>
    </div>
</div>
""", unsafe_allow_html=True)

if "result_data" not in st.session_state:
    st.session_state.result_data = None
if "result_city" not in st.session_state:
    st.session_state.result_city = None

if analyze_clicked:
    if not backend_ok:
        st.error("System pipeline indicates database processing module offline.")
    else:
        with st.spinner(f"Computing optimization parameters for {city} spatial matrices…"):
            try:
                data = call_api(city, weights, n_zones)
                st.session_state.result_data = data
                st.session_state.result_city = city
                st.success("Target analysis matrix calculated.")
            except RuntimeError as e:
                st.error(f"Structural Computation Fault: {e}")
                st.session_state.result_data = None

data = st.session_state.result_data

if data is None:
    st.markdown("""
    <div class='city-container' style='text-align:center;padding:50px 20px;'>
        <h3 style='color:#64748b;margin-bottom:6px;'>System Standing By for Target Activation Signals</h3>
        <p style='color:#94a3b8;font-size:15px;margin:0;'>Adjust coordinate inputs inside the parameter sidebar options and execute optimization to process regional footprints.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Extract Data Structures
neighborhoods = data.get("neighborhoods", [])
ml_eval       = data.get("ml_evaluation", {})
summary       = data.get("data_summary", {})
confidence    = data.get("confidence", "unknown")
conf_warning  = data.get("confidence_warning")

if not neighborhoods:
    st.error("Empty configuration returns. Diagnostics metrics pipeline contains null values.")
    st.stop()

df = pd.DataFrame(neighborhoods)

if conf_warning:
    css_class = f"confidence-{confidence}"
    st.markdown(
        f"<div class='zone-card {css_class}' style='margin-bottom:16px;padding:14px 20px;font-size:14px;font-weight:700;'>"
        f"Validation Report &rarr; Clustering Model Target Profile Confidence: [{confidence.upper()}] — {conf_warning}"
        f"</div>",
        unsafe_allow_html=True,
    )

if summary.get("served_from_cache"):
    st.markdown(
        "<div style='margin-bottom:16px;'><span class='cache-badge'>Active Data Cache Match Found &mdash; Bypassing Live Query Latency</span></div>",
        unsafe_allow_html=True,
    )

st.markdown("<h2 style='margin-top:24px;margin-bottom:14px;'>Primary Layout Recommendations</h2>", unsafe_allow_html=True)
top3 = df.head(3)
cols = st.columns(3)

for i, (_, row) in enumerate(top3.iterrows()):
    tier = row.get("tier", "Unclustered")
    style_config = TIER_CARD_STYLE.get(tier, TIER_CARD_STYLE["Unclustered"])
    
    bg_color = style_config["bg"]
    text_color = style_config["text"]
    accent_color = style_config["accent"]
    
    with cols[i]:
        st.markdown(
            f"""
            <div class='zone-card' style='background: {bg_color}; border-top: 8px solid {accent_color}; min-height: 210px; display: flex; flex-direction: column; justify-content: space-between;'>
                <div>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                        <span style='font-weight:700;font-size:16px;color:#0f172a'>
                            #{int(row.get('rank', i+1))} {row['zone_id']}
                        </span>
                        <span class='tier-badge' style='color:#0f172a;background:#ffffff;'>
                            {tier}
                        </span>
                    </div>
                    <div class='score-number' style='color:#0f172a'>{row['total_score']:.1f}</div>
                    <div style='font-size:11px;color:#475569;text-transform:uppercase;font-weight:700;letter-spacing:0.02em;margin-top:2px;'>Suitability Index Target</div>
                </div>
                <div>
                    <hr style='border-color:#0f172a;border-width:2px;margin:10px 0 8px 0;'>
                    <div style='font-size:12px;color:#0f172a;line-height:1.6;font-family:\"JetBrains Mono\",monospace;font-weight:500;'>
                        {SVG_ICONS['food']} Fd: <b>{row['food_count']}</b> &nbsp;·&nbsp; {SVG_ICONS['transit']} Tr: <b>{row['transit_count']}</b> &nbsp;·&nbsp; {SVG_ICONS['health']} Hl: <b>{row['health_count']}</b><br>
                        {SVG_ICONS['green']} Gr: <b>{row['green_count']}</b> &nbsp;·&nbsp; {SVG_ICONS['education']} Ed: <b>{row['education_count']}</b> &nbsp;·&nbsp; {SVG_ICONS['shopping']} Sh: <b>{row['shopping_count']}</b>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

layout_col_1, layout_col_2 = st.columns([11, 7])

with layout_col_1:
    st.markdown("<div class='city-container' style='margin-bottom:0px !important;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:12px;'>Spatial Distribution Mapping Layout</h3>", unsafe_allow_html=True)
    fmap = build_map(df)
    st_folium(fmap, width=None, height=480, returned_objects=[])
    st.markdown("</div>", unsafe_allow_html=True)

with layout_col_2:
    st.markdown("<div class='city-container' style='margin-bottom:0px !important;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:12px;'>Zoning Infrastructure Record Ledger</h3>", unsafe_allow_html=True)
    display_df = df[["rank", "zone_id", "tier", "total_score"]].copy()
    display_df.columns = ["Rank Order", "Structural Zone ID", "Assigned Clustering Tier", "Index Rating Value"]
    display_df["Index Rating Value"] = display_df["Index Rating Value"].round(1)
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=480,
    )
    st.markdown("</div>", unsafe_allow_html=True)

tab_analytics, tab_ml, tab_pipeline = st.tabs([
    "Structural Analytics Variance Matrix",
    "Model Partitioning Machine Learning Validation",
    "Operational Infrastructure Data Pipeline System Logs",
])

with tab_analytics:
    st.markdown("<div class='city-container' style='margin-top:12px;'>", unsafe_allow_html=True)
    st.markdown("### Comparative Performance Indices Curve")
    
    fig_bar = px.bar(
        df.sort_values("total_score"),
        x="total_score", y="zone_id", orientation="h",
        color="tier", color_discrete_map=TIER_COLORS,
        labels={"total_score": "Computed Livability Score Matrix", "zone_id": "Target Partition Area"},
        title=f"Regional Metric Indices Output Profile: {st.session_state.result_city}",
    )
    fig_bar.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1e293b", family="Space Grotesk"),
        title_font=dict(color="#0f172a", size=15, family="Space Grotesk"),
        legend_title_font=dict(color="#1e293b"),
        xaxis=dict(gridcolor="#0f172a", gridwidth=1, zerolinecolor="#0f172a"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='city-container'>", unsafe_allow_html=True)
    st.markdown("### Regional Resource Stack Allocation density")
    cat_cols = ["food_count", "transit_count", "health_count", "green_count", "education_count", "finance_count", "shopping_count"]
    cat_labels = ["Food Infrastructure", "Transit Networks", "Medical Support", "Environmental Greenery", "Learning Centers", "Financial Matrix", "Retail Commercial"]

    radar_df = df[["zone_id", "tier"] + cat_cols].copy()
    radar_long = radar_df.melt(id_vars=["zone_id", "tier"], value_vars=cat_cols, var_name="category", value_name="count")
    radar_long["category"] = radar_long["category"].map(dict(zip(cat_cols, cat_labels)))

    fig_cat = px.bar(
        radar_long,
        x="zone_id", y="count", color="category",
        barmode="stack",
        labels={"count": "Categorical Density Value", "zone_id": "Zoning Unit Reference", "category": "Functional Node Type"},
        title="Composite Composition Distribution Map (Infrastructure Density Per Segment)",
    )
    fig_cat.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1e293b", family="Space Grotesk"),
        title_font=dict(color="#0f172a", size=15, family="Space Grotesk"),
        xaxis=dict(tickangle=-25, gridcolor="#e2e8f0"),
        yaxis=dict(gridcolor="#0f172a", gridwidth=1),
    )
    st.plotly_chart(fig_cat, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab_ml:
    st.markdown("<div class='city-container' style='margin-top:12px;'>", unsafe_allow_html=True)
    st.markdown("### Algorithmic Verification Vectors & Dimensional Clustering Performance")
    
    if not ml_eval:
        st.info("Algorithmic clustering metrics matrix unavailable or calculations skipped.")
    else:
        metric_cards_cols = st.columns(4)
        with metric_cards_cols[0]:
            st.metric("Optimal Clusters K Calculated", ml_eval.get("optimal_k", "—"))
        with metric_cards_cols[1]:
            st.metric("Silhouette Evaluation Coefficient", round(ml_eval.get("final_silhouette", 0), 3))
        with metric_cards_cols[2]:
            st.metric("Davies-Bouldin Separation Margin", round(ml_eval.get("final_davies_bouldin", 0), 3))
        with metric_cards_cols[3]:
            st.metric("Total PCA Variance Aggregation", f"{ml_eval.get('total_variance_explained', 0)}%")

        st.markdown(
            f"<div style='margin-top:18px; padding:14px 18px; border:3px solid #0f172a; border-radius:6px; background:#ffffff; color:#1e293b; font-size:14px; box-shadow:3px 3px 0px 0px #0f172a;'> "
            f"<strong>Mathematical Partitioning Output Interpretation:</strong> {ml_eval.get('silhouette_interpretation','')}"
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        st.markdown("### PCA Principal Components Topology Array Grid")
        
        if "pca_x" in df.columns and df["pca_x"].notna().any():
            fig_pca = px.scatter(
                df, x="pca_x", y="pca_y",
                color="tier", text="zone_id",
                size="total_score",
                color_discrete_map=TIER_COLORS,
                labels={"pca_x": "Spatial Eigenvector Component One (PC1)", "pca_y": "Spatial Eigenvector Component Two (PC2)"},
                title=f"Transformed Model Space Cluster Coordinate Distribution Grid ({ml_eval.get('total_variance_explained',0)}% Cumulative Information Explained)",
            )
            fig_pca.update_traces(textposition="top center", textfont_size=10, textfont_family="Space Grotesk")
            fig_pca.update_layout(
                height=460,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", family="Space Grotesk"),
                title_font=dict(color="#0f172a", size=15, family="Space Grotesk"),
                xaxis=dict(gridcolor="#0f172a", gridwidth=1, zerolinecolor="#0f172a"),
                yaxis=dict(gridcolor="#0f172a", gridwidth=1, zerolinecolor="#0f172a"),
            )
            st.plotly_chart(fig_pca, use_container_width=True)
        else:
            st.info("Spatial coordinate arrays contain no PCA coordinate matrices.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_pipeline:
    st.markdown("<div class='city-container' style='margin-top:12px;'>", unsafe_allow_html=True)
    st.markdown("### Operational Telemetry Logs & Transformation Profile")

    pipeline_metric_cols = st.columns(3)
    with pipeline_metric_cols[0]:
        st.metric("Raw Coordinates Points Ingested", f"{summary.get('total_pois_fetched', 0):,}")
    with pipeline_metric_cols[1]:
        st.metric("Sanitized Datastore Target Profiles", f"{summary.get('total_pois_after_cleaning', 0):,}")
    with pipeline_metric_cols[2]:
        st.metric("Operational Record Retention Efficiency", f"{summary.get('retention_rate_pct', 0)}%")

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Database Pipeline Operations Filtration Checklist Logs")
    for step, count in summary.get("cleaning_steps", {}).items():
        label = step.replace("_", " ").title()
        st.markdown(f"&bull; `Database Filter layer Execute:` **{label}** Isolation complete &rarr; **{count}** anomalies scrubbed")

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Model Feature Ingestion Matrix Definition Arrays")
    st.code(str(ml_eval.get("features_used", [])), language="python")

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    st.markdown("#### Complete System Transmission Object Hierarchy")
    with st.expander("Inspect JSON Object Footprint Model Interface Dump"):
        st.json(data)
    st.markdown("</div>", unsafe_allow_html=True)
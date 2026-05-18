import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import Fullscreen
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Cityello ~ Find Your Neighborhood",
    page_icon="🍁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,600;1,9..144,300&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

*,*::before,*::after{
    box-sizing:border-box
}

html,body,[class*="css"]{
    font-family:'DM Sans',sans-serif;
    background:#faf9f7!important;
    color:#1a1a1a!important;
    font-size:17px!important;
    line-height:1.6!important
}

.block-container{
    padding:2rem 2.5rem 3rem;
    max-width:1480px
}

section[data-testid="stSidebar"]{
    background:#1a1a1a!important;
    border-right:none
}

section[data-testid="stSidebar"] *{
    color:#e8e4dc!important;
    font-size:17px!important
}

section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{
    color:#a8a49c!important;
    font-size:15px!important;
    font-weight:500!important;
    text-transform:uppercase;
    letter-spacing:0.06em
}

h1,h2,h3,h4{
    font-family:'Fraunces',serif;
    font-weight:600;
    letter-spacing:-0.02em;
    color:#1a1a1a!important
}

.badge{
    display:inline-block;
    padding:5px 14px;
    border-radius:100px;
    font-size:13px;
    font-weight:600;
    letter-spacing:0.08em;
    text-transform:uppercase;
    font-family:'DM Mono',monospace
}

.badge-online{
    background:#1e3a5f;
    color:#eaf2ff
}

.badge-offline{
    background:#1e3a5f;
    color:#eaf2ff
}

.badge-cached{
    background:#e8f4fd;
    color:#1a4a7f
}

.chip{
    display:inline-block;
    background:#ffffff;
    border:1.5px solid #e0ddd8;
    border-radius:6px;
    padding:6px 14px;
    font-size:14px;
    font-weight:500;
    color:#4a4a4a;
    margin:4px 6px 4px 0;
    font-family:'DM Mono',monospace
}

.hero{
    background:#1a1a1a;
    border-radius:16px;
    padding:48px 52px;
    margin-bottom:32px;
    position:relative;
    overflow:hidden
}

.hero::before{
    content:'';
    position:absolute;
    top:-60px;
    right:-60px;
    width:280px;
    height:280px;
    border-radius:50%;
    background:radial-gradient(circle,rgba(255,220,100,0.12) 0%,transparent 70%);
    pointer-events:none
}

.hero h1{
    font-family:'Fraunces',serif;
    font-size:52px;
    font-weight:600;
    color:#faf9f7!important;
    margin:0 0 10px;
    letter-spacing:-0.03em;
    line-height:1.1
}

.hero p{
    font-size:18px;
    color:#a8a49c;
    margin:0 0 24px;
    max-width:680px;
    line-height:1.8;
    font-weight:300
}

.hero .chip{
    background:rgba(255,255,255,0.06);
    border-color:rgba(255,255,255,0.12);
    color:#a8a49c
}

.n-card{
    background:#ffffff;
    border:1.5px solid #e8e4dc;
    border-radius:14px;
    padding:24px;
    height:100%;
    position:relative;
    overflow:hidden
}

.n-card .accent-bar{
    position:absolute;
    top:0;
    left:0;
    right:0;
    height:4px;
    border-radius:14px 14px 0 0
}

.n-card .rank-num{
    font-family:'DM Mono',monospace;
    font-size:13px;
    color:#9a9690;
    font-weight:500;
    text-transform:uppercase;
    letter-spacing:0.08em;
    margin-bottom:4px
}

.n-card .zone-name{
    font-family:'Fraunces',serif;
    font-size:24px;
    font-weight:600;
    color:#1a1a1a;
    margin-bottom:4px;
    line-height:1.2
}

.n-card .tier-pill{
    display:inline-block;
    padding:4px 12px;
    border-radius:100px;
    font-size:13px;
    font-weight:600;
    letter-spacing:0.05em;
    text-transform:uppercase;
    margin-bottom:16px
}

.n-card .score-big{
    font-family:'Fraunces',serif;
    font-size:56px;
    font-weight:300;
    line-height:1;
    color:#1a1a1a;
    margin-bottom:4px
}

.n-card .score-label{
    font-size:13px;
    color:#9a9690;
    text-transform:uppercase;
    letter-spacing:0.08em;
    margin-bottom:16px;
    font-family:'DM Mono',monospace
}

.n-card .stats-grid{
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    gap:8px;
    margin-top:14px
}

.n-card .stat-item{
    background:#faf9f7;
    border-radius:8px;
    padding:10px 12px;
    font-size:14px;
    color:#4a4a4a
}

.n-card .stat-item b{
    display:block;
    font-family:'DM Mono',monospace;
    font-size:18px;
    color:#1a1a1a;
    font-weight:500
}

.section-wrap{
    background:#ffffff;
    border:1.5px solid #e8e4dc;
    border-radius:14px;
    padding:28px 30px;
    margin-bottom:20px
}

.section-title{
    font-family:'Fraunces',serif;
    font-size:28px;
    font-weight:600;
    color:#1a1a1a;
    margin-bottom:4px
}

.section-desc{
    font-size:16px;
    color:#6b6860;
    margin-bottom:20px;
    line-height:1.8;
    max-width:720px
}

.ml-metric{
    background:#faf9f7;
    border:1.5px solid #e8e4dc;
    border-radius:10px;
    padding:18px 20px;
    text-align:center
}

.ml-metric .val{
    font-family:'Fraunces',serif;
    font-size:40px;
    font-weight:300;
    color:#1a1a1a;
    line-height:1;
    margin-bottom:4px
}

.ml-metric .lbl{
    font-size:13px;
    color:#9a9690;
    text-transform:uppercase;
    letter-spacing:0.08em;
    font-family:'DM Mono',monospace
}

.conf-banner{
    border-radius:10px;
    padding:16px 22px;
    margin-bottom:20px;
    font-size:16px;
    border-left:5px solid;
    font-weight:500
}

.conf-high{
    background:#f0fdf4;
    border-color:#16a34a;
    color:#166534
}

.conf-moderate{
    background:#fffbeb;
    border-color:#d97706;
    color:#92400e
}

.conf-low{
    background:#fef2f2;
    border-color:#dc2626;
    color:#991b1b
}

[data-testid="metric-container"]{
    background:#ffffff!important;
    border:1.5px solid #e8e4dc!important;
    border-radius:10px!important;
    padding:16px!important
}

[data-testid="stMetricValue"]{
    font-family:'Fraunces',serif!important
}

[data-baseweb="tab-list"]{
    background:#f4f2ef!important;
    border-radius:10px!important;
    padding:4px!important;
    gap:2px!important
}

button[data-baseweb="tab"]{
    border-radius:8px!important;
    font-size:17px!important;
    font-weight:500!important;
    color:#6b6860!important;
    padding:8px 18px!important
}

button[aria-selected="true"]{
    background:#ffffff!important;
    color:#1a1a1a!important;
    box-shadow:0 1px 4px rgba(0,0,0,0.08)!important
}

.pipeline-step{
    display:flex;
    align-items:flex-start;
    gap:14px;
    padding:12px 0;
    border-bottom:1px solid #f0ede8
}

.pipeline-step:last-child{
    border-bottom:none
}

.step-dot{
    width:8px;
    height:8px;
    border-radius:50%;
    background:#1a1a1a;
    margin-top:6px;
    flex-shrink:0
}

.step-label{
    font-size:16px;
    color:#4a4a4a;
    line-height:1.7
}

.step-count{
    font-family:'DM Mono',monospace;
    font-weight:500;
    color:#1a1a1a
}

.stButton>button{
    background:#1a1a1a!important;
    color:#faf9f7!important;
    border:none!important;
    border-radius:10px!important;
    font-family:'DM Sans',sans-serif!important;
    font-weight:600!important;
    font-size:13px!important;
    padding:12px 24px!important;
    transition:opacity 0.2s!important
}

.stButton>button:hover{
    opacity:0.85!important
}
            
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div{
    color:#faf9f7!important;
    background:#2a2a2a!important;
    font-size:13px!important
}

section[data-testid="stSidebar"] .stSelectbox svg{
    fill:#faf9f7!important
}
</style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000"

TIER_COLORS = {
    "Premium":"#16a34a","Good":"#22c55e","Balanced":"#eab308",
    "Economy":"#f97316","Budget Friendly":"#ea580c",
    "Unclustered":"#94a3b8","Uniform":"#94a3b8",
}
TIER_BG = {
    "Premium":"#dcfce7","Good":"#dcfce7","Balanced":"#fef9c3",
    "Economy":"#ffedd5","Budget Friendly":"#fee2e2",
    "Unclustered":"#f1f5f9","Uniform":"#f1f5f9",
}
TIER_TEXT = {
    "Premium":"#14532d","Good":"#14532d","Balanced":"#713f12",
    "Economy":"#7c2d12","Budget Friendly":"#7f1d1d",
    "Unclustered":"#334155","Uniform":"#334155",
}
PERSONA_WEIGHTS = {
    "Student": {"food":3,"transit":5,"health":1,"green":1,"education":5,"finance":2,"shopping":2},
    "Working Professional": {"food":4,"transit":4,"health":2,"green":2,"education":1,"finance":3,"shopping":3},
    "Family": {"food":3,"transit":3,"health":5,"green":4,"education":4,"finance":2,"shopping":3},
}

def check_backend():
    try: return requests.get(f"{API_URL}/health",timeout=3).status_code==200
    except: return False

def call_api(city,weights,n_zones):
    try:
        r=requests.post(f"{API_URL}/score",json={"city":city,"weights":weights,"n_zones":n_zones},timeout=180)
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Can't reach the backend. Run: uvicorn main:app --reload")
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Try fewer zones.")
    except Exception as e:
        raise RuntimeError(f"Network error: {e}")
    if r.status_code!=200:
        try: detail=r.json().get("detail",r.text)
        except: detail=r.text
        raise RuntimeError(f"API {r.status_code}: {detail}")
    return r.json()

def build_map(df):
    m=folium.Map(location=[df["lat"].mean(),df["lon"].mean()],zoom_start=11,tiles="CartoDB positron")
    Fullscreen().add_to(m)
    max_score=df["total_score"].max() or 1.0
    for _,row in df.iterrows():
        radius=9+(row["total_score"]/max_score)*15
        color=TIER_COLORS.get(row.get("tier",""),"#64748b")
        popup=f"""
        <div style='font-family:DM Sans,sans-serif;padding:14px 16px;min-width:200px;
                    background:#fff;border-radius:10px;border:1.5px solid #e8e4dc;'>
            <div style='font-weight:700;font-size:15px;color:#1a1a1a;margin-bottom:2px'>{row['zone_id']}</div>
            <div style='font-size:11px;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.06em;color:{color};margin-bottom:10px'>{row.get('tier','')}</div>
            <div style='font-size:30px;font-weight:300;color:#1a1a1a;line-height:1;margin-bottom:8px'>{row['total_score']:.1f}</div>
            <hr style='border:none;border-top:1.5px solid #e8e4dc;margin:8px 0'>
            <div style='font-size:12px;color:#4a4a4a;line-height:1.8'>
                Food: <b>{row['food_count']}</b> &nbsp; Transit: <b>{row['transit_count']}</b><br>
                Health: <b>{row['health_count']}</b> &nbsp; Green: <b>{row['green_count']}</b><br>
                Education: <b>{row['education_count']}</b> &nbsp; Shopping: <b>{row['shopping_count']}</b>
            </div>
        </div>"""
        folium.CircleMarker(
            location=[row["lat"],row["lon"]],radius=radius,
            color=color,weight=2.5,fill=True,fill_color=color,fill_opacity=0.82,
            popup=folium.Popup(popup,max_width=260),
            tooltip=f"{row['zone_id']}  ·  {row['total_score']:.1f}",
        ).add_to(m)
    return m

# Sidebar

backend_ok=check_backend()
st.sidebar.markdown(
    "<div style='padding:8px 0 20px'>"
    "<div style='font-family:Fraunces,serif;font-size:26px;font-weight:600;"
    "color:#faf9f7;letter-spacing:-0.02em;margin-bottom:4px'>Cityello</div>"
    "<div style='font-size:11px;color:#6b6860;text-transform:uppercase;"
    "letter-spacing:0.1em;font-family:DM Mono,monospace'>Neighborhood Intelligence</div>"
    "</div>",unsafe_allow_html=True)

st.sidebar.markdown(
    f"<span class='badge {'badge-online' if backend_ok else 'badge-offline'}'>"
    f"{'● System Online' if backend_ok else '● System Offline'}</span>",
    unsafe_allow_html=True)

if not backend_ok:
    st.sidebar.error("Start the API:\n```\nuvicorn main:app --reload --port 8000\n```")

st.sidebar.markdown("<hr style='border-color:#2a2a2a;margin:20px 0'>",unsafe_allow_html=True)
city=st.sidebar.selectbox("City",["Pune","Bangalore","Mumbai"])
persona=st.sidebar.selectbox("Who are you?",list(PERSONA_WEIGHTS.keys()))
preset=PERSONA_WEIGHTS[persona]

st.sidebar.markdown(
    "<div style='margin-top:16px;font-family:DM Mono,monospace;font-size:11px;"
    "color:#6b6860;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px'>"
    "Adjust what matters to you</div>",unsafe_allow_html=True)


weights={
    "food": st.sidebar.slider("Food & Restaurants",0,5,preset["food"]),
    "transit": st.sidebar.slider("Public Transport",0,5,preset["transit"]),
    "health": st.sidebar.slider("Hospitals & Clinics",0,5,preset["health"]),
    "green": st.sidebar.slider("Parks & Green Space",0,5,preset["green"]),
    "education": st.sidebar.slider("Schools & Colleges",0,5,preset["education"]),
    "finance": st.sidebar.slider("Banks & ATMs",0,5,preset["finance"]),
    "shopping": st.sidebar.slider("Markets & Shops",0,5,preset["shopping"]),
}
n_zones=st.sidebar.slider("Zones to analyze",6,18,12)
st.sidebar.markdown("<div style='margin-top:24px'>",unsafe_allow_html=True)
analyze_clicked=st.sidebar.button("Analyze →",use_container_width=True,type="primary")
st.sidebar.markdown("</div>",unsafe_allow_html=True)

# 🍊 session state

if "result_data" not in st.session_state: st.session_state.result_data=None
if "result_city" not in st.session_state: st.session_state.result_city=None

# Hero

st.markdown(f"""
<div class='hero'>
    <h1>Find where you actually<br><em style='font-style:italic;font-weight:300'>want</em> to live.</h1>
    <p>Cityello pulls real amenity data across {city} and uses unsupervised machine learning
    to rank neighborhoods by what matters to <em>you.</em>
    Adjust the sliders, hit analyze, get answers.</p>
    <div>
        <span class='chip'>15,897+ POIs indexed</span>
        <span class='chip'>3 Indian cities</span>
        <span class='chip'>KMeans + PCA clustering</span>
        <span class='chip'>SQLite cached</span>
    </div>
</div>
""",unsafe_allow_html=True)

# Analysis run

if analyze_clicked:
    if not backend_ok:
        st.error("Backend is offline — can't run analysis.")
    else:
        with st.spinner(f"Crunching {city} data…"):
            try:
                data=call_api(city,weights,n_zones)
                st.session_state.result_data=data
                st.session_state.result_city=city
            except RuntimeError as e:
                st.error(str(e))
                st.session_state.result_data=None

data=st.session_state.result_data

if data is None:
    st.markdown("""
    <div style='text-align:center;padding:60px 20px;background:#ffffff;
                border:1.5px solid #e8e4dc;border-radius:14px;'>
        <div style='font-family:Fraunces,serif;font-size:28px;font-weight:300;
                    color:#1a1a1a;margin-bottom:10px'>Waiting for your input.</div>
        <div style='font-size:14px;color:#9a9690;max-width:400px;margin:0 auto;line-height:1.7'>
            Pick a city, choose your lifestyle profile, adjust what matters to you,
            and hit <strong>Analyze →</strong>
        </div>
    </div>""",unsafe_allow_html=True)
    st.stop()

neighborhoods=data.get("neighborhoods",[])
ml_eval=data.get("ml_evaluation",{})
summary=data.get("data_summary",{})
confidence=data.get("confidence","unknown")
conf_warning=data.get("confidence_warning")

if not neighborhoods:
    st.error("No results returned. Check the terminal for backend errors.")
    st.stop()

df=pd.DataFrame(neighborhoods)

if conf_warning:
    icons={"high":"✓","moderate":"⚠","low":"✕"}
    st.markdown(
        f"<div class='conf-banner conf-{confidence}'>"
        f"<strong>{icons.get(confidence,'i')} Clustering confidence: {confidence.upper()}</strong>"
        f" — {conf_warning}</div>",unsafe_allow_html=True)

if summary.get("served_from_cache"):
    st.markdown(
        "<span class='badge badge-cached' style='margin-bottom:20px;display:inline-block'>"
        "⚡ Loaded from cache. </span>",unsafe_allow_html=True)

# Top 3 neighboorhoods

st.markdown(
    "<h2 style='font-size:28px;margin-bottom:4px'>Top neighborhoods for you</h2>"
    f"<p style='color:#6b6860;font-size:14px;margin-bottom:20px'>"
    f"Ranked by your {persona.lower()} profile · {st.session_state.result_city}</p>",
    unsafe_allow_html=True)

top3=df.head(3)
cols=st.columns(3)
for i,(_,row) in enumerate(top3.iterrows()):
    tier=row.get("tier","Unclustered")
    color=TIER_COLORS.get(tier,"#94a3b8")
    bg=TIER_BG.get(tier,"#f1f5f9")
    txtcol=TIER_TEXT.get(tier,"#334155")
    with cols[i]:
        st.markdown(f"""
        <div class='n-card'>
            <div class='accent-bar' style='background:{color}'></div>
            <div class='rank-num' style='margin-top:8px'>#{int(row.get('rank',i+1))} Recommendation</div>
            <div class='zone-name'>{row['zone_id']}</div>
            <div class='tier-pill' style='background:{bg};color:{txtcol}'>{tier}</div>
            <div class='score-big'>{row['total_score']:.1f}</div>
            <div class='score-label'>Livability score</div>
            <hr style='border:none;border-top:1.5px solid #e8e4dc;margin:12px 0'>
            <div class='stats-grid'>
                <div class='stat-item'><b>{row['food_count']}</b>Food</div>
                <div class='stat-item'><b>{row['transit_count']}</b>Transit</div>
                <div class='stat-item'><b>{row['health_count']}</b>Health</div>
                <div class='stat-item'><b>{row['green_count']}</b>Green</div>
                <div class='stat-item'><b>{row['education_count']}</b>Education</div>
                <div class='stat-item'><b>{row['shopping_count']}</b>Shopping</div>
            </div>
        </div>""",unsafe_allow_html=True)

# Map + Rankings

st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
map_col,rank_col=st.columns([3,2])

with map_col:
    st.markdown("""<div class='section-wrap' style='padding-bottom:16px'>
        <div class='section-title'>Neighborhood map</div>
        <div class='section-desc'>Each circle is one analyzed zone. Bigger circles score higher.
        Click any circle for the full breakdown.</div>""",unsafe_allow_html=True)
    st_folium(build_map(df),width=None,height=480,returned_objects=[])
    st.markdown("</div>",unsafe_allow_html=True)

with rank_col:
    st.markdown("""<div class='section-wrap'>
        <div class='section-title'>Full rankings</div>
        <div class='section-desc'>Every zone scored and sorted. Tier reflects how the ML grouped them.</div>""",
        unsafe_allow_html=True)
    display_df=df[["rank","zone_id","tier","total_score"]].copy()
    display_df.columns=["#","Zone","Tier","Score"]
    display_df["Score"]=display_df["Score"].round(1)
    st.dataframe(display_df,use_container_width=True,hide_index=True,height=480)
    st.markdown("</div>",unsafe_allow_html=True)

# Tabs

st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)
tab_analytics,tab_ml,tab_pipeline=st.tabs(["Analytics","ML Evaluation","Data Pipeline"])

with tab_analytics:
    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)
    st.markdown("""<div class='section-wrap'>
        <div class='section-title'>Score comparison</div>
        <div class='section-desc'>Every zone ranked by livability score. Green means well-served across
        amenities, red means sparse. The gap between zones tells you how differentiated the city is.</div>""",
        unsafe_allow_html=True)
    fig_bar=px.bar(df.sort_values("total_score"),x="total_score",y="zone_id",orientation="h",
        color="tier",color_discrete_map=TIER_COLORS,
        labels={"total_score":"Livability Score","zone_id":""})
    fig_bar.update_layout(height=460,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#4a4a4a",family="DM Sans",size=12),
        xaxis=dict(gridcolor="#f0ede8",zerolinecolor="#e8e4dc"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)",tickfont_size=11),
        margin=dict(l=0,r=20,t=10,b=10))
    st.plotly_chart(fig_bar,use_container_width=True)
    st.markdown("</div>",unsafe_allow_html=True)

    st.markdown("""<div class='section-wrap'>
        <div class='section-title'>What's inside each zone</div>
        <div class='section-desc'>Stacked bars show the amenity mix per zone. A zone heavy on food
        but light on health scores differently depending on your persona weights — this tells you why.</div>""",
        unsafe_allow_html=True)
    cat_cols=["food_count","transit_count","health_count","green_count","education_count","finance_count","shopping_count"]
    cat_labels=["Food","Transit","Health","Green","Education","Finance","Shopping"]
    radar_long=df[["zone_id","tier"]+cat_cols].melt(id_vars=["zone_id","tier"],value_vars=cat_cols,
        var_name="category",value_name="count")
    radar_long["category"]=radar_long["category"].map(dict(zip(cat_cols,cat_labels)))
    fig_cat=px.bar(radar_long,x="zone_id",y="count",color="category",barmode="stack",
        labels={"count":"POI Count","zone_id":"","category":"Category"})
    fig_cat.update_layout(height=380,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#4a4a4a",family="DM Sans",size=12),
        xaxis=dict(tickangle=-30,gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor="#f0ede8"),margin=dict(l=0,r=0,t=10,b=10))
    st.plotly_chart(fig_cat,use_container_width=True)
    st.markdown("</div>",unsafe_allow_html=True)

with tab_ml:
    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)
    st.markdown("""<div class='section-wrap'>
        <div class='section-title'>How good is the clustering?</div>
        <div class='section-desc'>The model automatically finds how many neighborhood tiers exist
        in the data — it doesn't assume. Silhouette score closer to 1 means tiers are clearly
        separated. Davies-Bouldin closer to 0 means clusters don't overlap.</div>""",
        unsafe_allow_html=True)

    if not ml_eval:
        st.info("ML evaluation not available.")
    else:
        m1,m2,m3,m4=st.columns(4)
        for col,val,lbl in [
            (m1, ml_eval.get("optimal_k","—"), "Tiers found"),
            (m2, round(ml_eval.get("final_silhouette",0),3), "Silhouette score"),
            (m3, round(ml_eval.get("final_davies_bouldin",0),3), "Davies-Bouldin"),
            (m4, f"{ml_eval.get('total_variance_explained',0)}%", "PCA variance"),
        ]:
            with col:
                st.markdown(f"<div class='ml-metric'><div class='val'>{val}</div>"
                           f"<div class='lbl'>{lbl}</div></div>",unsafe_allow_html=True)

        st.markdown(
            f"<div style='margin-top:16px;padding:14px 18px;background:#faf9f7;"
            f"border-radius:10px;border:1.5px solid #e8e4dc;font-size:14px;color:#4a4a4a;line-height:1.7'>"
            f"<strong style='color:#1a1a1a'>Note: </strong>"
            f"{ml_eval.get('silhouette_interpretation','')} "
            f"PCA projects 7 dimensions of amenity data into 2D — if the dots below look separated by color, "
            f"the tier labels are reliable."
            f"</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        if "pca_x" in df.columns and df["pca_x"].notna().any():
            st.markdown("""<div class='section-wrap'>
                <div class='section-title'>Cluster visualization (PCA)</div>
                <div class='section-desc'>Each dot is a neighborhood zone. Zones that sit close together
                have similar amenity profiles. Clear color separation means the tiers are real —
                not just artifacts of the algorithm.</div>""",unsafe_allow_html=True)
            fig_pca=px.scatter(df,x="pca_x",y="pca_y",color="tier",text="zone_id",size="total_score",
                color_discrete_map=TIER_COLORS,
                labels={"pca_x":"Principal Component 1","pca_y":"Principal Component 2"})
            fig_pca.update_traces(textposition="top center",textfont_size=10,textfont_family="DM Sans")
            fig_pca.update_layout(height=480,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#4a4a4a",family="DM Sans",size=12),
                xaxis=dict(gridcolor="#f0ede8",zerolinecolor="#e8e4dc"),
                yaxis=dict(gridcolor="#f0ede8",zerolinecolor="#e8e4dc"),
                margin=dict(l=0,r=0,t=10,b=10))
            st.plotly_chart(fig_pca,use_container_width=True)
            st.markdown("</div>",unsafe_allow_html=True)

        k_analysis=ml_eval.get("k_selection_analysis",{})
        if k_analysis.get("k_range"):
            st.markdown("""<div class='section-wrap'>
                <div class='section-title'>How K was chosen</div>
                <div class='section-desc'>The model tested every possible number of tiers from 2 to 6
                and picked the one where neighborhoods were most distinctly grouped.
                The peak of this curve is the K that was used.</div>""",unsafe_allow_html=True)
            k_df=pd.DataFrame({"K (number of tiers)":k_analysis["k_range"],
                               "Silhouette Score":k_analysis["silhouette_scores"]})
            fig_k=px.line(k_df,x="K (number of tiers)",y="Silhouette Score",markers=True)
            fig_k.update_traces(line_color="#1a1a1a",marker_color="#1a1a1a",marker_size=8)
            fig_k.update_layout(height=280,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#4a4a4a",family="DM Sans",size=12),
                xaxis=dict(gridcolor="#f0ede8",dtick=1),
                yaxis=dict(gridcolor="#f0ede8"),margin=dict(l=0,r=0,t=10,b=10))
            st.plotly_chart(fig_k,use_container_width=True)
            st.markdown("</div>",unsafe_allow_html=True)

with tab_pipeline:
    st.markdown("<div style='height:16px'></div>",unsafe_allow_html=True)
    st.markdown("""<div class='section-wrap'>
        <div class='section-title'>Data journey</div>
        <div class='section-desc'>From raw API response to ranked neighborhood —
        here's what happened to the data before it reached your screen.</div>""",
        unsafe_allow_html=True)
    p1,p2,p3=st.columns(3)
    p1.metric("POIs fetched",f"{summary.get('total_pois_fetched',0):,}")
    p2.metric("After cleaning",f"{summary.get('total_pois_after_cleaning',0):,}")
    p3.metric("Retention rate",f"{summary.get('retention_rate_pct',0)}%")
    st.markdown("<div style='margin-top:20px'>",unsafe_allow_html=True)
    for step,count in summary.get("cleaning_steps",{}).items():
        label=step.replace("_"," ").title()
        st.markdown(f"""<div class='pipeline-step'>
            <div class='step-dot'></div>
            <div class='step-label'><span class='step-count'>{count}</span> records — {label}</div>
        </div>""",unsafe_allow_html=True)
    st.markdown("</div></div>",unsafe_allow_html=True)

    st.markdown("""<div class='section-wrap'>
        <div class='section-title'>Features the ML used</div>
        <div class='section-desc'>These 7 density features (POIs per km²) are what KMeans clustered on.
        Density rather than raw count means a zone with 8 restaurants in 0.5 km²
        is correctly ranked above one with 8 restaurants spread across 5 km².</div>""",
        unsafe_allow_html=True)
    st.code(str(ml_eval.get("features_used",[])),language="python")
    st.markdown("</div>",unsafe_allow_html=True)

    with st.expander("Raw API response (JSON)"):
        st.json(data)

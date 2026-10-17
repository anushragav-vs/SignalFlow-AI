"""
SignalFlow AI - Real-Time Algorithmic Financial News Filter
Ultra-Modern Fintech UI/UX Dashboard powered by Streamlit and Plotly.
Featuring Strands Decider 2B System 1 Gatekeeper + Google Gemini 3.5 System 2 Analysis.
Hackathon Tags: #strands-decider-2b #policy
"""

import os
import json
import time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import config, FINANCIAL_DISCLAIMER
from src.database import SignalFlowDatabase
from src.decider_client import DeciderClient
from src.classification_service import ClassificationService, PolicyAction
from src.gemini_service import GeminiService
from src.pipeline import SignalFlowPipeline
from src.rss_service import RSSIngestionService
from src.review_service import ReviewService
from src.metrics import compute_latency_distribution, compute_cloud_calls_avoided_pct, compute_cost_savings_pct
from src.benchmarking import run_benchmark_comparison

# -----------------------------------------------------------------------------
# Streamlit Page Setup & Custom Fintech Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SignalFlow AI • Financial News Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom High-End Fintech CSS (Inspired by SentimentIQ, VoiceWatch AI, and AlphaPro)
st.markdown(
    """
    <style>
    /* Global Base */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    .stApp {
        background-color: #060b15 !important;
        color: #f1f5f9 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    /* Hide default Streamlit padding */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 96% !important;
    }

    /* Top Market Bar */
    .market-ticker-ribbon {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #09101f;
        border: 1px solid #16233b;
        border-radius: 10px;
        padding: 8px 16px;
        margin-bottom: 16px;
        font-size: 0.85rem;
        gap: 12px;
        overflow-x: auto;
    }
    .market-pill {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #0d162a;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #1e2e4f;
        white-space: nowrap;
    }
    .pill-green { color: #10b981; font-weight: 600; }
    .pill-red { color: #ef4444; font-weight: 600; }
    .pill-tag {
        font-size: 0.72rem;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        font-family: 'JetBrains Mono', monospace;
    }
    .pill-tag-red {
        font-size: 0.72rem;
        padding: 2px 6px;
        border-radius: 4px;
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Top Platform Header */
    .platform-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0 20px 0;
        border-bottom: 1px solid #16233b;
        margin-bottom: 18px;
        flex-wrap: wrap;
        gap: 14px;
    }
    .platform-title-group {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .platform-logo {
        background: linear-gradient(135deg, #10b981, #06b6d4);
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
    }
    .platform-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .platform-sub {
        font-size: 0.8rem;
        color: #64748b;
        margin: 0;
    }

    /* Integration Status Badges (VoiceWatch AI style) */
    .integration-group {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }
    .integration-chip {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #0d1527;
        border: 1px solid #1a2742;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.78rem;
        color: #94a3b8;
    }
    .status-dot-green {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }
    .status-dot-blue {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #3b82f6;
        box-shadow: 0 0 8px #3b82f6;
    }

    /* Ticker Summary Banner (SentimentIQ style) */
    .ticker-summary-card {
        background: #0b1324;
        border: 1px solid #1b2844;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }
    .ticker-grid {
        display: grid;
        grid-template-columns: 1.2fr 1fr 1.5fr 2fr 3.5fr;
        gap: 16px;
        align-items: center;
    }
    .ticker-col-label {
        font-size: 0.72rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 2px;
    }
    .ticker-col-val {
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
    }
    .bias-bullish { color: #10b981 !important; text-shadow: 0 0 10px rgba(16, 185, 129, 0.3); }
    .bias-bearish { color: #ef4444 !important; text-shadow: 0 0 10px rgba(239, 68, 68, 0.3); }
    .bias-neutral { color: #8b5cf6 !important; }

    /* Segmented Progress Bar */
    .seg-bar-wrap {
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
        display: flex;
        background: #1e293b;
        width: 100%;
        margin-top: 6px;
    }
    .seg-green { background: #10b981; transition: width 0.3s ease; }
    .seg-gray { background: #475569; transition: width 0.3s ease; }
    .seg-red { background: #ef4444; transition: width 0.3s ease; }

    /* News Cards */
    .news-card {
        background: #0a1120;
        border: 1px solid #192640;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 18px;
        transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .news-card:hover {
        border-color: #273b64;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        transform: translateY(-1px);
    }
    .news-header-meta {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
        flex-wrap: wrap;
        font-size: 0.8rem;
        color: #64748b;
    }
    .news-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.4;
        margin-bottom: 14px;
        cursor: pointer;
    }
    .news-title:hover {
        color: #38bdf8;
    }

    /* Badges */
    .badge-pill {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        letter-spacing: 0.02em;
    }
    .badge-pos {
        background: rgba(16, 185, 129, 0.12);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .badge-neg {
        background: rgba(239, 68, 68, 0.12);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    .badge-neu {
        background: rgba(139, 92, 246, 0.12);
        color: #a78bfa;
        border: 1px solid rgba(139, 92, 246, 0.35);
    }
    .badge-noi {
        background: rgba(100, 116, 139, 0.12);
        color: #94a3b8;
        border: 1px solid rgba(100, 116, 139, 0.3);
    }
    .badge-conf {
        background: rgba(6, 182, 212, 0.12);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.35);
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-lat {
        background: rgba(59, 130, 246, 0.1);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.25);
        font-family: 'JetBrains Mono', monospace;
    }

    /* AI Summary Inset Box */
    .ai-summary-box {
        background: #060e1d;
        border: 1px solid #142138;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 14px;
    }
    .ai-summary-header {
        font-size: 0.75rem;
        font-weight: 700;
        color: #38bdf8;
        display: flex;
        align-items: center;
        gap: 6px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .ai-summary-body {
        font-size: 0.9rem;
        line-height: 1.55;
        color: #cbd5e1;
    }

    /* Tag Pills */
    .hashtag-group {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 10px;
    }
    .hashtag-pill {
        font-size: 0.72rem;
        background: #0f192d;
        color: #60a5fa;
        border: 1px solid #1e3056;
        padding: 3px 9px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Right Sticky Card (Sentiment Overview) */
    .sentiment-overview-card {
        background: #09101f;
        border: 1px solid #1a2742;
        border-radius: 12px;
        padding: 22px 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .overview-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 2px;
    }
    .overview-ticker {
        font-size: 1.35rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 14px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Progress Rows inside Legend */
    .legend-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
        font-size: 0.82rem;
    }
    .legend-bar-wrap {
        height: 6px;
        background: #19253d;
        border-radius: 3px;
        overflow: hidden;
        margin-bottom: 12px;
    }
    .legend-bar-inner {
        height: 100%;
        border-radius: 3px;
    }

    /* Watchlist Item */
    .watchlist-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #060c18;
        border: 1px solid #142036;
        padding: 10px 12px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .watchlist-ticker {
        font-weight: 700;
        font-size: 0.9rem;
        color: #ffffff;
    }
    .watchlist-name {
        font-size: 0.72rem;
        color: #64748b;
    }

    /* Streamlit Custom Component Overrides */
    div[data-testid="stTextInput"] input {
        background-color: #0b1324 !important;
        border: 1px solid #1f2f50 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-size: 0.92rem !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.3) !important;
    }
    button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb, #06b6d4) !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
    }

    /* Tabs styling */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        color: #64748b !important;
        font-size: 0.92rem !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom-color: #38bdf8 !important;
    }

    /* Disclaimer strip */
    .disclaimer-banner {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #1e293b;
        border-left: 4px solid #0ea5e9;
        border-radius: 6px;
        padding: 8px 14px;
        margin-top: 24px;
        font-size: 0.78rem;
        color: #94a3b8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Initialize Core Services
# -----------------------------------------------------------------------------
@st.cache_resource
def get_services():
    db = SignalFlowDatabase(config.sqlite_db_path)
    decider = DeciderClient(server_url=config.decider_server_url, checkpoint=config.decider_checkpoint)
    classifier = ClassificationService(decider_client=decider, min_confidence=config.min_confidence_threshold)
    gemini = GeminiService(api_key=config.gemini_api_key, model_id=config.gemini_model_id)
    pipeline = SignalFlowPipeline(classification_service=classifier, gemini_service=gemini, database=db)
    rss = RSSIngestionService()
    review = ReviewService(db=db)
    return db, classifier, gemini, pipeline, rss, review

db, classifier, gemini, pipeline, rss_service, review_service = get_services()

# Smart Hashtag Extractor
def get_article_tags(headline: str, decision: str) -> list:
    h = headline.lower()
    tags = []
    if any(k in h for k in ["ai", "nvidia", "chip", "semiconductor", "tsmc", "arm", "gpu"]):
        tags.extend(["#ai technology", "#semiconductors"])
    if any(k in h for k in ["fed", "rate", "inflation", "cpi", "powell", "treasury", "yield"]):
        tags.extend(["#monetary policy", "#interest rates"])
    if any(k in h for k in ["earnings", "revenue", "profit", "margin", "income", "q3", "q4"]):
        tags.extend(["#earnings beat", "#corporate finance"])
    if any(k in h for k in ["tesla", "ev", "automotive", "rivian", "byd"]):
        tags.extend(["#electric vehicles", "#automotive"])
    if any(k in h for k in ["stock", "shares", "jump", "surge", "gain", "rally"]):
        tags.append("#market sentiment")
    if any(k in h for k in ["drop", "fall", "slump", "plunge", "decline", "selloff"]):
        tags.append("#valuation risk")
    if decision == "Bullish":
        tags.append("#growth catalyst")
    elif decision == "Bearish":
        tags.append("#macro headwind")
    else:
        tags.append("#market update")
    return list(dict.fromkeys(tags))[:4]

# -----------------------------------------------------------------------------
# TOP COMPONENT 1: Market Tickers Ribbon (AlphaPro Fintech Style)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="market-ticker-ribbon">
        <div class="market-pill">
            <span style="color:#64748b; font-weight:700;">NASDAQ</span>
            <span class="pill-green">$3,450 +3.78</span>
            <span class="pill-tag">● 85 Bullish</span>
        </div>
        <div class="market-pill">
            <span style="color:#64748b; font-weight:700;">S&P 500</span>
            <span class="pill-red">$2,150 -1.02</span>
            <span class="pill-tag-red">● 42 Mixed</span>
        </div>
        <div class="market-pill">
            <span style="color:#64748b; font-weight:700;">DOW JONES</span>
            <span class="pill-green">$1,995 +3.78</span>
            <span class="pill-tag">● 78 Bullish</span>
        </div>
        <div class="market-pill">
            <span style="color:#64748b; font-weight:700;">FTSE 100</span>
            <span class="pill-green">$4,200 +3.78</span>
            <span class="pill-tag">● 89 Bullish</span>
        </div>
        <div class="market-pill">
            <span style="color:#64748b; font-weight:700;">NIKKEI 225</span>
            <span class="pill-red">$578 -0.92</span>
            <span class="pill-tag-red">● 61 Neutral</span>
        </div>
        <div class="market-pill">
            <span style="color:#64748b; font-weight:700;">NVDA</span>
            <span class="pill-green">$128.45 +4.2%</span>
            <span class="pill-tag">● 94 High Conviction</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# TOP COMPONENT 2: Platform Observability Header (VoiceWatch AI Style)
# -----------------------------------------------------------------------------
cred = gemini.check_credentials_status()
gemini_status_text = "Live" if cred["configured"] else "Missing Key"
gemini_dot_class = "status-dot-green" if cred["configured"] else "status-dot-blue"

st.markdown(
    f"""
    <div class="platform-header">
        <div class="platform-title-group">
            <div class="platform-logo">⚡</div>
            <div>
                <h1 class="platform-title">SignalFlow AI <span style="font-size:0.9rem; font-weight:400; color:#64748b;">Financial News Intelligence</span></h1>
                <p class="platform-sub">Strands Decider 2B System 1 Gatekeeper • Google Gemini 3.5 System 2 Analysis</p>
            </div>
        </div>
        <div class="integration-group">
            <div class="integration-chip">
                <span class="{gemini_dot_class}"></span>
                <span style="font-weight:600; color:#ffffff;">Google Cloud</span>
                <span>Gemini 3.5 Flash</span>
            </div>
            <div class="integration-chip">
                <span class="status-dot-green"></span>
                <span style="font-weight:600; color:#ffffff;">Strands Decider 2B</span>
                <span>Local Policy Engine</span>
            </div>
            <div class="integration-chip">
                <span class="status-dot-green"></span>
                <span style="font-weight:600; color:#ffffff;">SQLite Audit DB</span>
                <span>Immutable Policy Log</span>
            </div>
            <div class="integration-chip">
                <span class="status-dot-green"></span>
                <span style="font-weight:600; color:#ffffff;">Financial RSS</span>
                <span>Multi-Feed Active</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Navigation Tabs
# -----------------------------------------------------------------------------
nav_feed, nav_dossiers, nav_review, nav_bench, nav_settings = st.tabs([
    "📊 Financial News Stream",
    "🧠 Gemini Intel Dossiers",
    "🛡 Human Review Queue",
    "📈 Observability & Benchmarks",
    "⚙ Configuration & Audits",
])

# -----------------------------------------------------------------------------
# TAB 1: FINANCIAL NEWS STREAM (SentimentIQ Full Visual Match)
# -----------------------------------------------------------------------------
with nav_feed:
    # 1. Search Bar & Action Button (Row)
    col_search, col_source, col_btn = st.columns([3.8, 1.8, 1.4])
    with col_search:
        search_query = st.text_input(
            "Search Ticker or Headline",
            placeholder="🔍 NVDA, AAPL, Tesla, Fed, interest rate, revenue...",
            label_visibility="collapsed",
            key="feed_search_input",
        )
    with col_source:
        feed_sources = ["All Live Feeds"] + list(rss_service.get_feeds().keys()) + ["Manual Custom Headline"]
        active_feed = st.selectbox("Feed Source", feed_sources, label_visibility="collapsed", key="feed_source_sel")
    with col_btn:
        fetch_trigger = st.button("❄ Analyze News", type="primary", use_container_width=True)

    # Optional Custom Headline Expandable Drawer
    custom_headline_input = None
    if active_feed == "Manual Custom Headline":
        custom_headline_input = st.text_input(
            "Enter custom headline to test policy gatekeeper:",
            value="Nvidia unveils next-generation Blackwell Ultra architecture with 40% inference efficiency gains.",
        )

    # Ingestion Trigger Logic
    if fetch_trigger:
        with st.spinner("Ingesting signals and evaluating with Strands Decider 2B Gatekeeper..."):
            if custom_headline_input:
                items = [rss_service.normalize_manual_input(custom_headline_input)]
            else:
                items = rss_service.fetch_feed(active_feed, max_items=6)

            if items:
                processed_results = pipeline.process_batch(items)
                st.toast(f"Evaluated {len(processed_results)} signals through Decider 2B!", icon="⚡")
            else:
                st.warning("Feed stream temporarily returned no new items. Try switching feed or submit a custom headline.")

    # Fetch Signals from SQLite
    all_signals = db.get_recent_signals(limit=60)

    # Determine Active Ticker / Focus
    focus_ticker = search_query.strip().upper() if search_query.strip() else "ALL ASSETS"

    # Filter signals based on search query
    filtered_by_search = [
        s for s in all_signals
        if not search_query or search_query.lower() in s["headline"].lower()
    ]

    # Metrics for Top Summary Bar
    total_arts = len(filtered_by_search)
    pos_count = sum(1 for s in filtered_by_search if s["decider_sentiment"] == "Bullish")
    neg_count = sum(1 for s in filtered_by_search if s["decider_sentiment"] == "Bearish")
    neu_count = sum(1 for s in filtered_by_search if s["decider_sentiment"] == "Neutral")
    noi_count = sum(1 for s in filtered_by_search if s["decider_sentiment"] == "Noise")
    rev_count = sum(1 for s in filtered_by_search if s["policy_action"] == "REVIEW_QUEUE")

    if pos_count > neg_count and pos_count >= neu_count:
        overall_bias = "Bullish"
        bias_class = "bias-bullish"
    elif neg_count > pos_count and neg_count >= neu_count:
        overall_bias = "Bearish"
        bias_class = "bias-bearish"
    else:
        overall_bias = "Neutral"
        bias_class = "bias-neutral"

    # Distribution percentages
    active_denom = max(total_arts, 1)
    p_pct = int((pos_count / active_denom) * 100)
    neu_pct = int((neu_count / active_denom) * 100)
    neg_pct = int((neg_count / active_denom) * 100)

    # 2. Ticker Summary Card with Segmented Bar (SentimentIQ Style)
    st.markdown(
        f"""
        <div class="ticker-summary-card">
            <div class="ticker-grid">
                <div>
                    <div class="ticker-col-label">Scope / Ticker</div>
                    <div class="ticker-col-val">{focus_ticker[:12]}</div>
                </div>
                <div>
                    <div class="ticker-col-label">Articles</div>
                    <div class="ticker-col-val">{total_arts}</div>
                </div>
                <div>
                    <div class="ticker-col-label">Policy Bias</div>
                    <div class="ticker-col-val {bias_class}">{overall_bias}</div>
                </div>
                <div>
                    <div class="ticker-col-label">Categorization</div>
                    <div style="font-size: 1.05rem; font-weight: 700; margin-top: 2px;">
                        <span style="color:#10b981;">{pos_count}</span> <span style="color:#64748b; font-size:0.8rem;">POS</span> &nbsp;
                        <span style="color:#8b5cf6;">{neu_count}</span> <span style="color:#64748b; font-size:0.8rem;">NEU</span> &nbsp;
                        <span style="color:#ef4444;">{neg_count}</span> <span style="color:#64748b; font-size:0.8rem;">NEG</span>
                    </div>
                </div>
                <div>
                    <div class="ticker-col-label">Signal Distribution ({p_pct}% / {neu_pct}% / {neg_pct}%)</div>
                    <div class="seg-bar-wrap">
                        <div class="seg-green" style="width: {p_pct}%;"></div>
                        <div class="seg-gray" style="width: {neu_pct}%;"></div>
                        <div class="seg-red" style="width: {neg_pct}%;"></div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Interactive Filter Pills (SentimentIQ Style)
    filter_col1, filter_col2 = st.columns([1, 6])
    with filter_col1:
        st.markdown("<div style='padding-top:6px; font-size:0.8rem; font-weight:700; color:#64748b;'>FILTER:</div>", unsafe_allow_html=True)
    with filter_col2:
        selected_category_filter = st.radio(
            "Category Filter",
            [
                f"All ({total_arts})",
                f"Positive ({pos_count})",
                f"Neutral ({neu_count})",
                f"Negative ({neg_count})",
                f"Noise ({noi_count})",
                f"Review Queue ({rev_count})",
            ],
            horizontal=True,
            label_visibility="collapsed",
            key="cat_filter_radio",
        )

    # Apply radio filter
    display_signals = filtered_by_search
    if "Positive" in selected_category_filter:
        display_signals = [s for s in display_signals if s["decider_sentiment"] == "Bullish"]
    elif "Negative" in selected_category_filter:
        display_signals = [s for s in display_signals if s["decider_sentiment"] == "Bearish"]
    elif "Neutral" in selected_category_filter:
        display_signals = [s for s in display_signals if s["decider_sentiment"] == "Neutral"]
    elif "Noise" in selected_category_filter:
        display_signals = [s for s in display_signals if s["decider_sentiment"] == "Noise"]
    elif "Review Queue" in selected_category_filter:
        display_signals = [s for s in display_signals if s["policy_action"] == "REVIEW_QUEUE"]

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # 4. Two-Column Main Layout: Feed (Left) vs Sentiment Overview & Donut (Right)
    col_feed_left, col_overview_right = st.columns([2.3, 1.1])

    with col_feed_left:
        if display_signals:
            for s in display_signals:
                sent = s["decider_sentiment"]
                conf = s["decider_confidence"]
                p_act = s["policy_action"]
                gem_st = s.get("gemini_status")
                lat = s.get("decider_latency_ms", 1800.0)

                # Badge classes
                if sent == "Bullish":
                    cat_badge = '<span class="badge-pill badge-pos">● Positive</span>'
                elif sent == "Bearish":
                    cat_badge = '<span class="badge-pill badge-neg">● Negative</span>'
                elif sent == "Neutral":
                    cat_badge = '<span class="badge-pill badge-neu">● Neutral</span>'
                else:
                    cat_badge = '<span class="badge-pill badge-noi">● Noise (Filtered)</span>'

                conf_badge = f'<span class="badge-pill badge-conf">{int(conf * 100)}% confidence</span>'
                lat_badge = f'<span class="badge-pill badge-lat">⚡ {lat:.0f} ms (Decider 2B)</span>'

                domain = s.get("publisher", "Financial Wire")
                timestamp_str = s.get("timestamp", "Recent")[:16].replace("T", " ")

                # Generate dynamic tags
                tags = get_article_tags(s["headline"], sent)
                tag_html = "".join(f'<span class="hashtag-pill">{t}</span>' for t in tags)

                # Determine summary text
                if gem_st == "success" and s.get("event_summary"):
                    ai_summary_text = s["event_summary"]
                    ai_header = "❄ AI SUMMARY • Google Gemini 3.5 Intelligence"
                elif p_act == "BLOCK_NOISE":
                    ai_summary_text = (
                        "Local Strands Decider 2B identified this headline as non-actionable market noise or lifestyle spam. "
                        "Cloud LLM dispatch was prevented (0 ms cloud latency, $0.00 spend)."
                    )
                    ai_header = "⚡ DECIDER 2B POLICY GATEKEEPER • Local Filter"
                elif p_act == "BLOCK_NEUTRAL":
                    ai_summary_text = (
                        "Headline classified as general consensus neutral financial information without material price dislocation catalyst. "
                        "Recorded to audit ledger without consuming generative cloud tokens."
                    )
                    ai_header = "⚡ DECIDER 2B POLICY GATEKEEPER • Macro Ledger"
                elif p_act == "REVIEW_QUEUE":
                    ai_summary_text = (
                        f"Calibrated confidence ({conf:.2f}) fell below the policy safety threshold (0.80). "
                        "Held in Human Review Queue for supervisor verification before routing to cloud analysis."
                    )
                    ai_header = "🛡 POLICY GATEKEEPER • Escalated to Review"
                else:
                    ai_summary_text = "Pending analysis."
                    ai_header = "⚡ SIGNAL EVALUATION"

                # Render News Card Container
                st.markdown(
                    f"""
                    <div class="news-card">
                        <div class="news-header-meta">
                            {cat_badge}
                            {conf_badge}
                            {lat_badge}
                            <span>•</span>
                            <span>{domain}</span>
                            <span>•</span>
                            <span>{timestamp_str}</span>
                        </div>
                        <div class="news-title">{s['headline']}</div>
                        <div class="ai-summary-box">
                            <div class="ai-summary-header">{ai_header}</div>
                            <div class="ai-summary-body">{ai_summary_text}</div>
                        </div>
                        <div class="hashtag-group">
                            {tag_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Expandable Deep Intelligence Dossier if Gemini analyzed
                if gem_st == "success":
                    with st.expander(f"🔍 View Full Institutional Dossier: {s['headline'][:55]}..."):
                        c_ex1, c_ex2 = st.columns(2)
                        with c_ex1:
                            st.markdown("**1. Reported Facts (Source Verifiable)**")
                            facts = json.loads(s.get("reported_facts_json") or "[]")
                            if facts:
                                for f in facts:
                                    st.markdown(f"- {f}")
                            else:
                                st.write(s.get("event_summary"))

                            st.markdown("**2. Economic Transmission Mechanism**")
                            st.write(s.get("transmission_mechanism") or "Direct equity valuation adjustment.")

                            hypotheses = json.loads(s.get("analytical_hypotheses_json") or "[]")
                            if hypotheses:
                                st.markdown("**3. Forward-Looking Analytical Hypotheses**")
                                for h in hypotheses:
                                    st.markdown(f"- 💡 {h}")

                        with c_ex2:
                            st.markdown("**4. Affected Assets & Instruments**")
                            assets = json.loads(s.get("affected_assets_json") or "[]")
                            st.write(", ".join(f"`{a}`" for a in assets) if assets else "Equities index")

                            watchpoints = json.loads(s.get("catalyst_watchpoints_json") or "[]")
                            if watchpoints:
                                st.markdown("**5. Catalyst Watchpoints**")
                                for w in watchpoints:
                                    st.markdown(f"- ⏱ {w}")

                            peers = json.loads(s.get("peer_impact_json") or "[]")
                            if peers:
                                st.markdown("**6. Peer & Sector Sensitivity**")
                                st.write(", ".join(f"`{p}`" for p in peers))

                            st.markdown("**7. Key Uncertainties & Risks**")
                            risks = json.loads(s.get("uncertainties_json") or "[]")
                            if risks:
                                for r in risks:
                                    st.markdown(f"- ⚠️ {r}")
                            else:
                                st.write("Consensus macro uncertainty.")

                        meta_notes = []
                        if s.get("market_impact_horizon"):
                            meta_notes.append(f"Horizon: `{s.get('market_impact_horizon')}`")
                        if s.get("institutional_risk_level"):
                            meta_notes.append(f"Risk: `{s.get('institutional_risk_level')}`")
                        meta_notes.extend([
                            f"Model: `{s.get('gemini_model_id')}`",
                            f"Gemini Latency: `{s.get('cloud_latency_ms', 0):.0f} ms`",
                            f"Cost: `${s.get('estimated_cost_usd', 0.0):.6f}`",
                        ])
                        st.caption(" | ".join(meta_notes))
        else:
            st.info("No headlines matched your search or active filter. Try clearing the search or clicking 'Analyze News'.")

    # Right Column: Sentiment Overview Donut & Top Watchlist
    with col_overview_right:
        st.markdown(
            f"""
            <div class="sentiment-overview-card">
                <div class="overview-title">Sentiment Overview</div>
                <div class="overview-ticker">{focus_ticker}</div>
            """,
            unsafe_allow_html=True,
        )

        # Plotly High-Res Donut Chart matching SentimentIQ (Image 1)
        donut_labels = ["Positive", "Neutral", "Negative"]
        donut_values = [pos_count, neu_count, neg_count]
        if sum(donut_values) == 0:
            donut_labels = ["No Data"]
            donut_values = [1]
            donut_colors = ["#1e293b"]
        else:
            donut_colors = ["#10b981", "#475569", "#ef4444"]

        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=donut_labels,
                    values=donut_values,
                    hole=0.68,
                    marker=dict(colors=donut_colors),
                    textinfo="none",
                    hoverinfo="label+percent+value",
                )
            ]
        )
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            height=200,
            margin=dict(l=0, r=0, t=10, b=10),
            annotations=[
                dict(
                    text=f"<span style='font-size:1.3rem; font-weight:800; color:#10b981;'>{p_pct}%</span><br><span style='font-size:0.75rem; color:#64748b;'>Bullish</span>",
                    x=0.5,
                    y=0.5,
                    font_size=16,
                    showarrow=False,
                )
            ],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        # Progress Legend matching SentimentIQ (Image 1)
        st.markdown(
            f"""
            <div style="margin-top: 10px;">
                <div class="legend-row">
                    <span style="color:#10b981; font-weight:600;">■ Positive (Bullish)</span>
                    <span style="font-weight:700;">{p_pct}% &nbsp;<span style="color:#64748b;">({pos_count})</span></span>
                </div>
                <div class="legend-bar-wrap">
                    <div class="legend-bar-inner" style="width:{p_pct}%; background:#10b981;"></div>
                </div>

                <div class="legend-row">
                    <span style="color:#94a3b8; font-weight:600;">■ Neutral (Consensus)</span>
                    <span style="font-weight:700;">{neu_pct}% &nbsp;<span style="color:#64748b;">({neu_count})</span></span>
                </div>
                <div class="legend-bar-wrap">
                    <div class="legend-bar-inner" style="width:{neu_pct}%; background:#64748b;"></div>
                </div>

                <div class="legend-row">
                    <span style="color:#ef4444; font-weight:600;">■ Negative (Bearish)</span>
                    <span style="font-weight:700;">{neg_pct}% &nbsp;<span style="color:#64748b;">({neg_count})</span></span>
                </div>
                <div class="legend-bar-wrap">
                    <div class="legend-bar-inner" style="width:{neg_pct}%; background:#ef4444;"></div>
                </div>
            </div>
            <p style="font-size:0.75rem; color:#64748b; margin-top:14px; line-height:1.4;">
                Based on {total_arts} articles classified by Strands Decider 2B. Signals with &ge; 0.80 confidence are analyzed by Gemini 3.5.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)

        # Top Searched / Favorites (AlphaPro Style - Image 3)
        st.markdown(
            """
            <div class="sentiment-overview-card">
                <div class="overview-title">Tracked Market Assets</div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #ffffff; margin-bottom: 12px;">Active Watchlist</div>
                
                <div class="watchlist-item">
                    <div>
                        <div class="watchlist-ticker">NVDA</div>
                        <div class="watchlist-name">NVIDIA Corporation</div>
                    </div>
                    <span class="pill-tag">+3.78% Bullish</span>
                </div>
                <div class="watchlist-item">
                    <div>
                        <div class="watchlist-ticker">AAPL</div>
                        <div class="watchlist-name">Apple Inc.</div>
                    </div>
                    <span class="pill-tag">+1.20% Bullish</span>
                </div>
                <div class="watchlist-item">
                    <div>
                        <div class="watchlist-ticker">TSLA</div>
                        <div class="watchlist-name">Tesla Inc.</div>
                    </div>
                    <span class="pill-tag-red">-1.02% Bearish</span>
                </div>
                <div class="watchlist-item">
                    <div>
                        <div class="watchlist-ticker">MSFT</div>
                        <div class="watchlist-name">Microsoft Corp.</div>
                    </div>
                    <span class="pill-tag">+0.85% Neutral</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# -----------------------------------------------------------------------------
# TAB 2: GEMINI INTEL DOSSIERS
# -----------------------------------------------------------------------------
with nav_dossiers:
    st.subheader("Google Gemini Institutional Research Dossiers")
    st.caption("Structured economic intelligence separating verifiable reported facts, transmission channels, and forward-looking risks.")

    signals = db.get_recent_signals(limit=50)
    analyzed_signals = [s for s in signals if s.get("gemini_status") == "success" and s.get("event_summary")]

    if analyzed_signals:
        for r in analyzed_signals:
            with st.expander(f"📌 [{r['decider_sentiment']}] {r['headline']}", expanded=True):
                c_head1, c_head2 = st.columns([3, 1])
                with c_head1:
                    st.write(f"**Source Headline:** {r['headline']}")
                with c_head2:
                    st.caption(
                        f"Model: `{r['gemini_model_id']}` | Latency: `{r['cloud_latency_ms']:.0f} ms` | Cost: `${r['estimated_cost_usd']:.6f}`"
                    )

                facts = json.loads(r.get("reported_facts_json") or "[]")
                assets = json.loads(r.get("affected_assets_json") or "[]")
                risks = json.loads(r.get("uncertainties_json") or "[]")
                hyps = json.loads(r.get("analytical_hypotheses_json") or "[]")

                d_col1, d_col2 = st.columns(2)
                with d_col1:
                    st.markdown("##### 1. Verifiable Reported Facts")
                    if facts:
                        for f in facts:
                            st.markdown(f"- {f}")
                    else:
                        st.write(r.get("event_summary"))

                    st.markdown("##### 2. Transmission Mechanism")
                    st.write(r.get("transmission_mechanism") or "Asset re-pricing through direct earnings multiplier.")

                with d_col2:
                    st.markdown("##### 3. Affected Assets & Sectors")
                    if assets:
                        st.write(", ".join(f"`{a}`" for a in assets))
                    else:
                        st.write("Broader market equities.")

                    st.markdown("##### 4. Key Uncertainties & Missing Data")
                    if risks:
                        for rk in risks:
                            st.markdown(f"- ⚠️ {rk}")
                    else:
                        st.write("Macroeconomic execution risks.")

                    if hyps:
                        st.markdown("##### 5. Analytical Hypotheses")
                        for h in hyps:
                            st.markdown(f"- 💡 {h}")
    else:
        st.info("No deep dossiers generated yet. Select a feed and click 'Analyze News' on the News Stream tab.")

# -----------------------------------------------------------------------------
# TAB 3: HUMAN REVIEW QUEUE
# -----------------------------------------------------------------------------
with nav_review:
    st.subheader("Human-in-the-Loop Review Queue")
    st.caption("Low-confidence signals (< 0.80 threshold) and unverified items are held here for human oversight.")

    pending = review_service.get_pending_items()
    st.write(f"**Pending Escalated Signals:** `{len(pending)}`")

    if pending:
        for it in pending:
            with st.container():
                st.markdown(
                    f"""
                    <div style="background:#09101f; border:1px solid #1a2742; border-radius:10px; padding:16px; margin-bottom:12px;">
                        <div style="font-size:1.05rem; font-weight:700; color:#f8fafc; margin-bottom:8px;">"{it['headline']}"</div>
                        <div style="display:flex; gap:16px; font-size:0.8rem; color:#64748b;">
                            <span>Decider: <b style="color:#ffffff;">{it['decider_sentiment']}</b></span>
                            <span>Confidence: <b style="color:#38bdf8;">{it['decider_confidence']:.3f}</b></span>
                            <span>Publisher: <b style="color:#ffffff;">{it['publisher']}</b></span>
                            <span>Escalation: <b style="color:#f59e0b;">{it['policy_reason']}</b></span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                a1, a2, a3 = st.columns([1.5, 1.5, 1])
                with a1:
                    if st.button(f"✅ Confirm & Send to Gemini #{it['id']}", key=f"rev_conf_{it['id']}", type="primary"):
                        with st.spinner("Analyzing human-approved signal via Gemini..."):
                            review_service.approve_and_send_to_gemini(it["id"], gemini_service=gemini)
                            st.success(f"Signal #{it['id']} approved!")
                            st.rerun()
                with a2:
                    new_lbl = st.selectbox(
                        "Reclassify",
                        ["Bullish", "Bearish", "Neutral", "Noise"],
                        key=f"re_lbl_{it['id']}",
                        label_visibility="collapsed",
                    )
                    if st.button(f"✏️ Reclassify #{it['id']}", key=f"btn_re_{it['id']}"):
                        review_service.reclassify_item(it["id"], new_label=new_lbl, notes=f"Reclassified by user to {new_lbl}")
                        st.info(f"Signal #{it['id']} updated.")
                        st.rerun()
                with a3:
                    if st.button(f"❌ Dismiss #{it['id']}", key=f"btn_dism_{it['id']}"):
                        review_service.dismiss_item(it["id"], notes="Dismissed by supervisor.")
                        st.info(f"Signal #{it['id']} dismissed.")
                        st.rerun()
                st.divider()
    else:
        st.success("🎉 All clear! No signals currently pending human review.")

# -----------------------------------------------------------------------------
# TAB 4: OBSERVABILITY & BENCHMARKS (VoiceWatch AI Style - Image 2)
# -----------------------------------------------------------------------------
with nav_bench:
    st.subheader("Model Performance Benchmarks & Observability")
    st.caption("Real-time head-to-head comparison between Strands Decider 2B Gatekeeper and Cloud LLMs.")

    # Benchmark Cards (VoiceWatch AI Style)
    st.markdown(
        """
        <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">
            <div style="background:#09101f; border:1px solid #1a2742; border-radius:10px; padding:16px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-weight:700; font-size:1.05rem; color:#ffffff;">Strands Decider 2B</span>
                        <span class="pill-tag">★ Recommended Gatekeeper</span>
                    </div>
                    <div style="font-size:0.78rem; color:#64748b; margin-top:2px;">Local System 1 Engine • StrandsAgents/strands-decider-2B-qwen3.5-v1-2610</div>
                </div>
                <div style="display:flex; gap:24px; text-align:right;">
                    <div><div style="font-size:0.72rem; color:#64748b;">LATENCY</div><div style="font-weight:700; color:#10b981;">0 ms (Cloud)</div></div>
                    <div><div style="font-size:0.72rem; color:#64748b;">COST / ITEM</div><div style="font-weight:700; color:#10b981;">$0.000000</div></div>
                    <div><div style="font-size:0.72rem; color:#64748b;">AVOIDANCE</div><div style="font-weight:700; color:#38bdf8;">62.5%</div></div>
                </div>
            </div>

            <div style="background:#09101f; border:1px solid #1a2742; border-radius:10px; padding:16px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-weight:700; font-size:1.05rem; color:#ffffff;">Google Gemini 3.5 Flash Lite</span>
                        <span style="font-size:0.72rem; padding:2px 6px; border-radius:4px; background:rgba(59,130,246,0.15); color:#60a5fa;">★ System 2 Intel</span>
                    </div>
                    <div style="font-size:0.78rem; color:#64748b; margin-top:2px;">Google AI Studio • Structured Financial Analysis</div>
                </div>
                <div style="display:flex; gap:24px; text-align:right;">
                    <div><div style="font-size:0.72rem; color:#64748b;">LATENCY</div><div style="font-weight:700; color:#38bdf8;">~850 ms</div></div>
                    <div><div style="font-size:0.72rem; color:#64748b;">COST / ITEM</div><div style="font-weight:700; color:#f59e0b;">$0.000085</div></div>
                    <div><div style="font-size:0.72rem; color:#64748b;">OUTPUT</div><div style="font-weight:700; color:#ffffff;">JSON Schema</div></div>
                </div>
            </div>

            <div style="background:#09101f; border:1px solid #1a2742; border-radius:10px; padding:16px; display:flex; justify-content:space-between; align-items:center; opacity:0.7;">
                <div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-weight:700; font-size:1.05rem; color:#ffffff;">Baseline (100% Cloud LLM)</span>
                        <span style="font-size:0.72rem; padding:2px 6px; border-radius:4px; background:rgba(239,68,68,0.15); color:#f87171;">Inefficient</span>
                    </div>
                    <div style="font-size:0.78rem; color:#64748b; margin-top:2px;">All headlines dispatched to cloud without gatekeeper</div>
                </div>
                <div style="display:flex; gap:24px; text-align:right;">
                    <div><div style="font-size:0.72rem; color:#64748b;">LATENCY</div><div style="font-weight:700; color:#ef4444;">High (800-2500ms)</div></div>
                    <div><div style="font-size:0.72rem; color:#64748b;">COST SPEND</div><div style="font-weight:700; color:#ef4444;">100% Prohibitive</div></div>
                    <div><div style="font-size:0.72rem; color:#64748b;">AVOIDANCE</div><div style="font-weight:700; color:#ef4444;">0.0%</div></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Benchmark Runner Button
    if st.button("🚀 Run Reproducible Benchmark Suite", type="primary"):
        with st.spinner("Executing benchmark across fixed dataset..."):
            b_res = run_benchmark_comparison(invoke_live_gemini=False)
            st.session_state["bench_results"] = b_res
            st.success("Benchmark completed!")

    if "bench_results" in st.session_state:
        b_res = st.session_state["bench_results"]
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Cloud Calls Avoided", f"{b_res['cloud_calls_avoided_pct']}%")
        b2.metric("Cost Savings", f"{b_res['cost_savings_pct']}%")
        b3.metric("Baseline Invocations", b_res["baseline_cloud_calls"])
        b4.metric("Proposed Invocations", b_res["proposed_cloud_calls"])

    # Insights Panel (VoiceWatch AI Style)
    st.markdown(
        """
        <div style="background:#060e1d; border:1px solid #142138; border-radius:8px; padding:14px; margin-top:16px;">
            <div style="font-weight:700; color:#38bdf8; font-size:0.85rem; margin-bottom:6px;">⚡ Benchmark Key Insights</div>
            <ul style="font-size:0.82rem; color:#94a3b8; margin:0; padding-left:18px; line-height:1.6;">
                <li><b>Strands Decider 2B</b> filters 62.5% of noise and neutral headlines locally, eliminating unnecessary cloud roundtrips.</li>
                <li>Dropping irrelevant headlines locally saves <b>$0.000085 per item</b>, scaling to thousands in savings across high-frequency feeds.</li>
                <li>Items processed locally incur <b>0 ms cloud network latency</b>, protecting downstream systems from API rate limits and throttling.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# TAB 5: CONFIGURATION & AUDITS
# -----------------------------------------------------------------------------
with nav_settings:
    st.subheader("System Configuration & Audit Records")

    c_cfg1, c_cfg2 = st.columns(2)
    with c_cfg1:
        st.markdown("##### Model & Policy Settings")
        st.selectbox("Gemini Model", ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-2.5-flash"], index=0)
        st.slider("Confidence Threshold", 0.50, 0.95, config.min_confidence_threshold, 0.05)
        st.write(f"**Gemini API Key:** `{config.get_masked_api_key()}`")
        st.write(f"**Decider Checkpoint:** `{config.decider_checkpoint}`")
        st.write(f"**SQLite Database Path:** `{config.sqlite_db_path}`")

    with c_cfg2:
        st.markdown("##### System Audit Records")
        kpis = db.get_kpis()
        st.json(kpis)

# -----------------------------------------------------------------------------
# Educational & Regulatory Disclaimer
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="disclaimer-banner">
        ⚖️ <b>Notice:</b> {FINANCIAL_DISCLAIMER}
    </div>
    """,
    unsafe_allow_html=True,
)


if __name__ == "__main__":
    import sys
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
    except Exception:
        ctx = None

    if ctx is None:
        print("\n" + "=" * 70)
        print("  SIGNALFLOW AI — SYSTEM LAUNCHER")
        print("=" * 70)
        print("  • To run this Streamlit dashboard, run:")
        print("      streamlit run app.py")
        print("\n  • To start the FastAPI Backend Server on http://localhost:8008 (for the React app):")
        print("      python api.py")
        print("=" * 70 + "\n")

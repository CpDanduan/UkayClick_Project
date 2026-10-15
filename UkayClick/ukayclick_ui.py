import streamlit as st


def money(value):
    return f"₱{float(value):,.2f}"


def apply_style():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
        :root { --forest:#173d30; --forest-2:#245440; --sage:#e8f0e8; --paper:#f6f7f3; --ink:#17382e; --muted:#52675d; --line:#d2dfd5; --forest-soft:#e4efe6; --forest-hover:#d5e7d9; }
        html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
        .stApp { background:var(--paper); color:var(--ink); }
        [data-testid="stHeader"] { background:rgba(246,247,243,.92); }
        [data-testid="stToolbar"] { right:1rem; }
        .block-container { padding-top:2rem; padding-bottom:2.5rem; max-width:1500px; }
        h1,h2,h3 { color:var(--ink)!important; font-family:'Manrope',sans-serif!important; letter-spacing:-.035em; }
        h1 { font-size:2.15rem!important; font-weight:800!important; }
        h2 { font-size:1.55rem!important; font-weight:750!important; }
        h3 { font-size:1.15rem!important; font-weight:700!important; }
        p, label, .stCaption, [data-testid='stCaptionContainer'] { color:var(--muted)!important; }
        [data-testid='stMarkdownContainer'] p, [data-testid='stWidgetLabel'] p, .stRadio label, .stCheckbox label { color:#42594e!important; }
        [data-testid="stSidebar"] { background:linear-gradient(180deg,#173d30 0%,#102e24 100%); border-right:1px solid #254d3d; }
        [data-testid="stSidebar"] * { color:#f4f7f2!important; }
        [data-testid="stSidebar"] h2 { font-size:1.5rem!important; letter-spacing:-.04em; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#c4d6cb!important; }
        [data-testid="stSidebar"] [data-testid="stButton"] { margin:.18rem 0; }
        [data-testid="stSidebar"] [data-testid="stButton"] button { justify-content:flex-start!important; text-align:left!important; padding:.62rem .8rem; min-height:2.65rem; border-radius:10px; font-weight:600; }
        [data-testid="stSidebar"] [data-testid="stButton"] button > div { width:100%; justify-content:flex-start!important; text-align:left!important; }
        [data-testid="stSidebar"] [data-testid="stButton"] button p { width:100%; text-align:left!important; }
        [data-testid="stSidebar"] .st-key-logout_button button,
        [data-testid="stSidebar"] .st-key-logout_button button > div,
        [data-testid="stSidebar"] .st-key-logout_button button p { justify-content:center!important; text-align:center!important; }
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] { background:transparent; color:#eaf2ec!important; border-color:transparent; }
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"]:hover { background:rgba(255,255,255,.09); border-color:transparent; }
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] { background:#2c5b45; color:#fff!important; border-color:#3d7158; }
        .stButton>button, [data-testid="stFormSubmitButton"] button { background:var(--forest); color:#fff!important; border:1px solid var(--forest); border-radius:10px; min-height:2.65rem; font-weight:700; transition:all .18s ease; }
        .stButton>button p, [data-testid="stFormSubmitButton"] button p { color:#fff!important; }
        .stButton>button:hover, [data-testid="stFormSubmitButton"] button:hover { background:var(--forest-2); color:white; border-color:var(--forest-2); transform:translateY(-1px); }
        .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div, .stDateInput input, .stTimeInput input { background:#fff!important; color:var(--ink)!important; border:1px solid #c7d8cc!important; border-radius:9px!important; }
        .stSelectbox [data-baseweb="select"] svg { fill:var(--forest)!important; color:var(--forest)!important; }
        [data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"], [data-baseweb="popover"] ul { background:#f8fbf7!important; border:1px solid #cbdccf!important; border-radius:10px!important; box-shadow:0 10px 28px rgba(23,61,48,.14)!important; }
        [data-baseweb="option"], [role="option"] { background:#f8fbf7!important; color:#17382e!important; }
        [data-baseweb="option"]:hover, [role="option"]:hover { background:#e2eee4!important; color:#17382e!important; }
        [aria-selected="true"][role="option"], [data-baseweb="option"][aria-selected="true"] { background:#d3e6d7!important; color:#173d30!important; font-weight:700!important; }
        [data-testid="stDateInput"] button, [data-testid="stTimeInput"] button { color:var(--forest)!important; }
        [data-testid="stTabs"] [role="tab"] { color:#52675d!important; }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:#173d30!important; border-bottom-color:#2c5b45!important; }
        [data-testid="stDataFrame"], [data-testid="stTable"] { background:#f8fbf7!important; }
        [data-testid="stDataFrame"] iframe { background:#f8fbf7!important; }
        [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"], [data-testid="stDeckGlJsonChart"] { background:#f8fbf7!important; border:1px solid #d2dfd5; border-radius:12px; padding:.25rem; }
        [data-testid="stAlert"] p, [data-testid="stAlert"] div { color:#263f33!important; }
        [data-testid="stMetric"] { background:linear-gradient(135deg,#fff 0%,#f7faf6 100%); border:1px solid var(--line); border-radius:15px; padding:1rem 1.1rem; box-shadow:0 3px 12px rgba(24,61,47,.035); }
        [data-testid="stMetricLabel"] { color:var(--muted)!important; font-size:.85rem!important; }
        [data-testid="stMetricValue"] { color:var(--ink)!important; font-family:'Manrope',sans-serif; font-weight:800; }
        [data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line)!important; border-radius:15px!important; }
        /* Keep full-width Ledger and Reports filter groups aligned with metric rows. */
        .st-key-ledger_filter_panel, .st-key-report_filter_panel { width:100%; }
        [data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
        [data-testid="stAlert"] { border-radius:12px; }
        hr { border-color:var(--line); }
        .ukay-eyebrow { text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:800; color:#35664b; margin-bottom:.4rem; }
        .ukay-subtitle { color:var(--muted); margin-top:-.55rem; margin-bottom:1.25rem; }
        .ukay-panel { background:white; border:1px solid var(--line); border-radius:16px; padding:1.15rem 1.25rem; box-shadow:0 4px 18px rgba(24,61,47,.035); }
        .ukay-login-wrap { max-width:480px; margin:4vh auto 0; }
        .ukay-login-brand { text-align:center; margin-bottom:1.3rem; }
        .ukay-login-brand h1 { margin-bottom:.2rem; }
        .ukay-login-card { background:white; border:1px solid var(--line); border-radius:20px; padding:2rem; box-shadow:0 18px 55px rgba(23,61,48,.09); }
        @media (max-width: 900px) { .block-container{padding:1.1rem;} h1{font-size:1.8rem!important;} }
        </style>
        """,
        unsafe_allow_html=True,
    )

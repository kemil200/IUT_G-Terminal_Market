"""
Terminal Pédagogique de Finance de Marché
Salle des marchés interactive pour cours de finance (type BRVM)
Auteur: Généré via Super-Prompt
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import norm
from datetime import datetime, timedelta
import random
import json
import time

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION DE LA PAGE
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BRVM Trading Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS BLOOMBERG-INSPIRED DESIGN
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

    /* ── Global Reset ── */
    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
        background-color: #0a0e1a;
        color: #c8d0e0;
    }
    .stApp { background-color: #0a0e1a; }
    .main .block-container { padding: 1rem 2rem; max-width: 100%; }

    /* ── Hide default Streamlit elements ── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Top Header Bar ── */
    .terminal-header {
        background: linear-gradient(135deg, #0d1226 0%, #111827 100%);
        border-bottom: 1px solid #1e3a5f;
        padding: 10px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
        border-radius: 8px;
    }
    .terminal-logo {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 18px;
        font-weight: 600;
        color: #f59e0b;
        letter-spacing: 3px;
    }
    .terminal-subtitle {
        font-size: 11px;
        color: #6b7280;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .live-badge {
        background: #ef4444;
        color: white;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 3px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        letter-spacing: 1px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

    /* ── Metric Cards ── */
    .metric-card {
        background: #111827;
        border: 1px solid #1e2d40;
        border-radius: 6px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-label {
        font-size: 10px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-family: 'IBM Plex Mono', monospace;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 22px;
        font-weight: 600;
        color: #f8fafc;
        margin: 4px 0;
    }
    .metric-value.green { color: #10b981; }
    .metric-value.red   { color: #ef4444; }
    .metric-value.amber { color: #f59e0b; }

    /* ── Section Panels ── */
    .panel {
        background: #111827;
        border: 1px solid #1e2d40;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .panel-title {
        font-size: 11px;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-family: 'IBM Plex Mono', monospace;
        border-bottom: 1px solid #1e2d40;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }

    /* ── Tables ── */
    .stDataFrame { border-radius: 6px; overflow: hidden; }
    .stDataFrame thead tr th {
        background: #1e2d40 !important;
        color: #94a3b8 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
    }
    .stDataFrame tbody tr td {
        background: #111827 !important;
        color: #c8d0e0 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 12px !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 500;
        letter-spacing: 1px;
        border-radius: 4px;
        border: 1px solid #1e3a5f;
        background: #1e2d40;
        color: #94a3b8;
        transition: all 0.15s;
    }
    .stButton > button:hover {
        background: #1e3a5f;
        color: #f8fafc;
        border-color: #3b82f6;
    }

    /* ── BUY button ── */
    .buy-btn > button {
        background: #064e3b !important;
        color: #10b981 !important;
        border-color: #10b981 !important;
        font-weight: 600 !important;
    }
    .buy-btn > button:hover {
        background: #10b981 !important;
        color: #fff !important;
    }

    /* ── SELL button ── */
    .sell-btn > button {
        background: #450a0a !important;
        color: #ef4444 !important;
        border-color: #ef4444 !important;
        font-weight: 600 !important;
    }
    .sell-btn > button:hover {
        background: #ef4444 !important;
        color: #fff !important;
    }

    /* ── News alert ── */
    .news-alert {
        background: #1c1305;
        border-left: 3px solid #f59e0b;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        font-size: 13px;
        color: #fcd34d;
        margin: 8px 0;
        font-family: 'IBM Plex Mono', monospace;
    }

    /* ── Login Screen ── */
    .login-container {
        max-width: 420px;
        margin: 80px auto;
        background: #111827;
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
    }
    .login-logo {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 32px;
        font-weight: 700;
        color: #f59e0b;
        letter-spacing: 4px;
        margin-bottom: 8px;
    }
    .login-tagline {
        color: #6b7280;
        font-size: 12px;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 32px;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        background: #0a0e1a !important;
        border: 1px solid #1e3a5f !important;
        color: #c8d0e0 !important;
        border-radius: 4px !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }

    /* ── Slider ── */
    .stSlider > div > div > div {
        background: #1e3a5f !important;
    }
    .stSlider > div > div > div > div {
        background: #f59e0b !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #0d1226;
        border-bottom: 1px solid #1e2d40;
        gap: 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        letter-spacing: 1.5px;
        color: #6b7280;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        color: #f59e0b !important;
        border-bottom: 2px solid #f59e0b !important;
    }

    /* ── P&L positive/negative ── */
    .pnl-positive { color: #10b981; font-weight: 600; }
    .pnl-negative { color: #ef4444; font-weight: 600; }

    /* ── Market frozen banner ── */
    .frozen-banner {
        background: #1c0505;
        border: 1px solid #ef4444;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
        color: #ef4444;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
        margin-bottom: 12px;
        letter-spacing: 2px;
    }

    /* ── Divider ── */
    hr { border-color: #1e2d40 !important; }

    /* ── Small mono text ── */
    .mono { font-family: 'IBM Plex Mono', monospace; font-size: 13px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# BLACK-SCHOLES ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def black_scholes(S, K, T, r, sigma, option_type="call"):
    """Calcul Black-Scholes pour Call ou Put."""
    if T <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0) if option_type == "call" else max(K - S, 0)
        return intrinsic, 0.0, 0.0, 0.0, 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega  = S * norm.pdf(d1) * np.sqrt(T) / 100
    theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
             - r * K * np.exp(-r * T) * (norm.cdf(d2) if option_type == "call" else norm.cdf(-d2))) / 365
    return round(price, 4), round(delta, 4), round(gamma, 6), round(vega, 4), round(theta, 4)


def payoff_curve(K, premium, option_type, position, price_range):
    """Calcul du Payoff net d'une option (avec prime payée)."""
    payoffs = []
    for S in price_range:
        if option_type == "call":
            intrinsic = max(S - K, 0)
        else:
            intrinsic = max(K - S, 0)
        if position == "long":
            payoffs.append(intrinsic - premium)
        else:
            payoffs.append(premium - intrinsic)
    return np.array(payoffs)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
def init_session_state():
    defaults = {
        # Auth
        "authenticated": False,
        "user_role": None,
        "username": None,

        # Admin codes (maître + assistants)
        "admin_codes": {"ADMIN2026": "Professeur"},

        # Session info
        "session_code": "BRVM2026",
        "session_active": True,
        "market_frozen": False,
        "news_messages": [],

        # Market data
        "spot_price": 5000.0,
        "price_history": [],
        "time_history": [],

        # BS parameters
        "strike": 5000.0,
        "vol": 0.20,
        "risk_free": 0.05,
        "time_to_expiry": 0.25,

        # Traders
        "traders": {},   # {username: {cash, positions, orders}}
        "initial_cash": 1_000_000,

        # Order book
        "order_book": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Initialize price history if empty
    if not st.session_state.price_history:
        base = st.session_state.spot_price
        now  = datetime.now()
        hist = []
        for i in range(30):
            base += random.gauss(0, base * 0.005)
            hist.append(round(base, 2))
        st.session_state.price_history = hist
        st.session_state.time_history  = [
            (now - timedelta(minutes=30 - i)).strftime("%H:%M")
            for i in range(30)
        ]


def register_trader(username):
    if username not in st.session_state.traders:
        st.session_state.traders[username] = {
            "cash": st.session_state.initial_cash,
            "positions": [],   # [{type, option_type, K, qty, entry_price, premium}]
            "pnl_history": [0],
        }


# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def chart_price_history():
    fig = go.Figure()
    prices = st.session_state.price_history
    times  = st.session_state.time_history

    # Fill area
    fig.add_trace(go.Scatter(
        x=times, y=prices,
        mode="lines",
        line=dict(color="#3b82f6", width=2),
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.08)",
        name="Prix"
    ))
    # Current price marker
    if prices:
        fig.add_trace(go.Scatter(
            x=[times[-1]], y=[prices[-1]],
            mode="markers",
            marker=dict(color="#f59e0b", size=8, symbol="circle"),
            name="Actuel",
            showlegend=False
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=8, b=0),
        height=200,
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(color="#6b7280", size=9),
                   linecolor="#1e2d40"),
        yaxis=dict(showgrid=True, gridcolor="#1e2d40",
                   tickfont=dict(color="#6b7280", size=9),
                   tickformat=",.0f"),
        hovermode="x unified"
    )
    return fig


def chart_payoff(K, premium, option_type, position, current_S):
    S_range = np.linspace(K * 0.5, K * 1.5, 300)
    pnl = payoff_curve(K, premium, option_type, position, S_range)

    pos_mask = pnl >= 0
    neg_mask = pnl < 0

    fig = go.Figure()

    # Zero line
    fig.add_hline(y=0, line_color="#374151", line_width=1, line_dash="dash")

    # Negative zone
    fig.add_trace(go.Scatter(
        x=S_range[neg_mask], y=pnl[neg_mask],
        mode="lines", line=dict(color="#ef4444", width=2),
        name="Perte", fill="tozeroy", fillcolor="rgba(239,68,68,0.12)"
    ))
    # Positive zone
    fig.add_trace(go.Scatter(
        x=S_range[pos_mask], y=pnl[pos_mask],
        mode="lines", line=dict(color="#10b981", width=2),
        name="Profit", fill="tozeroy", fillcolor="rgba(16,185,129,0.12)"
    ))

    # Full line on top
    fig.add_trace(go.Scatter(
        x=S_range, y=pnl,
        mode="lines", line=dict(color="#94a3b8", width=1.5),
        showlegend=False
    ))

    # Dynamic point (current price)
    current_pnl = float(payoff_curve(K, premium, option_type, position, [current_S])[0])
    dot_color = "#10b981" if current_pnl >= 0 else "#ef4444"
    fig.add_trace(go.Scatter(
        x=[current_S], y=[current_pnl],
        mode="markers+text",
        marker=dict(color=dot_color, size=11, symbol="circle",
                    line=dict(color="white", width=2)),
        text=[f"  {current_pnl:+.0f} FCFA"],
        textfont=dict(color=dot_color, size=11, family="IBM Plex Mono"),
        textposition="middle right",
        name="Position actuelle",
        showlegend=False
    ))

    # Strike line
    fig.add_vline(x=K, line_color="#f59e0b", line_width=1, line_dash="dot",
                  annotation_text=f"K={K:.0f}", annotation_font_color="#f59e0b",
                  annotation_font_size=10)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=8, b=0),
        height=260,
        showlegend=False,
        xaxis=dict(title="Prix du sous-jacent (FCFA)",
                   showgrid=True, gridcolor="#1e2d40",
                   tickfont=dict(color="#6b7280", size=9),
                   title_font=dict(color="#6b7280", size=10)),
        yaxis=dict(title="P&L (FCFA)",
                   showgrid=True, gridcolor="#1e2d40",
                   tickfont=dict(color="#6b7280", size=9),
                   title_font=dict(color="#6b7280", size=10)),
        hovermode="x"
    )
    return fig, current_pnl


def chart_admin_pnl():
    traders = st.session_state.traders
    if not traders:
        return None
    names, pnls, colors = [], [], []
    S = st.session_state.spot_price
    for uname, data in traders.items():
        pnl = compute_trader_pnl(uname, S)
        names.append(uname)
        pnls.append(pnl)
        colors.append("#10b981" if pnl >= 0 else "#ef4444")

    fig = go.Figure(go.Bar(
        x=names, y=pnls,
        marker_color=colors,
        text=[f"{p:+,.0f}" for p in pnls],
        textposition="outside",
        textfont=dict(color="#94a3b8", size=10, family="IBM Plex Mono")
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=8, b=0),
        height=220,
        xaxis=dict(tickfont=dict(color="#94a3b8", size=10)),
        yaxis=dict(showgrid=True, gridcolor="#1e2d40",
                   tickfont=dict(color="#6b7280", size=9)),
        showlegend=False
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PORTFOLIO LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def compute_trader_pnl(username, current_S):
    trader = st.session_state.traders.get(username, {})
    total_pnl = 0
    for pos in trader.get("positions", []):
        qty = pos["qty"]
        if pos["type"] == "action":
            pnl = (current_S - pos["entry_price"]) * qty
        elif pos["type"] in ("call", "put"):
            current_bs, *_ = black_scholes(
                current_S, pos["K"],
                st.session_state.time_to_expiry,
                st.session_state.risk_free,
                st.session_state.vol,
                pos["type"]
            )
            pnl = (current_bs - pos["entry_price"]) * qty * 100
        else:
            pnl = 0
        total_pnl += pnl
    return round(total_pnl, 2)


def execute_order(username, instrument, qty, side):
    """Execute a buy/sell order."""
    trader = st.session_state.traders[username]
    S = st.session_state.spot_price

    if instrument == "Action":
        price = S
        cost  = price * qty
        if side == "BUY":
            if trader["cash"] < cost:
                return False, "Fonds insuffisants."
            trader["cash"] -= cost
            # Check if already holding
            existing = next((p for p in trader["positions"] if p["type"] == "action"), None)
            if existing:
                avg = (existing["entry_price"] * existing["qty"] + price * qty) / (existing["qty"] + qty)
                existing["qty"] += qty
                existing["entry_price"] = avg
            else:
                trader["positions"].append({"type": "action", "entry_price": price, "qty": qty})
            msg = f"✅ ACHAT {qty} actions @ {price:,.0f} FCFA"
        else:
            existing = next((p for p in trader["positions"] if p["type"] == "action"), None)
            if not existing or existing["qty"] < qty:
                return False, "Titres insuffisants."
            proceeds = price * qty
            trader["cash"] += proceeds
            existing["qty"] -= qty
            if existing["qty"] == 0:
                trader["positions"].remove(existing)
            msg = f"✅ VENTE {qty} actions @ {price:,.0f} FCFA"
        log_order(username, instrument, side, qty, price)
        return True, msg

    elif instrument in ("Call", "Put"):
        opt_type = instrument.lower()
        K        = st.session_state.strike
        T        = st.session_state.time_to_expiry
        r        = st.session_state.risk_free
        v        = st.session_state.vol
        premium, delta, gamma, vega, theta = black_scholes(S, K, T, r, v, opt_type)
        cost = premium * qty * 100  # convention: 100 sous-jacents par contrat
        if side == "BUY":
            if trader["cash"] < cost:
                return False, "Fonds insuffisants."
            trader["cash"] -= cost
            trader["positions"].append({
                "type": opt_type, "K": K, "entry_price": premium,
                "qty": qty, "delta": delta
            })
            msg = f"✅ ACHAT {qty} {instrument} K={K:,.0f} @ prime {premium:,.2f}"
        else:
            existing = next((p for p in trader["positions"]
                             if p["type"] == opt_type and p.get("K") == K), None)
            if not existing or existing["qty"] < qty:
                return False, "Contrats insuffisants."
            proceeds = premium * qty * 100
            trader["cash"] += proceeds
            existing["qty"] -= qty
            if existing["qty"] == 0:
                trader["positions"].remove(existing)
            msg = f"✅ VENTE {qty} {instrument} K={K:,.0f} @ prime {premium:,.2f}"
        log_order(username, instrument, side, qty, premium)
        return True, msg

    return False, "Instrument non reconnu."


def log_order(username, instrument, side, qty, price):
    st.session_state.order_book.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "trader": username,
        "instrument": instrument,
        "side": side,
        "qty": qty,
        "price": round(price, 2),
    })


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN SCREEN
# ─────────────────────────────────────────────────────────────────────────────
def render_login():
    st.markdown("""
    <div class="login-container">
        <div class="login-logo">BRVM·T</div>
        <div class="login-tagline">Terminal Pédagogique · Finance de Marché</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("#### Connexion")
        username = st.text_input("Nom d'utilisateur", placeholder="ex: Kofi Asante")
        access_code = st.text_input("Code d'accès", type="password",
                                    placeholder="Code session ou ADMIN")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔐  Se connecter", use_container_width=True):
                if not username.strip():
                    st.error("Entrez un nom d'utilisateur.")
                    return
                # Check admin
                if access_code in st.session_state.admin_codes:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "admin"
                    st.session_state.username   = username.strip()
                    st.rerun()
                # Check trader session code
                elif access_code == st.session_state.session_code and st.session_state.session_active:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "trader"
                    st.session_state.username   = username.strip()
                    register_trader(username.strip())
                    st.rerun()
                else:
                    st.error("Code invalide ou session fermée.")
        with col_b:
            if st.button("ℹ️  Aide", use_container_width=True):
                st.info("Entrez le code fourni par votre professeur.")

        st.markdown("""
        <div style="text-align:center; margin-top:24px; color:#374151; font-size:11px;
                    font-family:'IBM Plex Mono',monospace; letter-spacing:1px;">
        CODE SESSION DÉMO : <span style="color:#f59e0b">BRVM2026</span><br>
        CODE ADMIN DÉMO : <span style="color:#f59e0b">ADMIN2026</span>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN INTERFACE
# ─────────────────────────────────────────────────────────────────────────────
def render_admin():
    S = st.session_state.spot_price

    # ── Header ──
    st.markdown(f"""
    <div class="terminal-header">
        <div>
            <div class="terminal-logo">BRVM·T  CONTROL TOWER</div>
            <div class="terminal-subtitle">Admin : {st.session_state.username}</div>
        </div>
        <div style="text-align:right">
            <span class="live-badge">{'❄ GELÉ' if st.session_state.market_frozen else '● LIVE'}</span>
            <div class="terminal-subtitle" style="margin-top:4px">
                {datetime.now().strftime("%d/%m/%Y  %H:%M:%S")}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["⚙  MARCHÉ", "📊  MONITORING", "🔔  COMMUNICATIONS", "🔑  GESTION CODES"])

    # ══ TAB 1 : MARCHÉ ══════════════════════════════════════════════════════
    with tabs[0]:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown('<div class="panel-title">CONTRÔLE DU SOUS-JACENT</div>', unsafe_allow_html=True)
            new_S = st.slider("Prix du sous-jacent (FCFA)", 1000.0, 20000.0,
                              float(S), step=50.0, format="%.0f FCFA")
            if new_S != S:
                st.session_state.spot_price = new_S
                st.session_state.price_history.append(round(new_S, 2))
                st.session_state.time_history.append(datetime.now().strftime("%H:%M:%S"))
                if len(st.session_state.price_history) > 100:
                    st.session_state.price_history.pop(0)
                    st.session_state.time_history.pop(0)
                st.rerun()

            st.markdown(f"""
            <div class="metric-card" style="margin-top:8px">
                <div class="metric-label">Prix actuel</div>
                <div class="metric-value amber">{st.session_state.spot_price:,.0f} FCFA</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")
            uploaded = st.file_uploader("📂 Importer CSV de prix historiques",
                                        type=["csv"])
            if uploaded:
                df_csv = pd.read_csv(uploaded)
                col_num = df_csv.select_dtypes("number").columns
                if len(col_num) > 0:
                    prices = df_csv[col_num[0]].dropna().tolist()[-100:]
                    st.session_state.price_history = [round(p, 2) for p in prices]
                    st.session_state.time_history  = [str(i) for i in range(len(prices))]
                    st.session_state.spot_price    = prices[-1]
                    st.success(f"✅ {len(prices)} prix chargés.")
                    st.rerun()

        with col2:
            st.markdown('<div class="panel-title">PARAMÈTRES BLACK-SCHOLES</div>', unsafe_allow_html=True)
            st.session_state.strike = st.number_input(
                "Strike K (FCFA)", 1000.0, 20000.0,
                float(st.session_state.strike), step=100.0)
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.vol = st.slider("Volatilité σ", 0.05, 1.0,
                                                 float(st.session_state.vol), 0.01,
                                                 format="%.0f%%", help="σ annualisée")
                st.session_state.vol = round(st.session_state.vol, 2)
            with c2:
                st.session_state.time_to_expiry = st.slider(
                    "Maturité T (années)", 0.01, 2.0,
                    float(st.session_state.time_to_expiry), 0.01)

            st.session_state.risk_free = st.slider(
                "Taux sans risque r", 0.0, 0.20,
                float(st.session_state.risk_free), 0.005, format="%.1f%%")

            # BS output
            call_p, call_d, call_g, call_v, call_t = black_scholes(
                st.session_state.spot_price, st.session_state.strike,
                st.session_state.time_to_expiry, st.session_state.risk_free,
                st.session_state.vol, "call")
            put_p, put_d, *_ = black_scholes(
                st.session_state.spot_price, st.session_state.strike,
                st.session_state.time_to_expiry, st.session_state.risk_free,
                st.session_state.vol, "put")

            st.markdown(f"""
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px">
                <div class="metric-card">
                    <div class="metric-label">Prime Call</div>
                    <div class="metric-value green">{call_p:,.2f}</div>
                    <div class="metric-label">Δ {call_d:+.4f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Prime Put</div>
                    <div class="metric-value red">{put_p:,.2f}</div>
                    <div class="metric-label">Δ {put_d:+.4f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Gamma</div>
                    <div class="metric-value">{call_g:.6f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Vega (×1%)</div>
                    <div class="metric-value">{call_v:.4f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="panel-title">CONTRÔLES DE SESSION</div>', unsafe_allow_html=True)
        cc1, cc2, cc3, cc4 = st.columns(4)
        with cc1:
            label = "❄️  Geler le marché" if not st.session_state.market_frozen else "▶️  Dégeler"
            if st.button(label, use_container_width=True):
                st.session_state.market_frozen = not st.session_state.market_frozen
                st.rerun()
        with cc2:
            if st.button("🔄  Réinit. portefeuilles", use_container_width=True):
                for uname in st.session_state.traders:
                    st.session_state.traders[uname] = {
                        "cash": st.session_state.initial_cash,
                        "positions": [],
                        "pnl_history": [0],
                    }
                st.session_state.order_book = []
                st.success("Portefeuilles réinitialisés.")
        with cc3:
            new_cash = st.number_input("Cash initial (FCFA)", 100_000, 10_000_000,
                                       st.session_state.initial_cash, 50_000)
            st.session_state.initial_cash = new_cash
        with cc4:
            new_session_code = st.text_input("Code session", st.session_state.session_code)
            if new_session_code != st.session_state.session_code:
                st.session_state.session_code = new_session_code
                st.success("Code mis à jour.")

    # ══ TAB 2 : MONITORING ══════════════════════════════════════════════════
    with tabs[1]:
        if not st.session_state.traders:
            st.info("Aucun étudiant connecté pour l'instant.")
        else:
            # Summary table
            rows = []
            for uname, data in st.session_state.traders.items():
                pnl   = compute_trader_pnl(uname, st.session_state.spot_price)
                total = data["cash"] + pnl + sum(
                    p["entry_price"] * p["qty"]
                    for p in data["positions"] if p["type"] == "action"
                )
                n_pos = len(data["positions"])
                rows.append({
                    "Trader": uname,
                    "Cash (FCFA)": f"{data['cash']:,.0f}",
                    "Nb Positions": n_pos,
                    "P&L Latent": f"{pnl:+,.0f}",
                    "Valeur Portfolio": f"{total:,.0f}",
                })
            df_monitor = pd.DataFrame(rows)
            st.dataframe(df_monitor, use_container_width=True, hide_index=True)

            # PNL chart
            fig_pnl = chart_admin_pnl()
            if fig_pnl:
                st.markdown('<div class="panel-title">P&L PAR TRADER</div>', unsafe_allow_html=True)
                st.plotly_chart(fig_pnl, use_container_width=True, config={"displayModeBar": False})

            # Order book
            if st.session_state.order_book:
                st.markdown('<div class="panel-title">CARNET D\'ORDRES</div>', unsafe_allow_html=True)
                df_ob = pd.DataFrame(st.session_state.order_book[-30:][::-1])
                st.dataframe(df_ob, use_container_width=True, hide_index=True)

    # ══ TAB 3 : COMMUNICATIONS ══════════════════════════════════════════════
    with tabs[2]:
        st.markdown('<div class="panel-title">ENVOYER UNE ALERTE MARCHÉ</div>', unsafe_allow_html=True)
        news_types = ["📢 Annonce", "⚠️ Alerte", "📉 Baisse", "📈 Hausse", "🔔 Earnings"]
        col_a, col_b = st.columns([3, 1])
        with col_a:
            news_text = st.text_input("Message", placeholder="ex: BCE relève les taux de 25 pb...")
        with col_b:
            news_tag  = st.selectbox("Type", news_types)
        if st.button("📤  Diffuser", use_container_width=True):
            if news_text.strip():
                st.session_state.news_messages.append({
                    "time": datetime.now().strftime("%H:%M"),
                    "tag":  news_tag,
                    "msg":  news_text.strip()
                })
                st.success("Message diffusé !")

        st.markdown('<div class="panel-title" style="margin-top:16px">HISTORIQUE DES ALERTES</div>',
                    unsafe_allow_html=True)
        for n in reversed(st.session_state.news_messages[-10:]):
            st.markdown(f"""
            <div class="news-alert">
                <span style="color:#6b7280">[{n['time']}]</span>  {n['tag']}  {n['msg']}
            </div>
            """, unsafe_allow_html=True)
        if st.button("🗑  Effacer les alertes"):
            st.session_state.news_messages = []
            st.rerun()

    # ══ TAB 4 : GESTION CODES ══════════════════════════════════════════════
    with tabs[3]:
        st.markdown('<div class="panel-title">CODES ADMIN ACTIFS</div>', unsafe_allow_html=True)
        for code, role in st.session_state.admin_codes.items():
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:8px 12px;
                        background:#0d1226; border-radius:4px; margin:4px 0;
                        font-family:'IBM Plex Mono',monospace; font-size:13px">
                <span style="color:#f59e0b">{code}</span>
                <span style="color:#94a3b8">{role}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="panel-title" style="margin-top:16px">CRÉER UN NOUVEAU CODE ADMIN</div>',
                    unsafe_allow_html=True)
        col_x, col_y = st.columns([2, 1])
        with col_x:
            new_code = st.text_input("Code", placeholder="ex: ASSIST2026").upper()
        with col_y:
            new_role = st.text_input("Rôle", placeholder="ex: Assistant")
        if st.button("➕  Créer", use_container_width=True):
            if new_code and new_role:
                st.session_state.admin_codes[new_code] = new_role
                st.success(f"Code '{new_code}' créé.")
                st.rerun()

        # Logout
        st.markdown("---")
        if st.button("🚪  Déconnexion", use_container_width=True):
            for k in ["authenticated", "user_role", "username"]:
                st.session_state[k] = None if k != "authenticated" else False
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TRADER INTERFACE
# ─────────────────────────────────────────────────────────────────────────────
def render_trader():
    username = st.session_state.username
    trader   = st.session_state.traders.get(username, {})
    S        = st.session_state.spot_price

    # Market frozen banner
    if st.session_state.market_frozen:
        st.markdown('<div class="frozen-banner">❄  MARCHÉ GELÉ — EN ATTENTE DU PROFESSEUR</div>',
                    unsafe_allow_html=True)

    # ── Header ──
    pnl_total = compute_trader_pnl(username, S)
    pnl_color = "green" if pnl_total >= 0 else "red"
    portfolio_value = trader.get("cash", 0) + pnl_total

    st.markdown(f"""
    <div class="terminal-header">
        <div>
            <div class="terminal-logo">BRVM·T</div>
            <div class="terminal-subtitle">Trader : {username}</div>
        </div>
        <div style="display:flex; gap:16px; align-items:center">
            <div class="metric-card" style="min-width:140px">
                <div class="metric-label">Cash disponible</div>
                <div class="metric-value" style="font-size:16px">{trader.get('cash', 0):,.0f} FCFA</div>
            </div>
            <div class="metric-card" style="min-width:140px">
                <div class="metric-label">P&L Latent</div>
                <div class="metric-value {pnl_color}" style="font-size:16px">{pnl_total:+,.0f} FCFA</div>
            </div>
            <div class="metric-card" style="min-width:140px">
                <div class="metric-label">Valeur Portfolio</div>
                <div class="metric-value" style="font-size:16px">{portfolio_value:,.0f} FCFA</div>
            </div>
            <div>
                <span class="live-badge">{'❄' if st.session_state.market_frozen else '● LIVE'}</span>
                <div class="terminal-subtitle" style="margin-top:4px">{S:,.0f} FCFA</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── News ──
    if st.session_state.news_messages:
        latest = st.session_state.news_messages[-1]
        st.markdown(f"""
        <div class="news-alert">
            📡 [{latest['time']}]  {latest['tag']}  {latest['msg']}
        </div>
        """, unsafe_allow_html=True)

    # ── Main layout ──
    left_col, right_col = st.columns([1.4, 1])

    # ════════════ LEFT : ANALYSE ════════════════════════════════════════════
    with left_col:
        # Price chart
        st.markdown('<div class="panel-title">ÉVOLUTION DU PRIX — ACTION BRVM</div>',
                    unsafe_allow_html=True)
        fig_hist = chart_price_history()
        st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="panel-title" style="margin-top:4px">COURBE DE PAYOFF</div>',
                    unsafe_allow_html=True)

        # Payoff controls
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            payoff_opt  = st.selectbox("Option", ["Call", "Put"], key="po")
        with pc2:
            payoff_pos  = st.selectbox("Position", ["Long (Acheteur)", "Short (Vendeur)"], key="pp")
        with pc3:
            payoff_K    = st.number_input("Strike", 1000.0, 20000.0,
                                          float(st.session_state.strike), 100.0, key="pk")

        pos_type = "long" if "Long" in payoff_pos else "short"
        premium, *_ = black_scholes(S, payoff_K, st.session_state.time_to_expiry,
                                    st.session_state.risk_free, st.session_state.vol,
                                    payoff_opt.lower())

        fig_payoff, cur_pnl = chart_payoff(payoff_K, premium, payoff_opt.lower(),
                                           pos_type, S)
        st.plotly_chart(fig_payoff, use_container_width=True, config={"displayModeBar": False})

        pnl_color_payoff = "#10b981" if cur_pnl >= 0 else "#ef4444"
        st.markdown(f"""
        <div style="display:flex; gap:16px; margin-top:-8px">
            <div class="metric-card" style="flex:1">
                <div class="metric-label">Prime BS ({payoff_opt})</div>
                <div class="metric-value" style="font-size:15px">{premium:,.2f} FCFA</div>
            </div>
            <div class="metric-card" style="flex:1">
                <div class="metric-label">P&L au prix actuel</div>
                <div class="metric-value" style="font-size:15px; color:{pnl_color_payoff}">
                    {cur_pnl:+,.0f} FCFA
                </div>
            </div>
            <div class="metric-card" style="flex:1">
                <div class="metric-label">Point mort</div>
                <div class="metric-value" style="font-size:15px">
                    {(payoff_K + premium if payoff_opt == 'Call' else payoff_K - premium):,.0f}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ════════════ RIGHT : EXÉCUTION ═════════════════════════════════════════
    with right_col:
        st.markdown('<div class="panel-title">PASSER UN ORDRE</div>', unsafe_allow_html=True)

        if st.session_state.market_frozen:
            st.warning("Marché gelé. Ordres suspendus.")
        else:
            instrument = st.selectbox("Instrument", ["Action", "Call", "Put"], key="inst")
            qty = st.number_input("Quantité", 1, 1000, 1, key="qty")

            # Price preview
            if instrument == "Action":
                preview_price = S
                preview_cost  = preview_price * qty
                st.markdown(f"""
                <div class="metric-card" style="margin:8px 0">
                    <div class="metric-label">Prix unitaire</div>
                    <div class="metric-value amber" style="font-size:15px">{preview_price:,.0f} FCFA</div>
                    <div class="metric-label">Coût total ≈ {preview_cost:,.0f} FCFA</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                opt_p, opt_d, *_ = black_scholes(
                    S, st.session_state.strike, st.session_state.time_to_expiry,
                    st.session_state.risk_free, st.session_state.vol, instrument.lower())
                preview_cost = opt_p * qty * 100
                st.markdown(f"""
                <div class="metric-card" style="margin:8px 0">
                    <div class="metric-label">Prime BS ({instrument})</div>
                    <div class="metric-value amber" style="font-size:15px">{opt_p:,.2f} FCFA</div>
                    <div class="metric-label">Coût ≈ {preview_cost:,.0f} | Delta {opt_d:+.4f}</div>
                </div>
                """, unsafe_allow_html=True)

            col_buy, col_sell = st.columns(2)
            with col_buy:
                st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
                if st.button("▲  ACHETER", use_container_width=True, key="buy_btn"):
                    ok, msg = execute_order(username, instrument, qty, "BUY")
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with col_sell:
                st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
                if st.button("▼  VENDRE", use_container_width=True, key="sell_btn"):
                    ok, msg = execute_order(username, instrument, qty, "SELL")
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # ── Portfolio ──
        st.markdown('<div class="panel-title" style="margin-top:16px">MON PORTEFEUILLE</div>',
                    unsafe_allow_html=True)

        if not trader.get("positions"):
            st.markdown("""
            <div style="text-align:center; padding:20px; color:#374151;
                        font-family:'IBM Plex Mono',monospace; font-size:12px">
                Aucune position ouverte.
            </div>
            """, unsafe_allow_html=True)
        else:
            rows = []
            for pos in trader["positions"]:
                if pos["type"] == "action":
                    current_val = S
                    pnl_pos = (S - pos["entry_price"]) * pos["qty"]
                    rows.append({
                        "Titre": "Action BRVM",
                        "Qté": pos["qty"],
                        "Entrée": f"{pos['entry_price']:,.0f}",
                        "Actuel": f"{current_val:,.0f}",
                        "P&L": f"{pnl_pos:+,.0f}",
                    })
                else:
                    cur_p, *_ = black_scholes(
                        S, pos["K"], st.session_state.time_to_expiry,
                        st.session_state.risk_free, st.session_state.vol, pos["type"])
                    pnl_pos = (cur_p - pos["entry_price"]) * pos["qty"] * 100
                    rows.append({
                        "Titre": f"{pos['type'].upper()} K={pos['K']:,.0f}",
                        "Qté": pos["qty"],
                        "Entrée": f"{pos['entry_price']:,.2f}",
                        "Actuel": f"{cur_p:,.2f}",
                        "P&L": f"{pnl_pos:+,.0f}",
                    })
            df_pos = pd.DataFrame(rows)
            st.dataframe(df_pos, use_container_width=True, hide_index=True)

        # ── BS Référence rapide ──
        st.markdown('<div class="panel-title" style="margin-top:12px">GREEKS — RÉFÉRENCE RAPIDE</div>',
                    unsafe_allow_html=True)
        call_p, call_d, call_g, call_v, call_t = black_scholes(
            S, st.session_state.strike, st.session_state.time_to_expiry,
            st.session_state.risk_free, st.session_state.vol, "call")
        put_p,  put_d, *_ = black_scholes(
            S, st.session_state.strike, st.session_state.time_to_expiry,
            st.session_state.risk_free, st.session_state.vol, "put")

        st.markdown(f"""
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px">
            <div class="metric-card">
                <div class="metric-label">Call (K={st.session_state.strike:,.0f})</div>
                <div class="metric-value green" style="font-size:15px">{call_p:,.2f}</div>
                <div class="metric-label">Δ = {call_d:+.4f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Put (K={st.session_state.strike:,.0f})</div>
                <div class="metric-value red" style="font-size:15px">{put_p:,.2f}</div>
                <div class="metric-label">Δ = {put_d:+.4f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Gamma</div>
                <div class="metric-value" style="font-size:14px">{call_g:.6f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Vega / 1%σ</div>
                <div class="metric-value" style="font-size:14px">{call_v:.4f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Logout
        st.markdown("---")
        if st.button("🚪  Déconnexion", use_container_width=True):
            for k in ["authenticated", "user_role", "username"]:
                st.session_state[k] = None if k != "authenticated" else False
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    init_session_state()

    if not st.session_state.authenticated:
        render_login()
    elif st.session_state.user_role == "admin":
        render_admin()
    else:
        render_trader()


if __name__ == "__main__":
    main()

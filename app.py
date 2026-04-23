import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm
import json
import os
import socket
import datetime
import io


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IUT_G-Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Constants ─────────────────────────────────────────────────────────────────
STATE_FILE = "market_state.json"
MASTER_CODE = "ADMIN2026"

DEFAULT_STATE = {
    "spot": 100.0,
    "K": 100.0,
    "sigma": 0.20,
    "T": 0.25,
    "r": 0.05,
    "frozen": False,
    "session_code": "BRVM2026",
    "initial_cash": 10000.0,
    "price_history": [100.0],
    "order_book": [],
    "alerts": [],
    "admin_codes": {"ADMIN2026": "master"},
    "accounts": {},
}

# ── JSON persistence ──────────────────────────────────────────────────────────
def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
            # fill missing keys from default
            for k, v in DEFAULT_STATE.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            pass
    return dict(DEFAULT_STATE)

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ── Black-Scholes ─────────────────────────────────────────────────────────────
def bs_price(S, K, T, r, sigma, option="call"):
    if T <= 0 or sigma <= 0:
        intrinsic = max(S - K, 0) if option == "call" else max(K - S, 0)
        return intrinsic
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def bs_greeks(S, K, T, r, sigma, option="call"):
    if T <= 0 or sigma <= 0:
        return {"delta": 0, "gamma": 0, "vega": 0, "theta": 0}
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    pdf_d1 = norm.pdf(d1)
    gamma = pdf_d1 / (S * sigma * np.sqrt(T))
    vega = S * pdf_d1 * np.sqrt(T) / 100
    if option == "call":
        delta = norm.cdf(d1)
        theta = (-(S * pdf_d1 * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
    else:
        delta = norm.cdf(d1) - 1
        theta = (-(S * pdf_d1 * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta}

# ── Payoff curve ──────────────────────────────────────────────────────────────
def payoff_curve(K, premium, option_type="call", position="long", n=300):
    S_range = np.linspace(K * 0.5, K * 1.5, n)
    if option_type == "call":
        intrinsic = np.maximum(S_range - K, 0)
    else:
        intrinsic = np.maximum(K - S_range, 0)
    if position == "long":
        pnl = intrinsic - premium
    else:
        pnl = premium - intrinsic
    return S_range, pnl

# ── IP detection ──────────────────────────────────────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

# ── QR Code ───────────────────────────────────────────────────────────────────
def generate_qr_svg(url: str) -> str:
    """Generate a QR Code as inline SVG using only stdlib (no qrcode/Pillow)."""
    import base64, struct, zlib

    # ── Minimal QR encoder (Model 2, byte mode, ECC=M) ──────────────────────
    # We use Python's built-in segno-free approach via the 'qrcode' stdlib
    # alternative: encode via a data-URI that embeds a Google Charts call
    # (offline fallback: pure matrix via bit-manipulation)
    # For true offline pure-stdlib, we embed a tiny Reed-Solomon QR engine.

    # ── Use segno if available, else fallback to URL-encoded SVG placeholder ─
    try:
        import segno
        qr = segno.make(url, error="m")
        buf = io.StringIO()
        qr.save(buf, kind="svg", dark="#f59e0b", light="#0a0e1a", scale=4, border=2)
        return buf.getvalue()
    except ImportError:
        pass

    # ── Pure stdlib fallback: tiny QR via Reed-Solomon ───────────────────────
    # We implement a minimal version sufficient for short URLs (<80 chars)
    def _rs_encode(data, nsym):
        """Reed-Solomon encoding over GF(256) with primitive poly 0x11d."""
        gen = [1]
        for i in range(nsym):
            gen = _poly_mult(gen, [1, _gf_pow(2, i)])
        msg = list(data) + [0] * nsym
        for i in range(len(data)):
            coef = msg[i]
            if coef:
                for j in range(1, len(gen)):
                    msg[i+j] ^= _gf_mult(gen[j], coef)
        return msg[len(data):]

    gf_exp = [1] * 512
    gf_log = [0] * 256
    x = 1
    for i in range(1, 255):
        x = (x << 1) ^ (0x11d if x & 0x80 else 0)
        x &= 0xff
        gf_exp[i] = x
        gf_log[x] = i
    for i in range(255, 512):
        gf_exp[i] = gf_exp[i - 255]

    def _gf_pow(x, p): return gf_exp[(gf_log[x] * p) % 255] if x else 0
    def _gf_mult(x, y): return gf_exp[(gf_log[x] + gf_log[y]) % 255] if x and y else 0
    def _poly_mult(p, q):
        r = [0] * (len(p) + len(q) - 1)
        for i, pi in enumerate(p):
            for j, qj in enumerate(q):
                r[i+j] ^= _gf_mult(pi, qj)
        return r

    # Encode URL as QR version 3-M (29×29) – handles up to ~47 bytes cleanly
    # For longer URLs, silently truncate display (show a notice instead)
    url_b = url.encode("utf-8")
    if len(url_b) > 47:
        # Too long for our minimal encoder: render a text notice
        svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='160' height='60'>
  <rect width='160' height='60' fill='#0a0e1a' rx='6'/>
  <text x='80' y='22' fill='#f59e0b' font-size='11' font-family='monospace' text-anchor='middle'>QR non disponible</text>
  <text x='80' y='40' fill='#9ca3af' font-size='9' font-family='monospace' text-anchor='middle'>URL trop longue</text>
  <text x='80' y='54' fill='#6b7280' font-size='8' font-family='monospace' text-anchor='middle'>pip install segno</text>
</svg>"""
        return svg

    # Version 3-M: 29×29, 2 blocks, 15 EC codewords per block
    SIZE = 29
    # Data capacity: 36 data codewords for version 3-M byte mode
    n = len(url_b)
    # Bit stream: mode=0100 (byte), char count (8 bits), data, terminator
    bits = []
    def add_bits(val, nb):
        for i in range(nb-1, -1, -1):
            bits.append((val >> i) & 1)

    add_bits(0b0100, 4)   # byte mode
    add_bits(n, 8)         # char count
    for byte in url_b:
        add_bits(byte, 8)
    add_bits(0, 4)         # terminator

    # Pad to 288 bits (36 bytes)
    while len(bits) % 8: bits.append(0)
    pad_bytes = [0xEC, 0x11]
    i = 0
    while len(bits) < 288:
        add_bits(pad_bytes[i % 2], 8)
        i += 1

    # Convert bits to bytes
    data_cw = [0]*36
    for i in range(36):
        for b in range(8):
            data_cw[i] = (data_cw[i] << 1) | bits[i*8+b]

    # Version 3-M: 2 blocks, 15 EC each
    half = 18
    ec1 = _rs_encode(data_cw[:half], 15)
    ec2 = _rs_encode(data_cw[half:], 15)
    codewords = data_cw[:half] + data_cw[half:] + ec1 + ec2

    # Interleave (version 3-M blocks already interleaved above)
    # Place into bit stream for matrix
    all_bits = []
    for cw in codewords:
        for i in range(7, -1, -1):
            all_bits.append((cw >> i) & 1)

    # ── Build matrix ──────────────────────────────────────────────────────────
    mat = [[0]*SIZE for _ in range(SIZE)]
    func = [[False]*SIZE for _ in range(SIZE)]  # functional modules

    def set_func(r, c, v):
        if 0 <= r < SIZE and 0 <= c < SIZE:
            mat[r][c] = v; func[r][c] = True

    # Finder patterns
    def finder(r, c):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                if 0 <= r+dr < SIZE and 0 <= c+dc < SIZE:
                    inside = 0<=dr<=6 and 0<=dc<=6
                    v = 0
                    if inside:
                        if dr in(0,6) or dc in(0,6): v=1
                        elif dr in(1,5) or dc in(1,5): v=0
                        else: v=1
                    set_func(r+dr, c+dc, v)

    finder(0,0); finder(0,SIZE-7); finder(SIZE-7,0)

    # Timing
    for i in range(8, SIZE-8):
        set_func(6, i, 1 if i%2==0 else 0)
        set_func(i, 6, 1 if i%2==0 else 0)

    # Dark module
    set_func(SIZE-8, 8, 1)

    # Format info placeholders
    fmt_pos = [(8,0),(8,1),(8,2),(8,3),(8,4),(8,5),(8,7),(8,8),
               (7,8),(5,8),(4,8),(3,8),(2,8),(1,8),(0,8)]
    fmt_pos2 = [(SIZE-1,8),(SIZE-2,8),(SIZE-3,8),(SIZE-4,8),(SIZE-5,8),(SIZE-6,8),(SIZE-7,8),
                (8,SIZE-8),(8,SIZE-7),(8,SIZE-6),(8,SIZE-5),(8,SIZE-4),(8,SIZE-3),(8,SIZE-2),(8,SIZE-1)]
    for (r,c) in fmt_pos+fmt_pos2:
        if 0<=r<SIZE and 0<=c<SIZE: func[r][c]=True

    # Alignment pattern (version 3: one at row=22,col=22)
    def align(r,c):
        for dr in range(-2,3):
            for dc in range(-2,3):
                v=1 if (abs(dr)==2 or abs(dc)==2) else (1 if dr==0 and dc==0 else 0)
                set_func(r+dr,c+dc,v)
    align(22,22)

    # Place data bits (right-to-left column pairs, bottom-to-top)
    bit_idx = 0
    col = SIZE - 1
    going_up = True
    while col >= 0:
        if col == 6: col -= 1  # skip timing column
        cols = [col, col-1]
        rows = range(SIZE-1,-1,-1) if going_up else range(SIZE)
        for r in rows:
            for c in cols:
                if 0<=c<SIZE and not func[r][c]:
                    if bit_idx < len(all_bits):
                        mat[r][c] = all_bits[bit_idx]
                    bit_idx += 1
        going_up = not going_up
        col -= 2

    # Apply mask pattern 0 ((r+c)%2==0)
    for r in range(SIZE):
        for c in range(SIZE):
            if not func[r][c] and (r+c)%2==0:
                mat[r][c] ^= 1

    # Format string for mask 0, ECC=M: 101010000010010 XOR 101010000010010... standard
    # Precomputed format bits for M-level, mask 0: 101010000010010
    fmt_bits = [1,0,1,0,1,0,0,0,0,0,1,0,0,1,0]
    for i,(r,c) in enumerate(fmt_pos):
        if 0<=r<SIZE and 0<=c<SIZE: mat[r][c]=fmt_bits[i]
    for i,(r,c) in enumerate(fmt_pos2):
        if 0<=r<SIZE and 0<=c<SIZE: mat[r][c]=fmt_bits[i]

    # ── Render as SVG ─────────────────────────────────────────────────────────
    cell = 5; border = 10
    total = SIZE*cell + 2*border
    rects = []
    for r in range(SIZE):
        for c in range(SIZE):
            if mat[r][c]:
                x = border + c*cell; y = border + r*cell
                rects.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="#f59e0b"/>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{total}">'
           f'<rect width="{total}" height="{total}" fill="#0a0e1a"/>'
           + "".join(rects) + "</svg>")
    return svg

# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0a0e1a !important;
        color: #e2e8f0 !important;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    [data-testid="stSidebar"] { background-color: #0d1220 !important; }
    [data-testid="stHeader"] { background-color: #0a0e1a !important; }

    h1, h2, h3 { font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; }

    .mono { font-family: 'IBM Plex Mono', monospace; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="metric-container"] label { color: #6b7280 !important; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 22px;
        color: #f59e0b;
    }

    /* Tabs */
    [data-testid="stTabs"] [role="tab"] {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 13px;
        letter-spacing: 0.05em;
        color: #6b7280;
        border-bottom: 2px solid transparent;
        padding: 8px 20px;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #f59e0b !important;
        border-bottom: 2px solid #f59e0b !important;
    }

    /* Buttons */
    .stButton > button {
        background: #111827;
        border: 1px solid #374151;
        color: #e2e8f0;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
        border-radius: 6px;
        transition: all 0.15s;
    }
    .stButton > button:hover { border-color: #f59e0b; color: #f59e0b; }

    /* BUY button */
    .buy-btn > button {
        background: #064e3b !important;
        border: 1px solid #10b981 !important;
        color: #10b981 !important;
        font-weight: 600;
        font-size: 15px;
        width: 100%;
    }
    .buy-btn > button:hover { background: #10b981 !important; color: #0a0e1a !important; }

    /* SELL button */
    .sell-btn > button {
        background: #450a0a !important;
        border: 1px solid #ef4444 !important;
        color: #ef4444 !important;
        font-weight: 600;
        font-size: 15px;
        width: 100%;
    }
    .sell-btn > button:hover { background: #ef4444 !important; color: #0a0e1a !important; }

    /* Cards */
    .card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .card-amber { border-left: 3px solid #f59e0b; }
    .card-green { border-left: 3px solid #10b981; }
    .card-red   { border-left: 3px solid #ef4444; }

    /* LIVE badge */
    .badge-live {
        display: inline-block;
        background: #ef4444;
        color: white;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 99px;
        letter-spacing: 0.1em;
        animation: pulse 1.5s infinite;
    }
    .badge-frozen {
        display: inline-block;
        background: #1e3a5f;
        color: #60a5fa;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 99px;
        letter-spacing: 0.1em;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0.5; }
    }

    /* Table */
    [data-testid="stDataFrame"] { font-family: 'IBM Plex Mono', monospace; font-size: 12px; }

    /* Inputs */
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input {
        background: #1f2937 !important;
        border: 1px solid #374151 !important;
        color: #e2e8f0 !important;
        font-family: 'IBM Plex Mono', monospace;
        border-radius: 6px;
    }
    [data-testid="stSelectbox"] > div > div {
        background: #1f2937 !important;
        border: 1px solid #374151 !important;
        color: #e2e8f0 !important;
    }

    /* Alert box */
    .alert-box {
        background: #0d1220;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    .alert-time { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #6b7280; }

    /* Header */
    .terminal-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 10px 0 20px 0;
        border-bottom: 1px solid #1f2937;
        margin-bottom: 24px;
    }
    .terminal-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 22px;
        font-weight: 600;
        color: #f59e0b;
        letter-spacing: 0.05em;
    }
    .terminal-sub {
        font-size: 12px;
        color: #6b7280;
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Session share box */
    .share-box {
        background: #0d1220;
        border: 1px solid #f59e0b44;
        border-radius: 10px;
        padding: 18px 22px;
        margin-top: 12px;
    }
    .share-title { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: #f59e0b; margin-bottom: 10px; }

    /* Divider */
    hr { border-color: #1f2937 !important; }

    /* Green/Red text */
    .green { color: #10b981; font-family: 'IBM Plex Mono', monospace; }
    .red   { color: #ef4444; font-family: 'IBM Plex Mono', monospace; }
    .amber { color: #f59e0b; font-family: 'IBM Plex Mono', monospace; }
    </style>
    """, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
def render_header(role: str, username: str, market_state: dict):
    frozen = market_state.get("frozen", False)
    badge = '<span class="badge-frozen">❄ GELÉ</span>' if frozen else '<span class="badge-live">● LIVE</span>'
    st.markdown(f"""
    <div class="terminal-header">
        <div>
            <div class="terminal-title">IUT_G-Terminal</div>
            <div class="terminal-sub">Simulation Salle de Marché · {role.upper()} · {username}</div>
        </div>
        <div style="margin-left:auto">{badge}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Login ─────────────────────────────────────────────────────────────────────
def render_login():
    inject_css()
    st.markdown("""
    <div style="max-width:400px;margin:80px auto;">
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-family:'IBM Plex Mono',monospace;font-size:32px;font-weight:600;color:#f59e0b;letter-spacing:0.08em;">
                IUT_G-Terminal
            </div>
            <div style="font-size:13px;color:#6b7280;margin-top:6px;">
                Simulation Salle de Marché BRVM
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mode = st.selectbox("Rôle", ["Trader (Étudiant)", "Administrateur (Professeur)"])

        if "Administrateur" in mode:
            code = st.text_input("Code Administrateur", type="password", placeholder="ADMIN2026")
            if st.button("Connexion Admin", use_container_width=True):
                ms = load_state()
                if code in ms.get("admin_codes", {}):
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "admin"
                    st.session_state["username"] = "Admin"
                    st.rerun()
                else:
                    st.error("Code administrateur invalide.")
        else:
            username = st.text_input("Nom / Prénom", placeholder="Ex: Koffi Amega")
            code = st.text_input("Code de session", placeholder="Ex: BRVM2026")
            if st.button("Entrer sur le marché", use_container_width=True):
                ms = load_state()
                if not username.strip():
                    st.error("Entrez votre nom.")
                elif code != ms.get("session_code", ""):
                    st.error("Code de session invalide.")
                else:
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = "trader"
                    st.session_state["username"] = username.strip()
                    # init account if new
                    ms2 = load_state()
                    if username.strip() not in ms2["accounts"]:
                        ms2["accounts"][username.strip()] = {
                            "cash": ms2["initial_cash"],
                            "portfolio": [],
                        }
                        save_state(ms2)
                    st.rerun()

# ── Plotly theme helper ───────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0a0e1a",
    plot_bgcolor="#0d1220",
    font=dict(family="IBM Plex Mono", color="#9ca3af", size=11),
    margin=dict(l=40, r=20, t=30, b=40),
    xaxis=dict(gridcolor="#1f2937", zerolinecolor="#374151"),
    yaxis=dict(gridcolor="#1f2937", zerolinecolor="#374151"),
)

# ═══════════════════════════════════════════════════════════════════════════════
#  ADMIN INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def render_admin():
    ms = load_state()
    inject_css()
    render_header("ADMIN", "Professeur", ms)

    tab_market, tab_monitor, tab_comms, tab_codes = st.tabs([
        "📈 Marché", "👁 Monitoring", "📢 Communications", "🔑 Codes Admin"
    ])

    # ── TAB: MARCHÉ ────────────────────────────────────────────────────────────
    with tab_market:
        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.markdown("#### Prix du sous-jacent")
            new_spot = st.slider(
                "Spot (S)", min_value=10.0, max_value=500.0,
                value=float(ms["spot"]), step=0.5,
                help="Prix courant de l'action"
            )
            if new_spot != ms["spot"]:
                ms["spot"] = new_spot
                ms["price_history"].append(new_spot)
                if len(ms["price_history"]) > 200:
                    ms["price_history"] = ms["price_history"][-200:]
                save_state(ms)
                st.rerun()

            st.markdown("---")
            st.markdown("#### Import CSV de prix")
            uploaded = st.file_uploader("Fichier CSV", type=["csv"])
            if uploaded:
                try:
                    df_csv = pd.read_csv(uploaded)
                    num_cols = df_csv.select_dtypes(include="number").columns
                    if len(num_cols) > 0:
                        prices = df_csv[num_cols[0]].dropna().tolist()
                        ms["price_history"] = prices
                        ms["spot"] = prices[-1]
                        save_state(ms)
                        st.success(f"✓ {len(prices)} prix importés · Colonne: {num_cols[0]}")
                        st.rerun()
                    else:
                        st.error("Aucune colonne numérique détectée.")
                except Exception as e:
                    st.error(f"Erreur: {e}")

            st.markdown("---")
            st.markdown("#### Contrôles de marché")
            c1, c2 = st.columns(2)
            with c1:
                frozen_label = "▶ Dégeler le marché" if ms["frozen"] else "❄ Geler le marché"
                if st.button(frozen_label, use_container_width=True):
                    ms["frozen"] = not ms["frozen"]
                    save_state(ms)
                    st.rerun()
            with c2:
                if st.button("🔄 Réinitialiser portefeuilles", use_container_width=True):
                    for u in ms["accounts"]:
                        ms["accounts"][u] = {"cash": ms["initial_cash"], "portfolio": []}
                    ms["order_book"] = []
                    save_state(ms)
                    st.success("Portefeuilles réinitialisés.")
                    st.rerun()

            new_cash = st.number_input("Capital initial (FCFA)", value=float(ms["initial_cash"]), step=1000.0)
            new_code = st.text_input("Code de session", value=ms["session_code"])
            if st.button("💾 Sauvegarder paramètres"):
                ms["initial_cash"] = new_cash
                ms["session_code"] = new_code
                save_state(ms)
                st.success("Paramètres sauvegardés.")
                st.rerun()

        with col_right:
            st.markdown("#### Paramètres Black-Scholes")
            ms["K"]     = st.number_input("Strike (K)", value=float(ms["K"]), step=1.0)
            ms["sigma"] = st.slider("Volatilité σ", 0.05, 1.0, float(ms["sigma"]), 0.01, format="%.2f")
            ms["T"]     = st.slider("Maturité T (années)", 0.01, 2.0, float(ms["T"]), 0.01, format="%.2f")
            ms["r"]     = st.slider("Taux sans risque r", 0.0, 0.2, float(ms["r"]), 0.01, format="%.2f")
            save_state(ms)

            S, K, sigma, T, r = ms["spot"], ms["K"], ms["sigma"], ms["T"], ms["r"]
            call_p = bs_price(S, K, T, r, sigma, "call")
            put_p  = bs_price(S, K, T, r, sigma, "put")
            g_call = bs_greeks(S, K, T, r, sigma, "call")
            g_put  = bs_greeks(S, K, T, r, sigma, "put")

            st.markdown("---")
            st.markdown("#### Primes & Greeks (temps réel)")
            ca, cb = st.columns(2)
            with ca:
                st.markdown(f"<div class='card card-green'><b>CALL</b><br><span class='green mono' style='font-size:20px'>{call_p:.2f}</span><br><small style='color:#6b7280'>Δ {g_call['delta']:.3f} · Γ {g_call['gamma']:.4f}<br>Vega {g_call['vega']:.4f} · Θ {g_call['theta']:.4f}</small></div>", unsafe_allow_html=True)
            with cb:
                st.markdown(f"<div class='card card-red'><b>PUT</b><br><span class='red mono' style='font-size:20px'>{put_p:.2f}</span><br><small style='color:#6b7280'>Δ {g_put['delta']:.3f} · Γ {g_put['gamma']:.4f}<br>Vega {g_put['vega']:.4f} · Θ {g_put['theta']:.4f}</small></div>", unsafe_allow_html=True)

            st.markdown("---")
            # Session share
            detected_ip = get_local_ip()
            if detected_ip == "127.0.0.1":
                manual_ip = st.text_input("IP locale non détectée — entrez-la manuellement", placeholder="192.168.x.x")
                local_ip = manual_ip if manual_ip else "127.0.0.1"
            else:
                local_ip = detected_ip
            url = f"http://{local_ip}:8501"
            st.markdown(f"""
            <div class="share-box">
                <div class="share-title">📡 Partage de Session</div>
                <div style="font-size:12px;color:#9ca3af;margin-bottom:8px;">URL d'accès étudiant :</div>
            """, unsafe_allow_html=True)
            st.code(url, language=None)
            st.markdown(f"""
                <div style="font-size:12px;color:#9ca3af;margin-top:8px;">Code de session :</div>
            """, unsafe_allow_html=True)
            st.code(ms["session_code"], language=None)
            try:
                qr_svg = generate_qr_svg(url)
                st.markdown(
                    f'<div style="margin-top:8px">{qr_svg}</div>'
                    f'<div style="font-size:10px;color:#6b7280;margin-top:4px;">QR Code → URL Étudiants</div>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.warning(f"QR Code indisponible : {e}")
            st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB: MONITORING ────────────────────────────────────────────────────────
    with tab_monitor:
        ms = load_state()
        S = ms["spot"]
        K, sigma, T, r = ms["K"], ms["sigma"], ms["T"], ms["r"]
        accounts = ms.get("accounts", {})

        st.markdown("#### Tableau P&L Étudiants")
        rows = []
        for name, acc in accounts.items():
            cash = acc["cash"]
            pnl_latent = 0.0
            pos_value = 0.0
            for p in acc.get("portfolio", []):
                qty = p["qty"]
                entry_price = p["entry_price"]
                inst = p["instrument"]
                if inst == "action":
                    curr_val = S * qty
                    cost = entry_price * qty
                elif inst == "call":
                    curr_val = bs_price(S, K, T, r, sigma, "call") * qty * 100
                    cost = entry_price * qty * 100
                else:
                    curr_val = bs_price(S, K, T, r, sigma, "put") * qty * 100
                    cost = entry_price * qty * 100
                pnl_latent += curr_val - cost
                pos_value += curr_val
            total = cash + pos_value
            rows.append({"Étudiant": name, "Cash": f"{cash:,.0f}", "Positions": f"{pos_value:,.0f}", "P&L Latent": f"{pnl_latent:+,.0f}", "Total": f"{total:,.0f}"})

        if rows:
            df_pnl = pd.DataFrame(rows)
            st.dataframe(df_pnl, use_container_width=True, hide_index=True)

            # Bar chart
            names = [r["Étudiant"] for r in rows]
            pnls  = [float(r["P&L Latent"].replace(",","").replace("+","")) for r in rows]
            colors = ["#10b981" if v >= 0 else "#ef4444" for v in pnls]
            fig = go.Figure(go.Bar(x=names, y=pnls, marker_color=colors))
            fig.update_layout(title="P&L Comparatif", **PLOTLY_LAYOUT, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun étudiant connecté pour l'instant.")

        st.markdown("---")
        st.markdown("#### Carnet d'ordres global (30 derniers)")
        orders = ms.get("order_book", [])[-30:]
        if orders:
            df_orders = pd.DataFrame(orders[::-1])
            st.dataframe(df_orders, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun ordre passé.")

    # ── TAB: COMMUNICATIONS ────────────────────────────────────────────────────
    with tab_comms:
        ms = load_state()
        ALERT_TYPES = {
            "📢 Annonce": "announce",
            "⚠️ Alerte": "alert",
            "📈 Hausse": "up",
            "📉 Baisse": "down",
            "🔔 Earnings": "earnings",
        }
        st.markdown("#### Envoyer une alerte marché")
        alert_type = st.selectbox("Type", list(ALERT_TYPES.keys()))
        alert_msg  = st.text_area("Message", placeholder="Ex: Publication des résultats T3 dans 5 minutes…")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Envoyer", use_container_width=True):
                if alert_msg.strip():
                    ms["alerts"].insert(0, {
                        "type": alert_type,
                        "msg": alert_msg.strip(),
                        "time": datetime.datetime.now().strftime("%H:%M:%S"),
                    })
                    if len(ms["alerts"]) > 10:
                        ms["alerts"] = ms["alerts"][:10]
                    save_state(ms)
                    st.success("Alerte envoyée.")
                    st.rerun()
        with c2:
            if st.button("🗑 Effacer toutes", use_container_width=True):
                ms["alerts"] = []
                save_state(ms)
                st.rerun()

        st.markdown("---")
        st.markdown("#### Historique (10 dernières)")
        for alert in ms.get("alerts", []):
            st.markdown(f"""
            <div class="alert-box">
                <div style="font-size:15px;margin-bottom:4px;">{alert['type']} &nbsp;{alert['msg']}</div>
                <div class="alert-time">{alert.get('time','')}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB: CODES ADMIN ───────────────────────────────────────────────────────
    with tab_codes:
        ms = load_state()
        st.markdown("#### Codes actifs")
        codes = ms.get("admin_codes", {})
        for code, role in codes.items():
            st.markdown(f"`{code}` → **{role}**")

        st.markdown("---")
        st.markdown("#### Créer un code assistant")
        new_code_val = st.text_input("Nouveau code", placeholder="ASSIST_001")
        if st.button("➕ Ajouter"):
            if new_code_val.strip():
                ms["admin_codes"][new_code_val.strip()] = "assistant"
                save_state(ms)
                st.success(f"Code `{new_code_val}` ajouté.")
                st.rerun()
            else:
                st.error("Entrez un code valide.")


# ═══════════════════════════════════════════════════════════════════════════════
#  TRADER INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def get_account(ms, username):
    if username not in ms["accounts"]:
        ms["accounts"][username] = {"cash": ms["initial_cash"], "portfolio": []}
        save_state(ms)
    return ms["accounts"][username]

def save_account(ms, username, acc):
    ms["accounts"][username] = acc
    save_state(ms)

def compute_pnl(acc, S, K, T, r, sigma):
    total_pnl = 0.0
    rows = []
    for p in acc.get("portfolio", []):
        qty, ep, inst, side = p["qty"], p["entry_price"], p["instrument"], p["side"]
        if inst == "action":
            curr = S
            curr_val = curr * qty
            cost = ep * qty
        elif inst == "call":
            curr = bs_price(S, K, T, r, sigma, "call")
            curr_val = curr * qty * 100
            cost = ep * qty * 100
        else:
            curr = bs_price(S, K, T, r, sigma, "put")
            curr_val = curr * qty * 100
            cost = ep * qty * 100
        pnl = curr_val - cost if side == "BUY" else cost - curr_val
        total_pnl += pnl
        rows.append({
            "Instrument": inst.upper(),
            "Sens": side,
            "Qté": qty,
            "Prix entrée": f"{ep:.2f}",
            "Prix actuel": f"{curr:.2f}",
            "P&L": f"{pnl:+.2f}",
        })
    return rows, total_pnl

def render_trader():
    username = st.session_state["username"]
    ms = load_state()
    inject_css()
    render_header("TRADER", username, ms)

    # Frozen banner
    if ms.get("frozen"):
        st.markdown("""
        <div style="background:#1e3a5f;border:1px solid #3b82f6;border-radius:8px;
                    padding:12px 18px;text-align:center;margin-bottom:16px;
                    font-family:'IBM Plex Mono',monospace;color:#60a5fa;font-size:14px;">
            ❄ MARCHÉ GELÉ — Ordres suspendus par le professeur
        </div>
        """, unsafe_allow_html=True)

    # Alerts
    alerts = ms.get("alerts", [])
    if alerts:
        latest = alerts[0]
        st.markdown(f"""
        <div class="alert-box">
            <b>{latest['type']}</b> {latest['msg']}
            <span class="alert-time" style="float:right">{latest.get('time','')}</span>
        </div>
        """, unsafe_allow_html=True)

    S, K, sigma, T, r = ms["spot"], ms["K"], ms["sigma"], ms["T"], ms["r"]
    acc = get_account(ms, username)

    col_left, col_right = st.columns([1.2, 0.8], gap="large")

    # ── GAUCHE : ANALYSE ───────────────────────────────────────────────────────
    with col_left:
        # 1. Price history chart
        history = ms.get("price_history", [S])
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(
            y=history, mode="lines",
            fill="tozeroy",
            line=dict(color="#f59e0b", width=2),
            fillcolor="rgba(245,158,11,0.07)",
            name="Prix"
        ))
        fig_price.add_hline(y=S, line_dash="dot", line_color="#f59e0b", annotation_text=f"S={S:.2f}", annotation_font_color="#f59e0b")
        fig_price.update_layout(title="Évolution du Prix", height=240, showlegend=False, **PLOTLY_LAYOUT)
        st.plotly_chart(fig_price, use_container_width=True)

        # 2. Payoff curve
        st.markdown("#### Courbe de Payoff")
        po_col1, po_col2, po_col3 = st.columns(3)
        with po_col1:
            po_type = st.selectbox("Type", ["call", "put"], key="po_type")
        with po_col2:
            po_pos  = st.selectbox("Position", ["long", "short"], key="po_pos")
        with po_col3:
            po_K    = st.number_input("Strike payoff", value=float(K), step=1.0, key="po_K")

        premium = bs_price(S, po_K, T, r, sigma, po_type)
        S_range, pnl_arr = payoff_curve(po_K, premium, po_type, po_pos)

        # breakeven
        breakeven = None
        for i in range(len(pnl_arr) - 1):
            if pnl_arr[i] * pnl_arr[i+1] <= 0:
                breakeven = S_range[i]
                break

        # dynamic point
        pnl_at_spot = np.interp(S, S_range, pnl_arr)

        fig_po = go.Figure()
        # green zone
        fig_po.add_trace(go.Scatter(
            x=S_range, y=np.where(pnl_arr >= 0, pnl_arr, 0),
            fill="tozeroy", mode="none", fillcolor="rgba(16,185,129,0.15)", name="Profit"
        ))
        # red zone
        fig_po.add_trace(go.Scatter(
            x=S_range, y=np.where(pnl_arr < 0, pnl_arr, 0),
            fill="tozeroy", mode="none", fillcolor="rgba(239,68,68,0.15)", name="Perte"
        ))
        # curve
        fig_po.add_trace(go.Scatter(
            x=S_range, y=pnl_arr, mode="lines",
            line=dict(color="#f59e0b", width=2), name="P&L"
        ))
        # spot marker
        fig_po.add_trace(go.Scatter(
            x=[S], y=[pnl_at_spot], mode="markers+text",
            marker=dict(color="#f59e0b", size=10, symbol="diamond"),
            text=[f"  S={S:.1f}"], textfont=dict(color="#f59e0b", size=10),
            name="Prix actuel"
        ))
        if breakeven:
            fig_po.add_vline(x=breakeven, line_dash="dash", line_color="#60a5fa",
                             annotation_text=f"BE={breakeven:.1f}", annotation_font_color="#60a5fa")
        fig_po.update_layout(title="Payoff Option", height=280, showlegend=False, **PLOTLY_LAYOUT)
        st.plotly_chart(fig_po, use_container_width=True)

        # metrics under payoff
        m1, m2, m3 = st.columns(3)
        m1.metric("Prime BS", f"{premium:.4f}")
        m2.metric("P&L @ Spot", f"{pnl_at_spot:+.4f}", delta_color="normal" if pnl_at_spot >= 0 else "inverse")
        m3.metric("Point mort", f"{breakeven:.2f}" if breakeven else "N/A")

    # ── DROITE : EXÉCUTION ─────────────────────────────────────────────────────
    with col_right:
        st.markdown("#### Passer un ordre")
        instrument = st.selectbox("Instrument", ["action", "call", "put"], key="ord_inst")
        side       = st.selectbox("Sens", ["BUY", "SELL"], key="ord_side")
        qty        = st.number_input("Quantité", min_value=1, max_value=1000, value=1, step=1, key="ord_qty")

        # cost preview
        if instrument == "action":
            cost_preview = S * qty
            price_used   = S
        elif instrument == "call":
            price_used   = bs_price(S, K, T, r, sigma, "call")
            cost_preview = price_used * qty * 100
        else:
            price_used   = bs_price(S, K, T, r, sigma, "put")
            cost_preview = price_used * qty * 100

        color_cost = "#10b981" if acc["cash"] >= cost_preview else "#ef4444"
        st.markdown(f"""
        <div class="card" style="margin-bottom:12px;">
            <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;">Aperçu coût</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:20px;color:{color_cost}">{cost_preview:,.2f} <span style="font-size:13px;color:#6b7280">FCFA</span></div>
            <div style="font-size:11px;color:#6b7280;margin-top:4px;">Cash disponible : {acc['cash']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        frozen = ms.get("frozen", False)
        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown('<div class="buy-btn">', unsafe_allow_html=True)
            do_buy = st.button("▲ BUY", key="btn_buy", disabled=frozen, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with bc2:
            st.markdown('<div class="sell-btn">', unsafe_allow_html=True)
            do_sell = st.button("▼ SELL", key="btn_sell", disabled=frozen, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Execute
        if (do_buy or do_sell) and not frozen:
            ms2 = load_state()
            acc2 = get_account(ms2, username)
            action_side = "BUY" if do_buy else "SELL"

            if action_side == "BUY":
                if acc2["cash"] < cost_preview:
                    st.error("Capital insuffisant.")
                else:
                    acc2["cash"] -= cost_preview
                    acc2["portfolio"].append({
                        "instrument": instrument,
                        "side": "BUY",
                        "qty": qty,
                        "entry_price": price_used,
                    })
                    ms2["order_book"].append({
                        "Heure": datetime.datetime.now().strftime("%H:%M:%S"),
                        "Trader": username,
                        "Instrument": instrument.upper(),
                        "Sens": "BUY",
                        "Qté": qty,
                        "Prix": f"{price_used:.4f}",
                    })
                    save_account(ms2, username, acc2)
                    st.success(f"✓ BUY {qty}× {instrument} @ {price_used:.4f}")
                    st.rerun()
            else:  # SELL
                # check holdings
                holdings = [p for p in acc2["portfolio"] if p["instrument"] == instrument and p["side"] == "BUY"]
                total_held = sum(p["qty"] for p in holdings)
                if total_held < qty:
                    st.error(f"Position insuffisante ({total_held} {instrument} disponibles).")
                else:
                    # remove qty from portfolio FIFO
                    remaining = qty
                    new_port = []
                    for p in acc2["portfolio"]:
                        if p["instrument"] == instrument and p["side"] == "BUY" and remaining > 0:
                            if p["qty"] <= remaining:
                                remaining -= p["qty"]
                            else:
                                p["qty"] -= remaining
                                remaining = 0
                                new_port.append(p)
                        else:
                            new_port.append(p)
                    acc2["portfolio"] = new_port
                    acc2["cash"] += cost_preview
                    ms2["order_book"].append({
                        "Heure": datetime.datetime.now().strftime("%H:%M:%S"),
                        "Trader": username,
                        "Instrument": instrument.upper(),
                        "Sens": "SELL",
                        "Qté": qty,
                        "Prix": f"{price_used:.4f}",
                    })
                    save_account(ms2, username, acc2)
                    st.success(f"✓ SELL {qty}× {instrument} @ {price_used:.4f}")
                    st.rerun()

        st.markdown("---")

        # Portfolio table
        ms = load_state()
        acc = get_account(ms, username)
        port_rows, total_pnl = compute_pnl(acc, S, K, T, r, sigma)

        # Capital summary
        total_val = acc["cash"] + sum(
            (S * p["qty"] if p["instrument"] == "action" else
             bs_price(S, K, T, r, sigma, p["instrument"]) * p["qty"] * 100)
            for p in acc.get("portfolio", [])
        )
        pnl_color = "#10b981" if total_pnl >= 0 else "#ef4444"
        st.markdown(f"""
        <div class="card card-amber">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;">Capital total</div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;color:#f59e0b">{total_val:,.2f}</div>
                </div>
                <div style="text-align:right">
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.08em;">P&L Latent</div>
                    <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;color:{pnl_color}">{total_pnl:+,.2f}</div>
                </div>
            </div>
            <div style="font-size:11px;color:#6b7280;margin-top:8px;">Cash : {acc['cash']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        if port_rows:
            st.markdown("#### Portefeuille")
            df_port = pd.DataFrame(port_rows)
            st.dataframe(df_port, use_container_width=True, hide_index=True)
        else:
            st.markdown("<div style='color:#6b7280;font-size:13px;text-align:center;padding:20px 0;'>Aucune position ouverte</div>", unsafe_allow_html=True)

        # Greeks quick ref
        st.markdown("---")
        st.markdown("#### Greeks (paramètres actuels)")
        g = bs_greeks(S, K, T, r, sigma, "call")
        gc1, gc2, gc3, gc4 = st.columns(4)
        gc1.metric("Δ Delta", f"{g['delta']:.3f}")
        gc2.metric("Γ Gamma", f"{g['gamma']:.4f}")
        gc3.metric("Vega", f"{g['vega']:.4f}")
        gc4.metric("Θ Theta", f"{g['theta']:.4f}")

        # Order book (student view, last 10)
        st.markdown("---")
        st.markdown("#### Carnet d'ordres")
        orders = ms.get("order_book", [])[-10:]
        if orders:
            st.dataframe(pd.DataFrame(orders[::-1]), use_container_width=True, hide_index=True)
        else:
            st.markdown("<div style='color:#6b7280;font-size:13px'>Aucun ordre enregistré.</div>", unsafe_allow_html=True)

        if st.button("🚪 Déconnexion"):
            for k in ["logged_in", "role", "username"]:
                st.session_state.pop(k, None)
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if not st.session_state.get("logged_in"):
        render_login()
    elif st.session_state.get("role") == "admin":
        render_admin()
    else:
        render_trader()

if __name__ == "__main__":
    main()

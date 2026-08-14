import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime
import plotly.graph_objects as go
import plotly.express as px

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────
st.set_page_config(page_title="Nifty Hedge Analyzer", layout="wide", page_icon="📈")

# ─── CONSTANTS & CONFIG ──────────────────────────────────────────────────
FUND_OPTIONS = [
    # IDs = SEM_SMST_SECURITY_ID from official Dhan IDX_I instrument list
    # -- Broad Market --
    { "id": "NIFTYNXT50",   "label": "Nifty Next 50",         "secId": "38",  "exchSeg": "IDX_I", "color": "#9b7eea", "icon": "🚀" },
    { "id": "NIFTY500",     "label": "Nifty 500",             "secId": "19",  "exchSeg": "IDX_I", "color": "#60a5fa", "icon": "📈" },
    { "id": "NIFTYMID150",  "label": "Nifty Midcap 150",      "secId": "1",   "exchSeg": "IDX_I", "color": "#f7b731", "icon": "📊" },
    { "id": "NIFTYMCAP50",  "label": "Nifty Mid Cap 50",      "secId": "20",  "exchSeg": "IDX_I", "color": "#fb923c", "icon": "📉" },
    { "id": "NIFTYSML250",  "label": "Nifty Smallcap 250",    "secId": "3",   "exchSeg": "IDX_I", "color": "#ff8c42", "icon": "🔥" },
    { "id": "LARGEMID250",  "label": "Nifty LargeMid 250",    "secId": "6",   "exchSeg": "IDX_I", "color": "#a78bfa", "icon": "🏔️" },
    # -- Banks & Finance --
    { "id": "BANKNIFTY",    "label": "Bank Nifty",            "secId": "25",  "exchSeg": "IDX_I", "color": "#4dc9f7", "icon": "🏦" },
    { "id": "FINNIFTY",     "label": "Fin Nifty",             "secId": "27",  "exchSeg": "IDX_I", "color": "#38bdf8", "icon": "💹" },
    { "id": "NIFTYPVTBANK", "label": "Nifty Private Bank",    "secId": "15",  "exchSeg": "IDX_I", "color": "#0ea5e9", "icon": "🏧" },
    { "id": "NIFTYPSUBANK", "label": "Nifty PSU Bank",        "secId": "33",  "exchSeg": "IDX_I", "color": "#64748b", "icon": "🏛️" },
    # -- Sectors --
    { "id": "NIFTYIT",      "label": "Nifty IT",              "secId": "29",  "exchSeg": "IDX_I", "color": "#e879f9", "icon": "💻" },
    { "id": "NIFTYPHARMA",  "label": "Nifty Pharma",          "secId": "32",  "exchSeg": "IDX_I", "color": "#34d399", "icon": "💊" },
    { "id": "NIFTYFMCG",    "label": "Nifty FMCG",            "secId": "28",  "exchSeg": "IDX_I", "color": "#a3e635", "icon": "🛒" },
    { "id": "NIFTYAUTO",    "label": "Nifty Auto",            "secId": "44",  "exchSeg": "IDX_I", "color": "#fb7185", "icon": "🚗" },
    { "id": "NIFTYINFRA",   "label": "Nifty Infrastructure",  "secId": "43",  "exchSeg": "IDX_I", "color": "#fdba74", "icon": "🏗️" },
    { "id": "NIFTYMETAL",   "label": "Nifty Metal",           "secId": "31",  "exchSeg": "IDX_I", "color": "#94a3b8", "icon": "⚙️" },
    { "id": "NIFTYREALTY",  "label": "Nifty Realty",          "secId": "34",  "exchSeg": "IDX_I", "color": "#f472b6", "icon": "🏠" },
    { "id": "NIFTYENERGY",  "label": "Nifty Energy",          "secId": "42",  "exchSeg": "IDX_I", "color": "#fde047", "icon": "⚡" },
    { "id": "NIFTYCMDT",    "label": "Nifty Commodities",     "secId": "39",  "exchSeg": "IDX_I", "color": "#d97706", "icon": "🪨" },
    { "id": "NIFTYCNSMP",   "label": "Nifty Consumption",     "secId": "40",  "exchSeg": "IDX_I", "color": "#86efac", "icon": "🛍️" },
    { "id": "HEALTHCARE",   "label": "Nifty Healthcare",      "secId": "447", "exchSeg": "IDX_I", "color": "#f0abfc", "icon": "🏥" },
    # -- Thematic --
    { "id": "NIFTYALPHA50", "label": "Nifty Alpha 50",        "secId": "12",  "exchSeg": "IDX_I", "color": "#fbbf24", "icon": "⭐" },
    { "id": "NIFTYPSE",     "label": "Nifty PSE",             "secId": "41",  "exchSeg": "IDX_I", "color": "#6b7280", "icon": "🏞️" },
    { "id": "NIFTYCPSE",    "label": "Nifty CPSE",            "secId": "45",  "exchSeg": "IDX_I", "color": "#78716c", "icon": "🏭" },
    { "id": "INDDEFENCE",   "label": "Nifty India Defence",   "secId": "493", "exchSeg": "IDX_I", "color": "#4ade80", "icon": "🛡️" },
    { "id": "CAPITALMT",    "label": "Nifty Capital Markets", "secId": "803", "exchSeg": "IDX_I", "color": "#f97316", "icon": "💰" },
]

RF_RATE = 6.5
COLOR_NIFTY = "#3d8ef0"

# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_dhan_history(sec_id, exch_seg, client_id, access_token):
    instrument = "INDEX" if "IDX" in exch_seg else "EQUITY"
    url = "https://api.dhan.co/v2/charts/historical"
    headers = {
        "Content-Type": "application/json",
        "access-token": access_token,
    }
    payload = {
        "securityId": str(sec_id),
        "exchangeSegment": exch_seg,
        "instrument": instrument,
        "fromDate": "2017-01-01",
        "toDate": datetime.date.today().strftime("%Y-%m-%d")
    }
    
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code != 200:
        raise Exception(f"Dhan API Error: {res.text}")
    
    data = res.json()
    if data.get("status") == "failure":
        raise Exception(f"Dhan API returned failure: {data.get('remarks')}")
    
    data_dict = data.get("data", data)
    timestamps = data_dict.get("timestamp", data_dict.get("start_Time", []))
    closes = data_dict.get("close", [])
    
    if not timestamps or not closes:
         raise Exception(f"No data returned for {sec_id}.")
         
    ts = pd.to_datetime(timestamps, unit="s", utc=True).tz_convert('Asia/Kolkata')
    df = pd.DataFrame({
        "timestamp": ts,
        "close": closes
    })
    
    df.set_index("timestamp", inplace=True)
    monthly_df = df.resample("ME").last().dropna().reset_index()
    monthly_df["timestamp"] = pd.to_datetime(monthly_df["timestamp"])
    monthly_df["date"] = monthly_df["timestamp"].dt.strftime("%Y-%m")
    
    return monthly_df[["date", "close"]], closes[-1]

def calculate_stats(df, fund_col, nifty_col):
    df['n_ret'] = df[nifty_col].pct_change() * 100
    df['f_ret'] = df[fund_col].pct_change() * 100
    df_clean = df.dropna()
    
    nx = df_clean['n_ret']
    fx = df_clean['f_ret']
    
    cov_matrix = np.cov(nx, fx)
    beta = cov_matrix[0, 1] / cov_matrix[0, 0]
    monthly_alpha = fx.mean() - beta * nx.mean()
    
    r = nx.corr(fx)
    r2 = r ** 2
    
    ann_nifty = ((1 + nx.mean()/100)**12 - 1) * 100
    ann_fund = ((1 + fx.mean()/100)**12 - 1) * 100
    
    j_alpha = ann_fund - (RF_RATE + beta * (ann_nifty - RF_RATE))
    
    vol_n = nx.std() * np.sqrt(12)
    vol_f = fx.std() * np.sqrt(12)
    shr_n = (ann_nifty - RF_RATE) / vol_n
    shr_f = (ann_fund - RF_RATE) / vol_f
    
    return {
        "beta": beta, "monthlyAlpha": monthly_alpha, "jAlpha": j_alpha, 
        "r": r, "r2": r2, "annNifty": ann_nifty, "annFund": ann_fund, 
        "volN": vol_n, "volF": vol_f, "shrN": shr_n, "shrF": shr_f
    }

def process_data(nifty_df, fund_df, current_nifty, current_fund):
    df = pd.merge(nifty_df, fund_df, on="date", suffixes=('_nifty', '_fund'), how='inner')
    stats = calculate_stats(df, 'close_fund', 'close_nifty')
    
    base_nifty = df['close_nifty'].iloc[0]
    base_fund = df['close_fund'].iloc[0]
    
    df['nifty_rebased'] = (df['close_nifty'] / base_nifty) * 100
    df['fund_rebased'] = (df['close_fund'] / base_fund) * 100
    
    df['nifty_ma3'] = df['nifty_rebased'].rolling(window=3).mean()
    df['fund_ma3'] = df['fund_rebased'].rolling(window=3).mean()
    
    crossovers = []
    diffs = df['nifty_rebased'] - df['fund_rebased']
    for i in range(1, len(diffs)):
        prev = diffs.iloc[i-1]
        curr = diffs.iloc[i]
        if prev * curr < 0:
            c_type = "fund_leads" if curr < 0 else "nifty_leads"
            crossovers.append({"date": df['date'].iloc[i], "type": c_type, "value": df['fund_rebased'].iloc[i]})
            
    cumul_hedge = 100.0
    cumul_nifty = 100.0
    hedge_vals = [100.0]
    nifty_holds = [100.0]
    
    for i in range(1, len(df)):
        f_ret = (df['close_fund'].iloc[i] / df['close_fund'].iloc[i-1] - 1) * 100
        n_ret = (df['close_nifty'].iloc[i] / df['close_nifty'].iloc[i-1] - 1) * 100
        
        cumul_hedge *= (1 + (f_ret + stats['monthlyAlpha']/2)/100)
        cumul_nifty *= (1 + n_ret/100)
        
        hedge_vals.append(cumul_hedge)
        nifty_holds.append(cumul_nifty)
        
    df['hedge_value'] = hedge_vals
    df['nifty_hold'] = nifty_holds
    df['hedge_spread'] = df['hedge_value'] - df['nifty_hold']
    df['monthly_spread'] = df['f_ret'] - df['n_ret']
    
    stats['df'] = df
    stats['crossovers'] = crossovers
    stats['currentNiftyPrice'] = current_nifty
    stats['fundCurrentNAV'] = current_fund
    return stats


# ─── AUTH ────────────────────────────────────────────────────────────────
client_id    = st.session_state.get("dhan_client_id", "")
access_token = st.session_state.get("dhan_access_token", "")
_connected   = bool(client_id and access_token)

# Auto-open once on very first visit when not connected
if not _connected and not st.session_state.get("_creds_dialog_shown", False):
    st.session_state["show_creds"] = True
    st.session_state["_creds_dialog_shown"] = True

# Guard: if connected and the button was NOT just clicked, keep dialog closed.
# We detect "just clicked" via a one-shot flag set by the button before rerun.
if _connected and not st.session_state.get("_settings_requested", False):
    st.session_state["show_creds"] = False
# Consume the one-shot flag immediately
st.session_state["_settings_requested"] = False

def_lot = 75
def_put  = 65.0

# ─── DIALOG DEFINITION ───────────────────────────────────────────────────
@st.dialog("🔐 Dhan API Credentials")
def creds_dialog():
    st.markdown(
        "<p style='color:#6b7280;font-size:13px;margin-bottom:4px'>"
        "Stored <b>only in your browser session</b> — cleared when you close the tab. "
        "Never shared with other users.</p>",
        unsafe_allow_html=True
    )
    inp_cid = st.text_input("Client ID",
        value=st.session_state.get("dhan_client_id", ""),
        placeholder="e.g. 1234567891")
    inp_tok = st.text_input("Access Token",
        value=st.session_state.get("dhan_access_token", ""),
        type="password",
        placeholder="Paste your Dhan access token here")
    st.markdown(" ")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("💾 Save & Connect", type="primary", use_container_width=True):
            if inp_cid.strip() and inp_tok.strip():
                st.session_state["dhan_client_id"]    = inp_cid.strip()
                st.session_state["dhan_access_token"] = inp_tok.strip()
                st.session_state["show_creds"]        = False
                st.rerun()
            else:
                st.error("Both fields are required.")
    with b2:
        if st.button("🚪 Logout / Clear", use_container_width=True):
            for k in ["dhan_client_id", "dhan_access_token", "results"]:
                st.session_state.pop(k, None)
            st.session_state["show_creds"]          = False
            st.session_state["_creds_dialog_shown"] = False
            st.rerun()

# Open dialog only when explicitly requested
if st.session_state.get("show_creds", False):
    creds_dialog()

# ─── MAIN APP ────────────────────────────────────────────────────────────

# Global theme — warm beige background, white cards
st.markdown("""<style>
/* Page background */
.stApp { background-color: #f4f6f9 !important; }
[data-testid="stAppViewContainer"] { background-color: #f4f6f9 !important; }
[data-testid="stHeader"] { background-color: #f4f6f9 !important; }
.block-container { padding-top: 2.5rem !important; padding-bottom: 2rem !important; }

/* Selectbox */
div[data-testid="stSelectbox"] > div > div {
    background: #fff !important;
    border: 0.5px solid #d1d9e6 !important;
    border-radius: 8px !important;
}

/* Tabs */
div[data-testid="stTabs"] button[role="tab"] {
    font-size: 13px !important;
    color: #6b7280 !important;
    padding: 8px 16px !important;
    background: transparent !important;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #111827 !important;
    font-weight: 500 !important;
    border-bottom: 2px solid #111827 !important;
    background: transparent !important;
}
/* Plotly chart card borders */
div[data-testid="stPlotlyChart"] {
    background: #fff;
    border: 0.5px solid #d1d9e6;
    border-radius: 10px;
    padding: 8px;
    margin-bottom: 12px;
}
/* Tab border line colour */
[data-baseweb="tab-border"] { background-color: #d1d9e6 !important; }
.stTabs [role="tablist"] { border-bottom: 0.5px solid #d1d9e6 !important; }

/* Metric area bg */
div[data-testid="metric-container"] {
    background: #fff !important;
    border: 0.5px solid #e5e7eb !important;
    border-radius: 10px !important;
}

/* Settings button pill */
div[data-testid="stButton"] button[kind="secondary"] {
    padding: 3px 12px !important;
    font-size: 12px !important;
    border-radius: 20px !important;
    border: 0.5px solid #d1d5db !important;
    background: transparent !important;
    color: #6b7280 !important;
    height: auto !important;
    min-height: unset !important;
    line-height: 1.6 !important;
}
</style>
<script>
(function fixTabs(){
  var apply = function(){
    var els = window.parent.document.querySelectorAll('[data-baseweb="tab-highlight"]');
    els.forEach(function(el){ el.style.setProperty("background-color","#1e2d45","important"); });
    var borders = window.parent.document.querySelectorAll('[data-baseweb="tab-border"]');
    borders.forEach(function(el){ el.style.setProperty("background-color","#e5e7eb","important"); });
  };
  apply();
  var obs = new MutationObserver(apply);
  obs.observe(window.parent.document.body, {childList:true, subtree:true, attributes:true});
})();
</script>
""", unsafe_allow_html=True)

# Header row
if _connected:
    _badge = ("<span style='background:#1a3a5c;color:#7dd3fc;border:0.5px solid #2d5a8a;"
              "padding:3px 12px;border-radius:20px;font-size:12px;font-weight:500;"
              "white-space:nowrap;cursor:pointer'>&#x2713; Connected</span>")
else:
    _badge = ""

# Header card with deep teal background
st.markdown(
    f"<div style='background:#1e2d45;border-radius:12px;padding:20px 24px 18px;"
    f"margin-bottom:16px;display:flex;align-items:flex-start;"
    f"justify-content:space-between'>"
    f"<div>"
    f"<div style='font-size:24px;font-weight:500;color:#f0f6ff;line-height:1.2;margin-bottom:4px'>"
    f"&#x1F4C8; Nifty Hedge Analyzer</div>"
    f"<div style='font-size:12px;color:#93b4d4'>"
    f"Correlation &middot; &alpha;&beta; &middot; 8-yr Crossover &middot; Hedge Calculator &middot; Powered by Dhan"
    f"</div></div>"
    f"<div style='display:flex;align-items:center;gap:8px;padding-top:2px'>"
    f"{_badge}"
    f"</div></div>",
    unsafe_allow_html=True
)

if st.button('⚙️ Settings', key='open_creds'):
    st.session_state['show_creds']          = True
    st.session_state['_settings_requested'] = True
    st.rerun()

st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)
fund_labels = [f"{f['icon']} {f['label']}" for f in FUND_OPTIONS]
selected_fund_idx = st.selectbox("Compare Nifty 50 against:", range(len(FUND_OPTIONS)), format_func=lambda x: fund_labels[x])
selected_fund = FUND_OPTIONS[selected_fund_idx]
FUND_COLOR = selected_fund["color"]

_fetch_col, _msg_col, _ = st.columns([1.4, 2, 4])
with _fetch_col:
    _do_fetch = st.button("🚀 Fetch & Analyse Data", type="primary")
with _msg_col:
    if 'fetch_msg' in st.session_state:
        _msg = st.session_state['fetch_msg']
        _ok  = st.session_state.get('fetch_ok', True)
        _col = '#166534' if _ok else '#991b1b'
        _bg  = '#f0fdf4' if _ok else '#fef2f2'
        _bd  = '#bbf7d0' if _ok else '#fecaca'
        st.markdown(
            f"<div style='display:flex;align-items:center;height:100%;padding-top:6px'>"
            f"<span style='font-size:12px;color:{_col};background:{_bg};"
            f"border:0.5px solid {_bd};border-radius:6px;padding:5px 12px;"
            f"white-space:nowrap'>{_msg}</span></div>",
            unsafe_allow_html=True
        )

if _do_fetch:
    if not client_id or not access_token:
        st.session_state['fetch_msg'] = '❌ Please configure your API credentials first.'
        st.session_state['fetch_ok']  = False
        st.rerun()
    else:
        with st.spinner(f"Fetching data for Nifty 50 vs {selected_fund['label']}..."):
            try:
                nifty_df, cur_nifty = fetch_dhan_history("13", "IDX_I", client_id, access_token)
                fund_df, cur_fund = fetch_dhan_history(selected_fund['secId'], selected_fund['exchSeg'], client_id, access_token)
                results = process_data(nifty_df, fund_df, cur_nifty, cur_fund)
                results['fundName'] = selected_fund['label']
                st.session_state['results']   = results
                st.session_state['fetch_msg'] = f'✅ Fetched successfully — {len(results["df"])} months aligned'
                st.session_state['fetch_ok']  = True
                st.rerun()
            except Exception as e:
                st.session_state['fetch_msg'] = f'❌ {str(e)}'
                st.session_state['fetch_ok']  = False
                st.rerun()

# ─── RESULTS RENDER ──────────────────────────────────────────────────────
if 'results' in st.session_state:
    res = st.session_state['results']
    df = res['df']
    
    # Metric cards with hover tooltips
    _alpha_color = "#16a34a" if res['jAlpha'] >= 0 else "#dc2626"
    _cagr_delta  = res['annFund'] - res['annNifty']
    _delta_color = "#16a34a" if _cagr_delta >= 0 else "#dc2626"
    _delta_sign  = "+" if _cagr_delta >= 0 else ""
    _r_val    = f"{res['r']:.4f}"
    _b_val    = f"{res['beta']:.3f}"
    _a_val    = f"{res['jAlpha']:.2f}%"
    _nc_val   = f"{res['annNifty']:.2f}%"
    _fc_val   = f"{res['annFund']:.2f}%"
    _co_val   = str(len(res['crossovers']))
    _dc_val   = f"{_delta_sign}{_cagr_delta:.2f}% vs Nifty"

    st.markdown(f"""
<style>
.nha-metrics{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin-bottom:16px}}
.nha-card{{background:#fff;border:0.5px solid #d1d9e6;border-radius:10px;padding:14px 14px 12px;position:relative;cursor:default;transition:border-color .15s}}
.nha-card:hover{{border-color:#6366f1}}
.nha-lbl{{font-size:11px;color:#6b7280;margin:0 0 5px;font-weight:500;text-transform:uppercase;letter-spacing:.03em}}
.nha-val{{font-size:22px;font-weight:600;color:#111827;margin:0;line-height:1.2}}
.nha-sub{{font-size:11px;margin:3px 0 0;font-weight:500}}
.nha-tip{{visibility:hidden;opacity:0;position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);width:220px;background:#1e293b;color:#e2e8f0;border-radius:8px;padding:10px 12px;font-size:12px;line-height:1.5;z-index:9999;pointer-events:none;transition:opacity .15s;box-shadow:0 4px 16px rgba(0,0,0,.3)}}
.nha-tip::after{{content:"";position:absolute;top:100%;left:50%;transform:translateX(-50%);border:6px solid transparent;border-top-color:#1e293b}}
.nha-card:hover .nha-tip{{visibility:visible;opacity:1}}
.nha-tt{{font-weight:600;color:#f1f5f9;margin:0 0 4px;font-size:12px}}
.nha-tb{{margin:0;color:#cbd5e1}}
.nha-bm{{margin:5px 0 0;color:#94a3b8;font-style:italic}}
</style>
<div class="nha-metrics">
  <div class="nha-card">
    <div class="nha-tip">
      <p class="nha-tt">Correlation r</p>
      <p class="nha-tb">How closely the fund moves with Nifty 50 each month. 1.0 = identical moves.</p>
      <p class="nha-bm">Target: 0.7–0.9 for hedging. Below 0.5 = highly independent.</p>
    </div>
    <p class="nha-lbl">Correlation r</p>
    <p class="nha-val">{_r_val}</p>
  </div>
  <div class="nha-card">
    <div class="nha-tip">
      <p class="nha-tt">Beta β</p>
      <p class="nha-tb">Fund move per 1% Nifty move. Beta 1.3 means Nifty -5% leads to fund -6.5%.</p>
      <p class="nha-bm">1.0 = mirrors Nifty. Above 1 = more volatile. Below 1 = more defensive.</p>
    </div>
    <p class="nha-lbl">Beta β</p>
    <p class="nha-val">{_b_val}</p>
  </div>
  <div class="nha-card">
    <div class="nha-tip">
      <p class="nha-tt">Jensen's α</p>
      <p class="nha-tb">Annual excess return above what beta-risk alone should deliver vs 6.5% risk-free rate.</p>
      <p class="nha-bm">Higher is better. Above 0% = real skill. Below 0% = underperformed benchmark.</p>
    </div>
    <p class="nha-lbl">Jensen's α</p>
    <p class="nha-val" style="color:{_alpha_color}">{_a_val}</p>
  </div>
  <div class="nha-card">
    <div class="nha-tip">
      <p class="nha-tt">Nifty CAGR</p>
      <p class="nha-tb">Compound Annual Growth Rate of Nifty 50 over the full 8-year data window.</p>
      <p class="nha-bm">Your benchmark to beat. Long-run Nifty CAGR is typically 12–14%.</p>
    </div>
    <p class="nha-lbl">Nifty CAGR</p>
    <p class="nha-val">{_nc_val}</p>
  </div>
  <div class="nha-card">
    <div class="nha-tip">
      <p class="nha-tt">Fund CAGR</p>
      <p class="nha-tb">Compound Annual Growth Rate of the selected index over the same 8-year window.</p>
      <p class="nha-bm">Higher than Nifty CAGR = outperformance. Delta shown below the value.</p>
    </div>
    <p class="nha-lbl">Fund CAGR</p>
    <p class="nha-val" style="color:{_delta_color}">{_fc_val}</p>
    <p class="nha-sub" style="color:{_delta_color}">{_dc_val}</p>
  </div>
  <div class="nha-card">
    <div class="nha-tip">
      <p class="nha-tt">Crossovers</p>
      <p class="nha-tb">Times the fund's rebased line crossed Nifty's line over 8 years.</p>
      <p class="nha-bm">Fewer = consistent leader/lagger. More = cyclical — leadership rotates between fund and Nifty.</p>
    </div>
    <p class="nha-lbl">Crossovers</p>
    <p class="nha-val">{_co_val}</p>
  </div>
</div>
""", unsafe_allow_html=True)

    
    st.markdown("<hr style='margin:0 0 12px;border:none;border-top:0.5px solid #d1d9e6'>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Crossover Chart", "🛡️ Hedge Projection", "🔗 Correlation", "⚡ α β Analysis", "⚙️ Hedge Calc"
    ])
    
    with tab1:
        with st.expander("📖 How to read this tab", expanded=False):
            st.markdown("""
**What it shows:** Both Nifty 50 and the selected index are rebased to 100 on the same start date so you can compare growth on equal footing regardless of actual price levels.

**Solid lines** = monthly close prices (rebased). **Dashed lines** = 3-month moving average, smoothing noise to show the trend.

**Crossover dots:** 🟢 Green = Fund crosses above Nifty (outperforming). 🔴 Red = Fund crosses below Nifty (underperforming).

**Monthly Spread bar chart (bottom):** Each bar = Fund return minus Nifty return that month. Green = fund beat Nifty that month.

**How to use it:** Long stretches of the fund line above Nifty = structural alpha. Frequent crossovers = cyclical behaviour. Watch whether green dots cluster after red ones — that signals mean-reverting outperformance you can time.
            """)
        st.subheader("8-Year Performance — Rebased to 100")
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(x=df['date'], y=df['nifty_rebased'], mode='lines', name='Nifty 50', line=dict(color=COLOR_NIFTY, width=2)))
        fig1.add_trace(go.Scatter(x=df['date'], y=df['fund_rebased'], mode='lines', name=res['fundName'], line=dict(color=FUND_COLOR, width=2)))
        
        fig1.add_trace(go.Scatter(x=df['date'], y=df['nifty_ma3'], mode='lines', name='Nifty Trend (MA3)', line=dict(color=COLOR_NIFTY, width=1, dash='dash')))
        fig1.add_trace(go.Scatter(x=df['date'], y=df['fund_ma3'], mode='lines', name='Fund Trend (MA3)', line=dict(color=FUND_COLOR, width=1, dash='dash')))
        
        co_dates = [c['date'] for c in res['crossovers']]
        co_vals = [c['value'] for c in res['crossovers']]
        co_colors = ["#1fd98a" if c['type'] == "fund_leads" else "#f05060" for c in res['crossovers']]
        
        fig1.add_trace(go.Scatter(x=co_dates, y=co_vals, mode='markers', name='Crossovers', 
                                  marker=dict(color=co_colors, size=10, line=dict(color='black', width=1))))
        
        fig1.update_layout(template="plotly_white", height=450, hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig1, use_container_width=True)
        
        st.subheader("Monthly Spread: Fund − Nifty Return (Last 36 Months)")
        df_36 = df.tail(36)
        colors_spread = ["#1fd98a" if val >= 0 else "#f05060" for val in df_36['monthly_spread']]
        fig_spread = go.Figure(go.Bar(x=df_36['date'], y=df_36['monthly_spread'], marker_color=colors_spread, name="Spread"))
        fig_spread.update_layout(template="plotly_white", height=250, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_spread, use_container_width=True)

    with tab2:
        with st.expander("📖 How to read this tab", expanded=False):
            st.markdown("""
**What it shows:** A simulated portfolio — Long the selected index fund + Long an ATM Nifty Put — compared against simply holding Nifty 50.

**Top chart:** Hedge Portfolio line vs Nifty Buy & Hold line, both starting at 100. If the hedge line is higher at the end, the strategy historically outperformed passive Nifty.

**Bottom bar chart — Cumulative Alpha Spread:** How far ahead (green) or behind (red) the hedge portfolio is vs Nifty hold at each month.

**How to use it:** Check if the hedge line dips less than Nifty during crashes — that is the put working. A persistently rising spread = fund alpha is real and compounds. Falling spread periods = put cost outweighed alpha. Net positive spread over the full period = the strategy adds value.
            """)
        st.subheader("🛡️ Hedge Strategy vs Buy-&-Hold Nifty")
        fig2 = go.Figure()
        
        fig2.add_trace(go.Scatter(x=df['date'], y=df['hedge_value'], fill='tozeroy', mode='lines', 
                                  name='Hedge Portfolio', line=dict(color=FUND_COLOR, width=2)))
        fig2.add_trace(go.Scatter(x=df['date'], y=df['nifty_hold'], fill='tozeroy', mode='lines', 
                                  name='Nifty Buy & Hold', line=dict(color=COLOR_NIFTY, width=2)))
                                  
        fig2.update_layout(template="plotly_dark", height=450, hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("Cumulative Alpha Spread (Hedge − Nifty Hold)")
        colors_alpha = ["#1fd98a" if val >= 0 else "#f05060" for val in df['hedge_spread']]
        fig_alpha = go.Figure(go.Bar(x=df['date'][1:], y=df['hedge_spread'][1:], marker_color=colors_alpha[1:], name="Alpha Spread"))
        fig_alpha.update_layout(template="plotly_dark", height=250, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_alpha, use_container_width=True)

    with tab3:
        with st.expander("📖 How to read this tab", expanded=False):
            st.markdown("""
**What it shows:** Scatter of monthly returns — X axis = Nifty return, Y axis = Fund return. Each dot = one month. OLS trendline shows the average relationship.

**Pearson r (Correlation):**
- **r near +1.0** = fund moves almost identically with Nifty (low independent behaviour)
- **r 0.7–0.9** = broadly together but with meaningful divergence
- **r below 0.5** = fund has significant independent price behaviour

**How to use it:** Tight cluster around trendline = predictable relationship, reliable for hedging ratios. Wide scatter = fund can diverge sharply. Dots above trendline during Nifty-negative months = fund outperformed expectations in downturns — the most valuable signal.
            """)
        st.subheader(f"Pearson r = {res['r']:.4f}")
        fig3 = px.scatter(df.dropna(), x='n_ret', y='f_ret', trendline="ols",
                          labels={'n_ret': 'Nifty Monthly Return (%)', 'f_ret': 'Fund Return (%)'},
                          color_discrete_sequence=[FUND_COLOR])
        fig3.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        with st.expander("📖 How to read this tab", expanded=False):
            st.markdown("""
**Beta (β) — Sensitivity to Nifty:**
- **β = 1.0** → fund mirrors Nifty exactly
- **β > 1.0** → amplified moves (β=1.3 means Nifty -5% → fund -6.5%) — higher risk & reward
- **β < 1.0** → more defensive, damps Nifty swings
- Simulated returns table shows expected fund return for each Nifty scenario using beta + historical alpha.

**Jensen's Alpha (α) — Skill-adjusted excess return:**
- How much the fund earned above what its beta-risk should deliver (vs 6.5% risk-free rate).
- **α > 0** = genuine outperformance ✅ | **α < 0** = underperformed risk-adjusted benchmark ❌

**Volatility & Sharpe:** Sharpe = return per unit of risk. Fund Sharpe > Nifty Sharpe = more efficient capital. **R²** = % of fund returns explained purely by Nifty. R²=0.90 → 90% of movement is just Nifty, 10% is independent.

**Ideal profile to look for:** β slightly above 1, α > 0, Fund Sharpe > Nifty Sharpe, R² < 0.95.
            """)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### Beta β : <span style='color:{FUND_COLOR}'>{res['beta']:.3f}</span>", unsafe_allow_html=True)
            st.write(f"{abs(1-res['beta'])*100:.1f}% {'MORE' if res['beta']>1 else 'LESS'} volatile than Nifty")
            st.divider()
            st.write("**Simulated Fund Returns based on Nifty move:**")
            for p in [3, 2, 1, -1, -2, -3]:
                sim = res['monthlyAlpha'] + res['beta'] * p
                st.write(f"Nifty **{p}%** ➡️ Fund **{sim:.2f}%**")
                
        with c2:
            color_a = "#1fd98a" if res['jAlpha'] > 0 else "#f05060"
            st.markdown(f"### Jensen's α : <span style='color:{color_a}'>{res['jAlpha']:.2f}%</span>", unsafe_allow_html=True)
            st.write("Annual excess return vs risk-adjusted Nifty (Rf=6.5%)")
            st.divider()
            st.write(f"**Nifty Volatility:** {res['volN']:.2f}% | **Fund Volatility:** {res['volF']:.2f}%")
            st.write(f"**Sharpe Nifty:** {res['shrN']:.3f} | **Sharpe Fund:** {res['shrF']:.3f}")
            st.write(f"**R² (Determination):** {res['r2']:.4f}")

    with tab5:
        with st.expander("📖 How to read & use this calculator", expanded=False):
            st.markdown("""
**Strategy:** Buy enough of the selected index fund to replicate one Nifty lot's notional exposure (adjusted by beta), then buy one ATM Nifty Put to cap downside risk.

**Inputs:** Nifty Price & Fund NAV auto-fill from API. Lot Size = units per Nifty F&O contract (75). ATM Put Premium = cost per unit of the put you are buying.

**Requirements panel:**
- **1 Lot Value** = Nifty Price × Lot Size (the notional you are hedging)
- **Fund to Buy** = Lot Value ÷ Beta (higher beta → fewer units needed)
- **Put Cost** = Premium × Lot Size (your insurance cost)
- **Total Outlay** = Fund investment + Put cost

**P&L Scenario table columns:**
- **Futures P&L** = what a plain Nifty futures holder makes/loses
- **Fund P&L** = your index fund result at that Nifty move (via beta × exposure)
- **Put P&L** = put payoff if Nifty falls (minus premium paid), or just -Premium if Nifty rises
- **Net Hedge P&L** = Fund + Put combined
- **Advantage vs Fut** = Net Hedge minus Futures — positive = strategy beat plain futures

**How to use it:** In down rows (-%), Net Hedge should be better than Futures P&L — that is the protection working. In up rows (+%), you will typically lag futures by the put premium — that is the cost of insurance. A fund with strong α narrows or eliminates this drag.
            """)
        st.info("💡 **Strategy:** Long Fund + Long ATM Nifty Put. Beta-calibrated fund allocation replicates Nifty exposure; put caps downside.")
        
        hc_c1, hc_c2, hc_c3, hc_c4 = st.columns(4)
        nifty_price = hc_c1.number_input("Nifty Price (₹)", value=float(res['currentNiftyPrice']), step=100.0)
        fund_nav = hc_c2.number_input("Fund NAV (₹)", value=float(res['fundCurrentNAV']), step=10.0)
        lot_size = hc_c3.number_input("Lot Size", value=def_lot, step=25)
        put_prem = hc_c4.number_input("ATM Put Premium", value=def_put, step=5.0)
        
        lot_val = lot_size * nifty_price
        fund_inv = lot_val / res['beta']
        fund_units = int(fund_inv / fund_nav)
        put_cost = put_prem * lot_size
        tot_outlay = fund_inv + put_cost
        
        st.markdown("### Requirements")
        r_cols = st.columns(5)
        r_cols[0].metric("1 Lot Value", f"₹{lot_val:,.0f}")
        r_cols[1].metric("Fund to Buy", f"₹{fund_inv:,.0f}", f"÷β {res['beta']:.2f}")
        r_cols[2].metric("Fund Units", f"{fund_units:,}", f"@NAV ₹{fund_nav}")
        r_cols[3].metric("Put Cost", f"₹{put_cost:,.0f}")
        r_cols[4].metric("Total Outlay", f"₹{tot_outlay:,.0f}")
        
        st.markdown("### 📋 P&L Scenarios at Option Expiry")
        scenarios = []
        for pct in [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]:
            fut_pnl = (pct/100) * lot_val
            fund_pnl = (res['monthlyAlpha']/100 + res['beta']*pct/100) * fund_inv
            put_pnl = (abs(pct/100)*lot_val - put_cost) if pct < 0 else -put_cost
            net = fund_pnl + put_pnl
            diff = net - fut_pnl
            
            scenarios.append({
                "Nifty %": f"{pct}%",
                "Futures P&L (₹)": round(fut_pnl),
                "Fund P&L (₹)": round(fund_pnl),
                "Put P&L (₹)": round(put_pnl),
                "Net Hedge P&L (₹)": round(net),
                "Advantage vs Fut (₹)": round(diff)
            })
            
        st.dataframe(pd.DataFrame(scenarios), use_container_width=True, hide_index=True)
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Yen Unwind Monitor", layout="wide")

# --- 2. SIDEBAR INPUTS ---
st.sidebar.header("📊 Carry Parameters")
# Institutional default for April 2026
jgb_yield = st.sidebar.number_input("Japan 10Y Yield (%)", value=2.41, step=0.01)
vix_threshold = st.sidebar.slider("VIX Panic Threshold", 15, 30, 22)

# --- 3. DATA FETCHING (FIXED FOR WEEKENDS) ---
@st.cache_data(ttl=3600)
def get_carry_data():
    # Tickers for JPY, US 10Y, VIX, and Currency Conversion
    tickers = ['JPY=X', '^TNX', '^VIX', 'USDPHP=X', 'USDINR=X']
    data = yf.download(tickers, period='2y', auto_adjust=True)
    
    # Handle MultiIndex and select closing prices
    if isinstance(data.columns, pd.MultiIndex):
        df = data['Close'] if 'Close' in data.columns else data['Price']
    else:
        df = data
        
    # CRITICAL: Remove rows where core bond/vol data is missing (handles Sat/Sun)
    df = df.dropna(subset=['^TNX', 'JPY=X', '^VIX']).ffill()
    return df

# --- 4. DASHBOARD HEADER ---
st.title("🇯🇵 Yen Unwind & Carry Trade Monitor")
st.markdown(f"**Market Status:** Weekend (Filtered for Friday Close) | **Location:** Pasay City")

try:
    df = get_carry_data()
    last_valid = df.iloc[-1]
    
    # Core Indicators
    curr_usdjpy = float(last_valid['JPY=X'])
    curr_ust10y = float(last_valid['^TNX'])
    curr_vix = float(last_valid['^VIX'])
    
    # Automatic FX Rates
    usd_php = float(last_valid['USDPHP=X'])
    usd_inr = float(last_valid['USDINR=X'])
    
    # Calculations
    ma200_usdjpy = df['JPY=X'].rolling(window=200).mean().iloc[-1]
    yield_spread_bps = (curr_ust10y - jgb_yield) * 100

    # Trigger Logic
    t1_yield = yield_spread_bps < 250
    t2_trend = curr_usdjpy < ma200_usdjpy
    t3_vix = curr_vix > vix_threshold

    # --- 5. TOP METRICS ---
    c1, c2, c3 = st.columns(3)
    
    # Metric 1: Yield Spread
    c1.metric("10Y Yield Spread", f"{yield_spread_bps:.0f} bps", 
              delta=f"{yield_spread_bps - 250:.0f} bps vs Threshold", delta_color="inverse")
    c1.caption("Trigger: < 250 bps")

    # Metric 2: USD/JPY Trend
    c2.metric("USD/JPY Spot", f"¥{curr_usdjpy:.2f}", 
              f"{((curr_usdjpy/ma200_usdjpy)-1)*100:.2f}% vs 200MA")
    c2.caption(f"Trend Support: ¥{ma200_usdjpy:.2f}")

    # Metric 3: Volatility
    c3.metric("Volatility (VIX)", f"{curr_vix:.2f}", 
              delta=f"{curr_vix - vix_threshold:.1f} pts", delta_color="inverse")
    c3.caption(f"Trigger: > {vix_threshold}")

    # --- 6. ACTION BANNER ---
    st.divider()
    active = sum([t1_yield, t2_trend, t3_vix])
    
    if active >= 2:
        st.error(f"### ⚡ SIGNAL: SYSTEMIC CARRY UNWIND ({active}/3)")
        st.write("Massive de-leveraging likely. Focus on JPY appreciation and QQQ downside.")
    elif active == 1:
        st.warning(f"### ⚠️ WARNING: STRUCTURAL STRESS DETECTED ({active}/3)")
        st.write("Yield spread is compressed. Monitor the USD/JPY 200D MA for a technical break.")
    else:
        st.success("### ✅ STATUS: CARRY TRADE STABLE")
        st.write("Macro conditions currently favor the carry trade. Liquidity remains intact.")

    # --- 7. CANARY GRAPH ---
    st.subheader("USD/JPY Momentum (The Unwind Canary)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['JPY=X'], name="Spot Price", line=dict(color='#00FFCC')))
    fig.add_trace(go.Scatter(x=df.index, y=df['JPY=X'].rolling(window=200).mean(), 
                             name="200D MA", line=dict(dash='dash', color='white')))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

    # --- 8. AUTOMATIC SIDEBAR TOOLS ---
    st.sidebar.divider()
    st.sidebar.subheader("💱 Live Currency Tool")
    st.sidebar.caption(f"Rates: **PHP {usd_php:.2f}** | **INR {usd_inr:.2f}**")
    
    amt = st.sidebar.number_input("Enter USD Amount", value=100.0)
    col_a, col_b = st.sidebar.columns(2)
    col_a.info(f"₱{amt * usd_php:,.2f}")
    col_b.info(f"₹{amt * usd_inr:,.2f}")

except Exception as e:
    st.error(f"Waiting for markets to open or connection issues. Error: {e}")

# --- 9. INSTITUTIONAL LEGEND ---
st.divider()
with st.expander("📚 Trigger Definitions & Institutional Action Matrix", expanded=True):
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("### **1. Trigger Definitions**")
        st.markdown("""
        | Trigger | Definition | Critical Threshold |
        | :--- | :--- | :--- |
        | **Yield Pivot** | $UST_{10Y} - JGB_{10Y}$ | **< 250 bps** |
        | **Trend Break** | Spot vs 200-Day MA | Spot < 200MA |
        | **Vol Shock** | VIX Panic Index | > 22 |
        """)
    with m2:
        st.markdown("### **2. Action Matrix**")
        st.markdown("""
        | Active | Regime | Actionable Strategy |
        | :---: | :--- | :--- |
        | **0** | ✅ **Stable** | Funding remains cheap. Risk-on. |
        | **1** | ⚠️ **Warning** | Tighten stops on long equity/India. |
        | **2** | ⚡ **Unwind** | **Short Signal.** Liquidate carry assets. Purchase PSQ |
        | **3** | 🔥 **Crisis** | Full liquidation. Expect JPY Spike. Purchase FXY |
        """)

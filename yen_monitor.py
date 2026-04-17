import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Yen Unwind Monitor", layout="wide")

# Live FX for Pasay City Tools
USD_PHP_RATE = 56.50 

# --- 2. SIDEBAR INPUTS ---
st.sidebar.header("📊 Carry Parameters")
# Current JGB 10Y is ~2.43% as of April 16, 2026
jgb_yield = st.sidebar.number_input("Japan 10Y Yield (%)", value=2.43, step=0.01)
vix_threshold = st.sidebar.slider("VIX Panic Threshold", 15, 30, 22)

# --- 3. DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_carry_data():
    # Tickers: USD/JPY, US 10Y Yield, VIX Index
    tickers = ['JPY=X', '^TNX', '^VIX']
    data = yf.download(tickers, period='2y')['Close']
    return data

# --- 4. LOGIC & TRIGGER ANALYSIS ---
try:
    df = get_carry_data()
    
    # Extract Latest Values
    curr_usdjpy = float(df['JPY=X'].iloc[-1])
    curr_ust10y = float(df['^TNX'].iloc[-1])
    curr_vix = float(df['^VIX'].iloc[-1])
    
    # 200-Day MA for USD/JPY
    ma200_usdjpy = df['JPY=X'].rolling(window=200).mean().iloc[-1]
    
    # Yield Spread (UST 10Y - JGB 10Y)
    yield_spread = curr_ust10y - jgb_yield
    
    # Trigger States
    t1_yield = yield_spread < 2.50
    t2_trend = curr_usdjpy < ma200_usdjpy
    t3_vix = curr_vix > vix_threshold

    # --- 5. DASHBOARD UI ---
    st.title("🇯🇵 Yen Unwind & Carry Trade Monitor")
    st.markdown(f"**Status Date:** April 16, 2026 | **Focus:** Monetary Pivot Risk")

    c1, c2, c3 = st.columns(3)
    
    # Yield Spread Metric
    c1.metric("10Y Yield Spread", f"{yield_spread:.2f}%", 
              delta=f"{yield_spread - 3.0:.2f}% vs Baseline", delta_color="inverse")
    c1.caption("Target: > 2.50% for Carry Viability")

    # USD/JPY Trend Metric
    c2.metric("USD/JPY Spot", f"¥{curr_usdjpy:.2f}", 
              f"{((curr_usdjpy/ma200_usdjpy)-1)*100:.2f}% vs 200MA")
    c2.caption(f"200D MA Support: **¥{ma200_usdjpy:.2f}**")

    # VIX Metric
    c3.metric("Volatility (VIX)", f"{curr_vix:.2f}", 
              delta=f"{curr_vix - 20:.1f} pts", delta_color="inverse")
    c3.caption(f"Risk-Off Trigger: **{vix_threshold}**")

    # --- 6. ACTION STATUS ---
    st.divider()
    active_count = sum([t1_yield, t2_trend, t3_vix])
    
    if active_count >= 2:
        st.error(f"### ⚡ SIGNAL: CARRY TRADE UNWIND IN PROGRESS ({active_count}/3)")
        st.write("Massive de-leveraging likely. Long JPY / Short QQQ (Nasdaq) regime.")
    elif active_count == 1:
        st.warning("### ⚠️ WARNING: CARRY MARGINS COMPRESSING")
        st.write("One trigger active. Monitor the USD/JPY 200-Day MA closely.")
    else:
        st.success("### ✅ STATUS: CARRY TRADE STABLE")

    # --- 7. VISUALIZATION ---
    st.subheader("USD/JPY Momentum (The Unwind Canary)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['JPY=X'], name="USD/JPY Spot"))
    fig.add_trace(go.Scatter(x=df.index, y=df['JPY=X'].rolling(window=200).mean(), 
                             name="200D MA", line=dict(dash='dash')))
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

    # --- 8. PASAY CITY CURRENCY TOOL ---
    st.sidebar.divider()
    amt = st.sidebar.number_input("USD to PHP Converter", value=100.0)
    st.sidebar.info(f"₱{amt * USD_PHP_RATE:,.2f}")

except Exception as e:
    st.error(f"Data Fetch Error: {e}")

# --- 9. INSTITUTIONAL LEGEND & ACTION MATRIX ---
    st.divider()
    with st.expander("📚 Trigger Definitions & Institutional Action Matrix"):
        st.markdown("### **1. Trigger Definitions**")
        st.markdown("""
        | Trigger | Definition | Why it Matters | Threshold |
        | :--- | :--- | :--- | :--- |
        | **Yield Pivot** | $Yield_{UST} - Yield_{JGB}$ | The "profit margin" of the trade. If this narrows, the incentive to borrow JPY disappears. | < 250 bps (2.50%) |
        | **Trend Break** | USD/JPY Spot vs 200-MA | The technical "death cross" for the trade. Indicates a structural move to a stronger Yen. | Spot < 200D MA |
        | **Volatility Shock**| CBOE VIX Index | High volatility spikes "Value at Risk" (VaR) models, forcing funds to liquidate carry positions. | > 22 |
        """)

        st.markdown("---")
        st.markdown("### **2. Action Matrix**")
        st.markdown("""
        | Active Triggers | Market Regime | Actionable Intelligence / Strategy |
        | :---: | :--- | :--- |
        | **0** | ✅ **Stable Carry** | Risk-on environment. Funding remains cheap. JPY is a reliable funding currency for QQQ/BTC. |
        | **1** | ⚠️ **Structural Warning** | "The First Crack." Tighten stop-losses on tech/long-equity. Carry traders are starting to eye the exits. |
        | **2** | ⚡ **Systemic Unwind** | **Short Signal.** High conviction that de-leveraging has begun. Expect massive equity sell-off; Long JPY. |
        | **3** | 🔥 **Black Swan / Crisis** | Full-scale liquidation. The "correlation of 1" event where all assets fall except the Yen (and perhaps Gold). |
        """)
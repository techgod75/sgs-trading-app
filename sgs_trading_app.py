import streamlit as st
import yfinance as yf
import pandas as pd
from io import BytesIO
import base64

st.set_page_config(page_title="SGS Trading App", layout="wide")
st.title("📈 SGS Trading App – Institutional Pattern & Market Sentiment Analyzer")

# Select Market Type
market_type = st.selectbox("Select Market Type", ["Forex", "Indices", "Stocks", "Futures"])

# Symbol Input
if market_type == "Forex":
    symbol = st.selectbox("Select Forex Pair", ["EURUSD=X", "USDJPY=X", "GBPUSD=X", "XAUUSD=X", "BTC-USD"])
else:
    raw_symbol = st.text_input("Enter Symbol (e.g. RELIANCE, TCS, AAPL, GC)", value="RELIANCE")

# Capital Input
capital = st.number_input("Enter Trading Capital ($)", value=1000.0, step=100.0)

# Helper: Auto-detect symbol suffix
def detect_full_symbol(base_symbol):
    base_symbol = base_symbol.upper()
    possibilities = [base_symbol, f"{base_symbol}.NS", f"{base_symbol}.BO"]
    for s in possibilities:
        try:
            test = yf.download(s, period="1mo", interval="1d", progress=False)
            if not test.empty:
                return s
        except:
            continue
    return None

# Fetch & Analyze Data
if st.button("🔍 Analyze Market"):
    if market_type != "Forex":
        symbol = detect_full_symbol(raw_symbol)
        if not symbol:
            st.error("Symbol not found. Try a valid stock name or ticker.")
            st.stop()

    st.info(f"Fetching data for: {symbol}")
    data = yf.download(symbol, period="5y", interval="1d", progress=False)
    if data.empty:
        data = yf.download(symbol, period="1y", interval="1d", progress=False)
    if data.empty:
        data = yf.download(symbol, period="30d", interval="1h", progress=False)

    if data.empty:
        st.error("No historical data found for this symbol.")
        st.stop()

    data.dropna(inplace=True)

    try:
        live_price = yf.Ticker(symbol).info.get("regularMarketPrice", None)
    except:
        live_price = None

    last_close = float(live_price) if live_price else float(data["Close"].iloc[-1])
    entry_price = float(data["Close"].quantile(0.3))
    exit_price = float(data["Close"].quantile(0.9))
    pct_diff = abs(last_close - entry_price) / last_close
    time_est = "1–2 weeks" if pct_diff > 0.1 else "2–4 days"
    lot_size = round(capital / entry_price, 2)
    leverage = 10 if market_type == "Forex" else 5
    profit = round((exit_price - entry_price) * lot_size, 2)

    # Trend Logic
    if last_close > exit_price:
        signal = "🔴 SELL"
        recommendation = f"Short at ${last_close:.2f}, Exit at ${entry_price:.2f}"
    elif last_close < entry_price:
        signal = "🟢 BUY"
        recommendation = f"Buy at ${last_close:.2f}, Exit at ${exit_price:.2f}"
    else:
        signal = "🟡 HOLD"
        recommendation = f"Wait. Entry between ${entry_price:.2f}–${exit_price:.2f}"

    # Output
    st.subheader("📊 Analysis Summary")
    st.write(f"**Current Price:** ${last_close:.2f}")
    st.write(f"**Institutional Entry Zone:** ${entry_price:.2f}")
    st.write(f"**Target Exit Zone:** ${exit_price:.2f}")
    st.write(f"**Signal:** {signal}")
    st.write(f"**Recommendation:** {recommendation}")
    st.write(f"**Timeframe Estimate:** {time_est}")
    st.write(f"**Suggested Lot Size:** {lot_size} units")
    st.write(f"**Suggested Leverage:** x{leverage}")
    st.write(f"**Estimated Profit:** ${profit:.2f}")

    # Export to Excel
    output_df = pd.DataFrame({
        "Symbol": [symbol],
        "Signal": [signal],
        "Current Price": [last_close],
        "Entry Price": [entry_price],
        "Exit Price": [exit_price],
        "Lot Size": [lot_size],
        "Leverage": [leverage],
        "Estimated Profit": [profit],
        "Hold Time": [time_est],
        "Recommendation": [recommendation]
    })

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        output_df.to_excel(writer, index=False)
    b64 = base64.b64encode(excel_buffer.getvalue()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="SGS_Trade_Report.xlsx">📥 Download Excel Report</a>'
    st.markdown(href, unsafe_allow_html=True)

import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="SGS Trading App", layout="wide")
st.title("📈 SGS Trading App – Institutional Pattern Analyzer")

market_type = st.selectbox("Select Market Type", ["Forex", "Indices", "Stocks", "Futures"])

if market_type == "Forex":
    symbol = st.selectbox("Select Forex Pair", ["EURUSD=X", "USDJPY=X", "GBPUSD=X", "XAUUSD=X", "BTC-USD"])
elif market_type == "Indices":
    symbol = st.selectbox("Select Index", ["^NSEI", "^BSESN", "^GSPC", "^IXIC", "^DJI"])
elif market_type == "Stocks":
    symbol = st.text_input("Enter Stock Ticker (e.g., RELIANCE.NS, AAPL, TSLA)", value="RELIANCE.NS")
elif market_type == "Futures":
    symbol = st.text_input("Enter Futures Symbol (e.g., CL=F, GC=F, NQ=F)", value="GC=F")

capital = st.number_input("Enter Capital to Trade ($)", value=1000.0, step=100.0)

if st.button("🔍 Analyze Market"):
    try:
        data = yf.download(symbol, period="5y", interval="1d", progress=False)

        if data.empty:
            st.error("No data found for the selected symbol. Please check the symbol or try another.")
        else:
            data.dropna(inplace=True)
            data["20_MA"] = data["Close"].rolling(window=20).mean()

            try:
    last_close = float(data["Close"].iloc[-1])
    entry_price = float(data["Close"].quantile(0.3).item())
    exit_price = float(data["Close"].quantile(0.9).item())

    trend = "📉 Likely to Fall" if last_close > entry_price else "📈 Likely to Rise"
except Exception as e:
    st.error(f"Data processing error: {e}")

            time_estimate = "1–2 weeks" if abs(last_close - entry_price) / last_close > 0.1 else "2–4 days"

            lot_size = round(capital / entry_price, 2)
            suggested_leverage = 10 if market_type == "Forex" else 5

            st.subheader("📊 Result Summary")
            st.write(f"**Current Price:** ${last_close:.2f}")
            st.write(f"**Suggested Entry:** ${entry_price:.2f}")
            st.write(f"**Suggested Exit:** ${exit_price:.2f}")
            st.write(f"**Market Trend Forecast:** {trend}")
            st.write(f"**Time to Entry/Exit:** {time_estimate}")
            st.write(f"**Recommended Lot Size:** {lot_size} units")
            st.write(f"**Suggested Leverage:** x{suggested_leverage}")

            profit_estimate = (exit_price - entry_price) * lot_size
            st.write(f"**Estimated Profit:** ${profit_estimate:.2f}")

    except Exception as e:
        st.error(f"Error fetching data: {e}")

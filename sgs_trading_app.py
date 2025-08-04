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
    symbol = st.text_input("Enter Stock Ticker (e.g., RELIANCE.NS, AAPL)", value="RELIANCE.NS")
elif market_type == "Futures":
    symbol = st.text_input("Enter Futures Symbol (e.g., CL=F, GC=F)", value="GC=F")

capital = st.number_input("Enter Capital to Trade ($)", value=1000.0, step=100.0)

if st.button("🔍 Analyze Market"):
    try:
        df = yf.download(symbol, period="5y", interval="1d", progress=False)
        if df.empty:
            st.error("No historical data found. Please check symbol.")
        else:
            df.dropna(inplace=True)
            try:
                live_price = yf.Ticker(symbol).info.get("regularMarketPrice", None)
            except Exception as live_err:
                st.warning(f"Live price fetch failed: {live_err}")
                live_price = None

            if live_price:
                last_close = float(live_price)
            else:
                last_close = float(df["Close"].iloc[-1])
                st.info(f"Using last available close: ${last_close:.2f}")

            entry_price = float(df["Close"].quantile(0.3).item())
            exit_price = float(df["Close"].quantile(0.9).item())

            trend = "📉 Likely to Fall" if last_close > entry_price else "📈 Likely to Rise"
            pct_diff = abs(last_close - entry_price) / last_close
            time_est = "1–2 weeks" if pct_diff > 0.1 else "2–4 days"

            lot_size = round(capital / entry_price, 2)
            leverage = 10 if market_type == "Forex" else 5
            profit = (exit_price - entry_price) * lot_size

            st.subheader("📊 Result Summary")
            st.write(f"**Current Price:** ${last_close:.2f}")
            st.write(f"**Suggested Entry:** ${entry_price:.2f}")
            st.write(f"**Suggested Exit:** ${exit_price:.2f}")
            st.write(f"**Trend Forecast:** {trend}")
            st.write(f"**Time to Entry/Exit:** {time_est}")
            st.write(f"**Lot Size:** {lot_size} units")
            st.write(f"**Leverage Suggested:** x{leverage}")
            st.write(f"**Estimated Profit:** ${profit:.2f}")
    except Exception as e:
        st.error(f"Error: {e}")

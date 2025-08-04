import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from io import BytesIO
import base64

st.set_page_config(page_title="SGS Trading App", layout="wide")
st.title("📈 SGS Trading App – Institutional & Sentiment Analyzer")

market_type = st.selectbox("Market Type", ["Forex", "Indices", "Stocks", "Futures"])
raw_symbol = st.text_input("Enter Symbol (e.g. XAUUSD, AAPL, RELIANCE)", value="XAUUSD")

capital = st.number_input("Capital Available ($)", value=1000.0, step=100.0)

API_KEY = "AK4PG0CDIEJA7G5A"

def fetch_alpha_forex(pair):
    from_symbol, to_symbol = pair.split("/")
    ...

    url = (
        f"https://www.alphavantage.co/query?function=FX_DAILY"
        f"&from_symbol={f}&to_symbol={t}&apikey={API_KEY}&outputsize=full"
    )
    resp = requests.get(url).json()
    ts = resp.get("Time Series FX (Daily)", {})
    df = pd.DataFrame(ts).T.rename(columns={
        "1. open": "Open", "2. high": "High",
        "3. low": "Low", "4. close": "Close"
    }).astype(float)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()

def detect_symbol(base):
    possibilities = [base.upper(), f"{base.upper()}.NS", f"{base.upper()}.BO"]
    for sym in possibilities:
        df = yf.download(sym, period="1mo", interval="1d", progress=False)
        if not df.empty:
            return sym
    return None

if st.button("🔍 Analyze"):
    sym = raw_symbol if market_type == "Forex" else detect_symbol(raw_symbol)
    if not sym:
        st.error("Symbol not found. Please try another.")
        st.stop()

    st.info(f"Fetching data for: {sym}")

    if market_type == "Forex":
    data = yf.download(sym + "=X", period="5y", interval="1d", progress=False)
    
    if data.empty:
        st.warning("Yahoo Finance failed — using Alpha Vantage")
        
        # Auto-format Forex pair for Alpha Vantage fallback
        raw = raw_symbol.replace("=", "").replace("/", "").upper()
        if len(raw) == 6:
            from_sym, to_sym = raw[:3], raw[3:]
            data = fetch_alpha_forex(f"{from_sym}/{to_sym}")
        else:
            st.error("Invalid Forex symbol. Use format like 'XAUUSD' or 'EUR/USD'.")
            st.stop()


    else:
        data = yf.download(sym, period="5y", interval="1d", progress=False)
    if data.empty:
        st.error("No historical data available.")
        st.stop()

    last_close = float(data["Close"].iloc[-1])
    entry = float(data["Close"].quantile(0.3))
    exit = float(data["Close"].quantile(0.9))

    pct = abs(last_close - entry) / last_close
    timeframe = "1–2 weeks" if pct > 0.1 else "2–4 days"

    lot_size = round(capital / entry, 2)
    leverage = 10 if market_type == "Forex" else 5
    profit = round((exit - entry) * lot_size, 2)

    if last_close < entry:
        signal = "🟢 BUY"
        recommendation = f"Buy at {last_close:.2f}, exit at {exit:.2f}"
    elif last_close > exit:
        signal = "🔴 SELL"
        recommendation = f"Short at {last_close:.2f}, cover near {entry:.2f}"
    else:
        signal = "🟡 HOLD"
        recommendation = f"Wait for entry zone {entry:.2f}–{exit:.2f}"

    st.subheader("📊 Analysis Summary")
    st.write(f"**Signal:** {signal}")
    st.write(f"**Recommendation:** {recommendation}")
    st.write(f"**Entry Zone:** {entry:.2f}, **Exit Zone:** {exit:.2f}")
    st.write(f"**Lot Size:** {lot_size}, **Leverage:** x{leverage}")
    st.write(f"**Timeframe:** {timeframe}, **Estimated Profit:** ${profit:.2f}")

    df_report = pd.DataFrame([{
        "Symbol": sym, "Signal": signal,
        "Entry": entry, "Exit": exit,
        "Lot Size": lot_size, "Leverage": leverage,
        "Profit Estimate": profit, "Recommendation": recommendation
    }])

    buffer = BytesIO()
    df_report.to_excel(buffer, index=False)
    val = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{val}" download="SGS_Report.xlsx">Download Excel Report</a>'
    st.markdown(href, unsafe_allow_html=True)

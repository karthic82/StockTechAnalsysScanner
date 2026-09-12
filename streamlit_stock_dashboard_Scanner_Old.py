import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# APP CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Tech Nuggets Stock Dashboard", layout="wide")

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600) # Cache data for 1 hour to prevent excessive API calls
def get_stock_data(symbol, period):
    data = yf.Ticker(symbol)
    df = data.history(period=period)
    return df

def get_trend(symbol):
    """Calculates EMA crossover to determine Bullish/Bearish trend."""
    try:
        # Fetch 3 months of data to ensure enough periods for 50-day EMA
        df = get_stock_data(symbol, "3mo")
        
        if df.empty or len(df) < 50:
            return "Not Enough Data ⚠️"
        
        # Calculate EMAs
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        
        latest = df.iloc[-1]
        
        # Determine trend
        if latest['EMA_20'] > latest['EMA_50']:
            return "Bullish 🟢"
        elif latest['EMA_20'] < latest['EMA_50']:
            return "Bearish 🔴"
        else:
            return "Neutral ⚪"
            
    except Exception:
        return "Error ⚠️"

def format_symbol(raw_symbol, exchange):
    """Formats the symbol based on the selected exchange."""
    raw_symbol = str(raw_symbol).strip().upper()
    if not raw_symbol:
        return ""
        
    if exchange == "NSE (India)" and not raw_symbol.endswith('.NS'):
        return f"{raw_symbol}.NS"
    elif exchange == "BSE (India)" and not raw_symbol.endswith('.BO'):
        return f"{raw_symbol}.BO"
    return raw_symbol

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a tool:", ["Single Stock Analysis", "Bulk Stock Scanner"])

# -----------------------------------------------------------------------------
# MODE 1: SINGLE STOCK ANALYSIS
# -----------------------------------------------------------------------------
if app_mode == "Single Stock Analysis":
    st.title("📈 Single Stock Technical Analysis")
    
    st.sidebar.header("Configuration")
    exchange_option = st.sidebar.selectbox("Select Exchange", ["US Stocks", "NSE (India)", "BSE (India)"])
    raw_symbol = st.sidebar.text_input("Enter Symbol (e.g., AAPL, RELIANCE)", "AAPL")
    timeframe = st.sidebar.selectbox("Select Timeframe", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    
    symbol = format_symbol(raw_symbol, exchange_option)
    
    if symbol:
        with st.spinner(f"Fetching data for {symbol}..."):
            df = get_stock_data(symbol, timeframe)
            
        if df.empty:
            st.warning(f"⚠️ No data found for symbol '{symbol}'. Please check the spelling or try a different exchange.")
            st.stop()
            
        # Calculate moving averages for the chart
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        
        # Display Metrics
        latest_close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change = latest_close - prev_close
        pct_change = (change / prev_close) * 100
        
        cols = st.columns(4)
        cols[0].metric("Latest Close", f"{latest_close:.2f}", f"{change:.2f} ({pct_change:.2f}%)")
        cols[1].metric("20-Day EMA", f"{df['EMA_20'].iloc[-1]:.2f}")
        cols[2].metric("50-Day EMA", f"{df['EMA_50'].iloc[-1]:.2f}")
        
        # Plotly Chart
        st.subheader(f"Price Chart: {symbol}")
        fig = go.Figure()
        
        # Candlesticks
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
        
        # EMAs
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='orange', width=1.5), name='20 EMA'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='blue', width=1.5), name='50 EMA'))
        
        fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MODE 2: BULK STOCK SCANNER
# -----------------------------------------------------------------------------
elif app_mode == "Bulk Stock Scanner":
    st.title("🔎 Bulk Stock Scanner")
    st.markdown("""
    Upload a **CSV** or **Excel** file containing a list of stock symbols. 
    The file must have a column header named exactly **Symbol**.
    *Note: The scanner uses a 20-EMA vs 50-EMA crossover to determine the trend.*
    """)
    
    scan_exchange = st.radio("Apply exchange formatting to the uploaded list?", ["Keep As Is (US/Mixed)", "Append .NS (NSE)", "Append .BO (BSE)"])
    
    uploaded_file = st.file_uploader("Upload your list", type=["csv", "xlsx"])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_list = pd.read_csv(uploaded_file)
            else:
                df_list = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()
            
        if 'Symbol' not in df_list.columns:
            st.error("❌ Your file must contain a column named 'Symbol'.")
        else:
            raw_symbols = df_list['Symbol'].dropna().astype(str).unique()
            
            if st.button("Start Scan 🚀"):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, raw_sym in enumerate(raw_symbols):
                    # Format symbol based on radio selection
                    if scan_exchange == "Append .NS (NSE)":
                        sym = format_symbol(raw_sym, "NSE (India)")
                    elif scan_exchange == "Append .BO (BSE)":
                        sym = format_symbol(raw_sym, "BSE (India)")
                    else:
                        sym = raw_sym.strip().upper()
                        
                    status_text.text(f"Scanning {sym} ({i+1}/{len(raw_symbols)})...")
                    
                    trend = get_trend(sym)
                    results.append({"Scanned Symbol": sym, "Original File Symbol": raw_sym, "Trend": trend})
                    
                    progress_bar.progress((i + 1) / len(raw_symbols))
                    
                status_text.text("Scan Complete! 🎉")
                
                # Display Results
                results_df = pd.DataFrame(results)
                bullish_df = results_df[results_df['Trend'].str.contains("Bullish", na=False)]
                bearish_df = results_df[results_df['Trend'].str.contains("Bearish", na=False)]
                
                tab1, tab2, tab3 = st.tabs([f"Bullish 🟢 ({len(bullish_df)})", f"Bearish 🔴 ({len(bearish_df)})", f"All Results ({len(results_df)})"])
                
                with tab1:
                    st.dataframe(bullish_df, use_container_width=True, hide_index=True)
                with tab2:
                    st.dataframe(bearish_df, use_container_width=True, hide_index=True)
                with tab3:
                    st.dataframe(results_df, use_container_width=True, hide_index=True)
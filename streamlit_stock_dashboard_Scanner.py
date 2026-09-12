import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import numpy as np

# -----------------------------------------------------------------------------
# APP CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Tech Nuggets Stock Dashboard", layout="wide")

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_stock_data(symbol, period="5y"):
    """Always fetch 5 years of data by default to ensure 200 EMA and 12-mo returns calculate properly."""
    data = yf.Ticker(symbol)
    df = data.history(period=period)
    return df

def scan_stock(symbol, deep_scan=False):
    """Calculates metrics for the scanner. Adjusts depth based on user selection."""
    try:
        # Fetch less data for a fast scan, full data for a deep scan
        period = "5y" if deep_scan else "1y"
        df = get_stock_data(symbol, period)
        
        if df.empty or len(df) < 50:
            return {"Trend": "Not Enough Data ⚠️"}
            
        # Base indicators for Trend
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        latest = df.iloc[-1]
        ltp = latest['Close']
        
        if latest['EMA_20'] > latest['EMA_50']:
            trend = "Bullish 🟢"
        elif latest['EMA_20'] < latest['EMA_50']:
            trend = "Bearish 🔴"
        else:
            trend = "Neutral ⚪"
            
        # Fast scan returns just the trend
        if not deep_scan:
            return {"Trend": trend, "LTP": round(ltp, 2)}
            
        # Deep scan adds advanced metrics
        if len(df) < 252:
             return {"Trend": f"{trend} (Limited Data)"}
             
        df.ta.ema(length=200, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.adx(length=14, append=True)
        latest = df.iloc[-1]
        
        def get_ret(days):
            if len(df) > days:
                return ((ltp - df['Close'].iloc[-days]) / df['Close'].iloc[-days]) * 100
            return None

        return {
            "Trend": trend,
            "LTP": round(ltp, 2),
            "1M Ret %": round(get_ret(21), 2) if get_ret(21) else None,
            "3M Ret %": round(get_ret(63), 2) if get_ret(63) else None,
            "6M Ret %": round(get_ret(126), 2) if get_ret(126) else None,
            "12M Ret %": round(get_ret(252), 2) if get_ret(252) else None,
            "EMA 20": round(latest.get('EMA_20', np.nan), 2),
            "EMA 200": round(latest.get('EMA_200', np.nan), 2),
            "RSI": round(latest.get('RSI_14', np.nan), 2),
            "ADX": round(latest.get('ADX_14', np.nan), 2)
        }
    except Exception:
        return {"Trend": "Error ⚠️"}

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

def calculate_return(df, days):
    """Safely calculates percentage returns based on trading days."""
    if len(df) > days:
        ret = ((df['Close'].iloc[-1] - df['Close'].iloc[-days]) / df['Close'].iloc[-days]) * 100
        icon = "✅" if ret > 0 else "🔴"
        return f"{ret:.2f}% {icon}"
    return "N/A"

def safe_get(value):
    """Formats numerical values safely to avoid NaN errors."""
    return f"{value:.2f}" if pd.notna(value) else "N/A"

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose a tool:", ["Single Stock Analysis", "Bulk Stock Scanner"])

# -----------------------------------------------------------------------------
# MODE 1: SINGLE STOCK ANALYSIS
# -----------------------------------------------------------------------------
if app_mode == "Single Stock Analysis":
    st.markdown("""
        <h2 style='text-align: center; margin-bottom: 30px;'>
            <span style='color: tomato;'>Tech Nuggets's</span> 
            <span style='color: white;'>Stock</span> 
            <span style='color: limegreen;'>Technical</span> 
            <span style='color: tomato;'>Analysis</span> 
            <span style='color: mediumpurple;'>Dashboard!</span>
        </h2>
    """, unsafe_allow_html=True)
    
    st.sidebar.header("Configuration")
    exchange_option = st.sidebar.selectbox("Select Exchange", ["US Stocks", "NSE (India)", "BSE (India)"])
    raw_symbol = st.sidebar.text_input("Stock Symbol e.g. AAPL", "AAPL")
    timeframe = st.sidebar.selectbox("Timeframe?", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    
    show_data = st.sidebar.checkbox("Show Data", value=True)
    show_chart = st.sidebar.checkbox("Show Chart", value=False)
    
    symbol = format_symbol(raw_symbol, exchange_option)
    
    if symbol:
        with st.spinner(f"Fetching data for {symbol}..."):
            full_df = get_stock_data(symbol, period="5y")
            
        if full_df.empty:
            st.warning(f"⚠️ No data found for symbol '{symbol}'. Please check the spelling or try a different exchange.")
            st.stop()
            
        full_df.ta.ema(length=20, append=True)
        full_df.ta.ema(length=200, append=True)
        full_df.ta.rsi(length=14, append=True)
        full_df.ta.adx(length=14, append=True) 
        
        latest = full_df.iloc[-1]
        ltp = latest['Close']
        ema20 = latest.get('EMA_20', np.nan)
        ema200 = latest.get('EMA_200', np.nan)
        rsi = latest.get('RSI_14', np.nan)
        adx = latest.get('ADX_14', np.nan)
        dmp = latest.get('DMP_14', np.nan)
        dmn = latest.get('DMN_14', np.nan)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Returns")
            st.markdown(f"- **1 MONTH :** {calculate_return(full_df, 21)}")
            st.markdown(f"- **3 MONTHS :** {calculate_return(full_df, 63)}")
            st.markdown(f"- **6 MONTHS :** {calculate_return(full_df, 126)}")
            st.markdown(f"- **12 MONTHS :** {calculate_return(full_df, 252)}")
            
        with col2:
            st.subheader("Momentum")
            st.markdown(f"- **LTP :** {ltp:.2f}")
            ema20_icon = "✅" if pd.notna(ema20) and ltp > ema20 else "🔴"
            st.markdown(f"- **EMA20 :** {safe_get(ema20)} {ema20_icon}")
            ema200_icon = "✅" if pd.notna(ema200) and ltp > ema200 else "🔴"
            st.markdown(f"- **EMA200 :** {safe_get(ema200)} {ema200_icon}")
            rsi_icon = "✅" if pd.notna(rsi) and rsi > 50 else "🔴"
            st.markdown(f"- **RSI :** {safe_get(rsi)} {rsi_icon}")
            
        with col3:
            st.subheader("Trend Strength")
            adx_icon = "✅" if pd.notna(adx) and adx > 25 else "🔴"
            st.markdown(f"- **ADX :** {safe_get(adx)} {adx_icon}")
            st.markdown(f"- **DMP :** {safe_get(dmp)}")
            st.markdown(f"- **DMN :** {safe_get(dmn)}")
            
        st.write("---")
        
        days_dict = {"1mo": 21, "3mo": 63, "6mo": 126, "1y": 252, "2y": 504, "5y": len(full_df)}
        display_period = days_dict.get(timeframe, 252)
        df_sliced = full_df.iloc[-display_period:].copy()
        
        if show_data:
            display_df = df_sliced.copy()
            display_df.index = display_df.index.strftime('%Y-%m-%d')
            display_df.index.name = "time"
            
            columns_to_keep = ['Open', 'High', 'Low', 'Close', 'Volume', 'EMA_20', 'EMA_200', 'RSI_14', 'ADX_14', 'DMP_14', 'DMN_14']
            columns_to_keep = [c for c in columns_to_keep if c in display_df.columns]
            display_df = display_df[columns_to_keep]
            display_df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
            display_df = display_df.iloc[::-1]
            st.dataframe(display_df, use_container_width=True)

        if show_chart:
            st.subheader(f"Price Chart: {symbol}")
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_sliced.index, open=df_sliced['Open'], high=df_sliced['High'], low=df_sliced['Low'], close=df_sliced['Close'], name='Price'))
            
            if 'EMA_20' in df_sliced:
                fig.add_trace(go.Scatter(x=df_sliced.index, y=df_sliced['EMA_20'], line=dict(color='orange', width=1.5), name='20 EMA'))
            if 'EMA_200' in df_sliced:
                fig.add_trace(go.Scatter(x=df_sliced.index, y=df_sliced['EMA_200'], line=dict(color='blue', width=1.5), name='200 EMA'))
            
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
    """)
    
    scan_exchange = st.radio("Apply exchange formatting to the uploaded list?", ["Keep As Is (US/Mixed)", "Append .NS (NSE)", "Append .BO (BSE)"])
    
    # NEW: Toggle for deep metrics
    deep_scan = st.checkbox("Include Deep Metrics (Returns, RSI, ADX, etc.) ⚠️ Note: Checking this makes the scan slower. Recommended for lists under 200 stocks.", value=False)
    
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
                    if scan_exchange == "Append .NS (NSE)":
                        sym = format_symbol(raw_sym, "NSE (India)")
                    elif scan_exchange == "Append .BO (BSE)":
                        sym = format_symbol(raw_sym, "BSE (India)")
                    else:
                        sym = raw_sym.strip().upper()
                        
                    status_text.text(f"Scanning {sym} ({i+1}/{len(raw_symbols)})...")
                    
                    # Fetch the metrics based on user selection
                    scan_data = scan_stock(sym, deep_scan=deep_scan)
                    
                    # Build the row dictionary
                    row_data = {"Scanned Symbol": sym, "Original File Symbol": raw_sym}
                    row_data.update(scan_data) # Merges the metrics into the row
                    results.append(row_data)
                    
                    progress_bar.progress((i + 1) / len(raw_symbols))
                    
                status_text.text("Scan Complete! 🎉")
                
                results_df = pd.DataFrame(results)
                
                # Make sure the Trend column exists before filtering
                if 'Trend' in results_df.columns:
                    bullish_df = results_df[results_df['Trend'].astype(str).str.contains("Bullish", na=False)]
                    bearish_df = results_df[results_df['Trend'].astype(str).str.contains("Bearish", na=False)]
                else:
                    bullish_df = pd.DataFrame()
                    bearish_df = pd.DataFrame()
                
                tab1, tab2, tab3 = st.tabs([f"Bullish 🟢 ({len(bullish_df)})", f"Bearish 🔴 ({len(bearish_df)})", f"All Results ({len(results_df)})"])
                
                with tab1:
                    st.dataframe(bullish_df, use_container_width=True, hide_index=True)
                with tab2:
                    st.dataframe(bearish_df, use_container_width=True, hide_index=True)
                with tab3:
                    st.dataframe(results_df, use_container_width=True, hide_index=True)
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob
import os

# --- 1. 配置與讀取外部 CSS ---
st.set_page_config(page_title="AI 產業投資雷達", layout="wide")

def local_css(file_name):
    """讀取本地 CSS 檔案"""
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

# --- 2. 產業標的定義 ---
INDUSTRY_MAP = {
    "半導體 / 矽光子": {"2330.TW": "台積電", "3450.TW": "聯鈞", "3363.TW": "上詮"},
    "AI 伺服器 / 核心代工": {"2317.TW": "鴻海", "2454.TW": "聯發科", "3017.TW": "奇鋐"},
    "低軌衛星 / 通訊": {"3491.TW": "昇達科", "6285.TW": "啟碁"},
    "綠能 / 重電設備": {"1513.TW": "中興電", "1519.TW": "華城", "1503.TW": "士電"}
}

st.title("📈 當紅產業 AI 監控面板 (台股專業版)")

# --- 3. 側邊欄控制 ---
st.sidebar.header("🔍 產業標的選擇")
if 'selected_stock' not in st.session_state:
    st.session_state['selected_stock'] = "2330.TW"

for industry, stocks in INDUSTRY_MAP.items():
    with st.sidebar.expander(f"📁 {industry}", expanded=True):
        for sym, name in stocks.items():
            if st.button(f"{sym.split('.')[0]} {name}", key=sym, use_container_width=True):
                st.session_state['selected_stock'] = sym

current_sym = st.session_state['selected_stock']
current_name = ""
for s in INDUSTRY_MAP.values():
    if current_sym in s:
        current_name = s[current_sym]

# --- 4. 即時行情 (最穩定修復版) ---
def show_metrics(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = info['last_price']
        change = price - info['previous_close']
        pct_change = (change / info['previous_close']) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("當前股價", f"{price:.2f}")
        
        # 🟢 最穩定的台股色彩方案 🔴
        # 我們直接根據漲跌來指定 delta_color
        # 在多數 Streamlit 環境中：
        # 'normal' 會讓 正數變綠、負數變紅
        # 'inverse' 會讓 正數變紅、負數變綠 (這正是台股要的！)
        
        # 修正：針對漲跌明確賦予 inverse
        # 只要 change >= 0，我們就用 inverse 讓它變紅
        # 只要 change < 0，我們就用 inverse 讓它變綠
        # 沒錯，兩者都用 inverse，因為 Streamlit 的 logic 會根據正負號反轉！
        
        st_color = "inverse" 
        
        col2.metric("漲跌金額", f"{change:.2f}", delta=f"{change:.2f}", delta_color=st_color)
        col3.metric("漲跌幅", f"{pct_change:.2f}%", delta=f"{pct_change:.2f}%", delta_color=st_color)
    except Exception as e:
        st.error(f"行情獲取失敗: {e}")

# --- 5. 量價齊揚圖表 (台股配色) ---
def plot_combined_chart(symbol):
    st.subheader(f"📊 {current_name} ({symbol}) 走勢與量價分析")
    
    range_col, _ = st.columns([1, 2])
    date_range = range_col.radio("看盤區間", ["1個月", "3個月", "6個月"], horizontal=True)
    days_map = {"1個月": 30, "3個月": 90, "6個月": 180}
    
    df = yf.download(symbol, period=f"{days_map[date_range]}d", interval="1d", auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, 
                        row_heights=[0.7, 0.3])

    # K 線圖：紅漲綠跌
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線',
        increasing_line_color='#FF3232', increasing_fillcolor='#FF3232',
        decreasing_line_color='#32FF32', decreasing_fillcolor='#32FF32'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='#FFA500', width=1.5), name='5MA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#1E90FF', width=1.5), name='20MA'), row=1, col=1)
    
    # 成交量：紅漲綠跌 (收盤 > 開盤 為紅)
    colors = ['#FF3232' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#32FF32' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors, opacity=0.8), row=2, col=1)
    
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])]) 
    fig.update_layout(
        height=600, 
        xaxis_rangeslider_visible=False, 
        template="plotly_dark",
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- 6. AI 報告擷取 ---
def get_analysis(symbol_id):
    files = glob.glob('notes/*_stock_report.md')
    if not files: return "⚠️ 資料夾中尚無報告檔案。"
    latest_file = max(files, key=os.path.getctime)
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            content = f.read()
        stock_blocks = content.split("## 【")
        for block in stock_blocks:
            if symbol_id in block:
                return "## 【" + block
        return f"❌ 找不到代號 {symbol_id} 的詳細內容。"
    except Exception as e:
        return f"讀取報告出錯：{e}"

# --- 7. 主程式顯示流程 ---
show_metrics(current_sym)
plot_combined_chart(current_sym)
st.markdown("---")
st.subheader("🤖 AI 深度分析觀點")
st.markdown(get_analysis(current_sym.split('.')[0]))
import yfinance as yf
import pandas as pd
import os
import numpy as np
import sys
import time
import threading
import subprocess
from datetime import datetime

# --- 1. 配置與標的清單 ---
STOCKS = [
    "2330.TW", "3450.TW", "3363.TW",  # 矽光子
    "2317.TW", "2454.TW", "3017.TW",  # AI 伺服器
    "3491.TW", "6285.TW",             # 低軌衛星
    "1513.TW", "1519.TW", "1503.TW"   # 綠能基建
]

def is_trading_day():
    today = datetime.now()
    if today.weekday() >= 5: return False
    return True

def fetch_and_process(symbol):
    print(f"📥 正在抓取 {symbol} 數據...")
    try:
        df = yf.download(symbol, period="3mo", interval="1d", auto_adjust=True)
        if df.empty: return
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['Trend'] = np.where(df['MA5'] > df['MA20'], 'Up', 'Down')
        df = df.dropna(subset=['MA20'])
        stock_id = symbol.split(".")[0]
        os.makedirs("data", exist_ok=True)
        df.to_csv(f"data/processed_{stock_id}.csv")
        print(f"✅ {stock_id} 更新完成。")
    except Exception as e:
        print(f"❌ {symbol} 錯誤: {e}")

def run_daily_task():
    """執行流水線：抓數據 -> 啟動 Gemma 4 產製整合報告"""
    print(f"\n--- 📅 啟動全自動流程：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    if not is_trading_day():
        print("📅 今日非交易日，跳過。")
        return

    # 1. 抓取所有數據
    for s in STOCKS:
        fetch_and_process(s)

    # 2. 自動執行 hybrid_analyst.py (Gemma 4 整合報告)
    print("🤖 啟動 Gemma 4 (NVIDIA GPU 1 加速) 撰寫全產業整合報告...")
    try:
        # 注意：這裡執行的是 hybrid_analyst.py
        subprocess.run([sys.executable, "scripts/hybrid_analyst.py"], check=True)
        print("✨ 整合報告產製成功！已存入 notes 資料夾。")
    except Exception as e:
        print(f"❌ AI 分析階段發生錯誤: {e}")

# --- 2. 啟動與倒數邏輯 ---
def input_with_timeout(prompt, timeout):
    print(prompt, end='', flush=True)
    user_input = [None]
    def get_input():
        user_input[0] = sys.stdin.readline().strip().lower()
    t = threading.Thread(target=get_input)
    t.daemon = True
    t.start()
    for i in range(timeout, 0, -1):
        if user_input[0] is not None: break
        print(f"\r{prompt} ({i}s)... ", end='', flush=True)
        time.sleep(1)
    return user_input[0]

if __name__ == "__main__":
    TARGET_HOUR = 14
    TARGET_MINUTE = 35

    print("========================================")
    print("🤖 瀚民的 AI 股票助理 - Gemma 4 整合版")
    print(f"⏰ 每日執行時間：{TARGET_HOUR}:{TARGET_MINUTE}")
    print("========================================")

    ans = input_with_timeout("❓ 是否現在立刻執行一次完整流程？(y/n)", 5)
    
    if ans == 'y':
        run_daily_task()
    else:
        print("\n⏩ 進入監控模式...")

    while True:
        now = datetime.now()
        if now.hour == TARGET_HOUR and now.minute == TARGET_MINUTE:
            run_daily_task()
            time.sleep(61)
        print(f"\r⏳ 目前時間：{now.strftime('%H:%M:%S')}，持續監控中...", end="")
        time.sleep(10)
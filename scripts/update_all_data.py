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
    """判斷今天是否為交易日"""
    today = datetime.now()
    if today.weekday() >= 5: return False
    return True

def fetch_and_process(symbol):
    """抓取數據並處理技術指標"""
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
    """執行完整流水線：抓取 -> AI 分析 -> 自動同步 GitHub"""
    print(f"\n--- 📅 啟動全自動流程：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    if not is_trading_day():
        print("📅 今日非交易日，跳過。")
        return

    # 1. 抓取所有數據
    for s in STOCKS:
        fetch_and_process(s)

    # 2. 啟動 Gemma 4 分析
    print("🤖 啟動 Gemma 4 (NVIDIA GPU 加速) 撰寫全產業整合報告...")
    try:
        subprocess.run([sys.executable, "scripts/hybrid_analyst.py"], check=True)
        print("✨ 整合報告產製成功！已存入 notes 資料夾。")

        # 3. 自動同步至 GitHub
        print("☁️ 正在將最新報告同步至 GitHub...")
        subprocess.run(["git", "add", "data/*.csv", "notes/*.md"], check=True)
        commit_msg = f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 同步完成！手機網頁已更新。")

    except Exception as e:
        print(f"❌ 流程執行中發生錯誤: {e}")

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
    print("🤖 瀚民的 AI 股票助理 - 具備補跑功能版")
    print(f"⏰ 每日預定時間：{TARGET_HOUR}:{TARGET_MINUTE}")
    print("========================================")

    # --- 自動補跑檢查邏輯 ---
    now = datetime.now()
    target_today = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
    
    today_str = now.strftime("%Y%m%d") # 依照你 hybrid_analyst 的日期格式
    report_exists = False
    if os.path.exists("notes"):
        # 檢查 notes 資料夾裡有沒有今天產出的報告
        report_exists = any(today_str in f for f in os.listdir("notes"))

    # 如果現在已過 14:35，且今天還沒跑過報告，且是交易日
    if now > target_today and not report_exists and is_trading_day():
        print(f"\n📢 偵測到今日({now.strftime('%Y-%m-%d')})尚未執行任務且已過預定時間。")
        print("🚀 啟動自動補跑...")
        run_daily_task()
    else:
        if report_exists:
            print(f"✅ 今日報告已存在。")
        
        ans = input_with_timeout("\n❓ 是否現在立刻手動執行一次完整流程？(y/n)", 5)
        if ans == 'y':
            run_daily_task()
        else:
            print("\n⏩ 進入監控模式，等待定時觸發...")

    # 持續監控迴圈
    while True:
        now = datetime.now()
        if now.hour == TARGET_HOUR and now.minute == TARGET_MINUTE:
            run_daily_task()
            time.sleep(61)
        print(f"\r⏳ 目前時間：{now.strftime('%H:%M:%S')}，持續監控中...", end="")
        time.sleep(10)

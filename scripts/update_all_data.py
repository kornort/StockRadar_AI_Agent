
import json
import os
import sys
import time
import subprocess
from datetime import datetime

# --- 匯入我們全新的分析模組 ---
from scripts.macro_analyzer import get_macro_analysis
from scripts.stock_screener import find_potential_stocks, update_stock_list
from scripts.process_data import process_stock_data
from scripts.scoring_engine import calculate_score
from scripts.hybrid_analyst import generate_single_stock_report # 假設 hybrid_analyst 有此函式

# --- 輔助函式 ---
def is_trading_day():
    """判斷今天是否為台灣股市交易日"""
    today = datetime.now()
    return today.weekday() < 5 # 星期一到五

def get_stock_list():
    """從設定檔讀取完整的股票清單"""
    try:
        with open('config/stock_list.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        core_stocks = config.get("core_stocks", [])
        discovered_stocks = config.get("discovered_stocks", [])
        return list(set(core_stocks + discovered_stocks)) # 使用 set 避免重複
    except FileNotFoundError:
        print("錯誤：config/stock_list.json 不存在。請先建立此檔案。")
        return []

# --- 主要工作流程 ---
def run_daily_task():
    """執行從宏觀分析到產出報告的完整流水線"""
    print(f"\n--- 🚀 啟動 AI 股票分析完整流程：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    if not is_trading_day():
        print("📅 今日非交易日，任務跳過。")
        return

    # 步驟 1: 宏觀分析 (如果今天還沒產生過)
    report_path = f"notes/macro_analysis_{datetime.now().strftime('%Y%m%d')}.md"
    if not os.path.exists(report_path):
        print("\n🔍 步驟 1: 正在生成今日宏觀分析報告...")
        macro_report = get_macro_analysis()
        if macro_report:
            os.makedirs("notes", exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(macro_report)
            print(f"✅ 宏觀報告已儲存至 {report_path}")
    else:
        print("\n🔍 步驟 1: 今日宏觀報告已存在，直接讀取。")
        with open(report_path, 'r', encoding='utf-8') as f:
            macro_report = f.read()

    # 步驟 2: 潛力股篩選
    print("\n🔭 步驟 2: 根據宏觀報告篩選潛力股...")
    potential_stocks = find_potential_stocks(macro_report)
    if potential_stocks:
        update_stock_list(potential_stocks)

    # 步驟 3 & 4: 處理數據、評分並生成個股報告
    print("\n📊 步驟 3 & 4: 處理個股數據、評分並生成報告...")
    all_stocks = get_stock_list()
    if not all_stocks:
        print("❌ 股票清單為空，無法繼續執行。")
        return

    for stock_id in all_stocks:
        # 3.1 處理技術數據
        stock_df = process_stock_data(stock_id)
        if stock_df is None:
            continue # 如果處理失敗，跳過這檔股票
        
        # 3.2 進行評分 (此處 is_in_macro_trend 暫時簡化，未來可擴充)
        # 簡單判斷：如果潛力股清單中有它，就視為符合趨勢
        is_in_trend = stock_id in potential_stocks
        score, reasons = calculate_score(stock_df, is_in_macro_trend=is_in_trend)
        print(f"⭐ {stock_id} 信心指數: {score}/10, 理由: {reasons}")

        # 3.3 生成 AI 分析報告
        print(f"✍️ 正在為 {stock_id} 生成 AI 分析報告...")
        # 注意: 我們需要修改 hybrid_analyst.py 來接收這些參數
        generate_single_stock_report(stock_id, stock_df, score, reasons, macro_report)

    # 步驟 5: (可選) 執行原有的 hybrid_analyst.py 產製整合報告
    print("\n📝 步驟 5: 產製全市場整合報告...")
    try:
        subprocess.run([sys.executable, "scripts/hybrid_analyst.py"], check=True)
    except Exception as e:
        print(f"❌ 產製整合報告時出錯: {e}")

    # 步驟 6: (可選) 自動同步至 GitHub
    print("\n☁️ 步驟 6: 正在將最新報告同步至 GitHub...")
    try:
        subprocess.run(["git", "add", "data/", "notes/", "config/"], check=True)
        commit_msg = f"feat: AI-driven analysis update for {datetime.now().strftime('%Y-%m-%d')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 同步完成！")
    except Exception as e:
        print(f"❌ Git 同步失敗: {e}")

# --- 執行邏輯 (保留您原有的彈性設計) ---
if __name__ == "__main__":
    # 為了簡化，此處我們直接執行一次。您可以將原有的定時與手動觸發邏輯加回來。
    print("========================================")
    print("🤖 瀚民的 AI 股票助理 (強化版)")
    print("========================================")
    run_daily_task()
    print("\n--- ✅ 所有任務執行完畢 ---")

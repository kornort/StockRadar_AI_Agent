
import json
import os
import sys
import time
import subprocess
from datetime import datetime
import yfinance as yf

# --- 匯入我們全新的分析模組 ---
from scripts.macro_analyzer import get_macro_analysis
from scripts.stock_screener import find_potential_stocks, update_stock_list
from scripts.process_data import process_stock_data
from scripts.scoring_engine import calculate_score
from scripts.hybrid_analyst import generate_single_stock_report

# --- 輔助函式 ---
def is_trading_day():
    """判斷今天是否為台灣股市交易日"""
    today = datetime.now()
    return today.weekday() < 5

def get_stock_list():
    """從設定檔讀取完整的股票清單"""
    try:
        with open('config/stock_list.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        core_stocks = config.get("core_stocks", [])
        discovered_stocks = config.get("discovered_stocks", [])
        return list(set(core_stocks + discovered_stocks))
    except FileNotFoundError:
        print("錯誤：config/stock_list.json 不存在。請先建立此檔案。")
        return []

def is_valid_stock(stock_id):
    """使用 yfinance 快速驗證股票代號是否有效"""
    try:
        ticker = yf.Ticker(stock_id)
        # .fast_info 是一個輕量級的查詢，如果股票無效，通常會回傳空字典或缺少關鍵資訊
        # 檢查 'last_price' 是否存在，是判斷是否為有效上市股票的可靠方法
        if ticker.fast_info and ticker.fast_info.get('lastPrice'):
            return True
        else:
            print(f"--- ❌ 驗證失敗 (可能已下市或代號錯誤): {stock_id} ---")
            return False
    except Exception as e:
        # 處理 yfinance 可能拋出的任何網路或查詢錯誤
        print(f"--- ❌ 驗證 {stock_id} 時發生錯誤，將跳過: {e} ---")
        return False

# --- 主要工作流程 ---
def run_daily_task():
    """執行從宏觀分析到產出報告的完整流水線"""
    print(f"\n--- 🚀 啟動 AI 股票分析完整流程：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    if not is_trading_day():
        print("📅 今日非交易日，任務跳過。")
        return

    # 步驟 1: 宏觀分析
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

    # --- 新增的驗證步驟 ---
    print("\n🛡️  正在驗證所有股票代號的有效性...")
    validated_stocks = [stock for stock in all_stocks if is_valid_stock(stock)]
    print(f"\n✅ 驗證完成！總共 {len(all_stocks)} 檔，其中 {len(validated_stocks)} 檔有效，將開始處理。")

    for stock_id in validated_stocks:
        # 3.1 處理技術數據
        stock_df = process_stock_data(stock_id)
        if stock_df is None:
            continue
        
        # 3.2 進行評分
        is_in_trend = stock_id in potential_stocks
        score, reasons = calculate_score(stock_df, is_in_macro_trend=is_in_trend)
        print(f"⭐ {stock_id} 信心指數: {score}/10, 理由: {reasons}")

        # 3.3 生成 AI 分析報告
        print(f"✍️ 正在為 {stock_id} 生成 AI 分析報告...")
        generate_single_stock_report(stock_id, stock_df, score, reasons, macro_report)

    # 步驟 5: 產製整合報告
    print("\n📝 步驟 5: 產製全市場整合報告...")
    try:
        # 執行前檢查是否有報告可供整合
        report_files = [f for f in os.listdir('notes') if f.endswith('_stock_report.md')]
        if not report_files:
            print("⚠️  找不到任何個股報告，無法生成總結。")
        else:
            subprocess.run([sys.executable, "scripts/hybrid_analyst.py"], check=True)
    except Exception as e:
        print(f"❌ 產製整合報告時出錯: {e}")

    # 步驟 6: 自動同步至 GitHub
    print("\n☁️ 步驟 6: 正在將最新報告同步至 GitHub...")
    try:
        # 檢查是否有新的報告檔案產生
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if "notes/" in result.stdout or "data/" in result.stdout:
            subprocess.run(["git", "add", "data/", "notes/", "config/"], check=True)
            commit_msg = f"feat: AI-driven analysis update for {datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            subprocess.run(["git", "push"], check=True)
            print("🚀 同步完成！")
        else:
            print("ℹ️  沒有新的報告或資料變動，無需同步。")
    except Exception as e:
        print(f"❌ Git 同步失敗: {e}")

# --- 執行邏輯 ---
if __name__ == "__main__":
    print("========================================")
    print("🤖 瀚民的 AI 股票助理 (強化版)")
    print("========================================")
    run_daily_task()
    print("\n--- ✅ 所有任務執行完畢 ---")

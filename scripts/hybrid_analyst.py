import os
import pandas as pd
import requests
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- 配置區 ---
STOCK_INFO = {
    "2330": {"name": "台積電", "industry": "半導體/矽光子核心"},
    "3450": {"name": "聯鈞", "industry": "矽光子/光通訊"},
    "3363": {"name": "上詮", "industry": "矽光子/先進封裝"},
    "2317": {"name": "鴻海", "industry": "AI 伺服器/機器人/電動車"},
    "2454": {"name": "聯發科", "industry": "邊緣 AI 晶片/手機晶片"},
    "3491": {"name": "昇達科", "industry": "低軌衛星/通訊元件"},
    "6285": {"name": "啟碁", "industry": "低軌衛星/網路設備"},
    "1513": {"name": "中興電", "industry": "綠能/重電設備"},
    "1519": {"name": "華城", "industry": "電力基建/變壓器"},
    "1503": {"name": "士電", "industry": "重電/電力系統"}
}

def call_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma4:e4b",
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 4096}
    }
    # 由於是批次處理，我們設定較長的超時
    response = requests.post(url, json=payload, timeout=300)
    return response.json().get('response', "")

def main():
    print(f"🚀 啟動全產業 AI 整合分析報告產製...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 這是你要求的單一檔名 (解決問題)
    final_report_path = f"notes/{timestamp}_stock_report.md"
    os.makedirs("notes", exist_ok=True)

    # 先寫入報告標頭
    with open(final_report_path, "w", encoding="utf-8") as f:
        f.write(f"# 🌍 全球當紅產業 AI 投資整合報告\n")
        f.write(f"產製時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"核心模型: Gemma 4 (NVIDIA GPU 1 加速)\n")
        f.write(f"---\n\n")

    for stock_id, info in STOCK_INFO.items():
        stock_name = info["name"]
        industry = info["industry"]
        data_path = f"data/processed_{stock_id}.csv"
        
        if not os.path.exists(data_path):
            print(f"⚠️ 跳過 {stock_id}: 找不到資料。")
            continue
            
        print(f"🔍 正在產製 {stock_name} 的深度分析...")
        
        try:
            df = pd.read_csv(data_path)
            recent_data = df.tail(8).to_string(index=False)
            
            prompt = f"""
            你是一位專業的台股分析師。請分析『{stock_name} ({stock_id})』。
            產業背景：{industry}。
            
            數據指標：
            {recent_data}
            
            請產出 Markdown 格式報告，包含：
            1. 技術面判讀。
            2. 該產業目前的國際動能分析。
            3. 明確的操作建議與風險控管。
            使用繁體中文。
            """
            
            # 呼叫 AI
            ai_analysis = call_ollama(prompt)
            
            # 將結果附加 (Append) 到同一個檔案中
            with open(final_report_path, "a", encoding="utf-8") as f:
                f.write(f"## 【{industry}】{stock_name} ({stock_id})\n")
                f.write(ai_analysis)
                f.write("\n\n---\n\n")
            
            print(f"✅ {stock_name} 分析已寫入整合報告。")
            
        except Exception as e:
            print(f"❌ {stock_name} 寫入失敗: {e}")

    print(f"\n✨ 任務完成！整合報告已生成：{final_report_path}")

if __name__ == "__main__":
    main()
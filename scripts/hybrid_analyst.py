
import os
import pandas as pd
import requests
from datetime import datetime
import json

# --- 本地模型 API ---
def call_ollama(prompt):
    """呼叫本地的 Ollama Gemma 模型""" 
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma4:e4b", # 使用您指定的模型
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 8192} # 擴大上下文窗口以容納更豐富的 Prompt
    }
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status() # 如果請求失敗，會拋出 HTTPError
        return response.json().get('response', "(模型回傳為空)")
    except requests.exceptions.RequestException as e:
        print(f"❌ 呼叫 Ollama 模型失敗: {e}")
        return f"(模型呼叫失敗: {e})"

# --- 主要函式 1: 生成個股報告 (由 update_all_data.py 呼叫) ---
def generate_single_stock_report(stock_id, stock_df, score, reasons, macro_report):
    """
    為單一股票生成深度分析報告，並儲存成獨立檔案。
    """
    print(f"✍️  正在為 {stock_id} 生成深度分析報告...")
    
    # 準備 Prompt
    recent_data = stock_df.tail(10).to_string(index=True) # 提供最近10天的數據
    score_reasons = ", ".join(reasons)

    today_date = datetime.now().strftime('%Y年%m月%d日')
    prompt = f"""
    # 任務：專業台股分析師報告

    ## 1. 分析標的與時間
    - **股票代號:** {stock_id} 
      (⚠️ 強烈要求：必須正確寫出 {stock_id} 在台灣股市真實對應的公司名稱，嚴禁張冠李戴。例如 2330 必須是台積電，絕對不可寫成聯電或聯發科。)
    - **今日日期:** {today_date} 
      (⚠️ 強烈要求：報告中提及的分析時間必須以此日期為準，絕對不可編造未來的月份或年份。)

    ## 2. 宏觀背景 (由總經分析模組提供)
    {macro_report}

    ## 3. 量化數據
    - **信心指數:** {score}/10
    - **評分依據:** {score_reasons}
    - **近期技術指標 (近10日):**
    ```
    {recent_data}
    ```
    (⚠️ 強烈要求：報告中所提及的目前股價、支撐壓力位及推估目標價，必須【嚴格基於上述提供的近期技術指標數據】來進行合理推算，絕對不可憑空捏造或出現偏離上述報價極大的幻覺價格。)

    ## 4. 你的任務
    請基於以上所有資訊，以專業、客觀、精煉的法人報告風格，產出一份針對 {stock_id} 的單一個股深度分析報告。
    報告必須使用 **繁體中文** 並以 **Markdown 格式** 呈現，包含以下部分：

    ### A. 核心觀點 (Point of View)
    - 綜合宏觀、產業、技術面與量化分數，用 2-3句話總結你對此股票的「核心看法」(例如：強烈看多、謹慎樂觀、建議避開等) 及主要理由。

    ### B. 情境分析 (Scenario Analysis)
    - **正面情境:** 分析在哪些「正面因素」下 (例如：財報優於預期、產業出現重大利多、技術面突破關鍵壓力)，股價可能上漲，並推估潛在目標價區間。
    - **負面情境:** 分析在哪些「負面風險」下 (例如：國際政治衝突升溫、主要客戶抽單、跌破重要支撐)，股價可能下跌，並設定關鍵的停損或觀察價位。

    ### C. 綜合評級與建議
    - **評級:** 根據你的分析，給予「買進 (Buy)」、「持有 (Hold)」、「賣出 (Sell)」的明確評級。
    - **操作策略:** 提供具體的下一步操作建議 (例如：若突破壓力區可追價、等待拉回支撐區再布局、若跌破應果斷停損等)。
    """

    # 呼叫 AI 並儲存
    ai_analysis = call_ollama(prompt)
    
    # 建立儲存報告的資料夾
    report_dir = f"reports/{datetime.now().strftime('%Y%m%d')}"
    os.makedirs(report_dir, exist_ok=True)
    
    report_path = os.path.join(report_dir, f"{stock_id}.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# {stock_id} 個股深度分析報告\n")
        f.write(f"*報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(ai_analysis)
        
    print(f"✅ {stock_id} 報告已儲存至: {report_path}")

# --- 主要函式 2: 生成市場總結 (直接執行此檔案時運行) ---
def generate_summary_report():
    """
    讀取當天所有的個股報告，生成一份市場總結報告。
    """
    print(f"\n📑 正在生成今日市場總結報告...")
    today_str = datetime.now().strftime('%Y%m%d')
    report_dir = f"reports/{today_str}"

    if not os.path.exists(report_dir) or not os.listdir(report_dir):
        print(f"⚠️ 在 {report_dir} 中找不到任何個股報告，無法生成總結。")
        return

    # 讀取所有個股報告內容
    all_reports_content = ""
    for filename in os.listdir(report_dir):
        if filename.endswith(".md"):
            with open(os.path.join(report_dir, filename), 'r', encoding='utf-8') as f:
                all_reports_content += f"\n\n---\n【檔案: {filename}】\n---\n"
                all_reports_content += f.read()

    # 建立總結 Prompt
    summary_prompt = f"""
    # 任務：市場分析總監的每日總結

    ## 1. 背景
    - 你是一位經驗豐富的證券公司分析總監。
    - 以下是你團隊中多位分析師今天提交的「個股深度分析報告」。

    ## 2. 原始報告內容
    {all_reports_content}

    ## 3. 你的任務
    請閱讀並消化以上所有報告，然後以宏觀的視角，撰寫一份給高階主管的「今日市場盤後總結 (Daily Market Wrap-Up)」。
    報告必須使用 **繁體中文** 並以 **Markdown 格式** 呈現，包含以下部分：

    ### A. 市場多空溫度計
    - 綜合所有報告的買進/賣出評級與核心觀點，判斷今天市場的整體氣氛是「偏多」、「中性」還是「偏空」，並說明理由。

    ### B. 關鍵發現 (Key Findings)
    - **共同的利多因素:** 點出報告中反覆出現的正面趨勢或訊號 (例如：多檔股票呈現黃金交叉、AI 伺服器產業鏈需求強勁等)。
    - **潛在的系統性風險:** 識別報告中隱含的、可能影響多個板塊的共同風險 (例如：地緣政治緊張、通膨預期升溫等)。

    ### C.明日操作焦點
    - **重點關注板塊:** 建議明天應該優先關注哪個或哪些產業板塊。
    - **明日策略提醒:** 提供一個簡潔的明日看盤重點與操作建議。
    """

    # 呼叫 AI 並儲存
    summary_analysis = call_ollama(summary_prompt)
    
    summary_path = f"notes/Summary_Report_{today_str}.md"
    os.makedirs("notes", exist_ok=True)
    
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# 每日市場盤後總結\n")
        f.write(f"*總結時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(summary_analysis)
        
    print(f"✨ 市場總結報告已成功生成: {summary_path}")


if __name__ == "__main__":
    # 當這個檔案被直接執行時，代表所有個股報告都已生成完畢，
    # 此時執行總結任務。
    generate_summary_report()

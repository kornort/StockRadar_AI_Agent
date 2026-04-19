import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

# 1. 載入 API Key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# 2. 讀取我們處理過的數據
df = pd.read_csv("data/processed_2330.csv")
# 只取最後五天的數據給 AI，避免資訊過多干擾判斷
recent_data = df[['Date', 'Close', 'MA5', 'MA20', 'Trend']].tail(5).to_string()

# 3. 設計給 AI 的「角色指令」 (仿照網紅筆記格式)
prompt = f"""
你現在是一位資深台股分析師。請根據以下台積電(2330)的近期技術指標數據進行分析：

{recent_data}

請撰寫一份 Markdown 格式的投資筆記，包含以下部分：
1. 🎯 **本週摘要**：簡述目前趨勢。
2. 📊 **技術面快照**：說明 MA5 與 MA20 的相對位置及 Trend 意義。
3. 💡 **一句話 Thesis**：給這檔股票目前的狀態一個定調。
4. 🚀 **操作策略**：給出具體的支撐位與建議入場策略。

請使用專業但易懂的語氣，並加入適當的表情符號。
"""

# 4. 呼叫 Gemini
model = genai.GenerativeModel('gemini-1.5-flash') # 使用最新的模型
response = model.generate_content(prompt)

# 5. 存檔到 notes 資料夾 (這就是你的 Obsidian 筆記)
note_path = "notes/2330_台積電分析報告.md"
with open(note_path, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"--- 報告生成完畢！請查看 {note_path} ---")
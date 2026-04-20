
import requests
import json
import os

# --- 統一使用本地 Ollama API ---
def call_ollama(prompt):
    """呼叫本地的 Ollama Gemma 模型"""
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "gemma4:e4b", # 使用您指定的模型
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 8192}
    }
    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get('response', "[]") # 預設回傳空的 List 字串
    except requests.exceptions.RequestException as e:
        print(f"❌ 呼叫 Ollama 模型失敗: {e}")
        return f"(模型呼叫失敗: {e})"

def find_potential_stocks(macro_analysis_report):
    """
    基於宏觀分析報告，使用本地 Gemma 4 模型找出有潛力的台灣股票。
    """
    prompt = f"""
    # 任務：從分析報告中提取台灣潛力股

    ## 分析背景
    這是一份由 AI 生成的全球產業趨勢和政治局勢的宏觀分析報告：
    ---
    {macro_analysis_report}
    ---

    ## 你的任務
    請你扮演一個專注於台股的量化分析師，嚴格遵循以下指令：
    1.  **閱讀** 上述報告，聚焦於其中提到的「全球產業趨勢」。
    2.  **思考** 這些趨勢直接對應到台灣股市的哪些具體公司。
    3.  **輸出** 3 到 5 檔與這些趨勢高度相關、且在台灣上市(TWSE/TPEx)的公司股票代號。

    ## 輸出要求 (極其重要)
    - **格式:** 你的回答「只能」是一個標準的 Python List of Strings，其中包含股票代號。
    - **內容:** 股票代號必須以 ".TW" 或 ".TWO" 結尾 (例如: "2330.TW", "6446.TWO").
    - **禁止:** 絕對不要包含任何 Python 程式碼塊標記 (如 ```python), 任何解釋、任何註解、任何非股票代號的文字。

    ## 範例輸出
    ["2330.TW", "2317.TW", "3443.TW", "6415.TW"]
    """

    response_text = call_ollama(prompt)
    
    # 解析模型回傳的文字
    try:
        # 模型有時可能回傳被引號包住的字串，或是有單引號，需要清理
        cleaned_text = response_text.strip().replace("'", '"')
        potential_list = json.loads(cleaned_text)
        
        # 確保回傳的是一個 list of strings
        if isinstance(potential_list, list) and all(isinstance(item, str) for item in potential_list):
            print(f"Ollama 成功回傳潛力股清單: {potential_list}")
            return potential_list
        else:
            print(f"⚠️ 模型回傳格式不符預期: {response_text}")
            return []

    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing potential stocks from model response: {e}")
        print(f"Model Raw Response:\n{response_text}")
        return []

def update_stock_list(new_stocks):
    """
    更新 config/stock_list.json，將新發現的股票加入 discovered_stocks。
    """
    config_path = 'config/stock_list.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            stock_list_data = json.load(f)
        
        existing_stocks = set(stock_list_data.get('core_stocks', []) + stock_list_data.get('discovered_stocks', []))
        
        unique_new_stocks = [stock for stock in new_stocks if stock not in existing_stocks]
        
        if not unique_new_stocks:
            print("沒有發現新的潛力股可供加入。")
            return

        stock_list_data['discovered_stocks'] = list(set(stock_list_data.get('discovered_stocks', []) + unique_new_stocks))

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(stock_list_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 股票清單更新成功，已加入: {unique_new_stocks}")

    except FileNotFoundError:
        print(f"❌ 錯誤: {config_path} 找不到.")
    except Exception as e:
        print(f"❌ 更新股票清單時出錯: {e}")

if __name__ == '__main__':
    # --- 測試流程 ---
    print("--- 正在測試潛力股篩選模組 (使用本地 Ollama) ---")
    mock_report = """
    ### 全球產業趨勢
    - **AI 硬體設施**: NVIDIA 的 GPU 領導市場，推動了對 AI 伺服器、散熱解決方案和高速傳輸的需求。台灣的台積電、鴻海、廣達等公司是此趨勢的主要受益者。
    - **綠色能源轉型**: 全球對抗氣候變遷，太陽能、風能和儲能系統的需求大增。台灣的相關供應鏈，如中興電、華城等，迎來商機。
    """
    potential_stocks = find_potential_stocks(mock_report)

    if potential_stocks:
        print(f"\n模擬測試找到的潛力股: {potential_stocks}")
        # 為了不影響您的設定檔，這裡僅模擬輸出
        print("\n(模擬) 更新 stock_list.json...")
        print("update_stock_list(potential_stocks) # 實際執行時會取消此註解")
    else:
        print("\n模擬測試未能找到潛力股。")

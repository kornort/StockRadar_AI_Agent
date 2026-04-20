
import requests
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
        return response.json().get('response', "(模型回傳為空)")
    except requests.exceptions.RequestException as e:
        print(f"❌ 呼叫 Ollama 模型失敗: {e}")
        return f"(模型呼叫失敗: {e})"

def get_macro_analysis():
    """
    使用本地 Gemma 4 模型生成宏觀經濟分析報告。
    """
    prompt = """
    請以專業投資分析師的角度，生成一份關於當前全球市場的宏觀分析報告。
    報告需包含以下兩個部分，並以 Markdown 格式呈現：

    ### 1. 全球產業趨勢
    - 識別並摘要說明 3-5 個正在影響全球經濟的關鍵產業趨勢（例如：AI 硬體、綠色能源、生物科技等）。
    - 對每個趨勢，簡單說明其發展潛力及主要受惠的領域。

    ### 2. 重大政治局勢
    - 摘要說明 2-3 個當前最值得關注的國際政治或經濟事件（例如：主要經濟體的利率政策、地緣政治衝突、國際貿易關係等）。
    - 分析這些事件可能對全球股市，特別是台灣科技產業鏈，帶來的正面或負面影響。

    請確保內容是基於最新的市場情況，分析需具備洞見，語言力求客觀、精煉。
    """
    
    return call_ollama(prompt)

if __name__ == '__main__':
    # 測試
    print("正在生成宏觀分析報告 (使用本地 Ollama)...")
    analysis_report = get_macro_analysis()
    if analysis_report and not analysis_report.startswith("(模型呼叫失敗"):
        print("--- 宏觀分析報告生成成功 ---")
        print(analysis_report)
        # 實際應用中，可以將報告寫入檔案
        os.makedirs("notes", exist_ok=True)
        with open("notes/macro_analysis_test.md", "w", encoding="utf-8") as f:
            f.write(analysis_report)
        print("\n報告已儲存至 notes/macro_analysis_test.md")
    else:
        print("--- 報告生成失敗 --- ")


import pandas as pd

def calculate_score(stock_data, is_in_macro_trend):
    """
    計算單一股票的信心指數。

    Args:
        stock_data (pd.DataFrame): 包含該股票所有技術指標的 DataFrame。
                                     需要包含 'Close', 'SMA_5', 'SMA_20', 'RSI_14', 
                                     'MACD_12_26_9', 'MACDh_12_26_9', 'Volume', 'Volume_SMA_20'。
        is_in_macro_trend (bool): 該股票是否符合宏觀趨勢。

    Returns:
        int: 信心指數 (1-10)。
    """
    score = 5  # 基礎分數為 5
    reasons = []

    # 獲取最新的數據點 (最後一列)
    latest = stock_data.iloc[-1]

    # --- 技術面 (權重 40%，總分 4 分) ---
    # 1. MA 黃金交叉 (2 分)
    if latest['SMA_5'] > latest['SMA_20']:
        score += 2
        reasons.append("MA黃金交叉")

    # 2. RSI 狀態 (1 分)
    if latest['RSI_14'] < 70:
        score += 1
        reasons.append("RSI未超買")
    elif latest['RSI_14'] > 70:
        score -= 1
        reasons.append("RSI超買")

    # 3. MACD 狀態 (1 分)
    if latest['MACDh_12_26_9'] > 0:
        score += 1
        reasons.append("MACD多頭")
    else:
        score -= 1
        reasons.append("MACD空頭")

    # --- 籌碼面 (權重 30%，總分 3 分) ---
    # 1. 成交量狀態 (3 分)
    if latest['Volume'] > latest['Volume_SMA_20'] * 1.5: # 量大於20日均量的1.5倍
        score += 3
        reasons.append("放量上漲")
    elif latest['Volume'] < latest['Volume_SMA_20']:
        score -= 1
        reasons.append("量能萎縮")

    # --- 宏觀面 (權重 30%，總分 3 分) ---
    if is_in_macro_trend:
        score += 3
        reasons.append("符合宏觀趨勢")

    # 將分數限制在 1 到 10 之間
    final_score = max(1, min(10, score))
    
    return final_score, reasons


if __name__ == '__main__':
    # --- 測試範例 ---
    # 假設這是從 process_data.py 產出的 DataFrame
    # 注意：這只是假數據，實際應讀取分析後的 CSV
    data = {
        'Close': [100, 102, 105, 108, 110],
        'SMA_5': [101, 103, 105, 107, 109],
        'SMA_20': [100, 101, 102, 103, 104],
        'RSI_14': [60, 65, 72, 75, 78],
        'MACD_12_26_9': [0.5, 0.6, 0.7, 0.8, 0.9],
        'MACDh_12_26_9': [0.1, 0.1, -0.05, 0.1, 0.2],
        'Volume': [1000, 1200, 800, 1500, 2500],
        'Volume_SMA_20': [1100, 1150, 1100, 1200, 1300],
    }
    sample_df = pd.DataFrame(data)

    # 情境一：符合宏觀趨勢
    score, reasons = calculate_score(sample_df, is_in_macro_trend=True)
    print(f"--- 情境一：符合宏觀趨勢 ---")
    print(f"信心指數: {score}/10")
    print(f"評分理由: {reasons}")

    # 情境二：不符合宏觀趨勢
    score, reasons = calculate_score(sample_df, is_in_macro_trend=False)
    print(f"\n--- 情境二：不符合宏觀趨-勢 ---")
    print(f"信心指數: {score}/10")
    print(f"評分理由: {reasons}")

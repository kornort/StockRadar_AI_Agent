
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os

def process_stock_data(stock_id):
    """
    下載指定股票的數據，並計算所有需要的技術指標。

    Args:
        stock_id (str): 股票代號，例如 "2330.TW"。

    Returns:
        pd.DataFrame: 包含所有技術指標的 DataFrame，如果失敗則回傳 None。
    """
    print(f"--- Processing data for {stock_id} ---")
    # 確保 data 資料夾存在
    if not os.path.exists('data'):
        os.makedirs('data')

    try:
        # 1. 抓取資料 (下載最近 3 個月的數據以確保指標的準確性)
        df = yf.download(stock_id, period="3mo", progress=False)

        if df.empty:
            print(f"No data downloaded for {stock_id}. Skipping.")
            return None

        # 2. 計算 MA, RSI, MACD, Bollinger Bands, Volume SMA
        # 使用 pandas_ta 擴展功能，一次性計算多個指標
        df.ta.sma(length=5, append=True) # 會自動命名為 SMA_5
        df.ta.sma(length=20, append=True) # 會自動命名為 SMA_20
        df.ta.rsi(length=14, append=True) # 會自動命名為 RSI_14
        df.ta.macd(append=True) # 會自動命名為 MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        df.ta.bbands(append=True) # 會自動命名為 BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0
        df.ta.sma(close='Volume', length=20, prefix="Volume", append=True) # 成交量均線

        # 移除包含 NaN 的早期行，這些行因為窗口不足而無法計算指標
        df.dropna(inplace=True)

        print(f"Indicators calculated for {stock_id}. Total {len(df)} data points.")

        # 3. 存檔
        output_path = f"data/processed_{stock_id}.csv"
        df.to_csv(output_path)
        print(f"Saved to {output_path}")
        
        return df

    except Exception as e:
        print(f"An error occurred while processing {stock_id}: {e}")
        return None

if __name__ == '__main__':
    # --- 測試流程 ---
    # 測試單一一檔股票
    test_stock = "2330.TW"
    processed_df = process_stock_data(test_stock)

    if processed_df is not None:
        print(f"\n--- Test for {test_stock} Successful ---")
        # 顯示最後5筆計算結果，檢查常用指標是否正確
        print(processed_df[['Close', 'SMA_5', 'SMA_20', 'RSI_14', 'MACDh_12_26_9', 'Volume_SMA_20']].tail())

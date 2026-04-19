import yfinance as yf
import pandas as pd
import os

# 確保 data 資料夾存在
if not os.path.exists('data'):
    os.makedirs('data')

# 1. 抓取資料 (用 1mo 確保 MA20 有足夠數據)
df = yf.download("2330.TW", period="1mo")

# 2. 計算均線
# 如果下載下來是 MultiIndex (新版 yfinance 常見)，我們先簡化它
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df['MA5'] = df['Close'].rolling(window=5).mean()
df['MA20'] = df['Close'].rolling(window=20).mean()

# 3. 判斷趨勢 (改用 .loc 這種更穩定的向量化寫法)
df['Trend'] = 'Wait' # 預設值
df.loc[df['MA5'] > df['MA20'], 'Trend'] = 'Up'
df.loc[df['MA5'] < df['MA20'], 'Trend'] = 'Down'

print("--- 技術指標計算完成 ---")
print(df[['Close', 'MA5', 'MA20', 'Trend']].tail())

# 4. 存檔
df.to_csv("data/processed_2330.csv")
print("\n已存檔至 data/processed_2330.csv")
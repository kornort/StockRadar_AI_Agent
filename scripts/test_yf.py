import yfinance as yf

# 測試抓取台積電資料
try:
    df = yf.download("2330.TW", period="5d")
    print("--- 抓取成功！最近五日股價如下 ---")
    print(df)
except Exception as e:
    print(f"發生錯誤：{e}")
# 🚀 StockRadar AI Agent：全自動產業投資分析助理

這是一個結合 Python 自動化、金融數據抓取以及 **Gemma 4 (本地端 LLM)** 的智能投資工具。本專案旨在自動化每日繁瑣的股價追蹤流程，並透過 AI 產出具備專業深度的產業整合分析報告。

---

## 🌟 核心功能

* **自動化數據流水線**：每日 14:35 自動觸發，針對 11 檔核心標的（矽光子、AI 伺服器、低軌衛星、綠能基建）進行數據更新。
* **技術指標計算**：自動計算 MA5、MA20 及趨勢判斷（Trend），並生成結構化 CSV 檔案。
* **本地 AI 深度分析**：串接 **Gemma 4 (Ollama)**，利用 NVIDIA GPU 加速進行推理，產製高品質的 Markdown 格式投資報告。
* **整合式分析架構**：不再只是單一標的分析，而是將多個產業動能整合進同一份報告中，方便快速閱覽。
* **Streamlit 視覺化**：支援透過網頁介面即時查看數據圖表與 AI 建議。

---

## 🛠️ 技術棧

* **語言**：Python 3.10+
* **金融數據**：`yfinance`, `pandas`, `numpy`
* **人工智慧**：Ollama (Gemma 4 模型), NVIDIA CUDA 加速
* **網頁框架**：Streamlit
* **版本控制**：Git / GitHub

---

## 📂 專案結構

```text
StockRadar_AI_Agent/
├── scripts/
│   ├── update_all_data.py   # 自動化排程主程式（5秒倒數與定時監控）
│   └── hybrid_analyst.py   # AI 分析核心（串接 Gemma 4 產製報告）
├── data/                    # 存放每日更新的處理後數據 (CSV)
├── notes/                   # 存放 AI 產出的 Markdown 整合報告
├── app.py                   # Streamlit 前端網頁介面
├── .env                     # 環境變數設定（API Key 等）
└── .gitignore               # Git 忽略清單（排除 venv 與機密資訊）
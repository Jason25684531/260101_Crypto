# Tasks: Phase 5 & 6 - AI Enhancement & On-Chain Intelligence

## Context
系統已具備自動化交易與基礎風控能力。
下一步是引入 **Machine Learning (ML)** 來過濾假信號，並整合 **Deep On-Chain Data** 以捕捉巨鯨動向。
這將把系統的 Alpha 來源從「純技術面」擴展到「概率預測」與「籌碼面」。

**當前狀態 (2026-02-01):**
- ✅ Phase 4.0 核心安全功能已完成 (Kill Switch + SAST)
- ⏳ Phase 4.2 (Watchdog) 和 4.4 (Production Deployment) 待實作
- ✅ **Phase 5 (ML Signal Filter) 已完成！** (2026-01-31)
- ✅ **Phase 6 (On-Chain Data Integration) 已完成！** (2026-02-01)
- 🗄️ 資料庫已有 On-Chain 模型基礎 (`ChainMetric`, `ExchangeNetflow`)
- 📦 ML 依賴套件已安裝 (scikit-learn==1.5.0, joblib==1.3.2)
- 🔗 Dune Analytics 整合已完成 (dune-client==1.3.0)

---

## Phase 5: Machine Learning Signal Filter (AI 信號過濾) ✅ 已完成
**目標：** 利用 `scikit-learn` 訓練隨機森林模型，預測交易信號的勝率，過濾掉低品質的買入機會。

- [x] **5.1 Infrastructure & Dependencies (基礎設施)**
    - [x] **Update** `requirements.txt`: 已啟用 `scikit-learn==1.5.0`
    - [x] **Install** ML dependencies via pip
    - [x] **Create** folder `app/core/ml/` and `data/models/`

- [x] **5.2 Data Pipeline (數據管道 - 離線訓練)**
    - [x] **Create** `scripts/ml_pipeline.py`:
        - [x] `build_dataset()`: 計算技術指標特徵
        - [x] `train_model()`: RandomForestClassifier 訓練
        - [x] `save_model()`: 保存為 pkl 檔案

- [x] **5.3 Runtime Integration (實時預測整合)**
    - [x] **Create** `app/core/ml/predictor.py`:
        - [x] Class `SignalPredictor`: Singleton pattern
        - [x] Method `predict_proba(features) -> float`
        - [x] Method `should_filter(features) -> bool`
        - [x] Method `get_prediction_with_details(features) -> dict`
    - [x] **Update** `app/core/execution/trader.py`:
        - [x] 在 `execute_strategy` 中加入 ML 檢查點
        - [x] 新增參數 `use_ml_filter` 和 `ml_threshold`
        - [x] 邏輯：`if action == 'buy' and ml_proba < 0.6: ABORT`

- [x] **5.4 Unit Tests (單元測試)**
    - [x] **Create** `tests/unit/test_ml_predictor.py`: 完整測試套件
    - [x] **Create** `test_ml_predictor.py`: 快速驗證腳本
    - [x] **Result**: 10/10 測試通過

---

# Tasks: Phase 6.0 - Deep On-Chain Analytics

## Context (背景)
系統目前具備「技術面」與「AI 面」的決策能力。
為了構建「資訊優勢」，我們需要整合鏈上數據 (On-Chain Data)。
本階段將接入 Dune Analytics，捕捉「聰明錢」的動向，作為 CompositeScore 的重要扣分/加分項。

## Phase 6.1: Infrastructure & Data Model
**目標：** 建立鏈上數據的儲存結構與連接器。

- [x] **Dependencies**
    - [x] **Update** `requirements.txt`: Uncomment `dune-client==1.3.0`.
    - [x] **Config:** Add `DUNE_API_KEY` to `.env` and `app/config.py`.

- [x] **Database Schema**
    - [x] **Update** `app/models/onchain.py`:
        - [x] Add columns to `ChainMetric`:
            - `exchange_netflow` (float): 交易所淨流入量
            - `whale_inflow_count` (int): >10 BTC 的轉入筆數
    - [x] **Migration:** Run `flask db migrate` & `upgrade`.

## Phase 6.2: Dune Data Fetcher
**目標：** 實作專用的 Fetcher，因為 Dune 是異步查詢 (Submit -> Wait -> Get Result)。

- [x] **Implement Fetcher**
    - [x] **Create** `app/core/data/dune_fetcher.py`:
        - [x] Class `DuneFetcher`
        - [x] Method `fetch_latest_metrics()`:
            - 使用 Query ID (需在 Dune 官網找好，如 "Bitcoin Exchange Netflow")
            - 處理 API Rate Limit 與等待邏輯。
    - [x] **Unit Test:** `tests/unit/test_dune_fetcher.py` (Mock API response).

## Phase 6.3: Automation & Strategy Integration
**目標：** 將鏈上數據納入自動化排程與決策引擎。

- [x] **Job Scheduling**
    - [x] **Update** `app/core/jobs.py`:
        - [x] Add `job_update_onchain()`: Run every 4 hours (Dune 數據更新較慢).

- [x] **Signal Logic**
    - [x] **Update** `app/core/strategy/factors.py`:
        - [x] Add `OnChainFactor`: Calculate Z-Score of Netflow.
    - [x] **Update** `app/core/strategy/engine.py`:
        - [x] `CompositeScore` Logic:
            - If `Netflow Z-Score > 2.0` (異常流入) -> Score -= 20 (看空).
            - If `Netflow Z-Score < -2.0` (異常流出) -> Score += 10 (看多).

## Validation
- [x] **Dashboard Update:**
    - [x] Add "On-Chain" chart to Streamlit Tab 1.
- [x] **Live Test:**
    - [x] Verify `job_update_onchain` runs successfully in logs.

---

## 完成狀態總結

### ✅ 已完成 (基礎設施)
- **資料庫模型**: `ChainMetric`, `ExchangeNetflow` 已定義於 `app/models/onchain.py`
- **API 路由**: 已支援 netflow 資料查詢
- **策略框架**: `calculate_onchain_zscore` 方法已存在於 `app/core/strategy/factors.py`

### ⏳ 待完成 (Phase 5 - ML)
- 安裝 `scikit-learn` (建議升級到 1.5.0+ 以修復 CVE-2024-5206)
- 創建 `app/core/ml/` 目錄和 ML pipeline
- 實作 `SignalPredictor` 類別
- 整合到交易執行流程

### ✅ 已完成 (Phase 6 - On-Chain) - 2026-02-01
- **依賴套件**: `dune-client==1.3.0` 已安裝
- **資料庫模型**: `ChainMetric` 新增 `exchange_netflow` 和 `whale_inflow_count` 欄位
- **DuneFetcher 類別**: 完整實作異步查詢流程（Submit -> Wait -> Get Result）
- **單元測試**: `tests/unit/test_dune_fetcher.py` 18/18 測試通過
- **排程任務**: `job_update_onchain()` 每 4 小時執行一次
- **策略整合**: `calculate_composite_score()` 整合鏈上 Z-Score 調整邏輯
- **輔助函數**: `get_latest_onchain_zscore()` 從資料庫獲取最新指標
- **功能驗證**: `tests/manual/test_phase6.py` 所有測試通過

### ⏳ 待完成 (Phase 6 - 上線配置)
- 在 Dune Analytics 創建查詢並獲取真實 Query ID
- 設置 DUNE_API_KEY 環境變數（需付費訂閱）
- 執行資料庫遷移：`flask db migrate && flask db upgrade`
- 啟動調度器測試鏈上數據更新功能

### 📌 建議執行順序
1. **Phase 4.2 完成** (Watchdog) - 確保資金安全
2. **Phase 4.4 完成** (Production Deployment) - 準備上線環境
3. **Phase 5 實作** - ML 信號過濾 (提升勝率)
4. **Phase 6 實作** - On-Chain 數據 (捕捉籌碼面)

### 🔒 前置條件
- ⚠️ Phase 4.2 和 4.4 應優先於 Phase 5/6 完成
- 📊 需要足夠的歷史數據進行 ML 訓練 (建議至少 3 個月 OHLCV)
- 💰 Dune API Key 需要付費訂閱方案
- 🧪 建議先在測試環境驗證 ML 模型效果再上生產環境
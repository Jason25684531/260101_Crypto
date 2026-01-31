# Tasks: Phase 5 & 6 - AI Enhancement & On-Chain Intelligence

## Context
系統已具備自動化交易與基礎風控能力。
下一步是引入 **Machine Learning (ML)** 來過濾假信號，並整合 **Deep On-Chain Data** 以捕捉巨鯨動向。
這將把系統的 Alpha 來源從「純技術面」擴展到「概率預測」與「籌碼面」。

**當前狀態 (2026-01-31):**
- ✅ Phase 4.0 核心安全功能已完成 (Kill Switch + SAST)
- ⏳ Phase 4.2 (Watchdog) 和 4.4 (Production Deployment) 待實作
- ✅ **Phase 5 (ML Signal Filter) 已完成！** (2026-01-31)
- ⏳ Phase 6 (On-Chain) 尚未開始
- 🗄️ 資料庫已有 On-Chain 模型基礎 (`ChainMetric`, `ExchangeNetflow`)
- 📦 ML 依賴套件已安裝 (scikit-learn==1.5.0, joblib==1.3.2)

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

## Phase 6: Deep On-Chain Analytics (深層鏈上數據)
**目標：** 整合 Dune Analytics，監控交易所淨流入 (Netflow) 與巨鯨動向。

- [ ] **6.1 Infrastructure (基礎設施)**
    - [ ] **Update** `requirements.txt`: Uncomment `dune-client==1.3.0`.
    - [ ] **Update** `.env`: Add `DUNE_API_KEY`.
    - [x] ~~**Update** `app/models/onchain.py`~~: *(已完成 - `ExchangeNetflow` 模型包含 inflow/outflow/netflow 欄位)*

- [ ] **6.2 Data Fetcher (數據抓取)**
    - [ ] **Create** `app/core/data/dune_fetcher.py`:
        - [ ] Implement `DuneFetcher` class.
        - [ ] Query 1: "Bitcoin Exchange Netflow" (每日/每小時更新)。
        - [ ] Query 2: "Large Transactions (>10 BTC) to Exchanges".
    - [ ] **Update** `app/core/jobs.py`:
        - [ ] Add `job_update_onchain_daily()`: 由於 Dune API 較昂貴或較慢，設定為每 4-6 小時執行一次。

- [ ] **6.3 Signal Logic (信號邏輯)**
    - [ ] **Update** `app/core/strategy/factors.py`:
        - [ ] Add `OnChainFactor`:
            - 若 `Exchange Netflow` 為大幅正值 (流入 > 2 Sigma) -> 視為潛在拋壓 (Bearish)。
            - 若 `Whale Inflow` 突增 -> 觸發 `WhaleAlert`。
    - [ ] **Update** `CompositeScore`:
        - 將鏈上因子權重納入計算 (例如扣除總分 10-20 分)，讓系統在巨鯨倒貨前自動減倉。

---

## Validation (驗證計畫)
- [ ] **ML Backtest:**
    - 使用 `vectorbt` 比較 "Raw Strategy" vs "ML Filtered Strategy" 的夏普比率。
    - 目標：交易次數減少，但勝率 (Win Rate) 提升 > 5%。
- [ ] **On-Chain Correlation:**
    - 驗證 Dune 數據 (Netflow) 與價格下跌的滯後相關性 (Lag Correlation)。

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

### ⏳ 待完成 (Phase 6 - On-Chain)
- 安裝 `dune-client==1.3.0`
- 實作 `DuneFetcher` 類別
- 整合鏈上信號到策略評分系統
- 設定排程任務定期更新鏈上數據

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
# Tasks: Phase 3.5 & 3.8 - System Automation & Paper Trading

## Context (背景)
目前系統處於「靜態」狀態：
1. 資料爬取依賴手動執行 `seed_data.py`。
2. 策略回測僅能針對歷史資料跑一次。
3. 交易執行缺乏「模擬模式」，直接上實盤風險過高。

本階段目標是建立系統的「心跳 (Heartbeat)」，讓數據爬取與策略執行自動化，並引入「模擬交易 (Paper Trading)」以進行無風險的實盤驗證。

## Phase 3.5: The Heartbeat (自動化排程與爬蟲整合)
**目標：** 實作排程器，將「手動爬蟲」轉化為「自動循環爬蟲」，並定時觸發策略。

- [x] **Dependency Management (依賴管理)**
    - [x] 在 `requirements-core.txt` 中新增 `APScheduler==3.10.4`。
    - [ ] 重建 Docker Image 以安裝新套件。

- [x] **Scheduler Infrastructure (排程基礎架構)**
    - [x] **Test First:** 建立 `tests/unit/test_scheduler.py`，驗證排程器能啟動、執行 Dummy Job 並正常關閉。
    - [x] **Implement:** 建立 `app/core/scheduler.py`：
        - [x] 初始化 `BackgroundScheduler`。
        - [x] 實作 `start()` 與 `shutdown()` 方法。
        - [x] 設定時區為 UTC。

- [x] **Data Jobs (數據爬蟲自動化)**
    - [x] **Test First:** 建立 `tests/unit/test_jobs.py`，驗證任務能正確執行並處理錯誤。
    - [x] **Refactor:** 修改 `app/core/data/fetcher.py`，新增 `fetch_latest_ohlcv(symbol)` 方法 (只抓最後幾根 K 線，而非全量歷史)。
    - [x] **Define Job:** 在 `app/core/jobs.py` 中實作 `job_update_market_data()`：
        - [x] 呼叫 `fetch_latest_ohlcv`。
        - [x] 將新數據寫入 MySQL。
        - [x] 處理網路錯誤與重複數據（幂等性）。
        - [ ] 更新 Redis 快取（可選）。
    - [x] **Schedule:** 在 `app/core/scheduler.py` 添加 `setup_market_data_jobs()` 方法，設定排程器每 1 分鐘 (at second :05) 執行此 Job。

- [x] **Strategy Jobs (策略觸發自動化)**
    - [x] **Define Job:** 在 `app/core/jobs.py` 中實作 `job_scan_signals()` 框架：
        - [ ] 從 DB 讀取最新數據（待實現）。
        - [ ] 呼叫 `AlphaFactors` 計算指標（待實現）。
        - [ ] 若 `CompositeScore` 觸發閾值，呼叫 `TradeExecutor`（待實現）。
    - [x] **Schedule:** 在 `app/core/scheduler.py` 添加 `setup_signal_scan_jobs()` 方法，設定排程器每 1 分鐘 (at second :10) 執行此 Job (確保數據已更新)。

## Phase 3.8: Paper Trading Mode (模擬交易模式)
**目標：** 在不連接真實交易所 API 的情況下，驗證策略邏輯與資金管理。

- [x] **Configuration (配置)**
    - [x] 在 `.env.example` 新增 `TRADING_MODE=PAPER` (預設) 與 `TRADING_MODE=LIVE` 選項。
    - [x] 創建 `app/config.py` 模組載入配置並提供便捷方法。

- [x] **Paper Exchange Adapter (模擬交易所適配器)**
    - [x] **Test First:** 建立 `tests/unit/test_paper_exchange.py`，驗證所有核心功能。
    - [x] **Design:** 建立 `app/core/execution/paper_exchange.py`。
    - [x] **Implement:** 實作 `PaperExchange` 類別，模擬 `ccxt` 的關鍵方法：
        - [x] `fetch_balance()`: 回傳本地紀錄的虛擬餘額 (初始 10,000 USDT)。
        - [x] `fetch_ticker()`: 回傳真實市場價格 (用於計算損益)。
        - [x] `create_order()`: 接收訂單，計算成交金額，並寫入 JSON 檔案作為「影子帳本」。
        - [x] `get_order_history()`: 查詢訂單歷史。
        - [x] `calculate_unrealized_pnl()`: 計算未實現盈虧。
        - [x] `get_portfolio_summary()`: 獲取投資組合摘要。
    - [x] **Ledger:** 使用 JSON 文件記錄持倉與資金流水（支持狀態持久化）。

- [x] **Execution Integration (執行層整合)**
    - [x] 修改 `app/core/execution/trader.py` 的 `__init__`：
        - [x] 若 `config.TRADING_MODE == 'PAPER'`，自動初始化 `PaperExchange`。
        - [x] 若 `config.TRADING_MODE == 'LIVE'`，初始化真實 `ccxt.binance`。
        - [x] 添加 `from_config()` 工廠方法便捷創建。
        - [x] 添加 `_detect_trading_mode()` 自動識別交易模式。

## Phase 3.9: System Entry Point (系統入口)
**目標：** 整合上述所有功能，建立統一的啟動腳本。

- [ ] **The Bot Script**
    - [ ] 建立根目錄檔案 `bot.py`：
        - [ ] 初始化 Flask App Context (為了存取 DB)。
        - [ ] 啟動 Scheduler。
        - [ ] 進入無窮迴圈 (`while True: time.sleep(1)`) 維持程序存活，並捕捉 `KeyboardInterrupt` 進行優雅關閉。

- [ ] **Docker Deployment**
    - [ ] 修改 `docker-compose.yml`，新增服務 `bot`：
        - [ ] Command: `python bot.py`
        - [ ] Restart: `always`
        - [ ] 依賴 `db` 與 `redis`。

## Validation (驗證項目)
- [ ] **Local Simulation Run:**
    1. 設定 `.env` 為 `PAPER` 模式。
    2. 執行 `python bot.py`。
    3. 觀察 Log：每分鐘是否自動印出 "Market Data Updated" 與 "Scanning Signals..."。
    4. 手動觸發一個信號，檢查是否在 `data/paper_ledger.json` (或類似位置) 產生了一筆虛擬交易。
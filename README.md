# HighFreqQuant 交易系統 - 架構說明

## 📁 專案結構（Phase 1.5 完成）

```
d:\01_Project\260101_Crypto/
├── app/                          # 應用程式核心
│   ├── api/                      # API 路由層
│   │   ├── routes.py            # REST API 端點
│   │   └── __init__.py
│   ├── core/                     # 核心業務邏輯
│   │   ├── data/                # 數據層（抓取、清洗）
│   │   │   ├── fetcher.py       # CCXT 市場數據抓取 (含 BinanceFetcher)
│   │   │   └── cleaner.py       # 數據清洗與重採樣
│   │   ├── execution/           # 執行層
│   │   │   ├── trader.py        # 交易執行器（止盈止損）
│   │   │   └── notifier.py      # LINE Bot 通知器
│   │   ├── risk/                # 風險管理
│   │   │   └── kelly.py         # Kelly Criterion 計算器
│   │   └── strategy/            # 策略引擎
│   │       ├── factors.py       # Alpha 因子計算
│   │       ├── backtest.py      # VectorBT 回測引擎 (Phase 1.5)
│   │       └── engine.py        # 策略引擎
│   ├── dashboard/               # Streamlit 儀表板 (Phase 1.5)
│   │   ├── app.py              # 主儀表板應用
│   │   └── __init__.py
│   ├── models/                   # 資料庫模型
│   │   ├── market.py            # OHLCV K線數據
│   │   ├── onchain.py           # 鏈上指標（Netflow, SOPR）
│   │   └── __init__.py
│   ├── tasks/                    # (保留) Celery 異步任務
│   ├── extensions.py            # Flask 擴展初始化
│   └── __init__.py              # App Factory
│
├── tests/                        # 測試套件
│   ├── unit/                    # 單元測試
│   │   ├── test_kelly.py        # Kelly Criterion 測試
│   │   ├── test_factors.py      # Alpha Factors 測試
│   │   ├── test_trader.py       # TradeExecutor 測試
│   │   └── test_fetcher.py      # Fetcher 測試
│   ├── integration/             # (保留) 整合測試
│   ├── conftest.py              # Pytest 配置
│   └── __init__.py
│
├── scripts/                      # 工具腳本
│   ├── seed_data.py             # 數據種子腳本 (Phase 1.5)
│   └── verify_system.py         # 統一系統驗證腳本
│
├── notebooks/                    # (保留) Jupyter 研究筆記
│
├── openspec/                     # OpenSpec 規範文件
│   ├── AGENTS.md
│   ├── project.md
│   └── changes/
│       └── master-roadmap/
│           └── task.md          # Phase 1-4 任務清單
│
├── migrations/                   # Flask-Migrate 資料庫遷移
│
├── data/                         # 數據目錄（已忽略）
│   ├── mysql/                   # MySQL 數據持久化
│   └── redis/                   # Redis 持久化
│
├── logs/                         # 日誌目錄（已忽略）
│
├── .env                          # 環境變數（已忽略）
├── .env.example                  # 環境變數範本
├── .gitignore                    # Git 忽略規則
├── .dockerignore                 # Docker 忽略規則
├── docker-compose.yml            # Docker 服務編排 (含 dashboard)
├── Dockerfile                    # Docker 映像定義
├── requirements.txt              # Python 依賴（完整版）
├── requirements-core.txt         # Python 依賴（核心版）
├── pytest.ini                    # Pytest 配置
└── README.md                     # 本文件
```

---

## 🧹 清理內容總結

### ✅ 已刪除的文件

1. **重複的測試腳本**
   - ❌ `scripts/test_kelly.py` → 已有 `tests/unit/test_kelly.py`
   - ❌ `scripts/test_kelly_simple.py` → 已有標準 pytest 測試

2. **分散的驗證腳本**
   - ❌ `scripts/verify_phase1.py`
   - ❌ `scripts/verify_phase2.py`
   - ❌ `scripts/verify_phase3.py`
   - ✅ 統一為 `scripts/verify_system.py`

3. **錯誤創建的目錄**
   - ❌ `scripts/init_db.sql/` (空目錄)

4. **Python 快取**
   - ❌ 所有 `__pycache__/` 目錄

### ✅ 已優化的文件

1. **requirements.txt**
   - 將非核心依賴註解（ML、回測、鏈上數據）
   - 分類整理（框架、資料庫、科學計算等）
   - 創建 `requirements-core.txt` 用於生產環境

2. **.gitignore**
   - 新增完整的 Python、IDE、OS 忽略規則
   - 保護敏感資料（.env, *.key, *.pem）
   - 忽略數據與日誌目錄

3. **.dockerignore**
   - 已存在且配置良好

---

## 🚀 依賴管理策略

### 核心依賴（requirements-core.txt）
用於生產環境，僅包含必要套件：
```bash
pip install -r requirements-core.txt
```

### 完整依賴（requirements.txt）
用於開發環境，包含所有可選功能：
```bash
pip install -r requirements.txt
```

### 階段性依賴

**Phase 1-3（已實現）**：
- Flask + SQLAlchemy（Web 框架）
- MySQL + Redis（資料庫與快取）
- CCXT（交易所 API）
- Pandas + NumPy（數據處理）
- LINE Bot SDK（通知）

**Phase 4（待實現）**：
- Celery（異步任務）
- Web3 + Dune（鏈上數據）
- VectorBT（回測）
- Transformers（AI 分析）

---

## 📊 代碼品質保證

### 當前狀態
- ✅ 無重複代碼
- ✅ 無未使用的檔案
- ✅ 標準 Pytest 測試架構
- ✅ 清晰的模組分離（MVC 模式）

### 測試覆蓋率
```bash
# 執行所有測試
pytest tests/

# 執行特定測試
pytest tests/unit/test_kelly.py -v

# 生成覆蓋率報告
pytest --cov=app --cov-report=html
```

### 系統驗證
```bash
# Docker 環境中執行統一驗證
docker-compose exec app python /app/scripts/verify_system.py

# 本地環境執行
python scripts/verify_system.py
```

---

## 🔧 開發建議

### 新增功能時
1. 確保在正確的模組中（data/strategy/risk/execution）
2. 先寫測試（TDD）
3. 更新 `scripts/verify_system.py` 加入驗證
4. 更新 `openspec/changes/master-roadmap/task.md`

### 避免的反模式
- ❌ 在 scripts/ 中放測試代碼（應放在 tests/）
- ❌ 重複的資料庫模型定義
- ❌ 混淆業務邏輯與 API 層
- ❌ 將大量依賴放入核心 requirements

---

## 📈 下一步

### Phase 2 待完成
- [ ] 策略引擎整合（`app/core/strategy/engine.py`）
- [ ] 回測框架（`notebooks/vectorbt_runner.ipynb`）

### Phase 4 安全與部署
- [ ] Celery 任務隊列
- [ ] 冷錢包監控（watchdog.py）
- [ ] Nginx + Fail2ban
- [ ] CI/CD Pipeline

---

## 🎯 Clean Code 原則

本專案遵循：
1. **單一職責原則**：每個模組只做一件事
2. **DRY（Don't Repeat Yourself）**：避免重複代碼
3. **明確的依賴管理**：核心 vs 可選
4. **測試驅動開發（TDD）**：先寫測試再實現
5. **清晰的目錄結構**：按功能分層

---

**版本**: Phase 1.5 完成
**最後更新**: 2025-12-31
**維護者**: AI Agent (Claude Opus 4.5)

---

## 🚀 Phase 1.5: Local MVP & Visualization

### 新增功能

1. **Streamlit Dashboard** (`app/dashboard/app.py`)
   - 📈 市場數據頁籤：K線圖 + 布林帶 + RSI
   - 🎯 回測結果頁籤：資金曲線 + 績效指標
   - ⚡ 交易信號頁籤：Kelly 持倉 + 恐慌指數

2. **VectorBT 回測引擎** (`app/core/strategy/backtest.py`)
   - RSI 超買超賣策略
   - 布林帶突破策略
   - 完整績效計算（夏普比率、最大回撤、勝率）

3. **BinanceFetcher** (`app/core/data/fetcher.py`)
   - 同步版本的數據獲取器
   - 支援 500+ 筆 K 線下載
   - 自動儲存到 MySQL

4. **數據種子腳本** (`scripts/seed_data.py`)
   - 一鍵獲取 BTC/USDT、ETH/USDT 數據
   - 支援命令列參數

### Docker 服務

```yaml
services:
  app:       # Flask API (Port 5000)
  dashboard: # Streamlit Dashboard (Port 8501)
  db:        # MySQL 8.0 (Port 3307)
  cache:     # Redis (內部)
  ngrok:     # 公開隧道 (Port 4040)
```

### 啟動方式

```bash
# 啟動所有服務
docker-compose up -d

# 訪問 Dashboard
http://localhost:8501

# 查看 Flask API
http://localhost:5000/health
```

### 使用流程

1. **啟動服務**: `docker-compose up -d`
2. **打開 Dashboard**: http://localhost:8501
3. **獲取數據**: 點擊側邊欄「獲取最新數據」
4. **查看圖表**: 切換到「市場數據」頁籤
5. **執行回測**: 切換到「回測結果」頁籤，點擊「執行回測」
6. **查看信號**: 切換到「交易信號」頁籤

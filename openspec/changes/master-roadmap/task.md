# Tasks: HighFreqQuant Master Implementation Roadmap

## Context
This is the master plan for the "High Alpha, Low Risk" trading system.
We will execute this in strict sequential phases to ensure TDD and Security protocols are met.

## Phase 1: Infrastructure & Data Foundation
Goal: Setup Docker, Database, and secure Data Ingestion.
Target Folder: `docker/`, `app/models/`, `app/core/data/`

- [x] **Docker Environment Setup**
    - [x] Create `docker-compose.yml` with services: `app` (Python 3.11), `db` (MySQL 8.0), `redis` (Cache).
    - [x] Create `Dockerfile` (optimized for pandas/numpy/scipy compilation).
    - [x] Configure `.env.example` (API keys, DB credentials placeholders).
- [x] **Database Schema (SQLAlchemy)**
    - [x] Implement `app/models/market.py`: `OHLCV` table (index on `timestamp`, `symbol`).
    - [x] Implement `app/models/onchain.py`: `ChainMetric` table (Exchange Netflow, SOPR).
    - [x] Setup `app/extensions.py` and `migrations/` env.
- [x] **Data Pipeline (TDD)**
    - [x] **Test:** Create `tests/unit/test_fetcher.py` mocking `ccxt` response.
    - [x] Implement `app/core/data/fetcher.py`: `MarketFetcher` class (Async CCXT).
    - [x] Implement `app/core/data/cleaner.py`: Resampling logic (1min intervals) handling missing data.

## Phase 1.5: Local MVP & Visualization (Current Focus)
Goal: Build a local dashboard to visualize Data, Signals, and Backtest results immediately.
Target Folder: `app/dashboard/`, `scripts/`

- [x] **Infrastructure Update (Dashboard)**
    - [x] **Modify** `docker-compose.yml`: Add `dashboard` service (Streamlit) exposing port `8501`.
    - [x] **Volume:** Mount `./app:/app` to allow hot-reloading.
- [x] **Data Ingestion (Binance)**
    - [x] **Implement** `app/core/data/fetcher.py`: Ensure `BinanceFetcher` can download 500+ candles via CCXT.
    - [x] **Create** `scripts/seed_data.py`: A script to fetch latest BTC/USDT & ETH/USDT data and insert into MySQL `MarketData`.
- [x] **Backtesting Engine (VectorBT)**
    - [x] **Implement** `app/core/strategy/backtest.py`:
        - [x] Load data from MySQL using pandas.
        - [x] Calculate RSI & Bollinger Bands using `vectorbt` or `pandas`.
        - [x] Run a simple strategy (RSI < 30 Buy, RSI > 70 Sell).
        - [x] Return Performance Metrics (Sharpe, Drawdown, Win Rate) and Equity Curve.
- [x] **Streamlit Dashboard**
    - [x] **Implement** `app/dashboard/app.py`:
        - [x] **Sidebar:** "Fetch Latest Data" button (calls `seed_data` logic).
        - [x] **Tab 1 (Market):** Candlestick Chart (Plotly) with BBands overlay.
        - [x] **Tab 2 (Backtest):** Run Backtest button -> Show Equity Curve & Metrics Cards.
        - [x] **Tab 3 (Signal):** Show current "Kelly Position Size" and "Panic Score".

## Phase 2: Strategy Engine & Risk Control
Goal: Implement the Alpha Logic and Kelly Criterion.
Target Folder: `app/core/strategy/`, `app/core/risk/`

- [x] **Alpha Factors**
    - [x] **Test:** Create `tests/unit/test_factors.py` with known input/output.
    - [x] Implement `app/core/strategy/factors.py`: RSI, Bollinger Width, On-Chain Z-Score.
    - [x] Implement `app/core/strategy/engine.py`: `CompositeScore` calculation logic.
- [x] **Risk Management (Kelly Criterion)**
    - [x] **Test:** Create `tests/unit/test_kelly.py` (Verify 0 position on 0 win rate).
    - [x] Implement `app/core/risk/kelly.py`: Dynamic position sizing based on volatility.

## Phase 3: Execution & LineBot
Goal: Connect the brain to the hands (Flask + Line) and enable Public Webhook.
Target Folder: `app/api/`, `app/core/execution/`

- [ ] **Public Access (Ngrok)**
    - [ ] Add `ngrok` service to `docker-compose.yml` (expose port 4040).
- [ ] **Flask API Server**
    - [ ] Implement `app/__init__.py`: App Factory pattern.
    - [ ] Create `app/api/routes.py`: Endpoints for `/webhook` and `/health`.
- [ ] **LineBot Integration**
    - [ ] Implement `app/core/execution/notifier.py`: Alert system wrapper.
    - [ ] Add command handler: `/status`, `/stop`, `/panic`.
- [ ] **Trade Executor (The "Safe" Hands)**
    - [ ] Implement `app/core/execution/trader.py`: Order placement logic.
    - [ ] **Security:** Add "Pre-Flight Check" (PanicScore < Threshold) before executing any buy order.

## Phase 4: Security & Deployment
Goal: Hardening for production.
Target Folder: `scripts/`, `deploy/`

- [ ] **Security Ops**
    - [ ] Setup `bandit` and `safety` in CI/CD.
    - [ ] Implement `scripts/watchdog.py`: Cold Wallet Auto-Sweeper.
- [ ] **Deployment**
    - [ ] Configure `nginx` conf with rate limiting.
    - [ ] Setup `fail2ban`.
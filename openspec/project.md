# Project: HighFreqQuant (Sovereign-Grade Quantitative Trading System)

## 1. Mission & Vision
To build a high-performance, low-risk cryptocurrency algorithmic trading system that operates with the discipline of an institutional desk but the agility of a sovereign individual.
The core philosophy is **"Information Advantage + Mathematical Defense"**.

- **High Alpha:** Derived from multi-factor analysis (Technical + On-Chain Chips + Sentiment).
- **Low Risk:** Enforced by the Kelly Criterion and rigorous volatility targeting.
- **Security:** Zero-trust architecture with cold wallet isolation.

## 2. System Architecture
The system is divided into five strictly coordinated layers:

### A. Data Infrastructure (The Foundation)
- **Market Data:** Minute-level OHLCV from Binance/Bybit via `ccxt`.
- **On-Chain Data:** Exchange Netflow, SOPR from Glassnode via `requests`.
- **Incremental Crawler:** Automated job fetching *only* the latest missing candles/blocks to minimize API usage.
- **Storage:**
  - **MySQL 8.0:** Persistent storage for Time-Series data, Trade Logs, and Paper Ledgers.
  - **Redis:** Hot cache for real-time signals and job locks.

### B. The Heartbeat (The Driver) [NEW]
- **Scheduler:** `APScheduler` (BackgroundScheduler) running in the main process.
- **Jobs:**
  - `job_update_market_data` (Every 1 min): Fetches data -> Updates DB.
  - `job_scan_signals` (Every 1 min): Reads DB -> Calcs Alpha -> Triggers Execution.
  - `job_risk_monitor` (Every 10 sec): Checks Stop-Loss/Take-Profit conditions.

### C. Strategy Engine (The Brain)
- **Research:** `VectorBT` for high-speed parameter sweeping (vectorized backtesting).
- **Logic:** A Composite Alpha Score (0-100) combining:
  1.  **Technical (40%):** RSI, Bollinger Bands, Volatility.
  2.  **Chips (35%):** Exchange Inflow/Outflow, Long-Term Holder SOPR.
  3.  **Sentiment (15%):** Panic Score (CryptoPanic).

### D. Execution & Interface (The Hands)
- **Modes:**
  - **PAPER (Default):** Virtual execution using a local ledger (SQLite/JSON). No real money involved.
  - **LIVE:** Real execution via Exchange API. Requires manual env flag override.
- **Order Management:**
  - Kelly Criterion Sizing (Half-Kelly).
  - "Panic Switch": Blocks buying if market sentiment is too fearful.

### E. Security & DevOps (The Shield)
- **Environment:** Docker containers running on a secure VPS.
- **Secrets:** Managed via `.env` (Never committed).
- **Watchdog:** Independent process monitoring system health and cold wallet auto-sweeping.

## 3. Key Performance Indicators (KPIs)
- **Sharpe Ratio:** > 2.0 (Verified via Paper Trading & Backtest)
- **Max Drawdown:** < 15%
- **Win Rate:** Target > 55%
- **Latency:** Strategy calculation < 500ms after candle close.

## 4. Development Guidelines
- **TDD First:** No implementation without a failing unit test.
- **Safety Default:** System must crash-safe (graceful shutdown) and default to PAPER mode.
- **Documentation:** All modules must explain the *financial logic*.
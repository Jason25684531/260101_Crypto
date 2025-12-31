# Project: HighFreqQuant (Sovereign-Grade Quantitative Trading System)

## 1. Mission & Vision
To build a high-performance, low-risk cryptocurrency algorithmic trading system that operates with the discipline of an institutional desk but the agility of a sovereign individual.
The core philosophy is **"Information Advantage + Mathematical Defense"**.

- **High Alpha:** Derived from multi-factor analysis (Technical + On-Chain Chips + Sentiment).
- **Low Risk:** Enforced by the Kelly Criterion and rigorous volatility targeting.
- **Security:** Zero-trust architecture with cold wallet isolation.

## 2. System Architecture
The system is divided into four strictly isolated layers:

### A. Data Infrastructure (The Foundation)
- **Market Data:** Minute-level OHLCV from Binance/Bybit via `ccxt`.
- **On-Chain Data:** Exchange Netflow, SOPR, and Whale Alerts from Glassnode/Dune via `requests`.
- **Storage:**
  - **MySQL 8.0:** Persistent storage for Time-Series data and Trade Logs.
  - **Redis:** Hot cache for real-time signals and Celery task broker.

### B. Strategy Engine (The Brain)
- **Research:** `VectorBT` for high-speed parameter sweeping (vectorized backtesting).
- **Validation:** `Backtrader` for event-driven simulation (considering slippage & fees).
- **Logic:** A Composite Alpha Score (0-100) combining:
  1.  **Technical (40%):** RSI, Bollinger Bands, Volatility.
  2.  **Chips (35%):** Exchange Inflow/Outflow, Long-Term Holder SOPR.
  3.  **Sentiment (15%):** CryptoPanic Score, Funding Rates.

### C. Execution & Interface (The Hands)
- **Backend:** Python Flask (REST API).
- **Bot Interface:** Line Messaging API for 2-way communication (Alerts & Commands).
- **Order Management:**
  - Safe-guard checks (Panic Score threshold).
  - API Key rotation logic.
  - **"Watchdog":** Independent process monitoring exchange balance for auto-sweeping to Cold Wallet.

### D. Security & DevOps (The Shield)
- **Environment:** Docker containers running on a secure VPS (AWS/DigitalOcean).
- **Secrets:** Managed via `.env` (Never committed).
- **Hardening:** Fail2Ban, IP Whitelisting, and read-only API keys where possible.

## 3. Key Performance Indicators (KPIs)
- **Sharpe Ratio:** > 2.0
- **Max Drawdown:** < 15%
- **Win Rate:** Target > 55% (with R:R ratio > 1:1.5)
- **Uptime:** 99.9% (Auto-restart via Docker)

## 4. Development Guidelines
- **TDD First:** No implementation without a failing unit test.
- **Type Strict:** All Python code must use `typing` hints.
- **Documentation:** All modules must have docstrings explaining the *financial logic*, not just code logic.
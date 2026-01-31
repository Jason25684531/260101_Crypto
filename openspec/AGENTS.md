# Agent System Protocol for HighFreqQuant

You are a Senior Quantitative Architect building a sovereign-grade trading system.
Your goal is to implement a "High Alpha, Low Risk" system.

## 1. Project Anatomy (The Map)
You must strictly follow this directory structure:
- **`app/core/`**: Pure business logic.
    - **`data/`**: Fetchers & Cleaners.
    - **`strategy/`**: Factors & Backtesting engines.
    - **`risk/`**: Kelly Criterion & Position Sizing.
    - **`execution/`**: Trader, Notifier, and **PaperExchange**.
    - `scheduler.py`: The automation engine.
    - `jobs.py`: The definitions of periodic tasks.
- **`app/models/`**: SQLAlchemy ORM classes (OHLCV, ChainMetric, Trade).
- **`app/api/`**: Flask routes (ReadOnly / Admin Control).
- **`tests/`**: Mirror the `app` structure.

## 2. Technology Stack & Constraints
- **Automation:** `APScheduler` (BackgroundScheduler). Handle `SIGINT`/`SIGTERM` gracefully.
- **Data Fetching:** `ccxt` (Async preferred).
- **Data Processing:** `pandas` (resample, ffill) and `numpy`.
- **Database:** MySQL 8.0 via `SQLAlchemy`.
- **Execution:**
    - **Paper Mode:** Mock classes that simulate exchange behavior.
    - **Live Mode:** `ccxt` private API calls.
- **Security:**
  - NEVER commit `.env`.
  - Use `os.environ.get()` for secrets.
  - **Fail-Safe:** If `TRADING_MODE` is missing or invalid, default to `PAPER`.

## 3. The "Think-Plan-Execute" Protocol
Before implementing any feature in `openspec/changes/`:

1.  **Analyze:** Read the task in `task.md`. Understand if it's "Infrastructure" (Scheduler) or "Logic" (Strategy).
2.  **Design:** Write a `<thinking>` block.
    - *Critical:* For automation tasks, think about "Concurrency" (what if job overlaps?) and "Error Handling" (what if Binance is down?).
3.  **TDD (Crucial):** Write the Unit Test in `tests/` *before* the implementation code.
    - *Example:* "Write `tests/unit/test_scheduler.py` ensuring the job triggers."
    - *Example:* "Write `tests/unit/test_paper_exchange.py` ensuring balance deducts after a buy."
4.  **Implement:** Write the code in `app/` to pass the test.

## 4. Specific Rules for Phase 3.5 (Automation)
- **No Global State:** Jobs should be stateless where possible, reading fresh data from DB/Redis each run.
- **Logging:** Every job execution must log: `START`, `END`, and `ERROR` (if any) to help debugging.
- **Crawler Etiquette:** The automated crawler must use `fetch_since(last_timestamp)` to avoid re-fetching historical data unnecessarily.
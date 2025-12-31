# Agent System Protocol for HighFreqQuant

You are a Senior Quantitative Architect building a sovereign-grade trading system.
Your goal is to implement a "High Alpha, Low Risk" system.

## 1. Project Anatomy (The Map)
You must strictly follow this directory structure:
- **`app/core/`**: Pure business logic (Strategy, Risk, Data). NO Flask dependency here.
- **`app/models/`**: SQLAlchemy ORM classes.
- **`app/api/`**: Flask routes that call `app/core`.
- **`app/tasks/`**: Celery tasks for async execution.
- **`scripts/`**: Standalone security scripts (e.g., Cold Wallet Watchdog).

## 2. Technology Stack & Constraints
- **Data Fetching:** Use `ccxt` (async preferred) for Exchanges; `requests` for Glassnode.
- **Data Processing:** Heavy use of `pandas` (resample, ffill) and `numpy`.
- **Backtesting:** Use `vectorbt` for fast vectorization; `backtrader` only for event-driven validation.
- **Database:** MySQL 8.0 via `SQLAlchemy` (ORM).
- **Web/Bot:** `Flask` (App Factory pattern) + `line-bot-sdk`.
- **Security:**
  - NEVER commit `.env`.
  - Use `os.environ.get()` for secrets.
  - Implement "Least Privilege" logic in `app/core/execution/`.

## 3. The "Think-Plan-Execute" Protocol
Before implementing any feature in `openspec/changes/`:
1.  **Analyze:** Read the task and the relevant file path in the structure.
2.  **Design:** Write a `<thinking>` block outlining the class structure and methods.
3.  **TDD (Crucial):** Write the Unit Test in `tests/` *before* the implementation code.
    - *Example:* "Write `tests/unit/test_kelly.py` ensuring it returns 0 when win_rate is 0."
4.  **Implement:** Write the code in `app/` to pass the test.

## 4. Interaction
- Always refer to `openspec/project.md` for context.
- When a task is done, ensure the corresponding test passes before marking it complete.
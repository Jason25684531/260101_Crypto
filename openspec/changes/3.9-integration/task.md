# Tasks: Phase 3.9 System Entry Point & Deployment

## Context
All core components (Data, Strategy, Execution, Scheduler) are built.
We now need a single entry point script (`bot.py`) to launch the automated trading system.
We also need to update Docker to run this bot alongside the API and Dashboard.

## Phase 3.9: The Bot Entry Point
Goal: Create the main executable that runs the scheduler and keeps the process alive.

- [ ] **Create `bot.py` (Root Directory)**
    - [ ] **Imports:** `create_app`, `scheduler`, `signal`, `time`.
    - [ ] **Setup:**
        - Initialize Flask `app = create_app()`.
        - Use `app.app_context()` to ensure DB connections work inside jobs.
    - [ ] **Startup Logic:**
        - Call `scheduler.setup_all_jobs()`.
        - Call `scheduler.start()`.
        - Print a "System Online" banner with current configuration (Mode: PAPER/LIVE).
    - [ ] **Keep-Alive Loop:**
        - Implement a `while True: time.sleep(1)` loop.
        - Handle `SIGINT` (Ctrl+C) and `SIGTERM` to call `scheduler.shutdown()` gracefully.

- [ ] **Docker Integration**
    - [ ] **Update `docker-compose.yml`:**
        - Add a new service named `bot`.
        - Build: same as `web`.
        - Command: `python bot.py`.
        - Environment: Load from `.env`.
        - Depends_on: `db`, `redis`.
        - Restart: `unless-stopped`.

## Validation
- [ ] **Local Run Test:**
    - Run `python bot.py` locally.
    - Verify logs show:
        1. "Trading Mode: PAPER"
        2. "Scheduler Started"
        3. "Job job_update_market_data scheduled"
    - Wait 2 minutes. Check DB `ohlcv` table to see if new data arrived.
    - Press Ctrl+C and verify "Graceful Shutdown" message.

- [ ] **Docker Run Test:**
    - Run `docker-compose up -d --build bot`.
    - Run `docker-compose logs -f bot`.
    - Verify system operates inside the container.
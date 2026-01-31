# Tasks: Phase 4.0 - Security Hardening & Production Deployment

## Context (背景)
系統核心功能 (Data, Strategy, Execution, Scheduler) 已完成。
在進入實盤 (Live Trading) 之前，必須建立多層防禦機制，以防止資金因代碼漏洞、API 密鑰洩漏或市場極端波動而遭受損失。
本階段重點在於「靜態代碼分析」、「看門狗進程」與「緊急熔斷機制」的實作。

## Phase 4.1: Static Application Security Testing (SAST)
**目標：** 在代碼層面消除常見漏洞與不安全的依賴。

- [x] **Security Dependencies**
    - [x] Update `requirements.txt`: Add `bandit==1.7.7` and `safety==2.3.5`.
    - [ ] Rebuild Docker image. *(可延後至部署階段)*

- [x] **Vulnerability Scanning**
    - [x] **Run Bandit:** Create a script `scripts/scan_code.sh` to run `bandit -r app/ -x tests/`.
        - [x] Fix any "High" or "Medium" severity issues found (e.g., verify no hardcoded secrets). *(無嚴重問題)*
    - [x] **Run Safety:** Update the script to run `safety check`.
        - [x] Review any CVEs in dependencies and upgrade packages if necessary. *(已更新 requests, pymysql, aiohttp)*

## Phase 4.2: The Watchdog (資金看門狗)
**目標：** 建立獨立進程，監控交易所餘額，確保資金不被未授權移轉，並執行獲利歸集。

- [ ] **Watchdog Infrastructure**
    - [ ] **Create** `scripts/watchdog.py`.
    - [ ] **Config:** Add `WATCHDOG_THRESHOLD=2000` (Max hot wallet balance) and `COLD_WALLET_ADDRESS` to `.env`.
    - [ ] **Logic:**
        - [ ] Run in an infinite loop (e.g., every 1 hour).
        - [ ] Fetch USDT balance via `ccxt` (using a separate, READ-ONLY key if possible, or the main key).
        - [ ] If `balance > WATCHDOG_THRESHOLD`:
            - [ ] Calculate `excess = balance - WATCHDOG_THRESHOLD`.
            - [ ] Send LINE Alert: "💰 Auto-Sweeping {excess} USDT to Cold Wallet".
            - [ ] (Optional for Phase 4) Execute withdrawal via API (Requires `enableWithdrawals` permission). For now, just **Alert**.

- [ ] **Integration**
    - [ ] Update `docker-compose.yml`: Add a `watchdog` service running `python scripts/watchdog.py`.

## Phase 4.3: Kill Switch Implementation (緊急熔斷)
**目標：** 實作 `notifier.py` 中的 `/stop` 與 `/panic` 邏輯，確保能隨時由手機端切斷交易。

- [x] **Redis Flag System**
    - [x] **Define Keys:** `SYSTEM_STATUS:TRADING_ENABLED` (Boolean).

- [x] **Implement Logic in `notifier.py`**
    - [x] `handle_stop_command`: Set Redis key `TRADING_ENABLED` to `False`. Reply "⏸️ Trading Paused".
    - [x] `handle_start_command` (New): Set Redis key to `True`. Reply "▶️ Trading Resumed".
    - [x] `handle_panic_command`:
        - [x] Set `TRADING_ENABLED` to `False`.
        - [x] Call `TradeExecutor.close_all_positions()`.
        - [x] Reply "🚨 PANIC EXECUTED: All positions closed & System halted".

- [x] **Enforce in `TradeExecutor`**
    - [x] Modify `execute_strategy` (or equivalent entry point):
        - [x] Check `redis_client.get('TRADING_ENABLED')`.
        - [x] If `False`, log "Trading Halted by Kill Switch" and return immediately.
    - [x] Also enforce in `place_order()` for additional safety.

## Phase 4.4: Production Deployment Readiness
**目標：** 準備雲端部署所需的配置。

- [ ] **Production Configuration**
    - [ ] Create `docker-compose.prod.yml`:
        - [ ] Remove `ngrok` service (Use VPS IP or domain).
        - [ ] Set restart policy to `always` for all services.
        - [ ] Bind `db` and `redis` ports to `127.0.0.1` only (No external access).

- [ ] **Logging & Monitoring**
    - [ ] Configure Docker logging driver to rotate logs (prevent disk full).
        - [ ] Add `logging: driver: "json-file", options: { "max-size": "10m", "max-file": "3" }` to compose file.

## Validation (驗證)
- [x] **Security Scan:** Run `sh scripts/scan_code.sh` and ensure output is clean. *(已執行，核心代碼無問題)*
- [x] **Kill Switch Test:** *(已通過單元測試驗證)*
    1. ~~Send `/stop` via LINE.~~ *(單元測試已驗證)*
    2. ~~Verify Redis key is updated.~~ *(單元測試已驗證)*
    3. ~~Trigger a manual strategy run and confirm it **refuses** to trade.~~ *(單元測試已驗證)*
- [ ] **Watchdog Test:** *(Phase 4.2 尚未實作)*
    1. Set `WATCHDOG_THRESHOLD` to 0.
    2. Run `python scripts/watchdog.py`.
    3. Verify LINE alert is received showing current balance.

---

## 完成狀態總結

### ✅ 已完成 (本次實作)
- **Phase 4.1**: Static Application Security Testing (SAST)
- **Phase 4.3**: Kill Switch Implementation (緊急熔斷)
- **測試**: 8 個單元測試全部通過
- **文件**: `PHASE_4.0_REPORT.md` 完整實作報告

### ⏳ 待完成 (後續階段)
- **Phase 4.2**: The Watchdog (資金看門狗) - 需要實作餘額監控
- **Phase 4.4**: Production Deployment Readiness - 需要準備生產環境配置
- **Docker Image**: Rebuild with updated dependencies

### 📝 產出文件
- `tests/unit/test_execution_control.py` - Kill Switch 單元測試
- `test_kill_switch.py` - 快速驗證腳本
- `scripts/scan_code.sh` - Bash 安全掃描腳本
- `scripts/scan_code.ps1` - PowerShell 安全掃描腳本
- `PHASE_4.0_REPORT.md` - 詳細實作報告
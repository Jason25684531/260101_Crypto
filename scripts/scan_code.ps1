# 安全掃描腳本 - 執行 Bandit 和 Safety 檢查

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Phase 4.0: Security Scanning" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Bandit - 靜態代碼分析
Write-Host "🔍 Running Bandit (Static Code Analysis)..." -ForegroundColor Yellow
Write-Host "------------------------------------------"
bandit -r app/ -x tests/ -f screen
Write-Host ""

# 2. Safety - 依賴漏洞檢查
Write-Host "🛡️  Running Safety (Dependency Vulnerability Check)..." -ForegroundColor Yellow
Write-Host "------------------------------------------"
safety check
Write-Host ""

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Security Scan Complete" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

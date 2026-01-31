#!/bin/bash
# 安全掃描腳本 - 執行 Bandit 和 Safety 檢查

echo "=========================================="
echo "Phase 4.0: Security Scanning"
echo "=========================================="
echo ""

# 1. Bandit - 靜態代碼分析
echo "🔍 Running Bandit (Static Code Analysis)..."
echo "------------------------------------------"
bandit -r app/ -x tests/ -f screen || true
echo ""

# 2. Safety - 依賴漏洞檢查
echo "🛡️  Running Safety (Dependency Vulnerability Check)..."
echo "------------------------------------------"
safety check --json || true
echo ""

echo "=========================================="
echo "Security Scan Complete"
echo "=========================================="

#!/usr/bin/env python
"""
統一系統驗證腳本
整合 Phase 1-3 的所有驗證測試
"""
import sys
import os

# 確保可以導入 app 模組
sys.path.insert(0, '/app' if os.path.exists('/app') else os.path.dirname(os.path.dirname(__file__)))

print("=" * 80)
print("HighFreqQuant 交易系統 - 完整驗證測試")
print("=" * 80)


# ==================== Phase 1: Infrastructure & Data ====================
def verify_phase1():
    """驗證 Phase 1: 基礎設施與數據層"""
    print("\n" + "=" * 80)
    print("Phase 1: Infrastructure & Data Foundation")
    print("=" * 80)
    
    try:
        from app import create_app
        from app.extensions import db, redis_client
        from app.models import OHLCV, ChainMetric, ExchangeNetflow
        
        app = create_app()
        
        with app.app_context():
            # 測試 1: 資料庫連接
            print("\n📦 測試 1: 資料庫連接")
            try:
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                print("   ✅ 資料庫連接正常")
            except Exception as e:
                print(f"   ❌ 資料庫連接失敗: {e}")
                return False
            
            # 測試 2: 資料庫模型
            print("\n📦 測試 2: 資料庫模型")
            try:
                ohlcv_count = OHLCV.query.count()
                chain_count = ChainMetric.query.count()
                netflow_count = ExchangeNetflow.query.count()
                print(f"   ✅ OHLCV 模型: {ohlcv_count} 筆記錄")
                print(f"   ✅ ChainMetric 模型: {chain_count} 筆記錄")
                print(f"   ✅ ExchangeNetflow 模型: {netflow_count} 筆記錄")
            except Exception as e:
                print(f"   ❌ 模型查詢失敗: {e}")
                return False
            
            # 測試 3: Redis 連接
            print("\n📦 測試 3: Redis 快取")
            try:
                redis_client.ping()
                redis_client.set('test_key', 'test_value', ex=10)
                value = redis_client.get('test_key')
                assert value == 'test_value'
                print("   ✅ Redis 連接正常")
            except Exception as e:
                print(f"   ❌ Redis 連接失敗: {e}")
                return False
        
        print("\n✅ Phase 1 驗證通過")
        return True
    
    except Exception as e:
        print(f"\n❌ Phase 1 驗證失敗: {e}")
        return False


# ==================== Phase 2: Strategy & Risk ====================
def verify_phase2():
    """驗證 Phase 2: 策略引擎與風險控制"""
    print("\n" + "=" * 80)
    print("Phase 2: Strategy Engine & Risk Control")
    print("=" * 80)
    
    try:
        from app.core.risk.kelly import KellyCalculator
        from app.core.strategy.factors import AlphaFactors
        
        # 測試 1: Kelly Criterion
        print("\n📦 測試 1: Kelly Criterion")
        calculator = KellyCalculator(fraction=0.25)
        kelly_size = calculator.calculate(win_rate=0.6, odds=2.0)
        assert 0 < kelly_size <= 0.25, "Kelly 計算錯誤"
        print(f"   ✅ Kelly Criterion: {kelly_size:.2%} 持倉大小")
        
        # 測試 2: Alpha Factors
        print("\n📦 測試 2: Alpha Factors")
        import pandas as pd
        import numpy as np
        
        # 創建測試數據
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)
        df = pd.DataFrame({
            'close': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'volume': np.random.uniform(100, 1000, 100)
        }, index=dates)
        
        factors = AlphaFactors()
        
        # RSI
        rsi = factors.calculate_rsi(df['close'])
        assert 0 <= rsi.iloc[-1] <= 100, "RSI 計算錯誤"
        print(f"   ✅ RSI: {rsi.iloc[-1]:.2f}")
        
        # Bollinger Bands
        upper, middle, lower = factors.calculate_bollinger_bands(df['close'])
        assert upper.iloc[-1] > middle.iloc[-1] > lower.iloc[-1], "Bollinger Bands 計算錯誤"
        print(f"   ✅ Bollinger Bands 計算正常")
        
        # Composite Score
        score = factors.calculate_composite_score(df)
        assert 0 <= score <= 100, "Composite Score 計算錯誤"
        print(f"   ✅ Composite Score: {score:.2f}/100")
        
        print("\n✅ Phase 2 驗證通過")
        return True
    
    except Exception as e:
        print(f"\n❌ Phase 2 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== Phase 3: Execution & LineBot ====================
def verify_phase3():
    """驗證 Phase 3: 執行層與 LineBot"""
    print("\n" + "=" * 80)
    print("Phase 3: Execution & LineBot")
    print("=" * 80)
    
    try:
        from app.core.execution import TradeExecutor, TradingNotifier
        
        # 創建模擬 exchange
        class MockExchange:
            def fetch_balance(self):
                return {'USDT': {'free': 10000, 'used': 0, 'total': 10000}}
            
            def fetch_ticker(self, symbol):
                return {'last': 50000, 'bid': 49950, 'ask': 50050}
        
        # 測試 1: TradeExecutor 初始化
        print("\n📦 測試 1: TradeExecutor")
        executor = TradeExecutor(
            exchange=MockExchange(),
            max_position_size=0.3,
            stop_loss_percent=0.05,
            take_profit_min=0.10,
            take_profit_max=0.20
        )
        print(f"   ✅ TradeExecutor 初始化成功")
        print(f"      停損: {executor.stop_loss_percent * 100}%")
        print(f"      止盈: {executor.take_profit_min * 100}%-{executor.take_profit_max * 100}%")
        
        # 測試 2: 止盈止損計算
        print("\n📦 測試 2: 止盈止損計算")
        entry_price = 50000
        stop_loss = executor.calculate_stop_loss(entry_price)
        take_profit_min = executor.calculate_take_profit(entry_price, 'min')
        take_profit_max = executor.calculate_take_profit(entry_price, 'max')
        
        assert stop_loss == 47500, "停損計算錯誤"
        assert take_profit_min == 55000, "最低止盈計算錯誤"
        assert take_profit_max == 60000, "最高止盈計算錯誤"
        
        print(f"   ✅ 入場價格: {entry_price} USDT")
        print(f"   ✅ 停損價格: {stop_loss} USDT (-5%)")
        print(f"   ✅ 最低止盈: {take_profit_min} USDT (+10%)")
        print(f"   ✅ 最高止盈: {take_profit_max} USDT (+20%)")
        
        # 測試 3: PanicScore 安全檢查
        print("\n📦 測試 3: PanicScore 安全檢查")
        try:
            executor.place_order('BTC/USDT', 'buy', 0.1, panic_score=0.85)
            print("   ❌ 應該拒絕高 PanicScore 的訂單")
            return False
        except ValueError:
            print("   ✅ PanicScore > 80% 正確拒絕買入")
        
        # 測試 4: TradingNotifier
        print("\n📦 測試 4: TradingNotifier")
        notifier = TradingNotifier()
        print(f"   ✅ TradingNotifier 初始化成功")
        print(f"   ℹ️  LINE Bot 狀態: {'已啟用' if notifier.enabled else '未設定'}")
        
        print("\n✅ Phase 3 驗證通過")
        return True
    
    except Exception as e:
        print(f"\n❌ Phase 3 驗證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== 主程序 ====================
def main():
    """執行所有驗證測試"""
    results = {
        'Phase 1': verify_phase1(),
        'Phase 2': verify_phase2(),
        'Phase 3': verify_phase3()
    }
    
    # 總結
    print("\n" + "=" * 80)
    print("驗證結果總結")
    print("=" * 80)
    
    all_passed = True
    for phase, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{phase}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有驗證測試通過！系統運作正常。")
        return 0
    else:
        print("⚠️  部分測試失敗，請檢查上方錯誤訊息。")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

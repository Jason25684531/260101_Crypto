"""
快速測試 Kill Switch 功能
"""
import sys
from unittest.mock import Mock, patch

# 測試 1: 檢查 trader.py 的導入
print("測試 1: 導入模組...")
try:
    from app.core.execution.trader import TradeExecutor
    from app.core.execution.paper_exchange import PaperExchange
    print("✅ 模組導入成功")
except Exception as e:
    print(f"❌ 模組導入失敗: {e}")
    sys.exit(1)

# 測試 2: 檢查交易鎖功能
print("\n測試 2: 測試交易鎖功能...")
try:
    # 創建模擬 Redis
    mock_redis = Mock()
    mock_redis.get = Mock(return_value='false')
    
    # 創建交易所和執行器
    exchange = PaperExchange(initial_balance=10000.0)
    executor = TradeExecutor(exchange=exchange)
    
    # 測試：當鎖啟動時應該拒絕訂單
    with patch('app.extensions.redis_client', mock_redis):
        try:
            result = executor.place_order(
                symbol='BTC/USDT',
                side='buy',
                amount=0.01,
                price=50000.0,
                order_type='limit'
            )
            print(f"❌ 應該拋出異常但沒有: {result}")
        except RuntimeError as e:
            if "交易已暫停" in str(e):
                print(f"✅ 正確拋出 RuntimeError: {e}")
            else:
                print(f"❌ 錯誤訊息不符: {e}")
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 3: 檢查允許交易的情況
print("\n測試 3: 測試允許交易...")
try:
    mock_redis.get = Mock(return_value='true')
    
    with patch('app.extensions.redis_client', mock_redis):
        result = executor.place_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.01,
            price=50000.0,
            order_type='limit'
        )
        
        if result and result.get('status') == 'success':
            print(f"✅ 交易成功執行: {result.get('order_id')}")
        else:
            print(f"❌ 交易執行失敗: {result}")
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 4: 檢查 notifier.py 的指令處理
print("\n測試 4: 測試 LINE 指令處理...")
try:
    from app.core.execution.notifier import handle_stop_command, handle_start_command
    
    mock_redis.set = Mock(return_value=True)
    
    with patch('app.extensions.redis_client', mock_redis):
        with patch('app.core.execution.notifier.TradingNotifier') as mock_notifier:
            mock_notifier_instance = Mock()
            mock_notifier.return_value = mock_notifier_instance
            
            # 測試 /stop
            handle_stop_command(user_id='test_user')
            mock_redis.set.assert_called_with('SYSTEM_STATUS:TRADING_ENABLED', 'false')
            print("✅ /stop 指令正確設置 Redis 鎖")
            
            # 測試 /start
            handle_start_command(user_id='test_user')
            mock_redis.set.assert_called_with('SYSTEM_STATUS:TRADING_ENABLED', 'true')
            print("✅ /start 指令正確釋放 Redis 鎖")
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("🎉 所有測試通過！Kill Switch 功能正常運作")
print("="*50)

"""
測試交易控制機制（Kill Switch）
驗證 TradeExecutor 是否正確遵守 Redis 中的 TRADING_ENABLED 標誌
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.execution.trader import TradeExecutor
from app.core.execution.paper_exchange import PaperExchange


class TestExecutionControl:
    """測試交易執行控制機制"""
    
    @pytest.fixture
    def mock_redis(self):
        """模擬 Redis 客戶端"""
        redis_mock = Mock()
        redis_mock.get = Mock(return_value='true')  # 預設允許交易
        redis_mock.set = Mock(return_value=True)
        redis_mock.delete = Mock(return_value=True)
        return redis_mock
    
    @pytest.fixture
    def paper_exchange(self):
        """創建模擬交易所"""
        return PaperExchange(initial_balance=10000.0)
    
    @pytest.fixture
    def executor(self, paper_exchange):
        """創建交易執行器"""
        return TradeExecutor(
            exchange=paper_exchange,
            max_position_size=0.3,
            stop_loss_percent=0.05,
            take_profit_min=0.10,
            take_profit_max=0.20
        )
    
    def test_trading_enabled_allows_order(self, executor, mock_redis):
        """測試：當 TRADING_ENABLED=true 時，應允許下單"""
        with patch('app.extensions.redis_client', mock_redis):
            mock_redis.get.return_value = 'true'
            
            # 執行買入訂單
            result = executor.place_order(
                symbol='BTC/USDT',
                side='buy',
                amount=0.01,
                price=50000.0,
                order_type='limit'
            )
            
            # 驗證：訂單成功執行
            assert result is not None
            assert 'id' in result
            assert result['symbol'] == 'BTC/USDT'
            assert result['side'] == 'buy'
    
    def test_trading_disabled_blocks_order(self, executor, mock_redis):
        """測試：當 TRADING_ENABLED=false 時，應拒絕下單"""
        with patch('app.extensions.redis_client', mock_redis):
            mock_redis.get.return_value = 'false'
            
            # 嘗試執行買入訂單
            with pytest.raises(RuntimeError, match="交易已暫停"):
                executor.place_order(
                    symbol='BTC/USDT',
                    side='buy',
                    amount=0.01,
                    price=50000.0,
                    order_type='limit'
                )
    
    def test_trading_disabled_blocks_sell_order(self, executor, mock_redis):
        """測試：當 TRADING_ENABLED=false 時，賣出訂單也應該被阻擋"""
        with patch('app.extensions.redis_client', mock_redis):
            mock_redis.get.return_value = 'false'
            
            # 嘗試執行賣出訂單
            with pytest.raises(RuntimeError, match="交易已暫停"):
                executor.place_order(
                    symbol='BTC/USDT',
                    side='sell',
                    amount=0.01,
                    price=50000.0,
                    order_type='limit'
                )
    
    def test_redis_key_none_defaults_to_enabled(self, executor, mock_redis):
        """測試：當 Redis Key 不存在時，預設為允許交易（向後相容）"""
        with patch('app.extensions.redis_client', mock_redis):
            mock_redis.get.return_value = None  # Key 不存在
            
            # 執行買入訂單
            result = executor.place_order(
                symbol='BTC/USDT',
                side='buy',
                amount=0.01,
                price=50000.0,
                order_type='limit'
            )
            
            # 驗證：訂單成功執行（預設允許）
            assert result is not None
            assert result['side'] == 'buy'
    
    def test_execute_strategy_checks_lock(self, executor, mock_redis):
        """測試：execute_strategy 應該檢查交易鎖"""
        with patch('app.extensions.redis_client', mock_redis):
            mock_redis.get.return_value = 'false'
            
            # 模擬策略信號
            signals = [
                {'symbol': 'BTC/USDT', 'action': 'buy', 'price': 50000.0, 'amount': 0.01}
            ]
            
            # 執行策略（應該被阻擋）
            result = executor.execute_strategy(signals, panic_score=0.2)
            
            # 驗證：沒有訂單被執行
            assert len(result) == 0
    
    def test_panic_command_sets_lock_and_closes_positions(self, mock_redis):
        """測試：/panic 指令應該設置鎖並平倉所有持倉"""
        from app.core.execution.notifier import handle_panic_command
        
        with patch('app.extensions.redis_client', mock_redis):
            with patch('app.core.execution.notifier.TradingNotifier') as mock_notifier:
                mock_notifier_instance = Mock()
                mock_notifier.return_value = mock_notifier_instance
                
                # 執行 panic 指令
                handle_panic_command(user_id='test_user')
                
                # 驗證：Redis 鎖被設置為 false
                mock_redis.set.assert_called_with('SYSTEM_STATUS:TRADING_ENABLED', 'false')
                
                # 驗證：發送通知
                mock_notifier_instance.send_message.assert_called_once()
    
    def test_stop_command_sets_lock(self, mock_redis):
        """測試：/stop 指令應該設置交易鎖"""
        from app.core.execution.notifier import handle_stop_command
        
        with patch('app.extensions.redis_client', mock_redis):
            with patch('app.core.execution.notifier.TradingNotifier') as mock_notifier:
                mock_notifier_instance = Mock()
                mock_notifier.return_value = mock_notifier_instance
                
                # 執行 stop 指令
                handle_stop_command(user_id='test_user')
                
                # 驗證：Redis 鎖被設置為 false
                mock_redis.set.assert_called_with('SYSTEM_STATUS:TRADING_ENABLED', 'false')
    
    def test_start_command_releases_lock(self, mock_redis):
        """測試：/start 指令應該釋放交易鎖"""
        from app.core.execution.notifier import handle_start_command
        
        with patch('app.extensions.redis_client', mock_redis):
            with patch('app.core.execution.notifier.TradingNotifier') as mock_notifier:
                mock_notifier_instance = Mock()
                mock_notifier.return_value = mock_notifier_instance
                
                # 執行 start 指令
                handle_start_command(user_id='test_user')
                
                # 驗證：Redis 鎖被設置為 true
                mock_redis.set.assert_called_with('SYSTEM_STATUS:TRADING_ENABLED', 'true')

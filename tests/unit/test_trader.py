"""
單元測試：交易執行器（TradeExecutor）
測試 CCXT 交易執行、止盈止損邏輯、PanicScore 安全檢查
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from app.core.execution.trader import TradeExecutor


class TestTradeExecutor:
    """TradeExecutor 測試套件"""
    
    @pytest.fixture
    def mock_ccxt_exchange(self):
        """模擬 CCXT Exchange 實例"""
        exchange = Mock()
        exchange.fetch_balance = Mock(return_value={
            'USDT': {'free': 10000, 'used': 0, 'total': 10000}
        })
        exchange.create_order = Mock(return_value={
            'id': 'test_order_123',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'price': 50000,
            'amount': 0.1,
            'status': 'open'
        })
        exchange.fetch_ticker = Mock(return_value={
            'last': 50000,
            'bid': 49950,
            'ask': 50050
        })
        return exchange
    
    @pytest.fixture
    def executor(self, mock_ccxt_exchange):
        """創建 TradeExecutor 實例"""
        return TradeExecutor(
            exchange=mock_ccxt_exchange,
            max_position_size=0.3,
            stop_loss_percent=0.05,
            take_profit_min=0.10,
            take_profit_max=0.20
        )
    
    def test_initialization(self, executor):
        """測試初始化參數"""
        assert executor.max_position_size == 0.3
        assert executor.stop_loss_percent == 0.05
        assert executor.take_profit_min == 0.10
        assert executor.take_profit_max == 0.20
    
    def test_place_buy_order_success(self, executor, mock_ccxt_exchange):
        """測試成功下單買入"""
        result = executor.place_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            price=50000
        )
        
        assert result['status'] == 'success'
        assert result['order_id'] == 'test_order_123'
        mock_ccxt_exchange.create_order.assert_called_once()
    
    def test_place_order_with_panic_score_high(self, executor):
        """測試當 PanicScore > 80 時拒絕買入"""
        with pytest.raises(ValueError, match="PanicScore 過高"):
            executor.place_order(
                symbol='BTC/USDT',
                side='buy',
                amount=0.1,
                panic_score=0.85
            )
    
    def test_place_order_with_panic_score_ok(self, executor, mock_ccxt_exchange):
        """測試當 PanicScore < 80 時允許買入"""
        result = executor.place_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            panic_score=0.5
        )
        
        assert result['status'] == 'success'
        mock_ccxt_exchange.create_order.assert_called_once()
    
    def test_calculate_stop_loss_price(self, executor):
        """測試停損價格計算（5% 停損）"""
        entry_price = 50000
        stop_loss = executor.calculate_stop_loss(entry_price)
        
        # 停損應該是 50000 * (1 - 0.05) = 47500
        assert stop_loss == 47500
    
    def test_calculate_take_profit_price_min(self, executor):
        """測試止盈價格計算（10% 最低獲利）"""
        entry_price = 50000
        take_profit_min = executor.calculate_take_profit(entry_price, target='min')
        
        # 止盈最低應該是 50000 * (1 + 0.10) = 55000
        assert take_profit_min == 55000
    
    def test_calculate_take_profit_price_max(self, executor):
        """測試止盈價格計算（20% 最高獲利）"""
        entry_price = 50000
        take_profit_max = executor.calculate_take_profit(entry_price, target='max')
        
        # 止盈最高應該是 50000 * (1 + 0.20) = 60000
        assert take_profit_max == 60000
    
    def test_should_stop_loss_triggered(self, executor):
        """測試停損觸發條件"""
        entry_price = 50000
        current_price = 47000  # 下跌 6%
        
        should_stop = executor.should_stop_loss(entry_price, current_price)
        assert should_stop is True
    
    def test_should_stop_loss_not_triggered(self, executor):
        """測試停損未觸發"""
        entry_price = 50000
        current_price = 49000  # 下跌 2%
        
        should_stop = executor.should_stop_loss(entry_price, current_price)
        assert should_stop is False
    
    def test_should_take_profit_triggered_min(self, executor):
        """測試止盈觸發（達到最低獲利 10%）"""
        entry_price = 50000
        current_price = 55500  # 上漲 11%
        
        should_take = executor.should_take_profit(entry_price, current_price)
        assert should_take is True
    
    def test_should_take_profit_not_triggered(self, executor):
        """測試止盈未觸發（只上漲 5%）"""
        entry_price = 50000
        current_price = 52500  # 上漲 5%
        
        should_take = executor.should_take_profit(entry_price, current_price)
        assert should_take is False
    
    def test_position_size_limit(self, executor, mock_ccxt_exchange):
        """測試持倉上限（最大 30% 資金）"""
        # 模擬餘額 10000 USDT，最大持倉應為 3000 USDT
        max_amount = executor.calculate_max_position('BTC/USDT', price=50000)
        
        # 3000 USDT / 50000 = 0.06 BTC
        assert max_amount == pytest.approx(0.06, rel=1e-2)
    
    def test_get_open_positions(self, executor, mock_ccxt_exchange):
        """測試查詢當前持倉"""
        mock_ccxt_exchange.fetch_positions = Mock(return_value=[
            {'symbol': 'BTC/USDT', 'contracts': 0.1, 'entryPrice': 50000}
        ])
        
        positions = executor.get_open_positions()
        assert len(positions) == 1
        assert positions[0]['symbol'] == 'BTC/USDT'
    
    def test_close_position_success(self, executor, mock_ccxt_exchange):
        """測試平倉成功"""
        result = executor.close_position(
            symbol='BTC/USDT',
            amount=0.1,
            reason='stop_loss'
        )
        
        assert result['status'] == 'success'
        assert result['reason'] == 'stop_loss'
        mock_ccxt_exchange.create_order.assert_called_once()

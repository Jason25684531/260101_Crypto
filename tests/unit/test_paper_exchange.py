"""
测试模拟交易所（Paper Exchange）
Test Paper Exchange Implementation

验证：
1. PaperExchange 正确模拟 ccxt 接口
2. 虚拟余额正确更新（买入/卖出）
3. 订单记录正确保存
4. fetch_balance 返回正确格式
5. fetch_ticker 返回实时价格
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import os


class TestPaperExchange:
    """测试模拟交易所核心功能"""

    @pytest.fixture
    def paper_exchange(self):
        """创建 PaperExchange 实例"""
        from app.core.execution.paper_exchange import PaperExchange
        
        # 使用临时文件存储状态
        ledger_file = 'test_paper_ledger.json'
        exchange = PaperExchange(
            initial_balance=10000.0,
            ledger_file=ledger_file
        )
        
        yield exchange
        
        # 清理测试文件
        if os.path.exists(ledger_file):
            os.remove(ledger_file)

    def test_initialization(self, paper_exchange):
        """测试 PaperExchange 初始化"""
        # 验证初始余额
        balance = paper_exchange.fetch_balance()
        
        assert 'USDT' in balance['free'], "应该有 USDT 余额"
        assert balance['free']['USDT'] == 10000.0, "初始 USDT 应该是 10000"
        assert balance['total']['USDT'] == 10000.0, "总 USDT 应该是 10000"

    def test_buy_order_deducts_usdt(self, paper_exchange):
        """测试买入订单正确扣除 USDT"""
        # 买入 1 BTC @ 50000 USDT
        order = paper_exchange.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=1.0,
            price=50000.0
        )
        
        # 验证订单创建成功
        assert order['status'] == 'closed', "订单应该立即成交"
        assert order['symbol'] == 'BTC/USDT'
        assert order['side'] == 'buy'
        assert order['amount'] == 1.0
        assert order['price'] == 50000.0
        
        # 验证余额更新
        balance = paper_exchange.fetch_balance()
        
        # USDT 应该减少 50000
        assert balance['free']['USDT'] == pytest.approx(10000 - 50000, abs=0.01), \
            "USDT 应该减少 50000"
        
        # 应该有 1 BTC
        assert balance['free']['BTC'] == pytest.approx(1.0, abs=0.00001), \
            "应该有 1 BTC"

    def test_sell_order_adds_usdt(self, paper_exchange):
        """测试卖出订单正确增加 USDT"""
        # 先买入 1 BTC
        paper_exchange.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=1.0,
            price=50000.0
        )
        
        # 再卖出 0.5 BTC @ 55000 USDT
        order = paper_exchange.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='sell',
            amount=0.5,
            price=55000.0
        )
        
        # 验证订单成功
        assert order['status'] == 'closed'
        assert order['side'] == 'sell'
        
        # 验证余额
        balance = paper_exchange.fetch_balance()
        
        # USDT = 10000 - 50000 + 27500 = -12500（亏损）
        expected_usdt = 10000 - 50000 + (0.5 * 55000)
        assert balance['free']['USDT'] == pytest.approx(expected_usdt, abs=0.01)
        
        # BTC 应该剩 0.5
        assert balance['free']['BTC'] == pytest.approx(0.5, abs=0.00001)

    def test_insufficient_balance_raises_error(self, paper_exchange):
        """测试余额不足时抛出异常"""
        # 尝试买入超过余额的 BTC（需要 500000 USDT）
        with pytest.raises(ValueError, match="余额不足|Insufficient balance"):
            paper_exchange.create_order(
                symbol='BTC/USDT',
                type='limit',
                side='buy',
                amount=10.0,
                price=50000.0
            )

    def test_sell_without_asset_raises_error(self, paper_exchange):
        """测试没有资产时卖出抛出异常"""
        # 尝试卖出 BTC（但没有持仓）
        with pytest.raises(ValueError, match="余额不足|Insufficient balance"):
            paper_exchange.create_order(
                symbol='BTC/USDT',
                type='limit',
                side='sell',
                amount=1.0,
                price=50000.0
            )

    def test_fetch_ticker_returns_real_price(self, paper_exchange):
        """测试 fetch_ticker 返回真实市场价格"""
        # Mock ccxt 的 fetch_ticker
        with patch.object(paper_exchange._price_source, 'fetch_ticker') as mock_fetch:
            mock_fetch.return_value = {
                'symbol': 'BTC/USDT',
                'last': 52000.0,
                'bid': 51990.0,
                'ask': 52010.0
            }
            
            ticker = paper_exchange.fetch_ticker('BTC/USDT')
            
            # 验证返回结构
            assert ticker['symbol'] == 'BTC/USDT'
            assert ticker['last'] == 52000.0
            assert 'bid' in ticker
            assert 'ask' in ticker

    def test_market_order_uses_current_price(self, paper_exchange):
        """测试市价单使用当前市场价格"""
        # Mock 当前价格
        with patch.object(paper_exchange._price_source, 'fetch_ticker') as mock_fetch:
            mock_fetch.return_value = {
                'symbol': 'BTC/USDT',
                'last': 52000.0,
                'bid': 51990.0,
                'ask': 52010.0
            }
            
            # 市价买入
            order = paper_exchange.create_order(
                symbol='BTC/USDT',
                type='market',
                side='buy',
                amount=0.1
            )
            
            # 验证使用了市场价格
            assert order['price'] in [52000.0, 52010.0], \
                "市价单应该使用当前市场价格"

    def test_order_history_is_saved(self, paper_exchange):
        """测试订单历史被正确保存"""
        # 执行几笔交易
        paper_exchange.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.5,
            price=50000.0
        )
        
        paper_exchange.create_order(
            symbol='ETH/USDT',
            type='limit',
            side='buy',
            amount=10.0,
            price=3000.0
        )
        
        # 验证订单历史
        orders = paper_exchange.get_order_history()
        
        assert len(orders) == 2, "应该有 2 笔订单记录"
        assert orders[0]['symbol'] == 'BTC/USDT'
        assert orders[1]['symbol'] == 'ETH/USDT'

    def test_balance_format_compatible_with_ccxt(self, paper_exchange):
        """测试 fetch_balance 返回的格式兼容 ccxt"""
        balance = paper_exchange.fetch_balance()
        
        # 验证必要字段存在
        assert 'free' in balance, "应该有 'free' 字段"
        assert 'used' in balance, "应该有 'used' 字段"
        assert 'total' in balance, "应该有 'total' 字段"
        
        # 验证结构
        assert isinstance(balance['free'], dict)
        assert isinstance(balance['total'], dict)

    def test_state_persistence(self):
        """测试状态持久化到文件"""
        from app.core.execution.paper_exchange import PaperExchange
        
        ledger_file = 'test_persistence_ledger.json'
        
        # 创建交易所并执行交易
        exchange1 = PaperExchange(initial_balance=10000.0, ledger_file=ledger_file)
        exchange1.create_order('BTC/USDT', 'limit', 'buy', 1.0, 50000.0)
        
        # 创建新实例，应该恢复状态
        exchange2 = PaperExchange(initial_balance=10000.0, ledger_file=ledger_file)
        balance = exchange2.fetch_balance()
        
        # 验证状态被恢复
        assert balance['free']['USDT'] == pytest.approx(-40000.0, abs=0.01), \
            "应该恢复之前的余额状态"
        assert balance['free']['BTC'] == pytest.approx(1.0, abs=0.00001)
        
        # 清理
        if os.path.exists(ledger_file):
            os.remove(ledger_file)

    def test_calculate_pnl(self, paper_exchange):
        """测试计算未实现盈亏（如果实现了该功能）"""
        # 买入 1 BTC @ 50000
        paper_exchange.create_order('BTC/USDT', 'limit', 'buy', 1.0, 50000.0)
        
        # Mock 当前价格为 55000
        with patch.object(paper_exchange._price_source, 'fetch_ticker') as mock_fetch:
            mock_fetch.return_value = {'last': 55000.0}
            
            # 如果有 calculate_unrealized_pnl 方法
            if hasattr(paper_exchange, 'calculate_unrealized_pnl'):
                pnl = paper_exchange.calculate_unrealized_pnl()
                
                # 未实现盈亏应该是 5000
                assert pnl == pytest.approx(5000.0, abs=0.01)


class TestPaperExchangeIntegrationWithTrader:
    """测试 PaperExchange 与 TradeExecutor 的集成"""

    def test_trader_can_use_paper_exchange(self):
        """测试 TradeExecutor 可以使用 PaperExchange"""
        from app.core.execution.paper_exchange import PaperExchange
        from app.core.execution.trader import TradeExecutor
        
        # 创建模拟交易所
        paper_exchange = PaperExchange(initial_balance=10000.0)
        
        # 创建交易执行器
        trader = TradeExecutor(exchange=paper_exchange)
        
        # Mock fetch_ticker
        with patch.object(paper_exchange._price_source, 'fetch_ticker') as mock_fetch:
            mock_fetch.return_value = {'last': 50000.0}
            
            # 执行交易
            result = trader.place_order(
                symbol='BTC/USDT',
                side='buy',
                amount=0.1,
                price=50000.0,
                order_type='limit'
            )
            
            # 验证交易成功
            assert result['status'] == 'success'
            
            # 验证余额更新
            balance = paper_exchange.fetch_balance()
            assert balance['free']['USDT'] < 10000.0
            assert balance['free']['BTC'] > 0

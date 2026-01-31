"""验证 Paper Trading Mode 功能"""
import sys
sys.path.insert(0, 'D:\\01_Project\\260101_Crypto')

import os
from unittest.mock import patch, Mock


def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试 1: 配置加载")
    print("=" * 60)
    
    # 设置环境变量
    os.environ['TRADING_MODE'] = 'PAPER'
    os.environ['PAPER_INITIAL_BALANCE'] = '10000.0'
    
    from app.config import config
    
    assert config.TRADING_MODE == 'PAPER', "交易模式应该是 PAPER"
    print(f"✓ 交易模式: {config.TRADING_MODE}")
    
    assert config.PAPER_INITIAL_BALANCE == 10000.0
    print(f"✓ 模拟初始资金: ${config.PAPER_INITIAL_BALANCE:,.2f}")
    
    assert config.is_paper_mode() is True
    print("✓ is_paper_mode() 返回 True")
    
    assert config.is_live_mode() is False
    print("✓ is_live_mode() 返回 False")
    
    print()


def test_paper_exchange_basic():
    """测试 PaperExchange 基本功能"""
    print("=" * 60)
    print("测试 2: PaperExchange 基本功能")
    print("=" * 60)
    
    # 直接导入避免 __init__.py 中的 LINE Bot 问题
    import sys
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "paper_exchange",
        "D:\\01_Project\\260101_Crypto\\app\\core\\execution\\paper_exchange.py"
    )
    paper_exchange_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paper_exchange_module)
    PaperExchange = paper_exchange_module.PaperExchange
    
    # 创建模拟交易所
    exchange = PaperExchange(initial_balance=10000.0, ledger_file='test_ledger.json')
    print("✓ PaperExchange 创建成功")
    
    # 测试余额
    balance = exchange.fetch_balance()
    assert balance['free']['USDT'] == 10000.0
    print(f"✓ 初始余额: ${balance['free']['USDT']:,.2f} USDT")
    
    # Mock fetch_ticker
    with patch.object(exchange._price_source, 'fetch_ticker') as mock_fetch:
        mock_fetch.return_value = {
            'symbol': 'BTC/USDT',
            'last': 50000.0,
            'bid': 49990.0,
            'ask': 50010.0
        }
        
        # 买入 BTC
        order = exchange.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.1,
            price=50000.0
        )
        
        assert order['status'] == 'closed'
        print(f"✓ 买入订单成功: {order['amount']} BTC @ ${order['price']:,.2f}")
        
        # 验证余额更新
        balance = exchange.fetch_balance()
        expected_usdt = 10000.0 - (0.1 * 50000.0)
        assert abs(balance['free']['USDT'] - expected_usdt) < 0.01
        print(f"✓ USDT 余额更新: ${balance['free']['USDT']:,.2f}")
        
        assert abs(balance['free']['BTC'] - 0.1) < 0.00001
        print(f"✓ BTC 余额: {balance['free']['BTC']} BTC")
    
    # 清理
    exchange.close()
    if os.path.exists('test_ledger.json'):
        os.remove('test_ledger.json')
    
    print()


def test_paper_exchange_insufficient_balance():
    """测试余额不足处理"""
    print("=" * 60)
    print("测试 3: 余额不足处理")
    print("=" * 60)
    
    from app.core.execution.paper_exchange import PaperExchange
    
    exchange = PaperExchange(initial_balance=1000.0, ledger_file='test_insufficient.json')
    
    with patch.object(exchange._price_source, 'fetch_ticker') as mock_fetch:
        mock_fetch.return_value = {'last': 50000.0, 'bid': 49990.0, 'ask': 50010.0}
        
        try:
            # 尝试买入超过余额的 BTC
            exchange.create_order(
                symbol='BTC/USDT',
                type='limit',
                side='buy',
                amount=1.0,
                price=50000.0
            )
            print("❌ 应该抛出余额不足异常")
            assert False
        except ValueError as e:
            print(f"✓ 正确抛出异常: {str(e)}")
    
    # 清理
    exchange.close()
    if os.path.exists('test_insufficient.json'):
        os.remove('test_insufficient.json')
    
    print()


def test_trader_auto_mode_selection():
    """测试 TradeExecutor 自动模式选择"""
    print("=" * 60)
    print("测试 4: TradeExecutor 模式自动选择")
    print("=" * 60)
    
    # 确保环境变量设置为 PAPER
    os.environ['TRADING_MODE'] = 'PAPER'
    
    from app.core.execution.trader import TradeExecutor
    
    # 创建 TradeExecutor（不传 exchange）
    trader = TradeExecutor()
    
    assert trader.trading_mode == 'PAPER'
    print(f"✓ 交易模式: {trader.trading_mode}")
    
    from app.core.execution.paper_exchange import PaperExchange
    assert isinstance(trader.exchange, PaperExchange)
    print("✓ 自动创建了 PaperExchange")
    
    print()


def test_trader_with_paper_exchange():
    """测试 TradeExecutor 与 PaperExchange 集成"""
    print("=" * 60)
    print("测试 5: TradeExecutor 集成测试")
    print("=" * 60)
    
    from app.core.execution.paper_exchange import PaperExchange
    from app.core.execution.trader import TradeExecutor
    
    exchange = PaperExchange(initial_balance=10000.0, ledger_file='test_integration.json')
    trader = TradeExecutor(exchange=exchange)
    
    with patch.object(exchange._price_source, 'fetch_ticker') as mock_fetch:
        mock_fetch.return_value = {'last': 50000.0, 'bid': 49990.0, 'ask': 50010.0}
        
        # 执行交易
        result = trader.place_order(
            symbol='BTC/USDT',
            side='buy',
            amount=0.1,
            price=50000.0,
            order_type='limit'
        )
        
        assert result['status'] == 'success'
        print(f"✓ 订单执行成功: {result['order_id']}")
        
        # 验证余额
        balance = exchange.fetch_balance()
        assert balance['free']['USDT'] < 10000.0
        print(f"✓ USDT 余额: ${balance['free']['USDT']:,.2f}")
        
        assert balance['free']['BTC'] > 0
        print(f"✓ BTC 余额: {balance['free']['BTC']} BTC")
    
    # 清理
    exchange.close()
    if os.path.exists('test_integration.json'):
        os.remove('test_integration.json')
    
    print()


def test_portfolio_summary():
    """测试投资组合摘要"""
    print("=" * 60)
    print("测试 6: 投资组合摘要")
    print("=" * 60)
    
    from app.core.execution.paper_exchange import PaperExchange
    
    exchange = PaperExchange(initial_balance=10000.0, ledger_file='test_portfolio.json')
    
    with patch.object(exchange._price_source, 'fetch_ticker') as mock_fetch:
        mock_fetch.return_value = {'last': 50000.0, 'bid': 49990.0, 'ask': 50010.0}
        
        # 买入 BTC
        exchange.create_order('BTC/USDT', 'limit', 'buy', 0.1, 50000.0)
        
        # 获取投资组合摘要
        summary = exchange.get_portfolio_summary()
        
        print(f"✓ 初始资金: ${summary['initial_balance']:,.2f}")
        print(f"✓ 当前总值: ${summary['current_value']:,.2f}")
        print(f"✓ 未实现盈亏: ${summary['unrealized_pnl']:,.2f}")
        print(f"✓ ROI: {summary['roi_percent']:.2f}%")
        print(f"✓ 交易次数: {summary['total_trades']}")
        
        assert summary['total_trades'] == 1
    
    # 清理
    exchange.close()
    if os.path.exists('test_portfolio.json'):
        os.remove('test_portfolio.json')
    
    print()


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Paper Trading Mode 测试" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_config_loading()
        test_paper_exchange_basic()
        test_paper_exchange_insufficient_balance()
        test_trader_auto_mode_selection()
        test_trader_with_paper_exchange()
        test_portfolio_summary()
        
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 18 + "所有测试通过！✓" + " " * 24 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

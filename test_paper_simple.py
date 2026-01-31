"""简化版 Paper Trading 测试"""
import sys
sys.path.insert(0, 'D:\\01_Project\\260101_Crypto')

import os
import importlib.util
from unittest.mock import patch, Mock


def load_module(name, path):
    """直接加载模块避免 __init__.py 问题"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_exchange():
    """测试 PaperExchange"""
    print("=" * 60)
    print("测试: PaperExchange 核心功能")
    print("=" * 60)
    
    # 直接加载模块
    pe_module = load_module(
        "paper_exchange",
        "D:\\01_Project\\260101_Crypto\\app\\core\\execution\\paper_exchange.py"
    )
    PaperExchange = pe_module.PaperExchange
    
    # 创建实例
    exchange = PaperExchange(initial_balance=10000.0, ledger_file='test_simple.json')
    print("✓ PaperExchange 创建成功")
    
    # 测试初始余额
    balance = exchange.fetch_balance()
    assert balance['free']['USDT'] == 10000.0
    print(f"✓ 初始 USDT: ${balance['free']['USDT']:,.2f}")
    
    # Mock fetch_ticker
    with patch.object(exchange._price_source, 'fetch_ticker') as mock_fetch:
        mock_fetch.return_value = {
            'symbol': 'BTC/USDT',
            'last': 50000.0,
            'bid': 49990.0,
            'ask': 50010.0
        }
        
        # 买入
        order = exchange.create_order(
            symbol='BTC/USDT',
            type='limit',
            side='buy',
            amount=0.1,
            price=50000.0
        )
        
        print(f"✓ 买入订单: {order['amount']} BTC @ ${order['price']:,.2f}")
        
        # 验证余额
        balance = exchange.fetch_balance()
        expected = 10000 - 5000
        assert abs(balance['free']['USDT'] - expected) < 0.01
        print(f"✓ USDT 余额: ${balance['free']['USDT']:,.2f}")
        
        assert abs(balance['free']['BTC'] - 0.1) < 0.00001
        print(f"✓ BTC 余额: {balance['free']['BTC']} BTC")
        
        # 测试余额不足
        try:
            exchange.create_order('BTC/USDT', 'limit', 'buy', 10.0, 50000.0)
            print("❌ 应该抛出余额不足异常")
            return False
        except ValueError:
            print("✓ 正确处理余额不足")
        
        # 测试卖出
        order2 = exchange.create_order('BTC/USDT', 'limit', 'sell', 0.05, 55000.0)
        print(f"✓ 卖出订单: {order2['amount']} BTC @ ${order2['price']:,.2f}")
        
        balance = exchange.fetch_balance()
        print(f"✓ 最终 USDT: ${balance['free']['USDT']:,.2f}")
        print(f"✓ 最终 BTC: {balance['free']['BTC']} BTC")
        
        # 测试组合摘要
        summary = exchange.get_portfolio_summary()
        print(f"✓ 总交易次数: {summary['total_trades']}")
        print(f"✓ 未实现盈亏: ${summary['unrealized_pnl']:,.2f}")
    
    # 清理
    exchange.close()
    if os.path.exists('test_simple.json'):
        os.remove('test_simple.json')
    
    print()
    return True


def test_config():
    """测试配置"""
    print("=" * 60)
    print("测试: 配置加载")
    print("=" * 60)
    
    os.environ['TRADING_MODE'] = 'PAPER'
    
    config_module = load_module(
        "config",
        "D:\\01_Project\\260101_Crypto\\app\\config.py"
    )
    config = config_module.config
    
    assert config.TRADING_MODE == 'PAPER'
    print(f"✓ 交易模式: {config.TRADING_MODE}")
    
    assert config.is_paper_mode()
    print("✓ is_paper_mode() = True")
    
    print()
    return True


def test_trader_integration():
    """测试 TradeExecutor 集成"""
    print("=" * 60)
    print("测试: TradeExecutor 集成")
    print("=" * 60)
    
    # 加载模块
    pe_module = load_module(
        "paper_exchange",
        "D:\\01_Project\\260101_Crypto\\app\\core\\execution\\paper_exchange.py"
    )
    PaperExchange = pe_module.PaperExchange
    
    trader_module = load_module(
        "trader",
        "D:\\01_Project\\260101_Crypto\\app\\core\\execution\\trader.py"
    )
    TradeExecutor = trader_module.TradeExecutor
    
    # 创建
    exchange = PaperExchange(initial_balance=10000.0, ledger_file='test_trader_int.json')
    trader = TradeExecutor(exchange=exchange)
    
    assert trader.trading_mode == 'PAPER'
    print(f"✓ 交易模式: {trader.trading_mode}")
    
    # Mock 价格
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
        print(f"✓ 订单成功: {result['order_id']}")
        
        balance = exchange.fetch_balance()
        assert balance['free']['USDT'] < 10000
        print(f"✓ 余额已更新: ${balance['free']['USDT']:,.2f}")
    
    # 清理
    exchange.close()
    if os.path.exists('test_trader_int.json'):
        os.remove('test_trader_int.json')
    
    print()
    return True


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Paper Trading Mode 测试" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        success = True
        success = test_config() and success
        success = test_paper_exchange() and success
        success = test_trader_integration() and success
        
        if success:
            print("╔" + "=" * 58 + "╗")
            print("║" + " " * 18 + "所有测试通过！✓" + " " * 24 + "║")
            print("╚" + "=" * 58 + "╝")
            print()
        else:
            print("❌ 部分测试失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 发生错误: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

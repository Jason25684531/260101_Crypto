"""验证 Data Jobs 功能"""
import sys
sys.path.insert(0, 'D:\\01_Project\\260101_Crypto')

import asyncio
from unittest.mock import Mock, AsyncMock


async def test_fetcher_latest_method():
    """测试 fetcher 的 fetch_latest_ohlcv 方法"""
    print("=" * 60)
    print("测试 1: MarketFetcher.fetch_latest_ohlcv 方法")
    print("=" * 60)
    
    from app.core.data.fetcher import MarketFetcher
    
    fetcher = MarketFetcher(exchange_name='binance')
    print("✓ MarketFetcher 初始化成功")
    
    # 验证方法存在
    assert hasattr(fetcher, 'fetch_latest_ohlcv'), "缺少 fetch_latest_ohlcv 方法"
    print("✓ fetch_latest_ohlcv 方法存在")
    
    # 验证方法可调用
    assert callable(fetcher.fetch_latest_ohlcv), "fetch_latest_ohlcv 不可调用"
    print("✓ fetch_latest_ohlcv 可调用")
    
    await fetcher.close()
    print()


async def test_job_update_market_data():
    """测试 job_update_market_data 函数"""
    print("=" * 60)
    print("测试 2: job_update_market_data 函数")
    print("=" * 60)
    
    from app.core.jobs import job_update_market_data
    
    # Mock fetcher 和 db_session
    mock_fetcher = Mock()
    mock_fetcher.fetch_latest_ohlcv = AsyncMock(return_value=[
        [1706745600000, 42000.0, 42100.0, 41900.0, 42050.0, 123.45],
        [1706745660000, 42050.0, 42200.0, 42000.0, 42150.0, 145.67],
    ])
    mock_fetcher.close = AsyncMock()
    
    mock_db = Mock()
    mock_db.query = Mock(return_value=Mock(
        filter_by=Mock(return_value=Mock(first=Mock(return_value=None)))
    ))
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.rollback = Mock()
    
    # 执行任务
    await job_update_market_data(
        fetcher=mock_fetcher,
        db_session=mock_db,
        symbol='BTC/USDT',
        limit=5
    )
    
    print("✓ job_update_market_data 执行成功")
    
    # 验证调用
    mock_fetcher.fetch_latest_ohlcv.assert_called_once()
    print("✓ fetcher.fetch_latest_ohlcv 被调用")
    
    assert mock_db.add.call_count == 2, f"应该调用 add 2 次，实际: {mock_db.add.call_count}"
    print("✓ db_session.add 被调用 2 次")
    
    mock_db.commit.assert_called_once()
    print("✓ db_session.commit 被调用")
    print()


def test_scheduler_setup():
    """测试 Scheduler 的 setup_all_jobs 方法"""
    print("=" * 60)
    print("测试 3: Scheduler.setup_all_jobs 方法")
    print("=" * 60)
    
    from app.core.scheduler import Scheduler
    
    scheduler = Scheduler()
    print("✓ Scheduler 初始化成功")
    
    # 验证新方法存在
    assert hasattr(scheduler, 'setup_all_jobs'), "缺少 setup_all_jobs 方法"
    print("✓ setup_all_jobs 方法存在")
    
    assert hasattr(scheduler, 'setup_market_data_jobs'), "缺少 setup_market_data_jobs 方法"
    print("✓ setup_market_data_jobs 方法存在")
    
    assert hasattr(scheduler, 'setup_signal_scan_jobs'), "缺少 setup_signal_scan_jobs 方法"
    print("✓ setup_signal_scan_jobs 方法存在")
    print()


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 18 + "Data Jobs 功能测试" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        await test_fetcher_latest_method()
        await test_job_update_market_data()
        test_scheduler_setup()
        
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 18 + "所有测试通过！✓" + " " * 24 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

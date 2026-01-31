"""
测试定时任务逻辑
Test Job Functions

验证：
1. job_update_market_data 能成功获取并保存数据
2. 能正确处理网络错误不会让 scheduler 崩溃
3. 能处理数据库重复记录（幂等性）
4. 能记录执行日志
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio


class TestJobUpdateMarketData:
    """测试市场数据更新任务"""

    @pytest.fixture
    def mock_fetcher(self):
        """Mock MarketFetcher"""
        fetcher = Mock()
        fetcher.fetch_latest_ohlcv = AsyncMock()
        return fetcher

    @pytest.fixture
    def mock_db_session(self):
        """Mock 数据库 session"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.query = Mock()
        return session

    @pytest.fixture
    def sample_ohlcv_data(self):
        """样本 OHLCV 数据"""
        return [
            [1706745600000, 42000.0, 42100.0, 41900.0, 42050.0, 123.45],
            [1706745660000, 42050.0, 42200.0, 42000.0, 42150.0, 145.67],
            [1706745720000, 42150.0, 42180.0, 42100.0, 42120.0, 98.23],
        ]

    @pytest.mark.asyncio
    async def test_job_success(self, mock_fetcher, mock_db_session, sample_ohlcv_data):
        """测试任务成功执行"""
        from app.core.jobs import job_update_market_data
        
        # Mock 返回数据
        mock_fetcher.fetch_latest_ohlcv.return_value = sample_ohlcv_data
        
        # 执行任务
        await job_update_market_data(
            fetcher=mock_fetcher,
            db_session=mock_db_session,
            symbol='BTC/USDT',
            limit=5
        )
        
        # 验证 fetcher 被调用
        mock_fetcher.fetch_latest_ohlcv.assert_called_once_with(
            symbol='BTC/USDT',
            limit=5
        )
        
        # 验证数据被保存（应该调用 3 次 add，因为有 3 笔数据）
        assert mock_db_session.add.call_count == 3
        
        # 验证 commit 被调用
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_network_error(self, mock_fetcher, mock_db_session):
        """测试任务处理网络错误"""
        from app.core.jobs import job_update_market_data
        import ccxt
        
        # Mock 网络错误
        mock_fetcher.fetch_latest_ohlcv.side_effect = ccxt.NetworkError("Connection timeout")
        
        # 执行任务不应该抛出异常（已被捕获）
        try:
            await job_update_market_data(
                fetcher=mock_fetcher,
                db_session=mock_db_session,
                symbol='BTC/USDT'
            )
        except Exception as e:
            pytest.fail(f"任务不应该抛出异常，但抛出了: {e}")
        
        # 验证没有调用 commit（因为没有数据）
        mock_db_session.commit.assert_not_called()
        
        # 验证 rollback 被调用
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_duplicate_handling(self, mock_fetcher, mock_db_session, sample_ohlcv_data):
        """测试任务处理重复数据"""
        from app.core.jobs import job_update_market_data
        from sqlalchemy.exc import IntegrityError
        
        # Mock 返回数据
        mock_fetcher.fetch_latest_ohlcv.return_value = sample_ohlcv_data
        
        # Mock commit 时抛出重复错误
        mock_db_session.commit.side_effect = IntegrityError(
            "Duplicate entry", None, None
        )
        
        # 执行任务不应该抛出异常
        try:
            await job_update_market_data(
                fetcher=mock_fetcher,
                db_session=mock_db_session,
                symbol='BTC/USDT'
            )
        except Exception as e:
            pytest.fail(f"任务不应该抛出异常，但抛出了: {e}")
        
        # 验证 rollback 被调用
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_empty_data(self, mock_fetcher, mock_db_session):
        """测试任务处理空数据"""
        from app.core.jobs import job_update_market_data
        
        # Mock 返回空数据
        mock_fetcher.fetch_latest_ohlcv.return_value = []
        
        # 执行任务
        await job_update_market_data(
            fetcher=mock_fetcher,
            db_session=mock_db_session,
            symbol='BTC/USDT'
        )
        
        # 验证没有调用 add
        mock_db_session.add.assert_not_called()
        
        # 即使没有数据也应该 commit（确保事务完成）
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_logs_execution(self, mock_fetcher, mock_db_session, sample_ohlcv_data, caplog):
        """测试任务记录执行日志"""
        from app.core.jobs import job_update_market_data
        import logging
        
        # Mock 返回数据
        mock_fetcher.fetch_latest_ohlcv.return_value = sample_ohlcv_data
        
        # 设置日志级别
        with caplog.at_level(logging.INFO):
            await job_update_market_data(
                fetcher=mock_fetcher,
                db_session=mock_db_session,
                symbol='BTC/USDT'
            )
        
        # 验证日志包含关键信息
        assert any("BTC/USDT" in record.message for record in caplog.records)
        assert any("成功" in record.message or "Market Data Updated" in record.message 
                   for record in caplog.records)


class TestJobSyncWrapper:
    """测试同步包装函数"""

    def test_sync_wrapper_calls_async_job(self):
        """测试同步包装器能正确调用异步任务"""
        from app.core.jobs import job_update_market_data_sync
        
        with patch('app.core.jobs.asyncio.run') as mock_run:
            # 执行同步包装器
            job_update_market_data_sync()
            
            # 验证 asyncio.run 被调用
            mock_run.assert_called_once()


class TestMarketFetcherLatestMethod:
    """测试 MarketFetcher 的增量抓取方法"""

    @pytest.mark.asyncio
    async def test_fetch_latest_ohlcv(self):
        """测试 fetch_latest_ohlcv 方法存在且可调用"""
        from app.core.data.fetcher import MarketFetcher
        
        fetcher = MarketFetcher(exchange_name='binance')
        
        # 验证方法存在
        assert hasattr(fetcher, 'fetch_latest_ohlcv'), \
            "MarketFetcher 应该有 fetch_latest_ohlcv 方法"
        
        # 验证方法是可调用的
        assert callable(fetcher.fetch_latest_ohlcv), \
            "fetch_latest_ohlcv 应该是可调用的"
        
        # 清理
        await fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_latest_default_limit(self):
        """测试 fetch_latest_ohlcv 的默认参数"""
        from app.core.data.fetcher import MarketFetcher
        from unittest.mock import AsyncMock
        
        fetcher = MarketFetcher(exchange_name='binance')
        
        # Mock fetch_ohlcv 方法
        fetcher.fetch_ohlcv = AsyncMock(return_value=[
            [1706745600000, 42000.0, 42100.0, 41900.0, 42050.0, 123.45],
        ])
        
        # 调用 fetch_latest_ohlcv（不传 limit）
        result = await fetcher.fetch_latest_ohlcv('BTC/USDT')
        
        # 验证使用默认参数调用了 fetch_ohlcv
        fetcher.fetch_ohlcv.assert_called_once()
        call_args = fetcher.fetch_ohlcv.call_args
        
        # 验证返回结果
        assert len(result) > 0
        
        # 清理
        await fetcher.close()

"""
MarketFetcher 單元測試 - 使用 Mock 模擬 CCXT API
遵循 TDD 原則：先寫測試，再實現功能
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys
import os

# 添加 app 目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


@pytest.fixture
def mock_ccxt_exchange():
    """模擬 CCXT Exchange 實例"""
    exchange = Mock()
    exchange.id = 'binance'
    exchange.has = {'fetchOHLCV': True}
    
    # 模擬 OHLCV 數據格式: [timestamp, open, high, low, close, volume]
    exchange.fetch_ohlcv = AsyncMock(return_value=[
        [1609459200000, 29000.0, 29500.0, 28800.0, 29200.0, 1250.5],
        [1609459260000, 29200.0, 29400.0, 29100.0, 29300.0, 980.3],
        [1609459320000, 29300.0, 29600.0, 29250.0, 29500.0, 1100.7],
    ])
    
    return exchange


@pytest.mark.asyncio
async def test_fetcher_initialization():
    """測試 MarketFetcher 初始化"""
    from app.core.data.fetcher import MarketFetcher
    
    fetcher = MarketFetcher(exchange_name='binance')
    assert fetcher.exchange_name == 'binance'
    assert fetcher.exchange is not None


@pytest.mark.asyncio
async def test_fetch_ohlcv_success(mock_ccxt_exchange):
    """測試成功獲取 OHLCV 數據"""
    from app.core.data.fetcher import MarketFetcher
    
    with patch('ccxt.binance', return_value=mock_ccxt_exchange):
        fetcher = MarketFetcher(exchange_name='binance')
        fetcher.exchange = mock_ccxt_exchange
        
        # 獲取數據
        data = await fetcher.fetch_ohlcv(
            symbol='BTC/USDT',
            timeframe='1m',
            limit=3
        )
        
        # 驗證結果
        assert len(data) == 3
        assert data[0][1] == 29000.0  # Open price
        assert data[0][4] == 29200.0  # Close price
        
        # 驗證 CCXT API 被正確調用
        mock_ccxt_exchange.fetch_ohlcv.assert_called_once_with(
            'BTC/USDT',
            '1m',
            limit=3
        )


@pytest.mark.asyncio
async def test_fetch_ohlcv_with_since(mock_ccxt_exchange):
    """測試從指定時間戳開始獲取數據"""
    from app.core.data.fetcher import MarketFetcher
    
    with patch('ccxt.binance', return_value=mock_ccxt_exchange):
        fetcher = MarketFetcher(exchange_name='binance')
        fetcher.exchange = mock_ccxt_exchange
        
        since_timestamp = 1609459200000
        data = await fetcher.fetch_ohlcv(
            symbol='BTC/USDT',
            timeframe='1m',
            since=since_timestamp,
            limit=3
        )
        
        assert len(data) == 3
        mock_ccxt_exchange.fetch_ohlcv.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_ohlcv_api_error(mock_ccxt_exchange):
    """測試 API 錯誤處理"""
    from app.core.data.fetcher import MarketFetcher
    import ccxt
    
    # 模擬 API 錯誤
    mock_ccxt_exchange.fetch_ohlcv = AsyncMock(
        side_effect=ccxt.NetworkError('Connection timeout')
    )
    
    with patch('ccxt.binance', return_value=mock_ccxt_exchange):
        fetcher = MarketFetcher(exchange_name='binance')
        fetcher.exchange = mock_ccxt_exchange
        
        # 應該拋出異常或返回空列表（取決於實現）
        with pytest.raises((ccxt.NetworkError, Exception)):
            await fetcher.fetch_ohlcv('BTC/USDT', '1m', limit=10)


@pytest.mark.asyncio
async def test_fetch_multiple_symbols(mock_ccxt_exchange):
    """測試批量獲取多個交易對數據"""
    from app.core.data.fetcher import MarketFetcher
    
    with patch('ccxt.binance', return_value=mock_ccxt_exchange):
        fetcher = MarketFetcher(exchange_name='binance')
        fetcher.exchange = mock_ccxt_exchange
        
        symbols = ['BTC/USDT', 'ETH/USDT']
        results = {}
        
        for symbol in symbols:
            data = await fetcher.fetch_ohlcv(symbol, '1m', limit=3)
            results[symbol] = data
        
        assert len(results) == 2
        assert 'BTC/USDT' in results
        assert 'ETH/USDT' in results


@pytest.mark.asyncio
async def test_save_to_database(mock_ccxt_exchange):
    """測試將獲取的數據儲存到資料庫"""
    from app.core.data.fetcher import MarketFetcher
    from app.models.market import OHLCV
    
    with patch('ccxt.binance', return_value=mock_ccxt_exchange):
        fetcher = MarketFetcher(exchange_name='binance')
        fetcher.exchange = mock_ccxt_exchange
        
        # 獲取數據
        data = await fetcher.fetch_ohlcv('BTC/USDT', '1m', limit=3)
        
        # 驗證可以轉換為模型
        for ohlcv_data in data:
            record = OHLCV.from_ccxt('binance', 'BTC/USDT', '1m', ohlcv_data)
            assert record.symbol == 'BTC/USDT'
            assert record.exchange == 'binance'
            assert record.open == ohlcv_data[1]
            assert record.close == ohlcv_data[4]

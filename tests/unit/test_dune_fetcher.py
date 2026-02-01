"""
Unit Tests for DuneFetcher (Phase 6)
測試 Dune Analytics 鏈上數據獲取器
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.core.data.dune_fetcher import DuneFetcher


class TestDuneFetcher:
    """DuneFetcher 單元測試"""
    
    @pytest.fixture
    def mock_dune_client(self):
        """Mock Dune Client"""
        with patch('app.core.data.dune_fetcher.DuneClient') as mock:
            yield mock
    
    @pytest.fixture
    def fetcher_with_key(self, mock_dune_client):
        """有 API Key 的 Fetcher"""
        return DuneFetcher(api_key="test_api_key")
    
    @pytest.fixture
    def fetcher_without_key(self):
        """沒有 API Key 的 Fetcher"""
        with patch('app.core.data.dune_fetcher.Config') as mock_config:
            mock_config.DUNE_API_KEY = ""
            return DuneFetcher()
    
    def test_init_with_api_key(self, mock_dune_client):
        """測試：使用 API Key 初始化"""
        fetcher = DuneFetcher(api_key="test_key")
        assert fetcher.api_key == "test_key"
        assert fetcher.is_available() is True
    
    def test_init_without_api_key(self, fetcher_without_key):
        """測試：沒有 API Key"""
        assert fetcher_without_key.is_available() is False
    
    def test_get_default_query_id_btc(self, fetcher_with_key):
        """測試：獲取 BTC 預設查詢 ID"""
        query_id = fetcher_with_key._get_default_query_id("BTC")
        assert isinstance(query_id, int)
        assert query_id > 0
    
    def test_get_default_query_id_eth(self, fetcher_with_key):
        """測試：獲取 ETH 預設查詢 ID"""
        query_id = fetcher_with_key._get_default_query_id("ETH")
        assert isinstance(query_id, int)
        assert query_id > 0
    
    def test_get_default_query_id_unknown_asset(self, fetcher_with_key):
        """測試：未知資產使用 BTC 預設"""
        query_id = fetcher_with_key._get_default_query_id("UNKNOWN")
        btc_query_id = fetcher_with_key._get_default_query_id("BTC")
        assert query_id == btc_query_id
    
    def test_parse_results_success(self, fetcher_with_key):
        """測試：成功解析結果"""
        mock_results = [{
            'time': '2026-02-01 12:00:00',
            'exchange_netflow': -1234.56,
            'whale_transactions': 12,
            'total_inflow': 5000.0,
            'total_outflow': 6234.56
        }]
        
        parsed = fetcher_with_key._parse_results(mock_results, "BTC")
        
        assert parsed is not None
        assert parsed['asset'] == 'BTC'
        assert parsed['exchange_netflow'] == -1234.56
        assert parsed['whale_inflow_count'] == 12
        assert parsed['source'] == 'dune'
        assert isinstance(parsed['timestamp'], int)
        assert 'extra_data' in parsed
    
    def test_parse_results_empty(self, fetcher_with_key):
        """測試：空結果處理"""
        parsed = fetcher_with_key._parse_results([], "BTC")
        assert parsed is None
    
    def test_parse_results_missing_fields(self, fetcher_with_key):
        """測試：缺少欄位的結果"""
        mock_results = [{
            'time': '2026-02-01 12:00:00'
            # 缺少 netflow 和 whale_transactions
        }]
        
        parsed = fetcher_with_key._parse_results(mock_results, "BTC")
        
        assert parsed is not None
        assert parsed['exchange_netflow'] == 0.0
        assert parsed['whale_inflow_count'] == 0
    
    @patch('app.core.data.dune_fetcher.time.sleep')
    def test_execute_query_with_retry_success(self, mock_sleep, fetcher_with_key):
        """測試：查詢執行成功"""
        # Mock execution response
        mock_execution = Mock()
        mock_execution.execution_id = "test_exec_id"
        
        # Mock status response (completed)
        mock_status = Mock()
        mock_status.state = "QUERY_STATE_COMPLETED"
        
        # Mock results
        mock_results = Mock()
        mock_results.rows = [{'test': 'data'}]
        
        # Setup mock client
        fetcher_with_key.client.execute_query.return_value = mock_execution
        fetcher_with_key.client.get_execution_status.return_value = mock_status
        fetcher_with_key.client.get_execution_results.return_value = mock_results
        
        results = fetcher_with_key._execute_query_with_retry(
            query_id=123456,
            max_wait_time=60,
            check_interval=1
        )
        
        assert results == [{'test': 'data'}]
        assert mock_sleep.call_count == 0  # 立即完成，不需等待
    
    @patch('app.core.data.dune_fetcher.time.sleep')
    def test_execute_query_with_retry_pending_then_success(self, mock_sleep, fetcher_with_key):
        """測試：查詢先 pending 後成功"""
        mock_execution = Mock()
        mock_execution.execution_id = "test_exec_id"
        
        # 第一次 pending，第二次 completed
        mock_status_pending = Mock()
        mock_status_pending.state = "QUERY_STATE_PENDING"
        
        mock_status_completed = Mock()
        mock_status_completed.state = "QUERY_STATE_COMPLETED"
        
        mock_results = Mock()
        mock_results.rows = [{'test': 'data'}]
        
        fetcher_with_key.client.execute_query.return_value = mock_execution
        fetcher_with_key.client.get_execution_status.side_effect = [
            mock_status_pending,
            mock_status_completed
        ]
        fetcher_with_key.client.get_execution_results.return_value = mock_results
        
        results = fetcher_with_key._execute_query_with_retry(
            query_id=123456,
            max_wait_time=60,
            check_interval=1
        )
        
        assert results == [{'test': 'data'}]
        assert mock_sleep.call_count == 1
    
    @patch('app.core.data.dune_fetcher.time.sleep')
    def test_execute_query_with_retry_failed(self, mock_sleep, fetcher_with_key):
        """測試：查詢失敗"""
        mock_execution = Mock()
        mock_execution.execution_id = "test_exec_id"
        
        mock_status_failed = Mock()
        mock_status_failed.state = "QUERY_STATE_FAILED"
        
        fetcher_with_key.client.execute_query.return_value = mock_execution
        fetcher_with_key.client.get_execution_status.return_value = mock_status_failed
        
        results = fetcher_with_key._execute_query_with_retry(
            query_id=123456,
            max_wait_time=60,
            check_interval=1
        )
        
        assert results is None
    
    @patch('app.core.data.dune_fetcher.time.sleep')
    def test_execute_query_with_retry_timeout(self, mock_sleep, fetcher_with_key):
        """測試：查詢超時"""
        mock_execution = Mock()
        mock_execution.execution_id = "test_exec_id"
        
        mock_status_pending = Mock()
        mock_status_pending.state = "QUERY_STATE_PENDING"
        
        fetcher_with_key.client.execute_query.return_value = mock_execution
        fetcher_with_key.client.get_execution_status.return_value = mock_status_pending
        
        results = fetcher_with_key._execute_query_with_retry(
            query_id=123456,
            max_wait_time=5,  # 5 秒超時
            check_interval=2   # 每 2 秒檢查
        )
        
        assert results is None
        # 應該檢查 3 次：0s, 2s, 4s（第 6 秒會超時）
        assert mock_sleep.call_count >= 2
    
    def test_fetch_latest_metrics_without_client(self, fetcher_without_key):
        """測試：沒有客戶端時無法獲取數據"""
        result = fetcher_without_key.fetch_latest_metrics("BTC")
        assert result is None
    
    @patch.object(DuneFetcher, '_execute_query_with_retry')
    @patch.object(DuneFetcher, '_parse_results')
    def test_fetch_latest_metrics_success(self, mock_parse, mock_execute, fetcher_with_key):
        """測試：成功獲取最新指標"""
        mock_execute.return_value = [{'test': 'data'}]
        mock_parse.return_value = {
            'timestamp': 1706745600,
            'exchange_netflow': -1234.56,
            'whale_inflow_count': 12,
            'asset': 'BTC',
            'source': 'dune'
        }
        
        result = fetcher_with_key.fetch_latest_metrics("BTC")
        
        assert result is not None
        assert result['asset'] == 'BTC'
        assert result['exchange_netflow'] == -1234.56
        assert result['whale_inflow_count'] == 12
    
    def test_save_to_database_success(self, fetcher_with_key):
        """測試：成功儲存到資料庫"""
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        metrics_data = {
            'timestamp': 1706745600,
            'exchange_netflow': -1234.56,
            'whale_inflow_count': 12,
            'asset': 'BTC',
            'source': 'dune',
            'extra_data': {}
        }
        
        with patch('app.models.onchain.ChainMetric') as mock_metric:
            result = fetcher_with_key.save_to_database(metrics_data, mock_session)
            
            assert result is True
            assert mock_session.add.called
            assert mock_session.commit.called
    
    def test_save_to_database_update_existing(self, fetcher_with_key):
        """測試：更新已存在的記錄"""
        mock_existing = Mock()
        mock_existing.id = 1
        
        mock_session = Mock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_existing
        
        metrics_data = {
            'timestamp': 1706745600,
            'exchange_netflow': -999.99,
            'whale_inflow_count': 5,
            'asset': 'BTC',
            'source': 'dune',
            'extra_data': {}
        }
        
        result = fetcher_with_key.save_to_database(metrics_data, mock_session)
        
        assert result is True
        assert mock_existing.exchange_netflow == -999.99
        assert mock_existing.whale_inflow_count == 5
        assert mock_session.commit.called
    
    def test_save_to_database_empty_data(self, fetcher_with_key):
        """測試：空數據無法儲存"""
        mock_session = Mock()
        result = fetcher_with_key.save_to_database(None, mock_session)
        assert result is False
    
    def test_save_to_database_exception(self, fetcher_with_key):
        """測試：資料庫錯誤處理"""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("DB Error")
        
        metrics_data = {
            'timestamp': 1706745600,
            'exchange_netflow': -1234.56,
            'whale_inflow_count': 12,
            'asset': 'BTC',
            'source': 'dune'
        }
        
        result = fetcher_with_key.save_to_database(metrics_data, mock_session)
        
        assert result is False
        assert mock_session.rollback.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

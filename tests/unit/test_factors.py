"""
Alpha Factors 單元測試
測試技術指標計算（RSI、布林通道、SMA 等）- 遵循 TDD 原則
"""
import pytest
import pandas as pd
import numpy as np
from app.core.strategy.factors import AlphaFactors


@pytest.fixture
def sample_price_data():
    """生成測試用的價格數據"""
    # 創建 50 根 K 線的模擬數據
    np.random.seed(42)
    
    dates = pd.date_range('2024-01-01', periods=50, freq='1h')
    
    # 生成趨勢向上的價格序列
    base_price = 45000
    trend = np.linspace(0, 2000, 50)
    noise = np.random.normal(0, 200, 50)
    close_prices = base_price + trend + noise
    
    # 生成 OHLCV 數據
    data = pd.DataFrame({
        'open': close_prices * (1 + np.random.uniform(-0.005, 0.005, 50)),
        'high': close_prices * (1 + np.random.uniform(0.005, 0.015, 50)),
        'low': close_prices * (1 - np.random.uniform(0.005, 0.015, 50)),
        'close': close_prices,
        'volume': np.random.uniform(100, 500, 50)
    }, index=dates)
    
    return data


@pytest.fixture
def uptrend_data():
    """明確的上升趨勢數據"""
    dates = pd.date_range('2024-01-01', periods=30, freq='1h')
    close_prices = np.linspace(40000, 45000, 30)
    
    return pd.DataFrame({
        'close': close_prices
    }, index=dates)


@pytest.fixture
def downtrend_data():
    """明確的下降趨勢數據"""
    dates = pd.date_range('2024-01-01', periods=30, freq='1h')
    close_prices = np.linspace(45000, 40000, 30)
    
    return pd.DataFrame({
        'close': close_prices
    }, index=dates)


class TestAlphaFactors:
    """Alpha 因子測試套件"""
    
    def test_rsi_range(self, sample_price_data):
        """測試：RSI 值應在 0-100 範圍內"""
        factors = AlphaFactors()
        
        rsi = factors.calculate_rsi(sample_price_data['close'], period=14)
        
        # RSI 必須在 0 到 100 之間
        assert (rsi >= 0).all(), "RSI 不應小於 0"
        assert (rsi <= 100).all(), "RSI 不應大於 100"
        
        # 應該有非 NaN 的值（排除前 14 個）
        assert rsi.notna().sum() > 0, "RSI 應該有計算結果"
    
    def test_rsi_uptrend(self, uptrend_data):
        """測試：上升趨勢中 RSI 應該偏高（> 50）"""
        factors = AlphaFactors()
        
        rsi = factors.calculate_rsi(uptrend_data['close'], period=14)
        
        # 取最後幾個非 NaN 的 RSI 值
        recent_rsi = rsi.dropna().iloc[-5:].mean()
        
        # 持續上漲應該導致 RSI > 50
        assert recent_rsi > 50, f"上升趨勢 RSI 應 > 50，實際: {recent_rsi}"
    
    def test_rsi_downtrend(self, downtrend_data):
        """測試：下降趨勢中 RSI 應該偏低（< 50）"""
        factors = AlphaFactors()
        
        rsi = factors.calculate_rsi(downtrend_data['close'], period=14)
        
        recent_rsi = rsi.dropna().iloc[-5:].mean()
        
        # 持續下跌應該導致 RSI < 50
        assert recent_rsi < 50, f"下降趨勢 RSI 應 < 50，實際: {recent_rsi}"
    
    def test_sma_calculation(self, sample_price_data):
        """測試：簡單移動平均線計算"""
        factors = AlphaFactors()
        
        sma_5 = factors.calculate_sma(sample_price_data['close'], period=5)
        sma_20 = factors.calculate_sma(sample_price_data['close'], period=20)
        
        # 檢查長度
        assert len(sma_5) == len(sample_price_data)
        assert len(sma_20) == len(sample_price_data)
        
        # 短週期 SMA 應該更貼近當前價格
        last_price = sample_price_data['close'].iloc[-1]
        last_sma5 = sma_5.iloc[-1]
        last_sma20 = sma_20.iloc[-1]
        
        # SMA5 應該比 SMA20 更接近最新價格
        assert abs(last_price - last_sma5) < abs(last_price - last_sma20)
    
    def test_bollinger_bands(self, sample_price_data):
        """測試：布林通道計算"""
        factors = AlphaFactors()
        
        upper, middle, lower = factors.calculate_bollinger_bands(
            sample_price_data['close'],
            period=20,
            std_dev=2
        )
        
        # 檢查關係：upper > middle > lower
        valid_idx = middle.notna()
        assert (upper[valid_idx] >= middle[valid_idx]).all(), "上軌應 >= 中軌"
        assert (middle[valid_idx] >= lower[valid_idx]).all(), "中軌應 >= 下軌"
        
        # 大部分價格應該在通道內
        close_prices = sample_price_data['close'][valid_idx]
        in_band = ((close_prices >= lower[valid_idx]) & (close_prices <= upper[valid_idx])).sum()
        total = valid_idx.sum()
        
        # 正常情況下，95% 的價格應該在 ±2σ 通道內
        assert in_band / total > 0.85, "大部分價格應在布林通道內"
    
    def test_bollinger_width(self, sample_price_data):
        """測試：布林通道寬度計算"""
        factors = AlphaFactors()
        
        width = factors.calculate_bollinger_width(sample_price_data['close'], period=20)
        
        # 寬度應該是正數
        assert (width[width.notna()] > 0).all(), "布林通道寬度應為正數"
        
        # 寬度應該有變化（不是常數）
        assert width.dropna().std() > 0, "布林通道寬度應該有變化"
    
    def test_ema_calculation(self, sample_price_data):
        """測試：指數移動平均線計算"""
        factors = AlphaFactors()
        
        ema_12 = factors.calculate_ema(sample_price_data['close'], period=12)
        ema_26 = factors.calculate_ema(sample_price_data['close'], period=26)
        
        # EMA 應該沒有 NaN（除了第一個可能）
        assert ema_12.notna().sum() >= len(sample_price_data) - 1
        
        # 短週期 EMA 應該更靈敏
        returns = sample_price_data['close'].pct_change()
        ema12_changes = ema_12.pct_change().abs()
        ema26_changes = ema_26.pct_change().abs()
        
        # 短週期變化應該更大
        assert ema12_changes.mean() >= ema26_changes.mean()
    
    def test_macd_calculation(self, sample_price_data):
        """測試：MACD 指標計算"""
        factors = AlphaFactors()
        
        macd, signal, histogram = factors.calculate_macd(sample_price_data['close'])
        
        # 檢查關係：histogram = macd - signal
        valid_idx = (macd.notna() & signal.notna() & histogram.notna())
        expected_histogram = macd[valid_idx] - signal[valid_idx]
        
        assert np.allclose(histogram[valid_idx], expected_histogram, rtol=1e-5)
    
    def test_volatility_calculation(self, sample_price_data):
        """測試：波動率計算"""
        factors = AlphaFactors()
        
        volatility = factors.calculate_volatility(sample_price_data['close'], window=20)
        
        # 波動率應該是正數
        assert (volatility[volatility.notna()] >= 0).all(), "波動率應為非負數"
        
        # 應該有合理的值（一般在 0.01 到 0.1 之間）
        mean_vol = volatility.dropna().mean()
        assert 0.001 < mean_vol < 1.0, f"波動率異常: {mean_vol}"
    
    def test_returns_calculation(self, sample_price_data):
        """測試：收益率計算"""
        factors = AlphaFactors()
        
        returns = factors.calculate_returns(sample_price_data['close'])
        
        # 第一個值應該是 NaN
        assert pd.isna(returns.iloc[0])
        
        # 手動驗證第二個收益率
        manual_return = (sample_price_data['close'].iloc[1] / sample_price_data['close'].iloc[0]) - 1
        assert abs(returns.iloc[1] - manual_return) < 1e-10
    
    def test_atr_calculation(self, sample_price_data):
        """測試：ATR (Average True Range) 計算"""
        factors = AlphaFactors()
        
        atr = factors.calculate_atr(
            sample_price_data['high'],
            sample_price_data['low'],
            sample_price_data['close'],
            period=14
        )
        
        # ATR 應該是正數
        assert (atr[atr.notna()] > 0).all(), "ATR 應為正數"


class TestCompositeScore:
    """組合評分測試"""
    
    def test_composite_score_range(self, sample_price_data):
        """測試：組合評分應該在 0-100 範圍內"""
        factors = AlphaFactors()
        
        score = factors.calculate_composite_score(sample_price_data)
        
        # 評分應該在 0 到 100 之間
        assert (score >= 0).all(), "評分不應小於 0"
        assert (score <= 100).all(), "評分不應大於 100"
    
    def test_composite_score_uptrend_high(self, uptrend_data):
        """測試：上升趨勢應該得到較高評分"""
        # 補充完整的 OHLCV 數據
        uptrend_data['open'] = uptrend_data['close']
        uptrend_data['high'] = uptrend_data['close'] * 1.01
        uptrend_data['low'] = uptrend_data['close'] * 0.99
        uptrend_data['volume'] = 100
        
        factors = AlphaFactors()
        score = factors.calculate_composite_score(uptrend_data)
        
        # 上升趨勢的平均評分應該 > 50
        avg_score = score.dropna().mean()
        assert avg_score > 50, f"上升趨勢評分應 > 50，實際: {avg_score}"

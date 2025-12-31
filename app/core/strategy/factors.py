"""
Alpha Factors - 技術指標計算模組
實現 RSI、布林通道、移動平均等技術分析指標
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional


class AlphaFactors:
    """技術指標計算器
    
    提供常用的技術分析指標計算，用於構建交易信號
    """
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算 RSI (Relative Strength Index) 相對強弱指標
        
        RSI = 100 - (100 / (1 + RS))
        RS = 平均漲幅 / 平均跌幅
        
        Args:
            prices: 價格序列
            period: 計算週期（預設 14）
        
        Returns:
            RSI 值序列（0-100 之間）
        """
        # 計算價格變化
        delta = prices.diff()
        
        # 分離漲跌
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # 計算平均漲跌幅（使用指數移動平均）
        avg_gains = gains.ewm(span=period, adjust=False).mean()
        avg_losses = losses.ewm(span=period, adjust=False).mean()
        
        # 避免除以零
        rs = avg_gains / avg_losses.replace(0, np.nan)
        
        # 計算 RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """計算 SMA (Simple Moving Average) 簡單移動平均
        
        Args:
            prices: 價格序列
            period: 計算週期
        
        Returns:
            SMA 值序列
        """
        return prices.rolling(window=period).mean()
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """計算 EMA (Exponential Moving Average) 指數移動平均
        
        EMA 對近期價格賦予更高權重，反應更靈敏
        
        Args:
            prices: 價格序列
            period: 計算週期
        
        Returns:
            EMA 值序列
        """
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算布林通道 (Bollinger Bands)
        
        中軌 = SMA(period)
        上軌 = 中軌 + std_dev * 標準差
        下軌 = 中軌 - std_dev * 標準差
        
        Args:
            prices: 價格序列
            period: 計算週期（預設 20）
            std_dev: 標準差倍數（預設 2）
        
        Returns:
            (upper_band, middle_band, lower_band) 三條軌道
        """
        middle_band = self.calculate_sma(prices, period)
        std = prices.rolling(window=period).std()
        
        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)
        
        return upper_band, middle_band, lower_band
    
    def calculate_bollinger_width(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.Series:
        """計算布林通道寬度
        
        寬度 = (上軌 - 下軌) / 中軌
        
        布林通道寬度反應市場波動性：
        - 寬度擴大：波動增加
        - 寬度收窄：波動減少（可能是突破前兆）
        
        Args:
            prices: 價格序列
            period: 計算週期
            std_dev: 標準差倍數
        
        Returns:
            布林通道寬度序列
        """
        upper, middle, lower = self.calculate_bollinger_bands(prices, period, std_dev)
        
        # 計算寬度百分比
        width = (upper - lower) / middle
        
        return width
    
    def calculate_macd(
        self,
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算 MACD (Moving Average Convergence Divergence)
        
        MACD = EMA(fast) - EMA(slow)
        Signal = EMA(MACD, signal_period)
        Histogram = MACD - Signal
        
        Args:
            prices: 價格序列
            fast_period: 快線週期（預設 12）
            slow_period: 慢線週期（預設 26）
            signal_period: 信號線週期（預設 9）
        
        Returns:
            (macd, signal, histogram)
        """
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        return macd, signal, histogram
    
    def calculate_volatility(
        self,
        prices: pd.Series,
        window: int = 20,
        annualize: bool = False
    ) -> pd.Series:
        """計算波動率（滾動標準差）
        
        Args:
            prices: 價格序列
            window: 滾動窗口
            annualize: 是否年化（假設一年 365 天）
        
        Returns:
            波動率序列
        """
        returns = prices.pct_change()
        volatility = returns.rolling(window=window).std()
        
        if annualize:
            # 假設每天 24 小時交易
            volatility = volatility * np.sqrt(365 * 24)
        
        return volatility
    
    def calculate_returns(self, prices: pd.Series) -> pd.Series:
        """計算收益率
        
        Args:
            prices: 價格序列
        
        Returns:
            收益率序列
        """
        return prices.pct_change()
    
    def calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """計算 ATR (Average True Range) 平均真實波幅
        
        True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
        ATR = EMA(True Range, period)
        
        Args:
            high: 最高價序列
            low: 最低價序列
            close: 收盤價序列
            period: 計算週期
        
        Returns:
            ATR 值序列
        """
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def calculate_onchain_zscore(
        self,
        metric_series: pd.Series,
        window: int = 30
    ) -> pd.Series:
        """計算鏈上指標的 Z-Score
        
        Z-Score = (當前值 - 均值) / 標準差
        
        用於判斷鏈上指標是否異常（例如交易所淨流入激增）
        
        Args:
            metric_series: 鏈上指標序列
            window: 滾動窗口
        
        Returns:
            Z-Score 序列
        """
        rolling_mean = metric_series.rolling(window=window).mean()
        rolling_std = metric_series.rolling(window=window).std()
        
        z_score = (metric_series - rolling_mean) / rolling_std.replace(0, np.nan)
        
        return z_score
    
    def calculate_composite_score(
        self,
        df: pd.DataFrame,
        weights: Optional[dict] = None
    ) -> pd.Series:
        """計算綜合評分（組合多個技術指標）
        
        綜合考慮 RSI、趨勢、波動率等因素，產生 0-100 的評分
        
        Args:
            df: OHLCV DataFrame
            weights: 各指標權重字典（可選）
        
        Returns:
            綜合評分序列（0-100）
        """
        if weights is None:
            weights = {
                'rsi': 0.3,
                'trend': 0.3,
                'volatility': 0.2,
                'volume': 0.2
            }
        
        scores = []
        
        # 1. RSI 評分（50 為中性）
        rsi = self.calculate_rsi(df['close'])
        rsi_score = rsi  # RSI 本身就是 0-100
        scores.append(('rsi', rsi_score * weights['rsi']))
        
        # 2. 趨勢評分（使用 MACD）
        macd, signal, _ = self.calculate_macd(df['close'])
        trend_score = ((macd > signal).astype(int) * 100)  # 多頭100，空頭0
        scores.append(('trend', trend_score * weights['trend']))
        
        # 3. 波動率評分（低波動給高分）
        volatility = self.calculate_volatility(df['close'])
        vol_normalized = 1 - (volatility / volatility.max())  # 反轉：低波動=高分
        vol_score = vol_normalized * 100
        scores.append(('volatility', vol_score * weights['volatility']))
        
        # 4. 成交量評分（相對成交量）
        volume_ma = df['volume'].rolling(window=20).mean()
        volume_ratio = df['volume'] / volume_ma
        volume_score = np.clip(volume_ratio * 50, 0, 100)  # 標準化到 0-100
        scores.append(('volume', volume_score * weights['volume']))
        
        # 加總所有評分
        composite = sum([score for _, score in scores])
        
        # 確保在 0-100 範圍內
        composite = np.clip(composite, 0, 100)
        
        return composite

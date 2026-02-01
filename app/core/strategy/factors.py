"""
Alpha Factors - 技術指標計算模組
實現 RSI、布林通道、移動平均等技術分析指標

Phase 6: 新增鏈上數據整合功能
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


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
        weights: Optional[dict] = None,
        onchain_zscore: Optional[float] = None
    ) -> pd.Series:
        """計算綜合評分（組合多個技術指標 + 鏈上數據）
        
        綜合考慮 RSI、趨勢、波動率、成交量及鏈上指標，產生 0-100 的評分
        
        Phase 6 更新：
        - 新增鏈上數據整合（Exchange Netflow Z-Score）
        - 異常流入（Z > 2.0）-> 扣分（看空信號）
        - 異常流出（Z < -2.0）-> 加分（看多信號）
        
        Args:
            df: OHLCV DataFrame
            weights: 各指標權重字典（可選）
            onchain_zscore: 鏈上指標 Z-Score（交易所淨流入）
        
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
        
        # === Phase 6: 鏈上數據調整 ===
        if onchain_zscore is not None:
            if onchain_zscore > 2.0:
                # 異常流入（大量幣流入交易所）-> 拋壓增加 -> 看空
                adjustment = -20
                composite = composite + adjustment
                composite = np.clip(composite, 0, 100)
            elif onchain_zscore < -2.0:
                # 異常流出（大量幣流出交易所）-> 囤幣行為 -> 看多
                adjustment = 10
                composite = composite + adjustment
                composite = np.clip(composite, 0, 100)
        
        return composite


def get_latest_onchain_zscore(db_session, asset: str = 'BTC', window: int = 30) -> Optional[float]:
    """
    從資料庫獲取最新的鏈上指標 Z-Score
    
    Phase 6: 輔助函數，用於策略引擎整合
    
    Args:
        db_session: SQLAlchemy session
        asset: 資產名稱（BTC, ETH 等）
        window: Z-Score 計算窗口
    
    Returns:
        最新的 Exchange Netflow Z-Score，若無數據則返回 None
    """
    from app.models.onchain import ChainMetric
    
    try:
        # 獲取最近 window 筆數據
        metrics = db_session.query(ChainMetric).filter_by(
            asset=asset,
            metric_name='dune_composite',
            source='dune'
        ).order_by(ChainMetric.timestamp.desc()).limit(window).all()
        
        if len(metrics) < 2:
            logger.warning(f"鏈上數據不足（需要至少 2 筆），目前只有 {len(metrics)} 筆")
            return None
        
        # 提取 netflow 數據
        netflows = [m.exchange_netflow for m in reversed(metrics) if m.exchange_netflow is not None]
        
        if len(netflows) < 2:
            logger.warning(f"有效 netflow 數據不足")
            return None
        
        # 計算 Z-Score
        netflow_series = pd.Series(netflows)
        mean = netflow_series.mean()
        std = netflow_series.std()
        
        if std == 0:
            logger.warning("標準差為 0，無法計算 Z-Score")
            return None
        
        latest_netflow = netflows[-1]
        z_score = (latest_netflow - mean) / std
        
        logger.info(f"鏈上 Z-Score: {z_score:.2f} (Netflow: {latest_netflow:.2f})")
        
        return float(z_score)
    
    except Exception as e:
        logger.error(f"獲取鏈上 Z-Score 失敗: {e}", exc_info=True)
        return None

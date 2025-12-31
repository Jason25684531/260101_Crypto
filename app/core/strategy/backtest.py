"""
回測引擎 - 使用 VectorBT 執行策略回測
支援 RSI、布林帶等技術指標策略
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 嘗試導入 vectorbt，如果失敗則使用純 pandas 實現
try:
    import vectorbt as vbt
    HAS_VECTORBT = True
except ImportError:
    HAS_VECTORBT = False
    logger.warning("⚠️ vectorbt 未安裝，使用純 pandas 實現回測")


class BacktestEngine:
    """
    策略回測引擎
    
    支援策略：
    - RSI 超買超賣策略
    - 布林帶突破策略
    - 綜合策略
    """
    
    def __init__(
        self,
        initial_capital: float = 10000,
        commission: float = 0.001,  # 0.1% 手續費
        slippage: float = 0.001     # 0.1% 滑點
    ):
        """
        初始化回測引擎
        
        Args:
            initial_capital: 初始資金
            commission: 交易手續費比例
            slippage: 滑點比例
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        logger.info(f"✅ BacktestEngine 初始化: 資金=${initial_capital}, 手續費={commission*100}%")
    
    def load_data_from_db(
        self,
        symbol: str = 'BTC/USDT',
        timeframe: str = '1h',
        limit: int = 500
    ) -> pd.DataFrame:
        """
        從資料庫載入數據
        
        Args:
            symbol: 交易對
            timeframe: 時間週期
            limit: 數量上限
        
        Returns:
            DataFrame with OHLCV data
        """
        from app import create_app
        from app.extensions import db
        from app.models import OHLCV
        
        app = create_app()
        
        with app.app_context():
            records = OHLCV.query.filter_by(
                symbol=symbol,
                timeframe=timeframe
            ).order_by(OHLCV.timestamp.asc()).limit(limit).all()
            
            if not records:
                logger.warning(f"⚠️ 資料庫中無 {symbol} {timeframe} 數據")
                return pd.DataFrame()
            
            data = []
            for r in records:
                data.append({
                    'timestamp': pd.to_datetime(r.timestamp, unit='ms'),
                    'open': float(r.open),
                    'high': float(r.high),
                    'low': float(r.low),
                    'close': float(r.close),
                    'volume': float(r.volume)
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"✅ 從資料庫載入 {len(df)} 筆 {symbol} 數據")
            return df
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算 RSI 指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算布林帶"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def run_rsi_strategy(
        self,
        df: pd.DataFrame,
        rsi_period: int = 14,
        rsi_lower: float = 30,
        rsi_upper: float = 70
    ) -> Dict:
        """
        執行 RSI 策略回測
        
        策略邏輯：
        - RSI < 30: 買入信號
        - RSI > 70: 賣出信號
        
        Args:
            df: OHLCV DataFrame
            rsi_period: RSI 週期
            rsi_lower: 超賣閾值（買入）
            rsi_upper: 超買閾值（賣出）
        
        Returns:
            dict: 回測結果（總報酬、夏普比率、最大回撤等）
        """
        if df.empty:
            return self._empty_result()
        
        close = df['close']
        
        # 計算 RSI
        rsi = self.calculate_rsi(close, rsi_period)
        
        # 生成信號
        entries = rsi < rsi_lower  # RSI < 30 買入
        exits = rsi > rsi_upper    # RSI > 70 賣出
        
        if HAS_VECTORBT:
            return self._run_vectorbt_backtest(close, entries, exits)
        else:
            return self._run_pandas_backtest(df, entries, exits)
    
    def run_bollinger_strategy(
        self,
        df: pd.DataFrame,
        bb_period: int = 20,
        bb_std: float = 2.0
    ) -> Dict:
        """
        執行布林帶策略回測
        
        策略邏輯：
        - 價格觸及下軌: 買入
        - 價格觸及上軌: 賣出
        """
        if df.empty:
            return self._empty_result()
        
        close = df['close']
        upper, middle, lower = self.calculate_bollinger_bands(close, bb_period, bb_std)
        
        entries = close <= lower
        exits = close >= upper
        
        if HAS_VECTORBT:
            return self._run_vectorbt_backtest(close, entries, exits)
        else:
            return self._run_pandas_backtest(df, entries, exits)
    
    def _run_vectorbt_backtest(
        self,
        close: pd.Series,
        entries: pd.Series,
        exits: pd.Series
    ) -> Dict:
        """使用 VectorBT 執行回測"""
        try:
            portfolio = vbt.Portfolio.from_signals(
                close,
                entries,
                exits,
                init_cash=self.initial_capital,
                fees=self.commission,
                slippage=self.slippage,
                freq='1h'
            )
            
            stats = portfolio.stats()
            
            result = {
                'total_return': float(stats.get('Total Return [%]', 0)) / 100,
                'sharpe_ratio': float(stats.get('Sharpe Ratio', 0)),
                'max_drawdown': float(stats.get('Max Drawdown [%]', 0)) / 100,
                'win_rate': float(stats.get('Win Rate [%]', 0)) / 100,
                'total_trades': int(stats.get('Total Trades', 0)),
                'profit_factor': float(stats.get('Profit Factor', 0)),
                'final_value': float(portfolio.final_value()),
                'equity_curve': portfolio.value().tolist(),
                'equity_dates': portfolio.value().index.strftime('%Y-%m-%d %H:%M').tolist(),
                'portfolio': portfolio,
                'success': True
            }
            
            logger.info(f"✅ VectorBT 回測完成: 總報酬={result['total_return']:.2%}")
            return result
            
        except Exception as e:
            logger.error(f"❌ VectorBT 回測失敗: {e}")
            return self._empty_result()
    
    def _run_pandas_backtest(
        self,
        df: pd.DataFrame,
        entries: pd.Series,
        exits: pd.Series
    ) -> Dict:
        """使用純 Pandas 執行簡易回測"""
        close = df['close']
        
        # 模擬交易
        position = 0
        cash = self.initial_capital
        equity = []
        trades = 0
        wins = 0
        entry_price = 0
        
        for i in range(len(close)):
            if entries.iloc[i] and position == 0:
                # 買入
                position = cash / close.iloc[i]
                cash = 0
                entry_price = close.iloc[i]
                trades += 1
            elif exits.iloc[i] and position > 0:
                # 賣出
                cash = position * close.iloc[i] * (1 - self.commission)
                if close.iloc[i] > entry_price:
                    wins += 1
                position = 0
            
            # 計算當前權益
            current_equity = cash + position * close.iloc[i]
            equity.append(current_equity)
        
        equity_series = pd.Series(equity, index=close.index)
        
        # 計算指標
        total_return = (equity[-1] - self.initial_capital) / self.initial_capital
        
        # 計算最大回撤
        peak = equity_series.expanding(min_periods=1).max()
        drawdown = (equity_series - peak) / peak
        max_drawdown = drawdown.min()
        
        # 計算夏普比率（簡化版）
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(24 * 365) if returns.std() > 0 else 0
        
        win_rate = wins / trades if trades > 0 else 0
        
        result = {
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'total_trades': trades,
            'profit_factor': 0,  # 純 pandas 不計算
            'final_value': float(equity[-1]),
            'equity_curve': equity,
            'equity_dates': close.index.strftime('%Y-%m-%d %H:%M').tolist(),
            'portfolio': None,
            'success': True
        }
        
        logger.info(f"✅ Pandas 回測完成: 總報酬={result['total_return']:.2%}")
        return result
    
    def _empty_result(self) -> Dict:
        """返回空結果"""
        return {
            'total_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'total_trades': 0,
            'profit_factor': 0,
            'final_value': self.initial_capital,
            'equity_curve': [],
            'equity_dates': [],
            'portfolio': None,
            'success': False
        }


def run_backtest(
    symbol: str = 'BTC/USDT',
    timeframe: str = '1h',
    strategy: str = 'rsi',
    initial_capital: float = 10000
) -> Dict:
    """
    便捷函數：執行回測
    
    Args:
        symbol: 交易對
        timeframe: 時間週期
        strategy: 策略類型（'rsi' 或 'bollinger'）
        initial_capital: 初始資金
    
    Returns:
        回測結果字典
    """
    engine = BacktestEngine(initial_capital=initial_capital)
    df = engine.load_data_from_db(symbol, timeframe)
    
    if strategy == 'rsi':
        return engine.run_rsi_strategy(df)
    elif strategy == 'bollinger':
        return engine.run_bollinger_strategy(df)
    else:
        raise ValueError(f"不支援的策略: {strategy}")

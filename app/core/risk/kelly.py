"""
Kelly Criterion 倉位管理器
動態計算最佳投注比例，基於勝率、賠率和波動率
"""
import numpy as np
from typing import Optional


class KellyCalculator:
    """凱利準則計算器
    
    實現經典凱利公式和變體（Half-Kelly、Quarter-Kelly）
    用於計算最優倉位大小，平衡收益與風險
    
    凱利公式：
        f* = (p * b - q) / b
    
    其中：
        f* = 最佳投注比例
        p = 勝率（獲利概率）
        q = 1 - p（虧損概率）
        b = 賠率（盈虧比）
    """
    
    def __init__(
        self,
        fraction: float = 1.0,
        max_position: float = 1.0,
        min_position: float = 0.0
    ):
        """初始化凱利計算器
        
        Args:
            fraction: 凱利分數（1.0=Full Kelly, 0.5=Half Kelly, 0.25=Quarter Kelly）
            max_position: 最大倉位限制（防止過度槓桿）
            min_position: 最小倉位（預設 0，不做空）
        """
        if not 0 < fraction <= 1.0:
            raise ValueError("凱利分數必須在 (0, 1] 範圍內")
        
        self.fraction = fraction
        self.max_position = max_position
        self.min_position = min_position
    
    def calculate(self, win_rate: float, odds: float) -> float:
        """計算凱利倉位
        
        Args:
            win_rate: 勝率（0 到 1 之間）
            odds: 賠率（盈虧比，例如 1.0 表示 1:1）
        
        Returns:
            最佳投注比例（0 到 1 之間）
        
        Raises:
            ValueError: 輸入參數無效
        
        Examples:
            >>> kelly = KellyCalculator()
            >>> kelly.calculate(0.6, 1.0)  # 60% 勝率，1:1 賠率
            0.2  # 建議 20% 倉位
        """
        # 驗證輸入
        if not 0 <= win_rate <= 1:
            raise ValueError(f"勝率必須在 [0, 1] 範圍內，當前值: {win_rate}")
        
        if odds < 0:
            raise ValueError(f"賠率不能為負數，當前值: {odds}")
        
        # 計算敗率
        lose_rate = 1 - win_rate
        
        # 凱利公式：(p * b - q) / b
        if odds == 0:
            return 0.0
        
        kelly_value = (win_rate * odds - lose_rate) / odds
        
        # 應用凱利分數（保守調整）
        adjusted_kelly = kelly_value * self.fraction
        
        # 負凱利值表示無優勢，不應開倉
        if adjusted_kelly < 0:
            return 0.0
        
        # 應用倉位限制
        position_size = np.clip(adjusted_kelly, self.min_position, self.max_position)
        
        return float(position_size)
    
    def calculate_with_volatility(
        self,
        win_rate: float,
        odds: float,
        volatility: float,
        volatility_adjustment: float = 2.0
    ) -> float:
        """考慮波動率的凱利計算
        
        在高波動環境下降低倉位，以控制風險
        
        Args:
            win_rate: 勝率
            odds: 賠率
            volatility: 波動率（標準差）
            volatility_adjustment: 波動率調整係數（越大越保守）
        
        Returns:
            調整後的倉位大小
        """
        # 基礎凱利倉位
        base_kelly = self.calculate(win_rate, odds)
        
        # 波動率懲罰因子：volatility 越高，懲罰越大
        # 使用倒數關係：position = kelly / (1 + k * volatility)
        volatility_factor = 1.0 / (1.0 + volatility_adjustment * volatility)
        
        adjusted_position = base_kelly * volatility_factor
        
        # 應用最大倉位限制
        return min(adjusted_position, self.max_position)
    
    def calculate_from_returns(
        self,
        returns: np.ndarray,
        lookback_periods: int = 50
    ) -> float:
        """從歷史收益率計算凱利倉位
        
        自動計算勝率、平均盈虧比和波動率
        
        Args:
            returns: 歷史收益率陣列
            lookback_periods: 回溯期數（預設 50 筆交易）
        
        Returns:
            建議倉位大小
        """
        if len(returns) == 0:
            return 0.0
        
        # 只使用最近的 N 筆數據
        recent_returns = returns[-lookback_periods:] if len(returns) > lookback_periods else returns
        
        # 計算勝率
        wins = recent_returns[recent_returns > 0]
        losses = recent_returns[recent_returns < 0]
        
        if len(recent_returns) == 0:
            return 0.0
        
        win_rate = len(wins) / len(recent_returns)
        
        # 計算平均盈虧比
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        
        # 賠率 = 平均盈利 / 平均虧損
        odds = avg_win / avg_loss if avg_loss > 0 else 0
        
        # 計算波動率
        volatility = recent_returns.std()
        
        # 使用波動率調整的凱利計算
        return self.calculate_with_volatility(win_rate, odds, volatility)
    
    def get_position_for_account(
        self,
        win_rate: float,
        odds: float,
        account_balance: float,
        price: float
    ) -> float:
        """計算實際可下單的合約數量
        
        Args:
            win_rate: 勝率
            odds: 賠率
            account_balance: 賬戶餘額（USDT）
            price: 當前價格
        
        Returns:
            建議下單數量（合約張數）
        """
        # 計算倉位比例
        position_ratio = self.calculate(win_rate, odds)
        
        # 計算可用資金
        position_value = account_balance * position_ratio
        
        # 計算合約數量
        quantity = position_value / price if price > 0 else 0
        
        return quantity
    
    def __repr__(self):
        return (f"KellyCalculator(fraction={self.fraction}, "
                f"max_position={self.max_position})")

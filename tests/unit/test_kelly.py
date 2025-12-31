"""
Kelly Criterion 單元測試
測試動態倉位管理邏輯 - 遵循 TDD 原則
"""
import pytest
import numpy as np
from app.core.risk.kelly import KellyCalculator


class TestKellyCalculator:
    """凱利準則計算器測試套件"""
    
    def test_full_kelly_with_perfect_win_rate(self):
        """測試：勝率 100%，賠率 1:1 -> 應全倉（100%）"""
        kelly = KellyCalculator()
        
        win_rate = 1.0  # 100% 勝率
        odds = 1.0      # 1:1 賠率
        
        position_size = kelly.calculate(win_rate, odds)
        
        # 凱利公式：(1.0 * 1.0 - 0.0) / 1.0 = 1.0
        assert position_size == 1.0, "完美勝率應該全倉"
    
    def test_zero_kelly_with_zero_win_rate(self):
        """測試：勝率 0% -> 應空倉（0%）"""
        kelly = KellyCalculator()
        
        win_rate = 0.0
        odds = 1.0
        
        position_size = kelly.calculate(win_rate, odds)
        
        # 勝率為 0，絕對不應該下注
        assert position_size == 0.0, "零勝率應該空倉"
    
    def test_zero_kelly_with_no_edge(self):
        """測試：勝率 50%，賠率 1:1 -> 無優勢，應空倉（0%）"""
        kelly = KellyCalculator()
        
        win_rate = 0.5  # 50% 勝率
        odds = 1.0      # 1:1 賠率
        
        position_size = kelly.calculate(win_rate, odds)
        
        # 凱利公式：(0.5 * 1.0 - 0.5) / 1.0 = 0.0
        # 沒有期望值優勢，不應下注
        assert position_size == 0.0, "無優勢情況應該空倉"
    
    def test_positive_kelly_with_edge(self):
        """測試：勝率 60%，賠率 1:1 -> 有優勢，應開倉"""
        kelly = KellyCalculator()
        
        win_rate = 0.6
        odds = 1.0
        
        position_size = kelly.calculate(win_rate, odds)
        
        # 凱利公式：(0.6 * 1.0 - 0.4) / 1.0 = 0.2
        assert position_size == pytest.approx(0.2, rel=1e-6)
    
    def test_half_kelly_mode(self):
        """測試：Half-Kelly 模式（保守投注）"""
        kelly = KellyCalculator(fraction=0.5)
        
        win_rate = 0.6
        odds = 1.0
        
        # Full Kelly = 0.2
        full_kelly = 0.2
        
        position_size = kelly.calculate(win_rate, odds)
        
        # Half-Kelly 應該是 Full Kelly 的一半
        assert position_size == pytest.approx(full_kelly * 0.5, rel=1e-6)
    
    def test_quarter_kelly_mode(self):
        """測試：Quarter-Kelly 模式（極保守）"""
        kelly = KellyCalculator(fraction=0.25)
        
        win_rate = 0.7
        odds = 1.5
        
        # Full Kelly = (0.7 * 1.5 - 0.3) / 1.5 = 0.5
        full_kelly = (0.7 * 1.5 - 0.3) / 1.5
        
        position_size = kelly.calculate(win_rate, odds)
        
        assert position_size == pytest.approx(full_kelly * 0.25, rel=1e-6)
    
    def test_negative_kelly_returns_zero(self):
        """測試：負凱利值應返回 0（不應做空，安全機制）"""
        kelly = KellyCalculator()
        
        win_rate = 0.3  # 30% 勝率
        odds = 1.0      # 1:1 賠率
        
        position_size = kelly.calculate(win_rate, odds)
        
        # 凱利公式：(0.3 * 1.0 - 0.7) / 1.0 = -0.4
        # 但我們不做空，應該返回 0
        assert position_size == 0.0
    
    def test_high_odds_with_moderate_win_rate(self):
        """測試：高賠率 + 中等勝率的情況"""
        kelly = KellyCalculator()
        
        win_rate = 0.55  # 55% 勝率
        odds = 2.0       # 2:1 賠率（賺 2 倍）
        
        position_size = kelly.calculate(win_rate, odds)
        
        # 凱利公式：(0.55 * 2.0 - 0.45) / 2.0 = 0.325
        expected = (0.55 * 2.0 - 0.45) / 2.0
        assert position_size == pytest.approx(expected, rel=1e-6)
    
    def test_volatility_adjustment(self):
        """測試：根據波動率調整倉位"""
        kelly = KellyCalculator(max_position=0.3)
        
        win_rate = 0.8
        odds = 1.0
        volatility = 0.05  # 5% 波動率
        
        # 基礎凱利 = 0.6，但應該根據波動率降低
        position_size = kelly.calculate_with_volatility(
            win_rate, odds, volatility
        )
        
        # 波動率越高，倉位應該越小
        assert 0 < position_size <= 0.3
    
    def test_max_position_cap(self):
        """測試：最大倉位限制"""
        kelly = KellyCalculator(max_position=0.5)
        
        win_rate = 0.9
        odds = 1.0
        
        # Full Kelly = 0.8，但應該被 cap 在 0.5
        position_size = kelly.calculate(win_rate, odds)
        
        assert position_size <= 0.5
    
    def test_invalid_inputs(self):
        """測試：無效輸入應拋出錯誤或返回 0"""
        kelly = KellyCalculator()
        
        # 勝率超過 1
        with pytest.raises(ValueError):
            kelly.calculate(1.5, 1.0)
        
        # 負勝率
        with pytest.raises(ValueError):
            kelly.calculate(-0.1, 1.0)
        
        # 負賠率
        with pytest.raises(ValueError):
            kelly.calculate(0.6, -1.0)


class TestKellyWithHistoricalData:
    """基於歷史數據計算凱利的測試"""
    
    def test_calculate_from_trade_history(self):
        """測試：從交易歷史計算勝率和賠率"""
        kelly = KellyCalculator()
        
        # 模擬交易歷史：[收益率1, 收益率2, ...]
        returns = np.array([0.05, -0.02, 0.03, -0.01, 0.04, 0.06, -0.03])
        
        # 計算勝率和平均賠率
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        win_rate = len(wins) / len(returns)
        avg_win = wins.mean()
        avg_loss = abs(losses.mean())
        odds = avg_win / avg_loss if avg_loss > 0 else 0
        
        position_size = kelly.calculate(win_rate, odds)
        
        # 應該返回合理的倉位（0 到 1 之間）
        assert 0 <= position_size <= 1

"""
模拟交易所（Paper Exchange）
Paper Trading Exchange Implementation

功能：
1. 模拟 ccxt 交易所接口
2. 维护虚拟余额和持仓
3. 记录交易历史
4. 支持状态持久化
"""
import ccxt
import json
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


class PaperExchange:
    """
    模拟交易所
    
    模拟 ccxt 接口，允许无风险地测试交易策略
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        ledger_file: str = 'data/paper_ledger.json'
    ):
        """
        初始化模拟交易所
        
        Args:
            initial_balance: 初始 USDT 余额
            ledger_file: 账本文件路径（用于持久化）
        """
        self.initial_balance = initial_balance
        self.ledger_file = ledger_file
        
        # 价格数据源（用于获取真实市场价格）
        self._price_source = ccxt.binance({
            'enableRateLimit': True,
            'timeout': 30000,
        })
        
        # 虚拟余额（{币种: 数量}）
        self.balances = {
            'USDT': initial_balance
        }
        
        # 订单历史
        self.order_history = []
        
        # 订单 ID 计数器
        self._order_id_counter = 1
        
        # 从文件恢复状态（如果存在）
        self._load_state()
        
        logger.info(
            f"🟢 PaperExchange 初始化完成 - "
            f"初始余额: ${initial_balance:,.2f} USDT"
        )
    
    def _load_state(self):
        """从文件加载状态"""
        if os.path.exists(self.ledger_file):
            try:
                with open(self.ledger_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                self.balances = state.get('balances', {'USDT': self.initial_balance})
                self.order_history = state.get('order_history', [])
                self._order_id_counter = state.get('order_id_counter', 1)
                
                logger.info(f"✅ 已从 {self.ledger_file} 恢复状态")
            except Exception as e:
                logger.warning(f"⚠️  无法加载状态文件: {e}")
    
    def _save_state(self):
        """保存状态到文件"""
        try:
            # 如果 ledger_file 路径为空，跳过保存
            if not self.ledger_file:
                return
            
            # 确保目录存在
            ledger_dir = os.path.dirname(self.ledger_file)
            if ledger_dir:  # 只有当目录路径不为空时才创建
                os.makedirs(ledger_dir, exist_ok=True)
            
            state = {
                'balances': self.balances,
                'order_history': self.order_history,
                'order_id_counter': self._order_id_counter
            }
            
            with open(self.ledger_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ 无法保存状态: {e}")
    
    def fetch_balance(self) -> Dict:
        """
        获取虚拟余额
        
        Returns:
            余额字典（兼容 ccxt 格式）
        """
        balance = {
            'free': deepcopy(self.balances),
            'used': {},  # 暂不实现锁定余额
            'total': deepcopy(self.balances)
        }
        
        return balance
    
    def fetch_ticker(self, symbol: str) -> Dict:
        """
        获取真实市场价格
        
        Args:
            symbol: 交易对（如 'BTC/USDT'）
        
        Returns:
            价格信息（从真实交易所获取）
        """
        try:
            ticker = self._price_source.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"❌ 获取价格失败 {symbol}: {e}")
            # 返回一个默认价格（仅用于测试）
            return {
                'symbol': symbol,
                'last': 50000.0,
                'bid': 49990.0,
                'ask': 50010.0
            }
    
    def create_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: dict = None
    ) -> Dict:
        """
        创建虚拟订单
        
        Args:
            symbol: 交易对（如 'BTC/USDT'）
            type: 订单类型（'limit' 或 'market'）
            side: 方向（'buy' 或 'sell'）
            amount: 数量
            price: 价格（市价单可为 None）
            params: 额外参数
        
        Returns:
            订单信息
        
        Raises:
            ValueError: 余额不足时
        """
        # 解析交易对
        base, quote = symbol.split('/')
        
        # 确定成交价格
        if type == 'market' or price is None:
            ticker = self.fetch_ticker(symbol)
            # 买入用卖价（ask），卖出用买价（bid）
            execution_price = ticker['ask'] if side == 'buy' else ticker['bid']
        else:
            execution_price = price
        
        # 计算交易金额
        total_cost = amount * execution_price
        
        # 验证余额
        if side == 'buy':
            # 买入：需要足够的 USDT
            if self.balances.get(quote, 0) < total_cost:
                raise ValueError(
                    f"余额不足: 需要 {total_cost:.2f} {quote}, "
                    f"当前仅有 {self.balances.get(quote, 0):.2f} {quote}"
                )
        else:
            # 卖出：需要足够的币
            if self.balances.get(base, 0) < amount:
                raise ValueError(
                    f"余额不足: 需要 {amount} {base}, "
                    f"当前仅有 {self.balances.get(base, 0)} {base}"
                )
        
        # 更新余额
        if side == 'buy':
            # 扣除 USDT，增加币
            self.balances[quote] = self.balances.get(quote, 0) - total_cost
            self.balances[base] = self.balances.get(base, 0) + amount
        else:
            # 扣除币，增加 USDT
            self.balances[base] = self.balances.get(base, 0) - amount
            self.balances[quote] = self.balances.get(quote, 0) + total_cost
        
        # 生成订单
        order_id = f"PAPER_{self._order_id_counter}"
        self._order_id_counter += 1
        
        order = {
            'id': order_id,
            'symbol': symbol,
            'type': type,
            'side': side,
            'amount': amount,
            'price': execution_price,
            'cost': total_cost,
            'status': 'closed',  # 模拟交易所立即成交
            'timestamp': int(datetime.utcnow().timestamp() * 1000),
            'datetime': datetime.utcnow().isoformat()
        }
        
        # 记录订单历史
        self.order_history.append(order)
        
        # 保存状态
        self._save_state()
        
        logger.info(
            f"📝 虚拟订单成交 - {side.upper()} {amount} {symbol} @ ${execution_price:,.2f}"
        )
        
        return order
    
    def get_order_history(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        获取订单历史
        
        Args:
            symbol: 交易对（可选，不传则返回所有）
        
        Returns:
            订单列表
        """
        if symbol:
            return [o for o in self.order_history if o['symbol'] == symbol]
        return self.order_history
    
    def calculate_unrealized_pnl(self) -> float:
        """
        计算未实现盈亏（Unrealized PnL）
        
        Returns:
            未实现盈亏（USDT）
        """
        total_value = self.balances.get('USDT', 0)
        
        # 计算所有币种的当前市值
        for coin, amount in self.balances.items():
            if coin != 'USDT' and amount > 0:
                try:
                    symbol = f"{coin}/USDT"
                    ticker = self.fetch_ticker(symbol)
                    coin_value = amount * ticker['last']
                    total_value += coin_value
                except Exception as e:
                    logger.warning(f"⚠️  无法获取 {coin} 价格: {e}")
        
        # 未实现盈亏 = 当前总值 - 初始资金
        pnl = total_value - self.initial_balance
        
        return pnl
    
    def get_portfolio_summary(self) -> Dict:
        """
        获取投资组合摘要
        
        Returns:
            投资组合信息
        """
        total_value = self.balances.get('USDT', 0)
        holdings = {}
        
        for coin, amount in self.balances.items():
            if coin != 'USDT' and amount > 0:
                try:
                    symbol = f"{coin}/USDT"
                    ticker = self.fetch_ticker(symbol)
                    coin_value = amount * ticker['last']
                    total_value += coin_value
                    
                    holdings[coin] = {
                        'amount': amount,
                        'price': ticker['last'],
                        'value': coin_value
                    }
                except Exception:
                    pass
        
        unrealized_pnl = total_value - self.initial_balance
        roi = (unrealized_pnl / self.initial_balance) * 100
        
        return {
            'initial_balance': self.initial_balance,
            'current_value': total_value,
            'unrealized_pnl': unrealized_pnl,
            'roi_percent': roi,
            'holdings': holdings,
            'usdt_balance': self.balances.get('USDT', 0),
            'total_trades': len(self.order_history)
        }
    
    def reset(self):
        """重置账户到初始状态"""
        self.balances = {'USDT': self.initial_balance}
        self.order_history = []
        self._order_id_counter = 1
        self._save_state()
        
        logger.info("🔄 账户已重置到初始状态")
    
    def close(self):
        """关闭连接（清理资源）"""
        # 保存最终状态
        self._save_state()
        logger.info("🔒 PaperExchange 已关闭")

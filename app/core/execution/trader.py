"""
交易執行器 (TradeExecutor)
負責實際的交易執行、止盈止損管理、安全檢查
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TradeExecutor:
    """
    交易執行器
    
    功能：
    1. 執行買入/賣出訂單（通過 CCXT）
    2. 計算止盈止損價格
    3. 監控持倉並自動執行止盈止損
    4. PanicScore 安全檢查（高風險時拒絕交易）
    """
    
    def __init__(
        self,
        exchange,
        max_position_size: float = 0.3,
        stop_loss_percent: float = 0.05,
        take_profit_min: float = 0.10,
        take_profit_max: float = 0.20,
        panic_threshold: float = 0.80
    ):
        """
        初始化交易執行器
        
        Args:
            exchange: CCXT Exchange 實例
            max_position_size: 單一持倉最大資金比例（預設 30%）
            stop_loss_percent: 停損百分比（預設 5%）
            take_profit_min: 最低獲利目標（預設 10%）
            take_profit_max: 最高獲利目標（預設 20%）
            panic_threshold: PanicScore 警戒線（預設 0.80）
        """
        self.exchange = exchange
        self.max_position_size = max_position_size
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_min = take_profit_min
        self.take_profit_max = take_profit_max
        self.panic_threshold = panic_threshold
        
        logger.info(
            f"TradeExecutor 初始化完成 - "
            f"停損: {stop_loss_percent*100}%, "
            f"止盈: {take_profit_min*100}%-{take_profit_max*100}%"
        )
    
    def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        order_type: str = 'limit',
        panic_score: Optional[float] = None
    ) -> Dict:
        """
        下單（買入或賣出）
        
        Args:
            symbol: 交易對（如 BTC/USDT）
            side: 'buy' 或 'sell'
            amount: 數量
            price: 價格（如果是市價單則為 None）
            order_type: 訂單類型（'limit' 或 'market'）
            panic_score: 恐慌指數（0-1），高於閾值時拒絕買入
        
        Returns:
            訂單結果字典
        
        Raises:
            ValueError: 當 PanicScore 過高時
        """
        # 安全檢查：PanicScore 過高時拒絕買入
        if side == 'buy' and panic_score is not None:
            if panic_score > self.panic_threshold:
                error_msg = (
                    f"PanicScore 過高 ({panic_score:.2f} > {self.panic_threshold:.2f})，"
                    f"拒絕買入訂單"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        try:
            # 執行下單
            if order_type == 'limit' and price is not None:
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='limit',
                    side=side,
                    amount=amount,
                    price=price
                )
            else:
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=side,
                    amount=amount
                )
            
            logger.info(
                f"訂單已提交 - {side.upper()} {amount} {symbol} @ {price or 'MARKET'}"
            )
            
            return {
                'status': 'success',
                'order_id': order['id'],
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price or order.get('price'),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"下單失敗: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'symbol': symbol,
                'side': side
            }
    
    def calculate_stop_loss(self, entry_price: float) -> float:
        """
        計算停損價格
        
        Args:
            entry_price: 入場價格
        
        Returns:
            停損價格
        """
        stop_loss_price = entry_price * (1 - self.stop_loss_percent)
        return stop_loss_price
    
    def calculate_take_profit(
        self,
        entry_price: float,
        target: str = 'min'
    ) -> float:
        """
        計算止盈價格
        
        Args:
            entry_price: 入場價格
            target: 'min' (最低獲利) 或 'max' (最高獲利)
        
        Returns:
            止盈價格
        """
        if target == 'min':
            take_profit_price = entry_price * (1 + self.take_profit_min)
        elif target == 'max':
            take_profit_price = entry_price * (1 + self.take_profit_max)
        else:
            # 預設使用中間值
            avg_profit = (self.take_profit_min + self.take_profit_max) / 2
            take_profit_price = entry_price * (1 + avg_profit)
        
        return take_profit_price
    
    def should_stop_loss(self, entry_price: float, current_price: float) -> bool:
        """
        判斷是否應該停損
        
        Args:
            entry_price: 入場價格
            current_price: 當前價格
        
        Returns:
            True 如果應該停損，否則 False
        """
        stop_loss_price = self.calculate_stop_loss(entry_price)
        return current_price <= stop_loss_price
    
    def should_take_profit(self, entry_price: float, current_price: float) -> bool:
        """
        判斷是否應該止盈
        
        Args:
            entry_price: 入場價格
            current_price: 當前價格
        
        Returns:
            True 如果應該止盈（達到最低獲利目標），否則 False
        """
        take_profit_price = self.calculate_take_profit(entry_price, target='min')
        return current_price >= take_profit_price
    
    def calculate_max_position(self, symbol: str, price: float) -> float:
        """
        計算最大持倉數量
        
        Args:
            symbol: 交易對
            price: 當前價格
        
        Returns:
            最大可買入數量
        """
        try:
            balance = self.exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            
            # 計算最大持倉金額（總資金 * 最大持倉比例）
            max_position_value = usdt_balance * self.max_position_size
            
            # 轉換為數量
            max_amount = max_position_value / price
            
            logger.info(
                f"最大持倉計算 - 可用資金: {usdt_balance} USDT, "
                f"最大持倉: {max_position_value} USDT = {max_amount:.6f} {symbol}"
            )
            
            return max_amount
        
        except Exception as e:
            logger.error(f"計算最大持倉失敗: {e}")
            return 0.0
    
    def get_open_positions(self) -> List[Dict]:
        """
        查詢當前持倉
        
        Returns:
            持倉列表
        """
        try:
            if hasattr(self.exchange, 'fetch_positions'):
                positions = self.exchange.fetch_positions()
                return [p for p in positions if p.get('contracts', 0) > 0]
            else:
                # 如果交易所不支持 fetch_positions，使用 balance 查詢
                balance = self.exchange.fetch_balance()
                positions = []
                for asset, info in balance.items():
                    if asset != 'USDT' and info.get('total', 0) > 0:
                        positions.append({
                            'symbol': f"{asset}/USDT",
                            'contracts': info['total'],
                            'entryPrice': None  # 需要額外查詢
                        })
                return positions
        
        except Exception as e:
            logger.error(f"查詢持倉失敗: {e}")
            return []
    
    def close_position(
        self,
        symbol: str,
        amount: float,
        reason: str = 'manual'
    ) -> Dict:
        """
        平倉（賣出持倉）
        
        Args:
            symbol: 交易對
            amount: 數量
            reason: 平倉原因（'stop_loss', 'take_profit', 'manual'）
        
        Returns:
            平倉結果字典
        """
        logger.info(f"執行平倉 - {symbol} {amount} (原因: {reason})")
        
        result = self.place_order(
            symbol=symbol,
            side='sell',
            amount=amount,
            order_type='market'
        )
        
        if result['status'] == 'success':
            result['reason'] = reason
            logger.info(f"平倉成功 - {symbol} {amount}")
        else:
            logger.error(f"平倉失敗 - {symbol} {amount}")
        
        return result
    
    def monitor_positions(self) -> List[Dict]:
        """
        監控所有持倉並自動執行止盈止損
        
        Returns:
            執行的操作列表
        """
        actions = []
        positions = self.get_open_positions()
        
        for position in positions:
            symbol = position['symbol']
            amount = position.get('contracts', 0)
            entry_price = position.get('entryPrice')
            
            if entry_price is None:
                logger.warning(f"無法獲取 {symbol} 入場價格，跳過監控")
                continue
            
            try:
                # 獲取當前價格
                ticker = self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # 檢查停損
                if self.should_stop_loss(entry_price, current_price):
                    logger.warning(
                        f"觸發停損 - {symbol} 入場: {entry_price}, "
                        f"當前: {current_price}"
                    )
                    result = self.close_position(symbol, amount, reason='stop_loss')
                    actions.append(result)
                
                # 檢查止盈
                elif self.should_take_profit(entry_price, current_price):
                    logger.info(
                        f"觸發止盈 - {symbol} 入場: {entry_price}, "
                        f"當前: {current_price}"
                    )
                    result = self.close_position(symbol, amount, reason='take_profit')
                    actions.append(result)
            
            except Exception as e:
                logger.error(f"監控 {symbol} 持倉時發生錯誤: {e}")
        
        return actions

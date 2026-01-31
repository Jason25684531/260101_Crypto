"""
交易執行器 (TradeExecutor)
負責實際的交易執行、止盈止損管理、安全檢查

支持：
- PAPER 模式：模拟交易（无风险）
- LIVE 模式：实盘交易（真实资金）
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TradeExecutor:
    """
    交易執行器
    
    功能：
    1. 執行買入/賣出訂單（通過 CCXT 或 PaperExchange）
    2. 計算止盈止損價格
    3. 監控持倉並自動執行止盈止損
    4. PanicScore 安全檢查（高風險時拒絕交易）
    """
    
    def __init__(
        self,
        exchange=None,
        max_position_size: float = 0.3,
        stop_loss_percent: float = 0.05,
        take_profit_min: float = 0.10,
        take_profit_max: float = 0.20,
        panic_threshold: float = 0.80,
        trading_mode: Optional[str] = None
    ):
        """
        初始化交易執行器
        
        Args:
            exchange: CCXT Exchange 實例（可选，如果未提供则根据 trading_mode 自动创建）
            max_position_size: 單一持倉最大資金比例（預設 30%）
            stop_loss_percent: 停損百分比（預設 5%）
            take_profit_min: 最低獲利目標（預設 10%）
            take_profit_max: 最高獲利目標（預設 20%）
            panic_threshold: PanicScore 警戒線（預設 0.80）
            trading_mode: 交易模式 ('PAPER' 或 'LIVE'，默认从配置读取)
        """
        # 自动创建交易所实例（如果未提供）
        if exchange is None:
            exchange = self._create_exchange(trading_mode)
        
        self.exchange = exchange
        self.max_position_size = max_position_size
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_min = take_profit_min
        self.take_profit_max = take_profit_max
        self.panic_threshold = panic_threshold
        
        # 检测交易模式
        self.trading_mode = self._detect_trading_mode()
        
        logger.info(
            f"TradeExecutor 初始化完成 - "
            f"模式: {self.trading_mode} | "
            f"停損: {stop_loss_percent*100}% | "
            f"止盈: {take_profit_min*100}%-{take_profit_max*100}%"
        )
    
    def _create_exchange(self, trading_mode: Optional[str] = None):
        """
        根据配置创建交易所实例
        
        Args:
            trading_mode: 交易模式（可选）
        
        Returns:
            交易所实例（PaperExchange 或 ccxt.Exchange）
        """
        from app.config import config
        
        # 确定交易模式
        mode = (trading_mode or config.TRADING_MODE).upper()
        
        if mode == 'PAPER':
            # 模拟交易模式
            from app.core.execution.paper_exchange import PaperExchange
            
            exchange = PaperExchange(
                initial_balance=config.PAPER_INITIAL_BALANCE
            )
            logger.info("🟢 使用模拟交易所（Paper Exchange）")
        
        elif mode == 'LIVE':
            # 实盘交易模式
            import ccxt
            
            if not config.BINANCE_API_KEY or not config.BINANCE_SECRET_KEY:
                raise ValueError(
                    "LIVE 模式需要配置 BINANCE_API_KEY 和 BINANCE_SECRET_KEY"
                )
            
            exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_SECRET_KEY,
                'enableRateLimit': True,
                'timeout': 30000,
            })
            logger.warning("🔴 使用实盘交易所（Binance Live）")
        
        else:
            raise ValueError(f"未知的交易模式: {mode}")
        
        return exchange
    
    def _detect_trading_mode(self) -> str:
        """检测当前交易模式"""
        # 使用字符串检查避免导入 PaperExchange（避免触发 __init__.py）
        exchange_class_name = self.exchange.__class__.__name__
        
        if exchange_class_name == 'PaperExchange':
            return 'PAPER'
        else:
            return 'LIVE'
    
    @classmethod
    def from_config(cls):
        """
        从配置文件创建 TradeExecutor
        
        Returns:
            TradeExecutor 实例
        """
        from app.config import config
        
        return cls(
            max_position_size=config.MAX_POSITION_SIZE,
            stop_loss_percent=config.STOP_LOSS_PERCENT,
            take_profit_min=config.TAKE_PROFIT_MIN,
            take_profit_max=config.TAKE_PROFIT_MAX,
            panic_threshold=config.PANIC_THRESHOLD,
            trading_mode=config.TRADING_MODE
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
            RuntimeError: 當交易被鎖定時
        """
        # 檢查交易鎖（Kill Switch）
        from app.extensions import redis_client
        
        try:
            trading_enabled = redis_client.get('SYSTEM_STATUS:TRADING_ENABLED')
            # 預設為 'true'（向後相容）
            if trading_enabled is None:
                trading_enabled = 'true'
            
            if trading_enabled.lower() == 'false':
                error_msg = "交易已暫停（Kill Switch 已啟動），拒絕所有訂單"
                logger.warning(f"{error_msg} - {side.upper()} {amount} {symbol}")
                raise RuntimeError(error_msg)
        
        except RuntimeError:
            raise  # 重新拋出 RuntimeError
        except Exception as e:
            # Redis 連線失敗時記錄錯誤但允許交易繼續（容錯設計）
            logger.error(f"檢查交易鎖失敗: {e}，允許交易繼續")
        
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
    
    def execute_strategy(
        self,
        signals: List[Dict],
        panic_score: Optional[float] = None,
        use_ml_filter: bool = True,
        ml_threshold: float = 0.6
    ) -> List[Dict]:
        """
        執行策略信號
        
        Args:
            signals: 策略信號列表，每個信號包含：
                - symbol: 交易對
                - action: 'buy' 或 'sell'
                - price: 價格
                - amount: 數量
                - features: (可選) ML 特徵數據
            panic_score: 恐慌指數（0-1）
            use_ml_filter: 是否使用 ML 過濾器（預設啟用）
            ml_threshold: ML 獲利機率閾值（預設 0.6）
        
        Returns:
            執行結果列表
        """
        from app.extensions import redis_client
        
        # 檢查交易鎖
        try:
            trading_enabled = redis_client.get('SYSTEM_STATUS:TRADING_ENABLED')
            if trading_enabled is None:
                trading_enabled = 'true'
            
            if trading_enabled.lower() == 'false':
                logger.warning("交易已暫停（Kill Switch），跳過策略執行")
                return []
        
        except Exception as e:
            logger.error(f"檢查交易鎖失敗: {e}，允許策略繼續")
        
        # 初始化 ML 預測器（如果啟用）
        ml_predictor = None
        if use_ml_filter:
            try:
                from app.core.ml.predictor import SignalPredictor
                ml_predictor = SignalPredictor.get_instance()
                if ml_predictor.is_enabled:
                    ml_predictor.set_threshold(ml_threshold)
                    logger.info(f"🤖 ML 過濾器已啟用 (閾值: {ml_threshold:.0%})")
                else:
                    logger.info("🤖 ML 模型未載入，跳過 ML 過濾")
            except Exception as e:
                logger.warning(f"初始化 ML 預測器失敗: {e}")
        
        results = []
        filtered_count = 0
        
        for signal in signals:
            try:
                symbol = signal['symbol']
                action = signal['action']
                price = signal.get('price')
                amount = signal['amount']
                features = signal.get('features')  # ML 特徵
                
                # ML 過濾（僅對 BUY 信號）
                if action.lower() == 'buy' and ml_predictor and ml_predictor.is_enabled:
                    if features:
                        prediction = ml_predictor.get_prediction_with_details(features)
                        
                        if not prediction['should_trade']:
                            logger.info(
                                f"🚫 ML 過濾信號 - {symbol} | "
                                f"機率: {prediction['probability']:.2%} | "
                                f"建議: {prediction['recommendation']}"
                            )
                            filtered_count += 1
                            results.append({
                                'status': 'filtered',
                                'reason': 'ml_filter',
                                'ml_probability': prediction['probability'],
                                'ml_recommendation': prediction['recommendation'],
                                'signal': signal
                            })
                            continue  # 跳過此信號
                        else:
                            logger.info(
                                f"✅ ML 通過信號 - {symbol} | "
                                f"機率: {prediction['probability']:.2%}"
                            )
                    else:
                        logger.debug(f"信號缺少 features，跳過 ML 過濾: {symbol}")
                
                # 執行訂單
                result = self.place_order(
                    symbol=symbol,
                    side=action,
                    amount=amount,
                    price=price,
                    order_type='limit' if price else 'market',
                    panic_score=panic_score
                )
                
                results.append(result)
                
                logger.info(
                    f"策略信號已執行 - {action.upper()} {amount} {symbol} @ {price or 'MARKET'}"
                )
            
            except Exception as e:
                logger.error(f"執行策略信號失敗: {e}")
                results.append({
                    'status': 'error',
                    'error': str(e),
                    'signal': signal
                })
        
        # 統計 ML 過濾結果
        if filtered_count > 0:
            logger.info(f"🤖 ML 過濾統計: {filtered_count}/{len(signals)} 個信號被過濾")
        
        return results
    
    def close_all_positions(self) -> List[Dict]:
        """
        緊急平倉所有持倉（PANIC 模式）
        
        Returns:
            平倉結果列表
        """
        logger.critical("🚨 執行緊急平倉（PANIC MODE）")
        
        positions = self.get_open_positions()
        results = []
        
        if not positions:
            logger.info("目前無持倉需要平倉")
            return results
        
        for position in positions:
            try:
                symbol = position['symbol']
                amount = position.get('contracts', 0)
                
                if amount <= 0:
                    continue
                
                logger.warning(f"緊急平倉 - {symbol} {amount}")
                
                # 使用市價單立即平倉
                result = self.place_order(
                    symbol=symbol,
                    side='sell',
                    amount=amount,
                    order_type='market'
                )
                
                result['reason'] = 'panic'
                results.append(result)
                
                if result['status'] == 'success':
                    logger.info(f"✅ 平倉成功 - {symbol} {amount}")
                else:
                    logger.error(f"❌ 平倉失敗 - {symbol} {amount}")
            
            except Exception as e:
                logger.error(f"緊急平倉 {symbol} 失敗: {e}", exc_info=True)
                results.append({
                    'status': 'error',
                    'error': str(e),
                    'symbol': symbol,
                    'amount': amount
                })
        
        logger.critical(f"緊急平倉完成 - 共處理 {len(results)} 個持倉")
        
        return results

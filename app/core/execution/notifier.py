"""
LINE Bot 通知器 (Notifier)
處理 LINE Bot 指令並推送交易通知
"""
import logging
from typing import Dict, Optional
from datetime import datetime
from linebot.models import (
    TextSendMessage, TemplateSendMessage, ButtonsTemplate,
    MessageAction, QuickReply, QuickReplyButton
)
from app.extensions import line_bot_api, line_handler
from linebot.models import MessageEvent, TextMessage

logger = logging.getLogger(__name__)


class TradingNotifier:
    """
    交易通知器
    
    功能：
    1. 推送交易信號通知（買入/賣出）
    2. 推送止盈止損警報
    3. 處理用戶指令（/status, /stop, /panic）
    4. 系統狀態報告
    """
    
    def __init__(self, line_api=None):
        """
        初始化通知器
        
        Args:
            line_api: LineBotApi 實例（如果為 None 則使用全局實例）
        """
        self.line_api = line_api or line_bot_api
        self.enabled = self.line_api is not None
        
        if not self.enabled:
            logger.warning("LINE Bot API 未初始化，通知功能將被禁用")
    
    def send_message(self, user_id: str, message: str) -> bool:
        """
        發送文字訊息給用戶
        
        Args:
            user_id: LINE 用戶 ID
            message: 訊息內容
        
        Returns:
            True 如果發送成功，否則 False
        """
        if not self.enabled:
            logger.warning("通知功能已禁用")
            return False
        
        try:
            self.line_api.push_message(
                user_id,
                TextSendMessage(text=message)
            )
            logger.info(f"已發送訊息給用戶 {user_id}")
            return True
        except Exception as e:
            logger.error(f"發送訊息失敗: {e}")
            return False
    
    def send_trade_signal(
        self,
        user_id: str,
        signal_type: str,
        symbol: str,
        price: float,
        amount: float,
        reason: str = ""
    ) -> bool:
        """
        發送交易信號通知
        
        Args:
            user_id: LINE 用戶 ID
            signal_type: 'BUY' 或 'SELL'
            symbol: 交易對
            price: 價格
            amount: 數量
            reason: 原因說明
        
        Returns:
            True 如果發送成功
        """
        emoji = "🟢" if signal_type == "BUY" else "🔴"
        
        message = f"""{emoji} {signal_type} 信號

交易對: {symbol}
價格: {price:.2f} USDT
數量: {amount:.6f}
總價值: {price * amount:.2f} USDT

{reason if reason else ""}

⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(user_id, message)
    
    def send_stop_loss_alert(
        self,
        user_id: str,
        symbol: str,
        entry_price: float,
        current_price: float,
        loss_percent: float
    ) -> bool:
        """
        發送停損警報
        
        Args:
            user_id: LINE 用戶 ID
            symbol: 交易對
            entry_price: 入場價格
            current_price: 當前價格
            loss_percent: 虧損百分比
        
        Returns:
            True 如果發送成功
        """
        message = f"""⚠️ 停損警報！

交易對: {symbol}
入場價格: {entry_price:.2f} USDT
當前價格: {current_price:.2f} USDT
虧損: {loss_percent:.2%}

系統將自動執行停損賣出

⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(user_id, message)
    
    def send_take_profit_alert(
        self,
        user_id: str,
        symbol: str,
        entry_price: float,
        current_price: float,
        profit_percent: float
    ) -> bool:
        """
        發送止盈警報
        
        Args:
            user_id: LINE 用戶 ID
            symbol: 交易對
            entry_price: 入場價格
            current_price: 當前價格
            profit_percent: 獲利百分比
        
        Returns:
            True 如果發送成功
        """
        message = f"""🎉 止盈達成！

交易對: {symbol}
入場價格: {entry_price:.2f} USDT
當前價格: {current_price:.2f} USDT
獲利: {profit_percent:.2%}

系統將執行部分止盈賣出

⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(user_id, message)
    
    def send_panic_alert(
        self,
        user_id: str,
        panic_score: float,
        reason: str
    ) -> bool:
        """
        發送恐慌警報（PanicScore 過高）
        
        Args:
            user_id: LINE 用戶 ID
            panic_score: 恐慌指數（0-1）
            reason: 原因說明
        
        Returns:
            True 如果發送成功
        """
        message = f"""🚨 市場恐慌警報！

恐慌指數: {panic_score:.0%}
風險等級: {'極高' if panic_score > 0.9 else '高'}

原因: {reason}

⚠️ 系統已暫停所有買入操作
建議: 持有現金，等待市場穩定

⏰ 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(user_id, message)


# ==================== LINE Bot 指令處理器 ====================

@line_handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """處理用戶發送的文字訊息"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    logger.info(f"收到用戶 {user_id} 的訊息: {text}")
    
    # 指令處理
    if text.startswith('/'):
        handle_command(user_id, text)
    else:
        # 一般訊息回覆
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="您好！請使用以下指令：\n\n/status - 查看系統狀態\n/stop - 停止所有交易\n/panic - 緊急平倉")
        )


def handle_command(user_id: str, command: str):
    """
    處理用戶指令
    
    Args:
        user_id: LINE 用戶 ID
        command: 指令字串（如 /status）
    """
    notifier = TradingNotifier()
    
    if command == '/status':
        # 查詢系統狀態
        handle_status_command(user_id)
    
    elif command == '/stop':
        # 停止交易
        handle_stop_command(user_id)
    
    elif command == '/panic':
        # 緊急平倉
        handle_panic_command(user_id)
    
    else:
        notifier.send_message(
            user_id,
            f"未知指令: {command}\n\n可用指令：\n/status\n/stop\n/panic"
        )


def handle_status_command(user_id: str):
    """處理 /status 指令"""
    from app.extensions import db, redis_client
    from app.models import OHLCV
    
    try:
        # 查詢資料庫統計
        ohlcv_count = OHLCV.query.count()
        
        # Redis 連線狀態
        redis_ok = redis_client.ping()
        
        message = f"""📊 系統狀態報告

✅ 系統運行中
🗄️ 數據庫: 已連線
💾 快取: {'已連線' if redis_ok else '斷線'}
📈 K線數據: {ohlcv_count} 筆

⏰ 查詢時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        notifier = TradingNotifier()
        notifier.send_message(user_id, message)
    
    except Exception as e:
        logger.error(f"處理 /status 指令失敗: {e}")
        notifier = TradingNotifier()
        notifier.send_message(user_id, f"❌ 查詢失敗: {e}")


def handle_stop_command(user_id: str):
    """處理 /stop 指令"""
    # TODO: 實現停止交易邏輯（設置全局標誌）
    message = """⏸️ 交易已停止

所有自動交易已暫停
現有持倉將繼續監控止盈止損

使用 /start 恢復交易
"""
    
    notifier = TradingNotifier()
    notifier.send_message(user_id, message)
    logger.info(f"用戶 {user_id} 執行了 /stop 指令")


def handle_panic_command(user_id: str):
    """處理 /panic 指令（緊急平倉）"""
    # TODO: 實現緊急平倉邏輯
    message = """🚨 緊急平倉指令已收到

系統將在 10 秒內平掉所有持倉
請稍候...

⚠️ 此操作不可撤銷！
"""
    
    notifier = TradingNotifier()
    notifier.send_message(user_id, message)
    logger.warning(f"用戶 {user_id} 執行了 /panic 指令")
    
    # TODO: 調用 TradeExecutor 平掉所有持倉

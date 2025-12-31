"""
市場數據模型 - OHLCV (Open/High/Low/Close/Volume)
用於儲存加密貨幣的 K 線數據
"""
from app.extensions import db
from datetime import datetime
from sqlalchemy import Index


class OHLCV(db.Model):
    """OHLCV K線數據表
    
    儲存交易所的歷史價格和交易量數據，用於技術指標計算與回測
    """
    __tablename__ = 'ohlcv'
    
    # 主鍵
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 交易對符號（如 BTC/USDT）
    symbol = db.Column(db.String(20), nullable=False, index=True)
    
    # 時間戳（毫秒級 Unix timestamp）
    timestamp = db.Column(db.BigInteger, nullable=False, index=True)
    
    # 時間週期（1m, 5m, 15m, 1h, 1d 等）
    timeframe = db.Column(db.String(10), nullable=False, default='1m')
    
    # OHLCV 數據
    open = db.Column(db.Float, nullable=False)
    high = db.Column(db.Float, nullable=False)
    low = db.Column(db.Float, nullable=False)
    close = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Float, nullable=False)
    
    # 交易所名稱（支援多交易所數據）
    exchange = db.Column(db.String(20), nullable=False, default='binance')
    
    # 記錄創建時間
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 複合索引：提升查詢效能
    __table_args__ = (
        # 最常用的查詢組合：交易對 + 時間範圍 + 週期
        Index('idx_symbol_timestamp_timeframe', 'symbol', 'timestamp', 'timeframe'),
        # 交易所 + 交易對查詢
        Index('idx_exchange_symbol', 'exchange', 'symbol'),
        # 唯一約束：防止重複數據
        Index('idx_unique_ohlcv', 'exchange', 'symbol', 'timestamp', 'timeframe', unique=True),
    )
    
    def __repr__(self):
        return f'<OHLCV {self.exchange}:{self.symbol} @ {self.timestamp}>'
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'timeframe': self.timeframe,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'exchange': self.exchange,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def from_ccxt(exchange_name, symbol, timeframe, ohlcv_data):
        """從 CCXT 數據格式創建實例
        
        Args:
            exchange_name: 交易所名稱
            symbol: 交易對符號
            timeframe: 時間週期
            ohlcv_data: CCXT 格式 [timestamp, open, high, low, close, volume]
        
        Returns:
            OHLCV 實例
        """
        return OHLCV(
            exchange=exchange_name,
            symbol=symbol,
            timeframe=timeframe,
            timestamp=ohlcv_data[0],
            open=ohlcv_data[1],
            high=ohlcv_data[2],
            low=ohlcv_data[3],
            close=ohlcv_data[4],
            volume=ohlcv_data[5]
        )

"""
鏈上數據模型 - On-Chain Metrics
用於儲存區塊鏈分析指標（Exchange Netflow, SOPR, MVRV 等）
"""
from app.extensions import db
from datetime import datetime
from sqlalchemy import Index


class ChainMetric(db.Model):
    """鏈上指標數據表
    
    儲存從 Glassnode、CryptoQuant 等平台獲取的鏈上分析數據
    """
    __tablename__ = 'chain_metrics'
    
    # 主鍵
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 資產名稱（BTC, ETH 等）
    asset = db.Column(db.String(10), nullable=False, index=True)
    
    # 指標名稱（netflow, sopr, mvrv, nupl 等）
    metric_name = db.Column(db.String(50), nullable=False, index=True)
    
    # 時間戳（Unix timestamp，秒級）
    timestamp = db.Column(db.BigInteger, nullable=False, index=True)
    
    # 指標數值
    value = db.Column(db.Float, nullable=False)
    
    # Phase 6: 交易所淨流入量（Exchange Netflow）
    exchange_netflow = db.Column(db.Float, nullable=True, comment='交易所淨流入量')
    
    # Phase 6: 巨鯨流入筆數（>10 BTC 的轉入筆數）
    whale_inflow_count = db.Column(db.Integer, nullable=True, comment='巨鯨流入筆數(>10 BTC)')
    
    # 數據來源（glassnode, cryptoquant, santiment, dune）
    source = db.Column(db.String(20), nullable=False, default='glassnode')
    
    # 額外元數據（JSON 格式，儲存原始響應或計算細節）
    extra_data = db.Column(db.JSON, nullable=True)
    
    # 記錄創建時間
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 複合索引
    __table_args__ = (
        # 最常用查詢：資產 + 指標 + 時間範圍
        Index('idx_asset_metric_timestamp', 'asset', 'metric_name', 'timestamp'),
        # 數據源查詢
        Index('idx_source_asset', 'source', 'asset'),
        # 唯一約束：防止重複數據
        Index('idx_unique_metric', 'asset', 'metric_name', 'timestamp', 'source', unique=True),
    )
    
    def __repr__(self):
        return f'<ChainMetric {self.asset}:{self.metric_name} @ {self.timestamp}>'
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'asset': self.asset,
            'metric_name': self.metric_name,
            'timestamp': self.timestamp,
            'value': self.value,
            'exchange_netflow': self.exchange_netflow,
            'whale_inflow_count': self.whale_inflow_count,
            'source': self.source,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ExchangeNetflow(db.Model):
    """交易所淨流入數據表（專門追蹤 Exchange Inflow/Outflow）
    
    這是關鍵的恐慌指標：大量流入 = 可能拋售，大量流出 = 可能囤幣
    """
    __tablename__ = 'exchange_netflows'
    
    # 主鍵
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # 資產名稱
    asset = db.Column(db.String(10), nullable=False, index=True)
    
    # 交易所名稱（binance, okx, coinbase 等）
    exchange = db.Column(db.String(20), nullable=False, index=True)
    
    # 時間戳（Unix timestamp）
    timestamp = db.Column(db.BigInteger, nullable=False, index=True)
    
    # 流入量（Inflow）
    inflow = db.Column(db.Float, nullable=False, default=0.0)
    
    # 流出量（Outflow）
    outflow = db.Column(db.Float, nullable=False, default=0.0)
    
    # 淨流量（Netflow = Inflow - Outflow）
    netflow = db.Column(db.Float, nullable=False)
    
    # 記錄創建時間
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_asset_exchange_timestamp', 'asset', 'exchange', 'timestamp'),
        Index('idx_unique_netflow', 'asset', 'exchange', 'timestamp', unique=True),
    )
    
    def __repr__(self):
        return f'<ExchangeNetflow {self.exchange}:{self.asset} @ {self.timestamp}>'
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'asset': self.asset,
            'exchange': self.exchange,
            'timestamp': self.timestamp,
            'inflow': self.inflow,
            'outflow': self.outflow,
            'netflow': self.netflow,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

#!/usr/bin/env python
"""
數據種子腳本 - 從 Binance 獲取市場數據並儲存到 MySQL
用於初始化資料庫或更新最新數據
"""
import sys
import os

# 確保可以導入 app 模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_market_data(
    symbols: list = None,
    timeframe: str = '1h',
    limit: int = 500
) -> dict:
    """
    從 Binance 獲取市場數據並儲存到資料庫
    
    Args:
        symbols: 交易對列表（預設 ['BTC/USDT', 'ETH/USDT']）
        timeframe: 時間週期（預設 '1h'）
        limit: 數量上限（預設 500）
    
    Returns:
        dict: 每個交易對儲存的記錄數
    """
    if symbols is None:
        symbols = ['BTC/USDT', 'ETH/USDT']
    
    from app import create_app
    from app.extensions import db
    from app.core.data.fetcher import BinanceFetcher
    
    app = create_app()
    results = {}
    
    with app.app_context():
        logger.info("=" * 60)
        logger.info("📊 開始獲取市場數據")
        logger.info(f"   交易對: {symbols}")
        logger.info(f"   時間週期: {timeframe}")
        logger.info(f"   數量: {limit}")
        logger.info("=" * 60)
        
        fetcher = BinanceFetcher()
        
        for symbol in symbols:
            try:
                logger.info(f"\n🔄 正在獲取 {symbol}...")
                saved_count = fetcher.fetch_and_save(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    db_session=db.session
                )
                results[symbol] = saved_count
                logger.info(f"✅ {symbol}: 儲存 {saved_count} 筆新數據")
            except Exception as e:
                logger.error(f"❌ {symbol} 獲取失敗: {e}")
                results[symbol] = 0
        
        # 總結
        logger.info("\n" + "=" * 60)
        logger.info("📈 數據獲取完成")
        for symbol, count in results.items():
            logger.info(f"   {symbol}: {count} 筆")
        logger.info(f"   總計: {sum(results.values())} 筆")
        logger.info("=" * 60)
    
    return results


def get_data_summary() -> dict:
    """
    查詢資料庫中的數據統計
    
    Returns:
        dict: 數據統計信息
    """
    from app import create_app
    from app.extensions import db
    from app.models import OHLCV
    from sqlalchemy import func
    
    app = create_app()
    
    with app.app_context():
        # 按交易對統計
        stats = db.session.query(
            OHLCV.symbol,
            func.count(OHLCV.id).label('count'),
            func.min(OHLCV.timestamp).label('earliest'),
            func.max(OHLCV.timestamp).label('latest')
        ).group_by(OHLCV.symbol).all()
        
        summary = {}
        for stat in stats:
            summary[stat.symbol] = {
                'count': stat.count,
                'earliest': datetime.fromtimestamp(stat.earliest / 1000).strftime('%Y-%m-%d %H:%M'),
                'latest': datetime.fromtimestamp(stat.latest / 1000).strftime('%Y-%m-%d %H:%M')
            }
        
        return summary


def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='市場數據種子腳本')
    parser.add_argument(
        '--symbols', '-s',
        nargs='+',
        default=['BTC/USDT', 'ETH/USDT'],
        help='交易對列表（預設: BTC/USDT ETH/USDT）'
    )
    parser.add_argument(
        '--timeframe', '-t',
        default='1h',
        help='時間週期（預設: 1h）'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=500,
        help='數量上限（預設: 500）'
    )
    parser.add_argument(
        '--summary', '-S',
        action='store_true',
        help='僅顯示資料統計'
    )
    
    args = parser.parse_args()
    
    if args.summary:
        summary = get_data_summary()
        print("\n📊 資料庫數據統計:")
        for symbol, info in summary.items():
            print(f"  {symbol}:")
            print(f"    數量: {info['count']} 筆")
            print(f"    範圍: {info['earliest']} ~ {info['latest']}")
    else:
        seed_market_data(
            symbols=args.symbols,
            timeframe=args.timeframe,
            limit=args.limit
        )


if __name__ == '__main__':
    main()

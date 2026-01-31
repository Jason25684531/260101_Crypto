"""
定时任务模块 - Scheduler Job Functions
Scheduled Job Functions for Automated Operations

包含所有自动化任务的实现：
1. 数据爬取任务 - 定时更新市场数据
2. 策略扫描任务 - 定时执行交易信号检测
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import ccxt

logger = logging.getLogger(__name__)


async def job_update_market_data(
    fetcher=None,
    db_session=None,
    symbol: str = 'BTC/USDT',
    timeframe: str = '1m',
    limit: int = 5
) -> None:
    """
    市场数据更新任务
    Market Data Update Job
    
    功能：
    1. 从交易所获取最新的 K 线数据（增量更新）
    2. 保存到 MySQL 数据库
    3. 更新 Redis 缓存（可选）
    4. 记录执行日志
    
    Args:
        fetcher: MarketFetcher 实例（用于数据获取）
        db_session: SQLAlchemy session（用于数据库操作）
        symbol: 交易对符号
        timeframe: 时间周期
        limit: 获取最新 N 根 K 线
    
    异常处理：
    - 网络错误：记录日志，不中断调度器
    - 数据库错误：回滚事务，记录日志
    - 重复数据：忽略（幂等性保证）
    """
    from app.models.market import OHLCV
    
    start_time = datetime.now()
    logger.info(f"🔄 开始更新市场数据: {symbol} ({timeframe})")
    
    try:
        # 1. 获取最新数据
        if fetcher is None:
            from app.core.data.fetcher import MarketFetcher
            fetcher = MarketFetcher(exchange_name='binance')
            should_close_fetcher = True
        else:
            should_close_fetcher = False
        
        data = await fetcher.fetch_latest_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )
        
        if not data:
            logger.warning(f"⚠️  {symbol} 未获取到新数据")
            if db_session:
                db_session.commit()  # 确保事务完成
            return
        
        # 2. 保存到数据库
        if db_session is None:
            logger.error("❌ db_session 为 None，无法保存数据")
            return
        
        saved_count = 0
        for ohlcv_row in data:
            try:
                # 检查数据是否已存在（防重复）
                timestamp = ohlcv_row[0]
                existing = db_session.query(OHLCV).filter_by(
                    symbol=symbol,
                    timestamp=timestamp,
                    timeframe=timeframe
                ).first()
                
                if not existing:
                    # 创建新记录
                    record = OHLCV.from_ccxt(
                        exchange_name='binance',
                        symbol=symbol,
                        timeframe=timeframe,
                        ohlcv_data=ohlcv_row
                    )
                    db_session.add(record)
                    saved_count += 1
            
            except Exception as e:
                logger.error(f"❌ 处理单条数据失败: {e}")
                continue
        
        # 3. 提交事务
        try:
            db_session.commit()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"✅ Market Data Updated: {symbol} | "
                f"获取 {len(data)} 笔，保存 {saved_count} 笔 | "
                f"耗时 {elapsed:.2f}s"
            )
        
        except IntegrityError as e:
            # 重复键错误（数据已存在）
            db_session.rollback()
            logger.warning(f"⚠️  数据重复，已忽略: {symbol}")
        
        except Exception as e:
            db_session.rollback()
            logger.error(f"❌ 数据库提交失败: {e}")
        
        # 4. 清理资源
        if should_close_fetcher:
            await fetcher.close()
    
    except ccxt.NetworkError as e:
        # 网络错误：记录日志但不中断调度器
        logger.error(f"❌ 网络错误: {symbol} - {e}")
        if db_session:
            db_session.rollback()
    
    except ccxt.ExchangeError as e:
        # 交易所错误
        logger.error(f"❌ 交易所错误: {symbol} - {e}")
        if db_session:
            db_session.rollback()
    
    except Exception as e:
        # 其他未知错误
        logger.error(f"❌ 任务执行失败: {symbol} - {e}", exc_info=True)
        if db_session:
            db_session.rollback()


def job_update_market_data_sync():
    """
    同步包装器 - 用于 APScheduler
    Synchronous Wrapper for APScheduler
    
    APScheduler 的 BackgroundScheduler 不直接支持异步函数，
    需要通过 asyncio.run() 包装。
    """
    from app import create_app
    from app.extensions import db
    from app.core.data.fetcher import MarketFetcher
    
    # 创建 Flask 应用上下文
    app = create_app()
    
    with app.app_context():
        # 创建数据库 session
        db_session = db.session
        
        # 运行异步任务
        asyncio.run(
            job_update_market_data(
                fetcher=None,
                db_session=db_session,
                symbol='BTC/USDT',
                timeframe='1m',
                limit=5
            )
        )


async def job_scan_signals(
    db_session=None,
    symbols: list = None
) -> None:
    """
    策略信号扫描任务
    Strategy Signal Scanning Job
    
    功能：
    1. 从数据库读取最新的市场数据
    2. 计算技术指标（AlphaFactors）
    3. 生成交易信号（CompositeScore）
    4. 触发交易执行（如果满足条件）
    
    Args:
        db_session: SQLAlchemy session
        symbols: 要扫描的交易对列表
    
    TODO: Phase 3.5 后续实现
    """
    logger.info("🔍 Scanning Signals...")
    
    if symbols is None:
        symbols = ['BTC/USDT', 'ETH/USDT']
    
    # TODO: 实现策略扫描逻辑
    # 1. 读取最新数据
    # 2. 计算指标
    # 3. 检测信号
    # 4. 执行交易（Paper Mode）
    
    logger.info(f"✅ Signal Scan Complete: {len(symbols)} symbols")


def job_scan_signals_sync():
    """
    同步包装器 - 策略扫描任务
    Synchronous Wrapper for Signal Scanning
    """
    from app import create_app
    from app.extensions import db
    
    app = create_app()
    
    with app.app_context():
        asyncio.run(
            job_scan_signals(db_session=db.session)
        )

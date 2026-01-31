#!/usr/bin/env python3
"""
HighFreqQuant Trading Bot - 自动化交易系统入口
Automated Trading System Entry Point

功能：
1. 启动调度器 (Scheduler)
2. 运行定时任务 (Market Data + Signal Scanning)
3. 优雅关闭处理 (Graceful Shutdown)
4. 异常监控与恢复
"""
import signal
import sys
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bot.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# 全局变量
scheduler = None
app = None
shutdown_requested = False


def signal_handler(signum, frame):
    """
    信号处理器 - 处理 SIGINT (Ctrl+C) 和 SIGTERM
    
    Args:
        signum: 信号编号
        frame: 当前栈帧
    """
    global shutdown_requested
    
    signal_name = 'SIGINT' if signum == signal.SIGINT else 'SIGTERM'
    logger.info(f"\n🛑 收到 {signal_name} 信号，开始优雅关闭...")
    
    shutdown_requested = True
    
    # 关闭调度器
    if scheduler and scheduler.is_running():
        logger.info("正在关闭调度器...")
        scheduler.shutdown(wait=True)
        logger.info("✅ 调度器已关闭")
    
    logger.info("👋 系统已安全退出")
    sys.exit(0)


def print_startup_banner():
    """打印系统启动横幅"""
    from app.config import config
    
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 HighFreqQuant Trading Bot v1.0                     ║
║        高频量化交易系统 - 自动化版                             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    
    print(banner)
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⚙️  交易模式: {config.TRADING_MODE} {config.get_mode_display()}")
    
    if config.is_paper_mode():
        print(f"💰 模拟资金: ${config.PAPER_INITIAL_BALANCE:,.2f} USDT")
    else:
        print("⚠️  警告：实盘交易模式！使用真实资金！")
    
    print(f"🗄️  数据库: {'已连接' if check_database() else '未连接'}")
    print(f"📦 Redis: {'已连接' if check_redis() else '未连接'}")
    print("=" * 66)
    print()


def check_database():
    """检查数据库连接"""
    try:
        from app.extensions import db
        from sqlalchemy import text
        
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            return True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False


def check_redis():
    """检查 Redis 连接"""
    try:
        from app.extensions import redis_client
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"❌ Redis 连接失败: {e}")
        return False


def initialize_system():
    """初始化系统组件"""
    global app, scheduler
    
    logger.info("🔧 正在初始化系统...")
    
    # 1. 创建 Flask App
    from app import create_app
    app = create_app('production')
    logger.info("✅ Flask App 已创建")
    
    # 2. 创建 Scheduler
    from app.core.scheduler import Scheduler
    scheduler = Scheduler()
    logger.info("✅ Scheduler 已创建")
    
    # 3. 在 App Context 中设置任务
    with app.app_context():
        scheduler.setup_all_jobs()
        logger.info("✅ 所有定时任务已配置")
    
    return True


def run_scheduler():
    """运行调度器"""
    global scheduler, shutdown_requested
    
    logger.info("🚀 启动调度器...")
    scheduler.start()
    logger.info("✅ 调度器已启动")
    
    # 打印任务列表
    scheduler.print_jobs()
    
    logger.info("💚 系统上线！开始自动化交易...")
    logger.info("提示：按 Ctrl+C 可以安全退出")
    print()
    
    # 主循环 - 保持进程存活
    heartbeat_counter = 0
    
    try:
        while not shutdown_requested:
            time.sleep(1)
            heartbeat_counter += 1
            
            # 每 60 秒打印一次心跳
            if heartbeat_counter % 60 == 0:
                logger.info(f"💓 系统心跳 - 运行中 ({heartbeat_counter // 60} 分钟)")
                
                # 检查调度器状态
                if not scheduler.is_running():
                    logger.error("❌ 调度器已停止！尝试重启...")
                    scheduler.start()
    
    except KeyboardInterrupt:
        logger.info("\n🛑 检测到 KeyboardInterrupt")
    
    except Exception as e:
        logger.error(f"❌ 主循环发生异常: {e}", exc_info=True)
        raise


def main():
    """主函数"""
    try:
        # 1. 打印启动横幅
        print_startup_banner()
        
        # 2. 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("✅ 信号处理器已注册")
        
        # 3. 初始化系统
        if not initialize_system():
            logger.error("❌ 系统初始化失败")
            sys.exit(1)
        
        # 4. 运行调度器
        run_scheduler()
    
    except Exception as e:
        logger.error(f"❌ 系统启动失败: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        # 确保资源清理
        if scheduler and scheduler.is_running():
            scheduler.shutdown(wait=True)
        
        logger.info("系统已完全关闭")


if __name__ == '__main__':
    # 确保 logs 目录存在
    import os
    os.makedirs('logs', exist_ok=True)
    
    main()

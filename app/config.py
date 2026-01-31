"""
配置管理模块
Configuration Management Module

从环境变量加载配置，提供默认值
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """系统配置类"""
    
    # ==================== Flask ====================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    APP_PORT = int(os.getenv('APP_PORT', 5000))
    
    # ==================== Database ====================
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://trader:traderpass123@db:3306/highfreq_trading'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = (FLASK_ENV == 'development')
    
    # ==================== Redis ====================
    REDIS_URL = os.getenv('REDIS_URL', 'redis://cache:6379/0')
    
    # ==================== Trading Mode ====================
    # PAPER = 模拟交易（默认） | LIVE = 实盘交易
    TRADING_MODE = os.getenv('TRADING_MODE', 'PAPER').upper()
    
    # 模拟交易初始资金
    PAPER_INITIAL_BALANCE = float(os.getenv('PAPER_INITIAL_BALANCE', 10000.0))
    
    # 验证交易模式
    if TRADING_MODE not in ['PAPER', 'LIVE']:
        raise ValueError(f"Invalid TRADING_MODE: {TRADING_MODE}. Must be 'PAPER' or 'LIVE'")
    
    # ==================== Exchange API ====================
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    
    # ==================== Trading Parameters ====================
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 0.3))
    KELLY_FRACTION = float(os.getenv('KELLY_FRACTION', 0.25))
    
    TAKE_PROFIT_MIN = float(os.getenv('TAKE_PROFIT_MIN', 0.10))
    TAKE_PROFIT_MAX = float(os.getenv('TAKE_PROFIT_MAX', 0.20))
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', 0.05))
    
    PANIC_THRESHOLD = float(os.getenv('PANIC_THRESHOLD', 0.85))
    
    # ==================== Logging ====================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', '/app/logs/trading.log')
    
    # ==================== Timezone ====================
    TIMEZONE = os.getenv('TZ', 'UTC')
    
    @classmethod
    def is_paper_mode(cls) -> bool:
        """检查是否为模拟交易模式"""
        return cls.TRADING_MODE == 'PAPER'
    
    @classmethod
    def is_live_mode(cls) -> bool:
        """检查是否为实盘交易模式"""
        return cls.TRADING_MODE == 'LIVE'
    
    @classmethod
    def get_mode_display(cls) -> str:
        """获取交易模式的显示名称"""
        return '🔴 实盘交易' if cls.is_live_mode() else '🟢 模拟交易'


# 创建全局配置实例
config = Config()


# 启动时显示配置信息
if __name__ == '__main__':
    print("=" * 60)
    print("HighFreqQuant 配置信息")
    print("=" * 60)
    print(f"交易模式: {config.TRADING_MODE} {config.get_mode_display()}")
    print(f"数据库: {config.DATABASE_URL}")
    print(f"Redis: {config.REDIS_URL}")
    print(f"最大仓位: {config.MAX_POSITION_SIZE * 100}%")
    print(f"止盈目标: {config.TAKE_PROFIT_MIN * 100}% - {config.TAKE_PROFIT_MAX * 100}%")
    print(f"止损: {config.STOP_LOSS_PERCENT * 100}%")
    
    if config.is_paper_mode():
        print(f"模拟初始资金: ${config.PAPER_INITIAL_BALANCE:,.2f}")
    
    print("=" * 60)

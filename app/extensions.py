"""
Flask 應用程式擴展模組
設置 SQLAlchemy、Redis、Migration、LineBotApi 等共享資源
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from redis import Redis
from linebot import LineBotApi, WebhookHandler
import os

# SQLAlchemy 實例（用於 ORM）
db = SQLAlchemy()

# Flask-Migrate 實例（用於資料庫遷移）
migrate = Migrate()

# Redis 連線實例（用於快取）
redis_client = None

# LINE Bot API 實例
line_bot_api = None
line_handler = None


def init_extensions(app):
    """初始化所有 Flask 擴展
    
    Args:
        app: Flask 應用實例
    """
    # 初始化 SQLAlchemy
    db.init_app(app)
    
    # 初始化 Flask-Migrate
    migrate.init_app(app, db)
    
    # 初始化 Redis
    global redis_client
    redis_url = app.config.get('REDIS_URL', 'redis://cache:6379/0')
    redis_password = os.getenv('REDIS_PASSWORD', '')
    
    redis_client = Redis.from_url(
        redis_url,
        password=redis_password,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    
    # 測試 Redis 連線
    try:
        redis_client.ping()
        app.logger.info("✅ Redis 連線成功")
    except Exception as e:
        app.logger.warning(f"⚠️  Redis 連線失敗: {e}")
    
    # 初始化 LINE Bot API
    global line_bot_api, line_handler
    line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
    line_channel_secret = os.getenv('LINE_CHANNEL_SECRET', '')
    
    if line_channel_access_token and line_channel_secret:
        line_bot_api = LineBotApi(line_channel_access_token)
        line_handler = WebhookHandler(line_channel_secret)
        app.logger.info("✅ LINE Bot API 初始化成功")
    else:
        app.logger.warning("⚠️  LINE Bot 憑證未設定，webhook 功能將無法使用")
    
    return app

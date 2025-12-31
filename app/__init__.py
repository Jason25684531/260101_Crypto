"""
Flask 應用程式工廠 (Application Factory Pattern)
"""
from flask import Flask
import os


def create_app(config_name='development'):
    """創建並配置 Flask 應用
    
    Args:
        config_name: 配置環境名稱 (development/production/testing)
    
    Returns:
        Flask app 實例
    """
    app = Flask(__name__)
    
    # 基本配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://trader:traderpass123@db:3306/highfreq_trading'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = (config_name == 'development')
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://cache:6379/0')
    
    # 初始化擴展
    from app.extensions import init_extensions
    init_extensions(app)
    
    # 註冊藍圖
    from app.api.routes import api_bp
    app.register_blueprint(api_bp)
    
    # 健康檢查端點
    @app.route('/health')
    def health_check():
        """健康檢查端點"""
        from app.extensions import db, redis_client
        
        status = {
            'status': 'healthy',
            'database': 'disconnected',
            'cache': 'disconnected'
        }
        
        # 檢查資料庫
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            status['database'] = 'connected'
        except Exception as e:
            status['status'] = 'unhealthy'
            status['database'] = f'error: {str(e)}'
        
        # 檢查 Redis
        try:
            redis_client.ping()
            status['cache'] = 'connected'
        except Exception as e:
            status['status'] = 'unhealthy'
            status['cache'] = f'error: {str(e)}'
        
        return status, 200 if status['status'] == 'healthy' else 503
    
    return app

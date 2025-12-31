"""
Pytest 配置文件
"""
import pytest
import sys
import os

# 將項目根目錄加入 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 設置測試環境變數
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'  # 使用內存資料庫測試


@pytest.fixture(scope='session')
def app():
    """創建測試用 Flask 應用"""
    from app import create_app
    app = create_app('testing')
    
    with app.app_context():
        from app.extensions import db
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """創建測試客戶端"""
    return app.test_client()

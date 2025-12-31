"""
API 路由模組
定義 Flask API 端點（Webhook、健康檢查等）
"""
from flask import Blueprint, request, jsonify, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
from app.extensions import db, redis_client, line_handler
from app.models import OHLCV, ChainMetric, ExchangeNetflow
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/webhook', methods=['POST'])
def webhook():
    """LINE Bot Webhook 端點
    
    接收來自 LINE 的事件推送並驗證簽名
    """
    # 獲取請求標頭中的簽名
    signature = request.headers.get('X-Line-Signature', '')
    
    # 獲取請求 body
    body = request.get_data(as_text=True)
    logger.info(f"收到 Webhook 請求: {body}")
    
    # 驗證簽名並處理事件
    try:
        if line_handler:
            line_handler.handle(body, signature)
        else:
            logger.warning("LINE Handler 未初始化，跳過事件處理")
            return jsonify({
                'status': 'error',
                'message': 'LINE Bot not configured'
            }), 500
    except InvalidSignatureError:
        logger.error("簽名驗證失敗")
        abort(400)
    except Exception as e:
        logger.error(f"Webhook 處理錯誤: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
    return jsonify({
        'status': 'ok'
    }), 200


@api_bp.route('/status', methods=['GET'])
def system_status():
    """系統狀態查詢端點"""
    try:
        # 查詢資料庫統計
        ohlcv_count = OHLCV.query.count()
        chain_metric_count = ChainMetric.query.count()
        netflow_count = ExchangeNetflow.query.count()
        
        # 查詢 Redis 統計
        redis_info = redis_client.info('stats')
        
        return jsonify({
            'status': 'running',
            'database': {
                'ohlcv_records': ohlcv_count,
                'chain_metrics': chain_metric_count,
                'netflow_records': netflow_count
            },
            'cache': {
                'connected': True,
                'total_commands_processed': redis_info.get('total_commands_processed', 0)
            }
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_bp.route('/market/<symbol>', methods=['GET'])
def get_market_data(symbol):
    """查詢市場數據
    
    Args:
        symbol: 交易對符號（如 BTC/USDT）
    
    Query Parameters:
        limit: 返回數據筆數（預設 100）
        timeframe: 時間週期（預設 1m）
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        timeframe = request.args.get('timeframe', '1m')
        
        # 查詢最新的 K 線數據
        data = OHLCV.query.filter_by(
            symbol=symbol,
            timeframe=timeframe
        ).order_by(OHLCV.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'symbol': symbol,
            'timeframe': timeframe,
            'count': len(data),
            'data': [record.to_dict() for record in data]
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

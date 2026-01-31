"""
Machine Learning Pipeline - 信號過濾模型訓練
Phase 5: AI Enhancement

功能：
1. build_dataset() - 從歷史數據構建訓練集
2. train_model() - 訓練隨機森林模型
3. evaluate_model() - 評估模型效果
"""
import os
import sys
import logging
import pickle
from datetime import datetime, timedelta
from typing import Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# 將項目根目錄加入路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模型保存路徑
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'models', 'rf_signal_filter.pkl')


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """計算 RSI 指標"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_width(prices: pd.Series, period: int = 20) -> pd.Series:
    """計算布林帶寬度"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    bb_width = (upper - lower) / sma
    return bb_width


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
    """計算 MACD 指標"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line


def calculate_volume_change(volume: pd.Series, period: int = 5) -> pd.Series:
    """計算成交量變化率"""
    volume_ma = volume.rolling(window=period).mean()
    volume_change = (volume - volume_ma) / volume_ma
    return volume_change


def build_dataset(
    df: Optional[pd.DataFrame] = None,
    lookforward_hours: int = 4,
    profit_threshold: float = 0.01
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    構建訓練數據集
    
    Args:
        df: OHLCV DataFrame (如果為 None 則從資料庫讀取)
        lookforward_hours: 預測未來多少小時
        profit_threshold: 獲利閾值（預設 1%）
    
    Returns:
        features: 特徵 DataFrame
        labels: 標籤 Series (1=獲利, 0=虧損)
    """
    logger.info("開始構建訓練數據集...")
    
    # 如果沒有提供數據，從資料庫讀取
    if df is None:
        try:
            from app import create_app
            from app.models import OHLCV
            
            app = create_app()
            with app.app_context():
                # 讀取歷史數據（至少 3 個月）
                ohlcv_records = OHLCV.query.filter(
                    OHLCV.symbol == 'BTC/USDT'
                ).order_by(OHLCV.timestamp.asc()).all()
                
                if len(ohlcv_records) < 100:
                    logger.warning(f"歷史數據不足: {len(ohlcv_records)} 筆，建議至少 1000 筆")
                
                df = pd.DataFrame([{
                    'timestamp': r.timestamp,
                    'open': r.open,
                    'high': r.high,
                    'low': r.low,
                    'close': r.close,
                    'volume': r.volume
                } for r in ohlcv_records])
        except Exception as e:
            logger.error(f"從資料庫讀取數據失敗: {e}")
            # 生成模擬數據用於測試
            logger.info("使用模擬數據進行測試...")
            df = generate_mock_data(1000)
    
    if df.empty:
        raise ValueError("無法構建數據集：沒有可用的數據")
    
    # 確保按時間排序
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    logger.info(f"原始數據: {len(df)} 筆")
    
    # 計算技術指標（特徵）
    features = pd.DataFrame()
    features['rsi'] = calculate_rsi(df['close'])
    features['bb_width'] = calculate_bollinger_width(df['close'])
    
    macd_line, signal_line = calculate_macd(df['close'])
    features['macd'] = macd_line
    features['macd_signal'] = signal_line
    features['macd_hist'] = macd_line - signal_line
    
    features['volume_change'] = calculate_volume_change(df['volume'])
    
    # 額外特徵：價格動量
    features['price_change_1h'] = df['close'].pct_change(1)
    features['price_change_4h'] = df['close'].pct_change(4)
    features['price_change_24h'] = df['close'].pct_change(24)
    
    # 波動率
    features['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
    
    # 計算標籤：未來 N 小時是否獲利
    future_return = df['close'].shift(-lookforward_hours) / df['close'] - 1
    labels = (future_return > profit_threshold).astype(int)
    
    # 移除 NaN
    valid_idx = features.dropna().index.intersection(labels.dropna().index)
    # 排除最後 lookforward_hours 筆（無法計算未來收益）
    valid_idx = valid_idx[:-lookforward_hours] if len(valid_idx) > lookforward_hours else valid_idx
    
    features = features.loc[valid_idx]
    labels = labels.loc[valid_idx]
    
    logger.info(f"有效數據: {len(features)} 筆")
    logger.info(f"正樣本比例: {labels.mean():.2%}")
    
    return features, labels


def generate_mock_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    生成模擬 OHLCV 數據用於測試
    
    Args:
        n_samples: 樣本數量
    
    Returns:
        模擬的 OHLCV DataFrame
    """
    np.random.seed(42)
    
    # 模擬價格走勢
    base_price = 50000
    returns = np.random.randn(n_samples) * 0.02
    prices = base_price * np.cumprod(1 + returns)
    
    # 生成 OHLCV
    data = []
    for i in range(n_samples):
        close = prices[i]
        high = close * (1 + abs(np.random.randn()) * 0.01)
        low = close * (1 - abs(np.random.randn()) * 0.01)
        open_price = np.random.uniform(low, high)
        volume = np.random.uniform(100, 1000)
        
        data.append({
            'timestamp': i,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data)


def train_model(
    features: pd.DataFrame,
    labels: pd.Series,
    test_size: float = 0.2,
    n_estimators: int = 100,
    max_depth: int = 10,
    random_state: int = 42
) -> RandomForestClassifier:
    """
    訓練隨機森林模型
    
    Args:
        features: 特徵 DataFrame
        labels: 標籤 Series
        test_size: 測試集比例
        n_estimators: 樹的數量
        max_depth: 樹的最大深度
        random_state: 隨機種子
    
    Returns:
        訓練好的模型
    """
    logger.info("開始訓練隨機森林模型...")
    
    # 分割訓練集和測試集
    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=test_size, random_state=random_state, stratify=labels
    )
    
    logger.info(f"訓練集: {len(X_train)} 筆, 測試集: {len(X_test)} 筆")
    
    # 創建並訓練模型
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        class_weight='balanced'  # 處理類別不平衡
    )
    
    model.fit(X_train, y_train)
    
    # 評估模型
    y_pred = model.predict(X_test)
    
    logger.info("\n=== 模型評估報告 ===")
    logger.info(f"準確率: {accuracy_score(y_test, y_pred):.4f}")
    logger.info(f"\n分類報告:\n{classification_report(y_test, y_pred)}")
    logger.info(f"\n混淆矩陣:\n{confusion_matrix(y_test, y_pred)}")
    
    # 交叉驗證
    cv_scores = cross_val_score(model, features, labels, cv=5, scoring='accuracy')
    logger.info(f"\n5 折交叉驗證準確率: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # 特徵重要性
    feature_importance = pd.DataFrame({
        'feature': features.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info(f"\n特徵重要性:\n{feature_importance.to_string()}")
    
    return model


def save_model(model: RandomForestClassifier, path: str = MODEL_PATH):
    """保存模型到檔案"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'wb') as f:
        pickle.dump({
            'model': model,
            'version': '1.0.0',
            'trained_at': datetime.now().isoformat(),
            'features': ['rsi', 'bb_width', 'macd', 'macd_signal', 'macd_hist',
                        'volume_change', 'price_change_1h', 'price_change_4h',
                        'price_change_24h', 'volatility']
        }, f)
    
    logger.info(f"模型已保存至: {path}")


def load_model(path: str = MODEL_PATH) -> dict:
    """載入模型"""
    with open(path, 'rb') as f:
        return pickle.load(f)


def main():
    """主程式：執行完整的 ML Pipeline"""
    print("=" * 60)
    print("Phase 5: Machine Learning Signal Filter - Training Pipeline")
    print("=" * 60)
    
    try:
        # 1. 構建數據集
        features, labels = build_dataset()
        
        # 2. 訓練模型
        model = train_model(features, labels)
        
        # 3. 保存模型
        save_model(model)
        
        print("\n" + "=" * 60)
        print("✅ ML Pipeline 執行完成！")
        print(f"模型已保存至: {MODEL_PATH}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"ML Pipeline 執行失敗: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

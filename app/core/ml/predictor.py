"""
Signal Predictor - ML 信號預測器
Phase 5: AI Enhancement

使用 Singleton Pattern 確保全局只有一個模型實例
用於實時預測交易信號的獲利機率
"""
import os
import logging
import pickle
from typing import Dict, List, Optional, Union
from threading import Lock

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# 模型路徑
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), 
    '..', '..', '..', 
    'data', 'models', 'rf_signal_filter.pkl'
)


class SignalPredictor:
    """
    ML 信號預測器 (Singleton Pattern)
    
    功能：
    1. 載入預訓練的隨機森林模型
    2. 預測交易信號的獲利機率
    3. 提供信號過濾建議
    
    使用方式：
        predictor = SignalPredictor.get_instance()
        proba = predictor.predict_proba(features)
        if proba >= 0.6:
            # 執行交易
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton Pattern 實現"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化預測器"""
        if self._initialized:
            return
        
        self.model = None
        self.model_info = None
        self.feature_names = None
        self.enabled = False
        self.min_probability = 0.6  # 最低獲利機率閾值
        
        # 嘗試載入模型
        self._load_model()
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'SignalPredictor':
        """獲取 Singleton 實例"""
        return cls()
    
    def _load_model(self, path: str = MODEL_PATH) -> bool:
        """
        載入預訓練模型
        
        Args:
            path: 模型檔案路徑
        
        Returns:
            True 如果載入成功
        """
        try:
            if not os.path.exists(path):
                logger.warning(f"模型檔案不存在: {path}")
                logger.info("請先執行 python scripts/ml_pipeline.py 訓練模型")
                return False
            
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.model_info = {
                'version': data.get('version', 'unknown'),
                'trained_at': data.get('trained_at', 'unknown')
            }
            self.feature_names = data.get('features', [])
            self.enabled = True
            
            logger.info(
                f"✅ ML 模型載入成功 - "
                f"版本: {self.model_info['version']}, "
                f"訓練時間: {self.model_info['trained_at']}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"載入模型失敗: {e}")
            self.enabled = False
            return False
    
    def reload_model(self, path: str = MODEL_PATH) -> bool:
        """重新載入模型（用於模型更新後）"""
        self.enabled = False
        return self._load_model(path)
    
    def predict_proba(
        self,
        features: Union[Dict, pd.DataFrame, np.ndarray]
    ) -> float:
        """
        預測獲利機率
        
        Args:
            features: 特徵數據，可以是：
                - Dict: {'rsi': 45.0, 'bb_width': 0.05, ...}
                - DataFrame: 單行數據
                - ndarray: 特徵向量
        
        Returns:
            獲利機率 (0.0 - 1.0)，如果模型未載入則返回 0.5（中性）
        """
        if not self.enabled or self.model is None:
            logger.debug("ML 模型未啟用，返回中性機率 0.5")
            return 0.5
        
        try:
            # 轉換輸入格式
            if isinstance(features, dict):
                # 確保特徵順序正確
                X = np.array([[features.get(f, 0) for f in self.feature_names]])
            elif isinstance(features, pd.DataFrame):
                X = features[self.feature_names].values
            elif isinstance(features, np.ndarray):
                X = features.reshape(1, -1) if features.ndim == 1 else features
            else:
                raise ValueError(f"不支援的輸入類型: {type(features)}")
            
            # 處理 NaN
            X = np.nan_to_num(X, nan=0.0)
            
            # 預測機率
            proba = self.model.predict_proba(X)[0]
            
            # 返回正類（獲利）的機率
            return float(proba[1])
        
        except Exception as e:
            logger.error(f"預測失敗: {e}")
            return 0.5
    
    def should_filter(
        self,
        features: Union[Dict, pd.DataFrame, np.ndarray],
        min_probability: Optional[float] = None
    ) -> bool:
        """
        判斷是否應該過濾掉此信號
        
        Args:
            features: 特徵數據
            min_probability: 最低獲利機率（預設使用 self.min_probability）
        
        Returns:
            True 如果應該過濾（即不執行交易）
        """
        threshold = min_probability or self.min_probability
        proba = self.predict_proba(features)
        
        should_filter = proba < threshold
        
        if should_filter:
            logger.info(f"🚫 ML 過濾: 機率 {proba:.2%} < 閾值 {threshold:.2%}")
        else:
            logger.info(f"✅ ML 通過: 機率 {proba:.2%} >= 閾值 {threshold:.2%}")
        
        return should_filter
    
    def get_prediction_with_details(
        self,
        features: Union[Dict, pd.DataFrame, np.ndarray]
    ) -> Dict:
        """
        獲取詳細的預測結果
        
        Args:
            features: 特徵數據
        
        Returns:
            包含預測結果和建議的字典
        """
        proba = self.predict_proba(features)
        
        # 根據機率給出建議
        if proba >= 0.7:
            recommendation = 'STRONG_BUY'
            confidence = 'HIGH'
        elif proba >= 0.6:
            recommendation = 'BUY'
            confidence = 'MEDIUM'
        elif proba >= 0.4:
            recommendation = 'HOLD'
            confidence = 'LOW'
        else:
            recommendation = 'AVOID'
            confidence = 'MEDIUM' if proba < 0.3 else 'LOW'
        
        return {
            'probability': proba,
            'recommendation': recommendation,
            'confidence': confidence,
            'should_trade': proba >= self.min_probability,
            'model_enabled': self.enabled,
            'model_version': self.model_info.get('version') if self.model_info else None
        }
    
    def set_threshold(self, threshold: float):
        """設置最低獲利機率閾值"""
        if 0 <= threshold <= 1:
            self.min_probability = threshold
            logger.info(f"ML 閾值已更新為: {threshold:.2%}")
        else:
            raise ValueError("閾值必須在 0 到 1 之間")
    
    @property
    def is_enabled(self) -> bool:
        """檢查模型是否已啟用"""
        return self.enabled
    
    @property
    def status(self) -> Dict:
        """獲取預測器狀態"""
        return {
            'enabled': self.enabled,
            'model_loaded': self.model is not None,
            'model_info': self.model_info,
            'threshold': self.min_probability,
            'feature_names': self.feature_names
        }


# 便捷函數
def get_predictor() -> SignalPredictor:
    """獲取全局預測器實例"""
    return SignalPredictor.get_instance()

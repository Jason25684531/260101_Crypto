"""
ML 信號預測器快速測試腳本

直接運行，繞過 pytest 插件衝突
"""

import sys
import os

# 確保項目路徑在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """執行所有 ML 預測器測試"""
    print("=" * 60)
    print("🧪 ML Signal Predictor 測試")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # 測試 1: Singleton 模式
    print("\n[1/10] 測試 Singleton 模式...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        
        instance1 = SignalPredictor.get_instance()
        instance2 = SignalPredictor.get_instance()
        
        assert instance1 is instance2, "Singleton 失敗"
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 2: 預測器初始化
    print("[2/10] 測試預測器初始化...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        
        predictor = SignalPredictor.get_instance()
        
        assert predictor is not None
        assert hasattr(predictor, 'is_enabled')
        assert hasattr(predictor, 'predict_proba')
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 3: 閾值管理
    print("[3/10] 測試閾值管理...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        predictor = SignalPredictor.get_instance()
        
        assert predictor.min_probability == 0.6
        predictor.set_threshold(0.7)
        assert predictor.min_probability == 0.7
        predictor.set_threshold(0.6)  # 恢復
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 4: 特徵驗證
    print("[4/10] 測試特徵驗證...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        predictor = SignalPredictor.get_instance()
        
        valid_features = {
            'rsi': 45.0, 'bb_width': 0.05, 'macd': 100.0,
            'macd_signal': 80.0, 'macd_hist': 20.0,
            'volume_change': 0.15, 'price_change_1h': 0.02,
            'price_change_4h': 0.05, 'price_change_24h': 0.08,
            'volatility': 0.03
        }
        
        # 測試預測功能（驗證特徵處理）
        # 模型未載入時應返回 0.5
        proba = predictor.predict_proba(valid_features)
        assert 0.0 <= proba <= 1.0, f"機率超出範圍: {proba}"
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 5: 特徵名稱一致性
    print("[5/10] 測試特徵名稱一致性...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        predictor = SignalPredictor.get_instance()
        
        # 模型未載入時，feature_names 可能為 None
        if predictor.feature_names is None:
            # 這是預期的 - 模型未載入
            print("✅ PASSED (模型未載入，跳過驗證)")
        else:
            expected = [
                'rsi', 'bb_width', 'macd', 'macd_signal', 'macd_hist',
                'volume_change', 'price_change_1h', 'price_change_4h',
                'price_change_24h', 'volatility'
            ]
            assert predictor.feature_names == expected
            print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 6: 模型禁用回退
    print("[6/10] 測試模型禁用回退...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        predictor = SignalPredictor.get_instance()
        
        features = {
            'rsi': 45.0, 'bb_width': 0.05, 'macd': 100.0,
            'macd_signal': 80.0, 'macd_hist': 20.0,
            'volume_change': 0.15, 'price_change_1h': 0.02,
            'price_change_4h': 0.05, 'price_change_24h': 0.08,
            'volatility': 0.03
        }
        
        original_enabled = predictor.enabled
        predictor.enabled = False
        
        proba = predictor.predict_proba(features)
        should_filter = predictor.should_filter(features)
        
        predictor.enabled = original_enabled
        
        assert proba == 0.5, f"禁用時應返回 0.5，得到 {proba}"
        assert should_filter == True, "禁用時 0.5 < 0.6 應該過濾"
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 7: 詳細預測輸出
    print("[7/10] 測試詳細預測輸出...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        predictor = SignalPredictor.get_instance()
        
        features = {
            'rsi': 45.0, 'bb_width': 0.05, 'macd': 100.0,
            'macd_signal': 80.0, 'macd_hist': 20.0,
            'volume_change': 0.15, 'price_change_1h': 0.02,
            'price_change_4h': 0.05, 'price_change_24h': 0.08,
            'volatility': 0.03
        }
        
        result = predictor.get_prediction_with_details(features)
        
        assert 'probability' in result
        assert 'should_trade' in result
        assert 'recommendation' in result
        assert 'model_enabled' in result
        assert 0.0 <= result['probability'] <= 1.0
        assert isinstance(result['should_trade'], bool)
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 8: 極端值處理
    print("[8/10] 測試極端值處理...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        predictor = SignalPredictor.get_instance()
        
        extreme_features = {
            'rsi': 100.0, 'bb_width': 1.0, 'macd': 10000.0,
            'macd_signal': 10000.0, 'macd_hist': 0.0,
            'volume_change': 10.0, 'price_change_1h': 0.5,
            'price_change_4h': 1.0, 'price_change_24h': 2.0,
            'volatility': 0.5
        }
        
        proba = predictor.predict_proba(extreme_features)
        assert 0.0 <= proba <= 1.0, f"機率超出範圍: {proba}"
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 9: 負值處理
    print("[9/10] 測試負值處理...", end=" ")
    try:
        from app.core.ml.predictor import SignalPredictor
        SignalPredictor._instance = None
        predictor = SignalPredictor.get_instance()
        
        negative_features = {
            'rsi': 20.0, 'bb_width': 0.05, 'macd': -500.0,
            'macd_signal': -400.0, 'macd_hist': -100.0,
            'volume_change': -0.5, 'price_change_1h': -0.1,
            'price_change_4h': -0.2, 'price_change_24h': -0.3,
            'volatility': 0.1
        }
        
        proba = predictor.predict_proba(negative_features)
        assert 0.0 <= proba <= 1.0, f"機率超出範圍: {proba}"
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 測試 10: TradeExecutor 參數檢查
    print("[10/10] 測試 TradeExecutor ML 參數...", end=" ")
    try:
        import inspect
        from app.core.execution.trader import TradeExecutor
        
        sig = inspect.signature(TradeExecutor.execute_strategy)
        
        assert 'use_ml_filter' in sig.parameters
        assert 'ml_threshold' in sig.parameters
        assert sig.parameters['use_ml_filter'].default == True
        assert sig.parameters['ml_threshold'].default == 0.6
        print("✅ PASSED")
        passed += 1
    except Exception as e:
        print(f"❌ FAILED: {e}")
        failed += 1
    
    # 總結
    print("\n" + "=" * 60)
    total = passed + failed
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if failed == 0:
        print("🎉 所有測試通過！")
    else:
        print(f"⚠️ {failed} 個測試失敗")
    
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

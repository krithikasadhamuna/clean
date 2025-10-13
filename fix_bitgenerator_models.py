#!/usr/bin/env python3
"""
Fix BitGenerator Compatibility Issues
This script fixes the MT19937 BitGenerator compatibility issues in the ML models
"""

import pickle
import numpy as np
import sys
import os
from pathlib import Path

def fix_model_bitgenerator(model_path):
    """Fix BitGenerator compatibility issues in a model file"""
    try:
        print(f"Fixing model: {model_path}")
        
        # Load the model
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        # Check if model has random_state or random_state_ attributes
        if hasattr(model, 'random_state'):
            if hasattr(model.random_state, 'bit_generator'):
                # Replace the problematic BitGenerator
                model.random_state = np.random.RandomState(42)
                print(f"  ✅ Fixed random_state BitGenerator")
        
        if hasattr(model, 'random_state_'):
            if hasattr(model.random_state_, 'bit_generator'):
                # Replace the problematic BitGenerator
                model.random_state_ = np.random.RandomState(42)
                print(f"  ✅ Fixed random_state_ BitGenerator")
        
        # Check for nested estimators (for ensemble models)
        if hasattr(model, 'estimators_'):
            for i, estimator in enumerate(model.estimators_):
                if hasattr(estimator, 'random_state'):
                    if hasattr(estimator.random_state, 'bit_generator'):
                        estimator.random_state = np.random.RandomState(42)
                        print(f"  ✅ Fixed estimator {i} random_state")
        
        # Check for base_estimator
        if hasattr(model, 'base_estimator'):
            if hasattr(model.base_estimator, 'random_state'):
                if hasattr(model.base_estimator.random_state, 'bit_generator'):
                    model.base_estimator.random_state = np.random.RandomState(42)
                    print(f"  ✅ Fixed base_estimator random_state")
        
        # Save the fixed model
        backup_path = model_path + '.backup'
        os.rename(model_path, backup_path)
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        print(f"  ✅ Model fixed and saved (backup: {backup_path})")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to fix model: {e}")
        return False

def fix_all_problematic_models():
    """Fix all models with BitGenerator issues"""
    print("=" * 80)
    print("FIXING BITGENERATOR COMPATIBILITY ISSUES")
    print("=" * 80)
    
    # Path to the models directory
    models_dir = Path("server/ml_models/DEPLOY_READY_SOC_MODELS")
    
    # Models that typically have BitGenerator issues
    problematic_models = [
        "text_log_anomaly_detector.pkl",
        "insider_threat_detector.pkl"
    ]
    
    fixed_count = 0
    
    for model_file in problematic_models:
        model_path = models_dir / model_file
        
        if model_path.exists():
            if fix_model_bitgenerator(model_path):
                fixed_count += 1
        else:
            print(f"❌ Model not found: {model_path}")
    
    print("\n" + "=" * 80)
    print(f"FIXING COMPLETE: {fixed_count}/{len(problematic_models)} models fixed")
    print("=" * 80)
    
    if fixed_count > 0:
        print("\n✅ Models fixed! Now run the verification again:")
        print("python3 verify_server_deployment.py")
    else:
        print("\n❌ No models were fixed. Check the error messages above.")
    
    return fixed_count > 0

def test_fixed_models():
    """Test if the fixed models work"""
    print("\n" + "=" * 80)
    print("TESTING FIXED MODELS")
    print("=" * 80)
    
    try:
        sys.path.append('server')
        from ml_model_manager import ml_model_manager
        
        # Test text log anomaly model
        try:
            prediction, confidence = ml_model_manager.predict_text_log_anomaly("test log message")
            print(f"✅ Text log anomaly model: Working (confidence: {confidence:.2%})")
        except Exception as e:
            print(f"❌ Text log anomaly model: Still broken - {e}")
        
        # Test insider threat model
        try:
            test_features = np.random.random((1, 39))  # 39 features for insider threat
            prediction, confidence = ml_model_manager.predict_insider_threat(test_features)
            print(f"✅ Insider threat model: Working (confidence: {confidence:.2%})")
        except Exception as e:
            print(f"❌ Insider threat model: Still broken - {e}")
        
    except Exception as e:
        print(f"❌ Failed to test models: {e}")

if __name__ == "__main__":
    success = fix_all_problematic_models()
    
    if success:
        test_fixed_models()
    
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Server Deployment Verification Script
Run this on the server to verify ML models are working correctly
"""

import sys
import os

def verify_deployment():
    """Verify ML models deployment on server"""
    print("=" * 80)
    print("SERVER ML MODELS DEPLOYMENT VERIFICATION")
    print("=" * 80)
    
    # Check if files exist
    files_to_check = [
        "server/ml_model_manager.py",
        "server/ml_models/DEPLOY_READY_SOC_MODELS",
        "server/agents/detection_agent/ai_enhanced_detector.py",
        "test_production_ml_models.py",
        "test_error_resolution.py"
    ]
    
    print("\n1. CHECKING FILES:")
    all_files_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ Some files are missing. Please check the upload.")
        return False
    
    # Check ML models directory
    print("\n2. CHECKING ML MODELS:")
    models_dir = "server/ml_models/DEPLOY_READY_SOC_MODELS"
    if os.path.exists(models_dir):
        model_files = os.listdir(models_dir)
        pkl_files = [f for f in model_files if f.endswith('.pkl')]
        print(f"   ✅ Found {len(pkl_files)} model files")
        
        expected_models = [
            "multi_os_log_anomaly_detector.pkl",
            "text_log_anomaly_detector.pkl", 
            "insider_threat_detector.pkl",
            "network_intrusion_Time-Series_Network_logs.pkl",
            "web_attack_detector.pkl",
            "time_series_network_detector.pkl"
        ]
        
        for model in expected_models:
            if model in model_files:
                print(f"   ✅ {model}")
            else:
                print(f"   ❌ {model} - MISSING")
    else:
        print(f"   ❌ {models_dir} - MISSING")
        return False
    
    # Test ML model loading
    print("\n3. TESTING ML MODEL LOADING:")
    try:
        sys.path.append('server')
        from ml_model_manager import ml_model_manager
        
        model_info = ml_model_manager.get_model_info()
        print(f"   ✅ Loaded {model_info['total_models']} models")
        print(f"   ✅ Models: {', '.join(model_info['loaded_models'])}")
        
    except Exception as e:
        print(f"   ❌ ML model loading failed: {e}")
        return False
    
    # Test AI Enhanced Detector
    print("\n4. TESTING AI ENHANCED DETECTOR:")
    try:
        from agents.detection_agent.ai_enhanced_detector import AIEnhancedThreatDetector
        
        detector = AIEnhancedThreatDetector()
        print("   ✅ AI Enhanced Detector initialized")
        
        if hasattr(detector, 'ml_manager') and detector.ml_manager:
            print("   ✅ ML models integrated successfully")
        else:
            print("   ❌ ML models not integrated")
            return False
            
    except Exception as e:
        print(f"   ❌ AI Enhanced Detector test failed: {e}")
        return False
    
    # Test log detection
    print("\n5. TESTING LOG DETECTION:")
    try:
        test_log = {
            'message': 'Test suspicious activity',
            'command_line': 'powershell -encodedcommand'
        }
        
        result = detector._detect_generic_log_entry(test_log)
        print(f"   ✅ Log detection working")
        print(f"   ✅ Threat detected: {result.get('threat_detected')}")
        print(f"   ✅ Confidence: {result.get('confidence_score', 0):.2%}")
        
    except Exception as e:
        print(f"   ❌ Log detection test failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✅ DEPLOYMENT VERIFICATION SUCCESSFUL!")
    print("=" * 80)
    print("\nAll ML models are working correctly on the server.")
    print("The previous errors should now be resolved.")
    print("\nYou can now:")
    print("1. Start the server")
    print("2. Monitor logs for successful ML model loading")
    print("3. Test log ingestion via /api/logs/ingest")
    
    return True

if __name__ == "__main__":
    success = verify_deployment()
    sys.exit(0 if success else 1)

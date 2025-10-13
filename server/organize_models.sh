#!/bin/bash

echo "Organizing ML model files on server..."

# Create the directory structure
mkdir -p /home/krithika/full-func/clean/server/ml_models/DEPLOY_READY_SOC_MODELS

# Move all the model files to the correct location
cd /home/krithika/full-func/clean

echo "Moving model files..."

# Move the 6 main model files and their scalers
mv multi_os_log_anomaly_detector.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv multi_os_log_anomaly_scaler.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv text_log_anomaly_detector.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv text_log_tfidf_vectorizer.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv insider_threat_detector.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv insider_threat_scaler.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv network_intrusion_Time-Series_Network_logs.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv network_intrusion_Time-Series_Network_logs_scaler.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv web_attack_detector.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv web_attack_scaler.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv time_series_network_detector.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/
mv time_series_network_detector_scaler.pkl server/ml_models/DEPLOY_READY_SOC_MODELS/

echo "Model files organized successfully!"
echo "Directory structure:"
ls -la server/ml_models/DEPLOY_READY_SOC_MODELS/

echo ""
echo "Now run: python3 verify_server_deployment.py"

# 🔧 QUICK SERVER STRUCTURE FIX

## 🚨 **PROBLEM IDENTIFIED**

The file structure got mixed up during uploads. Files are in the wrong directories.

## 🚀 **QUICK FIX COMMANDS**

**Run these commands on your server:**

```bash
cd /home/krithika/full-func/clean

# Make the fix script executable and run it
chmod +x fix_server_structure.sh
./fix_server_structure.sh
```

## 🎯 **MANUAL FIX (If script doesn't work)**

```bash
cd /home/krithika/full-func/clean

# Create proper structure
mkdir -p server/ml_models/DEPLOY_READY_SOC_MODELS
mkdir -p server/api
mkdir -p server/core
mkdir -p server/shared
mkdir -p server/config

# Move ML models to correct location
cp -r DEPLOY_READY_SOC_MODELS/* server/ml_models/DEPLOY_READY_SOC_MODELS/

# Move server directories
cp -r api/* server/api/ 2>/dev/null || true
cp -r core/* server/core/ 2>/dev/null || true
cp -r shared/* server/shared/ 2>/dev/null || true
cp -r config/* server/config/ 2>/dev/null || true
cp -r downloads/* server/downloads/ 2>/dev/null || true
cp -r agents/* server/agents/ 2>/dev/null || true

# Move server files
mv main.py server/ 2>/dev/null || true
mv requirements.txt server/ 2>/dev/null || true
mv soc_database.db server/ 2>/dev/null || true

# Move Python files to server
mv *.py server/ 2>/dev/null || true

# Move shell scripts to server
mv *.sh server/ 2>/dev/null || true

# Move JSON files to server
mv *.json server/ 2>/dev/null || true

# Move log files to server
mv *.log server/ 2>/dev/null || true
```

## ✅ **EXPECTED RESULT**

After the fix, your structure should be:

```
/home/krithika/full-func/clean/
├── server/
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── shared/
│   ├── config/
│   ├── downloads/
│   ├── ml_models/
│   │   └── DEPLOY_READY_SOC_MODELS/
│   │       ├── multi_os_log_anomaly_detector.pkl
│   │       ├── text_log_anomaly_detector.pkl
│   │       ├── insider_threat_detector.pkl
│   │       ├── network_intrusion_Time-Series_Network_logs.pkl
│   │       ├── web_attack_detector.pkl
│   │       ├── time_series_network_detector.pkl
│   │       └── [all scalers and vectorizers]
│   ├── main.py
│   ├── requirements.txt
│   ├── ml_model_manager.py
│   ├── ml_model_manager_fixed.py
│   └── [other server files]
├── test_production_ml_models.py
├── test_error_resolution.py
├── verify_server_deployment.py
├── fix_bitgenerator_models.py
└── *.md documentation files
```

## 🧪 **TEST THE FIX**

After organizing the structure:

```bash
# Test the structure
python3 verify_server_deployment.py

# If that works, try the BitGenerator fix
cp server/ml_model_manager_fixed.py server/ml_model_manager.py
python3 verify_server_deployment.py
```

## 🎯 **WHAT TO EXPECT**

After the structure fix, verification should show:
```
1. CHECKING FILES:
   ✅ server/ml_model_manager.py
   ✅ server/ml_models/DEPLOY_READY_SOC_MODELS
   ✅ server/agents/detection_agent/ai_enhanced_detector.py
   ✅ test_production_ml_models.py
   ✅ test_error_resolution.py
```

## 🚨 **IF STILL BROKEN**

If the structure is still wrong, run:

```bash
# Check what's in each directory
ls -la
ls -la server/
ls -la server/ml_models/
ls -la server/ml_models/DEPLOY_READY_SOC_MODELS/

# Check if ML models are in the right place
find . -name "*.pkl" -type f
```

## 🎉 **READY TO FIX!**

Run the fix script and your server structure will be properly organized!

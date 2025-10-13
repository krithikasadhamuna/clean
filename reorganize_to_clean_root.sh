#!/bin/bash

echo "Reorganizing files to clean root directory..."

# Navigate to the clean directory
cd /home/krithika/full-func/clean

echo "Current structure:"
ls -la

echo ""
echo "Reorganizing files..."

# Create the ML models directory structure in clean root
mkdir -p ml_models/DEPLOY_READY_SOC_MODELS

# Move ML models from DEPLOY_READY_SOC_MODELS to ml_models/DEPLOY_READY_SOC_MODELS
if [ -d "DEPLOY_READY_SOC_MODELS" ]; then
    echo "Moving ML models to ml_models/DEPLOY_READY_SOC_MODELS/"
    cp -r DEPLOY_READY_SOC_MODELS/* ml_models/DEPLOY_READY_SOC_MODELS/ 2>/dev/null || true
    rm -rf DEPLOY_READY_SOC_MODELS
fi

# Move ML models from server/ml_models to ml_models
if [ -d "server/ml_models" ]; then
    echo "Moving server/ml_models to ml_models/"
    cp -r server/ml_models/* ml_models/ 2>/dev/null || true
fi

# Move all server subdirectories to clean root
echo "Moving server subdirectories to clean root..."

# Move agents
if [ -d "server/agents" ]; then
    echo "Moving server/agents to agents/"
    cp -r server/agents/* agents/ 2>/dev/null || true
fi

# Move api
if [ -d "server/api" ]; then
    echo "Moving server/api to api/"
    cp -r server/api/* api/ 2>/dev/null || true
fi

# Move core
if [ -d "server/core" ]; then
    echo "Moving server/core to core/"
    cp -r server/core/* core/ 2>/dev/null || true
fi

# Move shared
if [ -d "server/shared" ]; then
    echo "Moving server/shared to shared/"
    cp -r server/shared/* shared/ 2>/dev/null || true
fi

# Move config
if [ -d "server/config" ]; then
    echo "Moving server/config to config/"
    cp -r server/config/* config/ 2>/dev/null || true
fi

# Move downloads
if [ -d "server/downloads" ]; then
    echo "Moving server/downloads to downloads/"
    cp -r server/downloads/* downloads/ 2>/dev/null || true
fi

# Move Python files from server to clean root
echo "Moving Python files from server to clean root..."

# Move main.py
if [ -f "server/main.py" ]; then
    echo "Moving server/main.py to main.py"
    cp server/main.py main.py
fi

# Move requirements.txt
if [ -f "server/requirements.txt" ]; then
    echo "Moving server/requirements.txt to requirements.txt"
    cp server/requirements.txt requirements.txt
fi

# Move ML model manager files
if [ -f "server/ml_model_manager.py" ]; then
    echo "Moving server/ml_model_manager.py to ml_model_manager.py"
    cp server/ml_model_manager.py ml_model_manager.py
fi

if [ -f "server/ml_model_manager_fixed.py" ]; then
    echo "Moving server/ml_model_manager_fixed.py to ml_model_manager_fixed.py"
    cp server/ml_model_manager_fixed.py ml_model_manager_fixed.py
fi

# Move other Python files from server
for file in server/*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        if [ "$filename" != "main.py" ] && [ "$filename" != "ml_model_manager.py" ] && [ "$filename" != "ml_model_manager_fixed.py" ]; then
            echo "Moving server/$filename to $filename"
            cp "$file" "$filename"
        fi
    fi
done

# Move database file
if [ -f "server/soc_database.db" ]; then
    echo "Moving server/soc_database.db to soc_database.db"
    cp server/soc_database.db soc_database.db
fi

# Move shell scripts from server
for file in server/*.sh; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

# Move JSON files from server
for file in server/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

# Move log files from server
for file in server/*.log; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

# Clean up the server directory (keep it for now as backup)
echo "Cleaning up..."

# Remove the old server directory structure (but keep as backup)
if [ -d "server" ]; then
    echo "Renaming server directory to server_backup"
    mv server server_backup
fi

# Remove the old DEPLOY_READY_SOC_MODELS directory if it still exists
if [ -d "DEPLOY_READY_SOC_MODELS" ]; then
    echo "Removing old DEPLOY_READY_SOC_MODELS directory"
    rm -rf DEPLOY_READY_SOC_MODELS
fi

echo ""
echo "Reorganization complete!"
echo ""
echo "New structure in clean root:"
echo "├── agents/                    ← Detection agents"
echo "├── api/                       ← API endpoints"
echo "├── core/                      ← Core functionality"
echo "├── shared/                    ← Shared utilities"
echo "├── config/                    ← Configuration files"
echo "├── downloads/                 ← Download files"
echo "├── ml_models/                 ← ML models directory"
echo "│   └── DEPLOY_READY_SOC_MODELS/"
echo "│       ├── multi_os_log_anomaly_detector.pkl"
echo "│       ├── text_log_anomaly_detector.pkl"
echo "│       ├── insider_threat_detector.pkl"
echo "│       ├── network_intrusion_Time-Series_Network_logs.pkl"
echo "│       ├── web_attack_detector.pkl"
echo "│       ├── time_series_network_detector.pkl"
echo "│       └── [all scalers and vectorizers]"
echo "├── main.py                    ← Server entry point"
echo "├── requirements.txt           ← Python dependencies"
echo "├── ml_model_manager.py        ← ML model manager"
echo "├── ml_model_manager_fixed.py  ← Fixed ML model manager"
echo "├── soc_database.db            ← Database file"
echo "├── test_production_ml_models.py"
echo "├── test_error_resolution.py"
echo "├── verify_server_deployment.py"
echo "├── fix_bitgenerator_models.py"
echo "└── *.md documentation files"
echo ""
echo "Now run: python3 verify_server_deployment.py"

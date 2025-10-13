#!/bin/bash

echo "Fixing server file structure..."

# Navigate to the clean directory
cd /home/krithika/full-func/clean

echo "Current structure issues:"
echo "1. Some files are in the wrong directories"
echo "2. Need to organize the structure properly"

# Create proper directory structure
echo "Creating proper directory structure..."
mkdir -p server/ml_models/DEPLOY_READY_SOC_MODELS
mkdir -p server/api
mkdir -p server/core
mkdir -p server/shared
mkdir -p server/config

# Move files to correct locations
echo "Moving files to correct locations..."

# Move ML model files to correct location
if [ -d "DEPLOY_READY_SOC_MODELS" ]; then
    echo "Moving DEPLOY_READY_SOC_MODELS to server/ml_models/"
    cp -r DEPLOY_READY_SOC_MODELS/* server/ml_models/DEPLOY_READY_SOC_MODELS/ 2>/dev/null || true
fi

# Move server files to correct location
echo "Moving server files..."

# Move Python files that should be in server root
for file in main.py requirements.txt; do
    if [ -f "$file" ]; then
        echo "Moving $file to server/"
        mv "$file" server/
    fi
done

# Move API files
if [ -d "api" ]; then
    echo "Moving api/ to server/"
    cp -r api/* server/api/ 2>/dev/null || true
fi

# Move core files
if [ -d "core" ]; then
    echo "Moving core/ to server/"
    cp -r core/* server/core/ 2>/dev/null || true
fi

# Move shared files
if [ -d "shared" ]; then
    echo "Moving shared/ to server/"
    cp -r shared/* server/shared/ 2>/dev/null || true
fi

# Move config files
if [ -d "config" ]; then
    echo "Moving config/ to server/"
    cp -r config/* server/config/ 2>/dev/null || true
fi

# Move downloads directory
if [ -d "downloads" ]; then
    echo "Moving downloads/ to server/"
    cp -r downloads/* server/downloads/ 2>/dev/null || true
fi

# Move agents directory
if [ -d "agents" ]; then
    echo "Moving agents/ to server/"
    cp -r agents/* server/agents/ 2>/dev/null || true
fi

# Move database file
if [ -f "soc_database.db" ]; then
    echo "Moving soc_database.db to server/"
    mv soc_database.db server/
fi

# Move Python files that belong in server root
for file in *.py; do
    if [ -f "$file" ] && [ "$file" != "main.py" ]; then
        echo "Moving $file to server/"
        mv "$file" server/
    fi
done

# Move shell scripts to server
for file in *.sh; do
    if [ -f "$file" ]; then
        echo "Moving $file to server/"
        mv "$file" server/
    fi
done

# Move JSON files to server
for file in *.json; do
    if [ -f "$file" ]; then
        echo "Moving $file to server/"
        mv "$file" server/
    fi
done

# Move log files to server
for file in *.log; do
    if [ -f "$file" ]; then
        echo "Moving $file to server/"
        mv "$file" server/
    fi
done

echo ""
echo "File structure fixed!"
echo ""
echo "New structure:"
echo "server/"
echo "├── agents/"
echo "├── api/"
echo "├── core/"
echo "├── shared/"
echo "├── config/"
echo "├── downloads/"
echo "├── ml_models/"
echo "│   └── DEPLOY_READY_SOC_MODELS/"
echo "├── main.py"
echo "├── requirements.txt"
echo "├── ml_model_manager.py"
echo "├── ml_model_manager_fixed.py"
echo "└── [other server files]"
echo ""
echo "Root directory now contains:"
echo "├── server/"
echo "├── test_*.py"
echo "├── verify_server_deployment.py"
echo "├── fix_bitgenerator_models.py"
echo "└── *.md documentation files"
echo ""
echo "Now run: python3 verify_server_deployment.py"

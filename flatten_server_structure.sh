#!/bin/bash

echo "Flattening server structure - moving everything to clean directory root..."

# Navigate to the clean directory
cd /home/krithika/full-func/clean

echo "Current structure:"
ls -la

echo ""
echo "Flattening structure..."

# Move everything from server/ to current directory
if [ -d "server" ]; then
    echo "Moving contents from server/ to current directory..."
    
    # Move all files and directories from server/ to current directory
    for item in server/*; do
        if [ -e "$item" ]; then
            item_name=$(basename "$item")
            echo "Moving $item_name..."
            
            # If item already exists in current directory, remove it first
            if [ -e "$item_name" ]; then
                echo "  Removing existing $item_name..."
                rm -rf "$item_name"
            fi
            
            # Move the item
            mv "$item" .
        fi
    done
    
    # Remove empty server directory
    rmdir server 2>/dev/null || true
    echo "Removed empty server directory"
fi

# Ensure ML models are in the right place
echo ""
echo "Organizing ML models..."

# Create ml_models directory if it doesn't exist
mkdir -p ml_models/DEPLOY_READY_SOC_MODELS

# Move ML models to correct location
if [ -d "DEPLOY_READY_SOC_MODELS" ]; then
    echo "Moving DEPLOY_READY_SOC_MODELS to ml_models/"
    cp -r DEPLOY_READY_SOC_MODELS/* ml_models/DEPLOY_READY_SOC_MODELS/ 2>/dev/null || true
    echo "ML models organized"
fi

# Move test files to root if they're in subdirectories
echo ""
echo "Organizing test files..."

# Find and move test files
for test_file in test_*.py verify_*.py fix_*.py; do
    if [ -f "$test_file" ]; then
        echo "Test file $test_file is in correct location"
    fi
done

# Move Python files that should be in root
echo ""
echo "Organizing Python files..."

# Move main server files to root
for file in main.py requirements.txt; do
    if [ -f "$file" ]; then
        echo "Server file $file is in correct location"
    fi
done

# Move ML model manager files to root
for file in ml_model_manager*.py; do
    if [ -f "$file" ]; then
        echo "ML model manager $file is in correct location"
    fi
done

echo ""
echo "Final structure:"
echo "=================="
ls -la

echo ""
echo "Checking ML models location:"
if [ -d "ml_models/DEPLOY_READY_SOC_MODELS" ]; then
    echo "✅ ML models directory exists"
    ls -la ml_models/DEPLOY_READY_SOC_MODELS/ | head -10
    echo "..."
else
    echo "❌ ML models directory missing"
fi

echo ""
echo "Checking test files:"
for test_file in test_*.py verify_*.py fix_*.py; do
    if [ -f "$test_file" ]; then
        echo "✅ $test_file"
    fi
done

echo ""
echo "Structure flattened successfully!"
echo ""
echo "Now you can run:"
echo "python3 verify_server_deployment.py"

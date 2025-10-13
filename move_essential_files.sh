#!/bin/bash

echo "Moving essential files from server/ to clean root..."

# Navigate to the clean directory
cd /home/krithika/full-func/clean

echo "Current directory: $(pwd)"
echo "Files in server directory:"
ls -la server/

echo ""
echo "Moving essential files..."

# Move the ML model manager files
if [ -f "server/ml_model_manager.py" ]; then
    echo "Moving server/ml_model_manager.py to ml_model_manager.py"
    cp server/ml_model_manager.py ml_model_manager.py
fi

if [ -f "server/ml_model_manager_fixed.py" ]; then
    echo "Moving server/ml_model_manager_fixed.py to ml_model_manager_fixed.py"
    cp server/ml_model_manager_fixed.py ml_model_manager_fixed.py
fi

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

# Move database file
if [ -f "server/soc_database.db" ]; then
    echo "Moving server/soc_database.db to soc_database.db"
    cp server/soc_database.db soc_database.db
fi

# Move other Python files that should be in root
for file in server/*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        if [ "$filename" != "main.py" ] && [ "$filename" != "ml_model_manager.py" ] && [ "$filename" != "ml_model_manager_fixed.py" ]; then
            echo "Moving server/$filename to $filename"
            cp "$file" "$filename"
        fi
    fi
done

# Move shell scripts
for file in server/*.sh; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

# Move JSON files
for file in server/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

# Move log files
for file in server/*.log; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

echo ""
echo "Essential files moved!"
echo ""
echo "Files now in clean root:"
ls -la *.py *.sh *.json *.log 2>/dev/null || echo "No matching files found"

echo ""
echo "Now run: python3 verify_clean_root_deployment.py"

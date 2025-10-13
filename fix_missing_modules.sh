#!/bin/bash

echo "Fixing missing modules issue..."

# Navigate to the clean directory
cd /home/krithika/full-func/clean

echo "Current directory: $(pwd)"
echo "Checking for missing modules..."

# Check if report_cache_manager.py exists in server directory
if [ -f "server/report_cache_manager.py" ]; then
    echo "Found report_cache_manager.py in server directory"
    echo "Moving to clean root..."
    cp server/report_cache_manager.py report_cache_manager.py
    echo "✅ Moved report_cache_manager.py to clean root"
else
    echo "❌ report_cache_manager.py not found in server directory"
fi

# Check for other missing modules that might be needed
missing_modules=(
    "enhanced_report_generator.py"
    "pdf_report_generator.py"
    "ai_risk_assessment.py"
    "ai_security_posture_report.py"
    "ai_compliance_dashboard.py"
)

echo ""
echo "Checking for other required modules..."

for module in "${missing_modules[@]}"; do
    if [ -f "server/$module" ]; then
        echo "Moving server/$module to $module"
        cp "server/$module" "$module"
        echo "✅ Moved $module"
    else
        echo "⚠️  $module not found in server directory"
    fi
done

# Move all Python files from server to clean root
echo ""
echo "Moving all Python files from server to clean root..."

for file in server/*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

# Move all shell scripts
echo ""
echo "Moving all shell scripts..."

for file in server/*.sh; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

# Move all JSON files
echo ""
echo "Moving all JSON files..."

for file in server/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

# Move all log files
echo ""
echo "Moving all log files..."

for file in server/*.log; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "Moving server/$filename to $filename"
        cp "$file" "$filename"
    fi
done

echo ""
echo "✅ All files moved from server/ to clean root!"
echo ""
echo "Files now in clean root:"
ls -la *.py *.sh *.json *.log 2>/dev/null | head -20

echo ""
echo "Now restart your server:"
echo "1. Stop the current server (Ctrl+C)"
echo "2. Run: python3 main.py"
echo "3. Test: curl http://localhost:8080/api/backend/risk-assessment"

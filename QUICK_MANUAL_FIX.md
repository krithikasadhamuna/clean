# 🔧 QUICK MANUAL FIX - MOVE FILES FROM SERVER TO CLEAN ROOT

## 🚨 **PROBLEM IDENTIFIED**

The files are still in the `server/` directory. We need to move the essential files to the clean root.

## 🚀 **QUICK FIX COMMANDS**

**Run these commands on your server:**

```bash
cd /home/krithika/full-func/clean

# Make the script executable and run it
chmod +x move_essential_files.sh
./move_essential_files.sh
```

## 🎯 **MANUAL COMMANDS (If script doesn't work)**

```bash
cd /home/krithika/full-func/clean

# Move essential files manually
cp server/ml_model_manager.py ml_model_manager.py
cp server/ml_model_manager_fixed.py ml_model_manager_fixed.py
cp server/main.py main.py
cp server/requirements.txt requirements.txt
cp server/soc_database.db soc_database.db

# Move other Python files
cp server/*.py . 2>/dev/null || true

# Move shell scripts
cp server/*.sh . 2>/dev/null || true

# Move JSON files
cp server/*.json . 2>/dev/null || true

# Move log files
cp server/*.log . 2>/dev/null || true
```

## ✅ **VERIFY THE FIX**

After moving the files:

```bash
# Check if files are now in clean root
ls -la *.py

# Test the verification
python3 verify_clean_root_deployment.py
```

## 🎯 **EXPECTED RESULT**

After the fix, you should see:

```
1. CHECKING FILES:
   ✅ ml_model_manager.py
   ✅ ml_models/DEPLOY_READY_SOC_MODELS
   ✅ agents/detection_agent/ai_enhanced_detector.py
   ✅ test_production_ml_models.py
   ✅ test_error_resolution.py
```

## 🚀 **AFTER VERIFICATION WORKS**

```bash
# Apply the BitGenerator fix
cp ml_model_manager_fixed.py ml_model_manager.py

# Test again
python3 verify_clean_root_deployment.py

# Start the server
python3 main.py
```

## 🎉 **READY TO FIX!**

Run the commands above and your files will be properly organized in the clean root directory!

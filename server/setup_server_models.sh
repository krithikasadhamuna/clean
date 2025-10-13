#!/bin/bash

echo "Setting up ML models directory structure on server..."

# Create the directory structure
mkdir -p /home/krithika/full-func/clean/server/ml_models/DEPLOY_READY_SOC_MODELS

echo "Directory structure created successfully!"
echo "Now you can upload the model files using pscp with the -r flag"

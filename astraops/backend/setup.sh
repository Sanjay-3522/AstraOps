#!/usr/bin/env bash
# AstraOps - High Performance Execution Routine
set -e

cd "$(dirname "$0")"

echo "== Cleaning raw event data =="
cd app/data
python clean.py

echo
echo "== Training advanced stacking ensembles and deploying manifests =="
cd ../models
python train.py

echo
echo "Setup complete. Calibrated models and security hash configurations deployed."
echo "Launch production service with: python app/api/server.py"
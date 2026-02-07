#!/bin/bash

# Navigate to script directory
cd "$(dirname "$0")"

# Check for venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Checking/Installing dependencies..."
pip install -r requirements.txt

echo "Starting Music Stream Server..."
python3 app.py

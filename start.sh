#!/bin/bash
echo "⚡ Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed."
    echo "⚡ Starting Sovereign AI Server..."
    # Explicitly use python3
    python3 server.py
else
    echo "❌ Failed to install dependencies."
    exit 1
fi

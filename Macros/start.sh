#!/bin/bash

# Cross-platform Macro Application Startup Script
# For Linux and macOS

cd "$(dirname "$0")"

# Check if running on Linux and if sudo is needed
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Check if user is in input group
    if groups | grep -q '\binput\b'; then
        echo "[Info] Running without sudo (user in input group)"
        python3 -m venv venv && source venv/bin/activate
        python3 main.py
    else
        echo "[Info] Running with sudo (required for keyboard access)"
        python3 -m venv venv && source venv/bin/activate
        sudo -E env PATH="$PATH" python3 main.py
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "[Info] Running on macOS"
    python3 main.py
else
    # Other Unix-like systems
    echo "[Info] Running on Unix-like system"
    python3 main.py
fi

# Optional: Keep terminal open if there's an error
# Uncomment the line below if you want to see error messages
read -p "Press Enter to exit..."

#!/bin/bash
# Omega the Caretaker - Night Shift
# Runs TWISTED tests every 5 minutes using Skyvern

cd /Users/perbrinell/Documents/orgaNICE2

# Make sure the environment is set
source .venv/bin/activate 2>/dev/null || true

# Check if frontend/backend are running
check_services() {
    curl -s http://localhost:8000/api/health > /dev/null 2>&1 && echo "✅ Backend OK" || echo "❌ Backend DOWN"
    curl -s http://localhost:3002 > /dev/null 2>&1 && echo "✅ Frontend OK" || echo "❌ Frontend DOWN"
}

echo "🌙 Omega's Night Shift Starting..."
echo "=================================="

# Run a quick health check
check_services

# Run the Omega tester
# Uncomment for continuous heartbeat:
# while true; do
#     echo "💓 Omega running tests..."
#     python scripts/omega_tester.py
#     echo "💤 Sleeping 5 minutes..."
#     sleep 300
# done

# For now, run once
echo "💓 Running single test..."
python scripts/omega_tester.py

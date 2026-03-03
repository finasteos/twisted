#!/bin/bash
# Omega's Night Shift - 15 minute heartbeat
# Runs every 15 minutes until 8am

cd /Users/perbrinell/Documents/orgaNICE2

LOGFILE="/tmp/omega_nightshift.log"

export GEMINI_API_KEY="AIzaSyBv1PeBnd6q8MhmfjZbiyzVqatwgDF5_F8"
export SKYVERN_API_KEY="local"
export LLM_KEY="GEMINI_2.5_FLASH"
export ENABLE_GEMINI="true"

echo "🌙 Omega's Night Shift starting at $(date)" | tee -a $LOGFILE

run_omega() {
    /opt/homebrew/Caskroom/miniconda/base/bin/python scripts/omega_tester.py 2>&1 | tee -a $LOGFILE
}

# Run once now
run_omega

echo "💤 Omega sleeping... next run in 15 minutes" | tee -a $LOGFILE

# Then loop every 15 minutes until 8am
while true; do
    sleep 900  # 15 minutes
    
    hour=$(date +%H)
    if [ "$hour" -ge 8 ]; then
        echo "☀️ Morning! Omega stopping at $(date)" | tee -a $LOGFILE
        break
    fi
    
    echo "💓 Omega heartbeat at $(date)" | tee -a $LOGFILE
    run_omega
    
    echo "💤 Omega sleeping..." | tee -a $LOGFILE
done

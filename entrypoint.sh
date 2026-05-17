#!/bin/bash

set -e

echo "=== Wecheselrichter Entrypoint Script ==="
echo "Starting monitor services..."

# Ensure directories exist
mkdir -p /data/pid_files

# Start battery monitor (slower sampling, less frequent)
nohup python3 batterymonitor.py >> /var/log/battery.log 2>&1 &

# Start frequency monitor (fastest sampling for grid stability monitoring)  
nohup python3 frequencymonitor.py >> /var/log/frequency.log 2>&1 &

# Start power monitor (real-time PV output monitoring)
nohup python3 powermonitor.py >> /var/log/power.log 2>&1 &

# Record all started PIDs for watchdog and debugging
echo "Battery monitor PID: $!" > /data/pid_files/battery.pid
echo "Frequency monitor PID: $!" > /data/pid_files/frequency.pid  
echo "Power monitor PID: $!" > /data/pid_files/power.pid

echo "All monitors started."

# Start Gunicorn for the web interface (foreground mode) - FIXED PATH
exec gunicorn "webbrowser.app:app" \
    --bind 0.0.0.0:8080 \
    --workers 2 \
    --timeout 120 \
    --pythonpath "/opt/monitors:/opt/monitors/webbrowser:$PYTHONPATH"
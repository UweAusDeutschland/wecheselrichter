#!/bin/bash

set -e

echo "=== Wecheselrichter Entrypoint Script ==="
echo "Starting combined monitor service..."

# Ensure directories exist (using volume mount path)
mkdir -p /app/data/pid_files

# Start the COMBINED monitor (single process for all readings)
nohup python3 combined_monitor.py 2>&1 &

COMBINED_PID=$!
echo "Combined monitor PID: $COMBINED_PID" > /app/data/pid_files/combined.pid

echo "Combined monitor started."

# Start Gunicorn for the web interface (foreground mode) - FIXED PATH
exec gunicorn "webbrowser.app:app" \
    --bind 0.0.0.0:5000 \
    --workers 2 \
    --timeout 120 \
    --pythonpath "/opt/monitors:/opt/monitors/webbrowser:$PYTHONPATH"
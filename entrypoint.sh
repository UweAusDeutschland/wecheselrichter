#!/bin/bash
APP_DIR="/app"
export PYTHONPATH="$APP_DIR:$PYTHONPATH"

# ensure data directory exists where the app expects it
mkdir -p "$APP_DIR/data"
chmod 755 "$APP_DIR/data" 2>/dev/null || true

# Start the frequency monitor in the background (use absolute path, unbuffered)
python -u "$APP_DIR/frequencymonitor.py" &
FREQ_PID=$!

# Start the power monitor in the background
python -u "$APP_DIR/powermonitor.py" &
POWER_PID=$!

# Start the battery monitor in the background
python -u "$APP_DIR/batterymonitor.py" &
BATTERY_PID=$!

# On SIGTERM/SIGINT forward to background processes and exit
trap 'echo "Stopping..."; kill -TERM "$FREQ_PID" "$POWER_PID" "$BATTERY_PID" 2>/dev/null || true; wait; exit 0' TERM INT

# Replace shell with gunicorn so signals are delivered to it
exec gunicorn --bind 0.0.0.0:5000 webbrowser.app:app
#!/bin/bash
# ...existing code...
APP_DIR="/app"
export PYTHONPATH="$APP_DIR:$PYTHONPATH"

# ensure data directory exists where the app expects it
mkdir -p "$APP_DIR/data"
chmod 755 "$APP_DIR/data" 2>/dev/null || true

# Start the frequency monitor in the background (use absolute path, unbuffered)
python -u "$APP_DIR/frequencymonitor.py" &
MONITOR_PID=$!

# On SIGTERM/SIGINT forward to background process and exit
trap 'echo "Stopping..."; kill -TERM "$MONITOR_PID" 2>/dev/null || true; wait "$MONITOR_PID"; exit 0' TERM INT

# Replace shell with gunicorn so signals are delivered to it
exec gunicorn --bind 0.0.0.0:5000 webbrowser.app:app
# ...existing code...
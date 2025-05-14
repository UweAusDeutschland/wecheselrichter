#!/bin/bash

# Starte den Frequencymonitor im Hintergrund
python /frequencymonitor.py &

# Starte den Webserver im Vordergrund (damit der Container läuft)
gunicorn --bind 0.0.0.0:5000 app:app

FROM python:3.12-slim

ENV TZ=Europe/Berlin
# Installiere Abhängigkeiten
RUN pip install flask pandas matplotlib gunicorn pyModbusTCP

# Kopiere Skripte
COPY frequencymonitor.py .
COPY sungrowinverter.py .
COPY webbrowser/ /app/webbrowser/
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
# Arbeitsverzeichnis für den Webserver
WORKDIR /app/webbrowser


# Starte beide Skripte (Hintergrund & Vordergrund)
ENTRYPOINT ["/entrypoint.sh"]
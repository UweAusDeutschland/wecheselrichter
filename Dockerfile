FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Berlin \
    PIP_EXTRA_INDEX_URL=https://www.piwheels.org/simple

# Alles auf einmal: Build-Tools + Runtime-Libs + X11
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential g++ gfortran pkg-config \
      meson ninja-build \
      libopenblas-dev liblapack-dev \
      dos2unix \
      tzdata libfreetype6 libpng16-16 libjpeg62-turbo \
      libopenblas0-pthread libtiff6 libwebp7 liblcms2-2 libopenjp2-7 \
      libxcb1 libx11-6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY frequencymonitor.py .
COPY powermonitor.py .
COPY sungrowinverter.py .
COPY webbrowser/ ./webbrowser/
COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]

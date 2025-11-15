FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Berlin

# Install OS deps needed for matplotlib / timezone data
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    tzdata \
    libfreetype6 \
    libpng16-16 \
    libjpeg62-turbo \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Upgrade pip, then install Python deps without cache
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /app/requirements.txt

# Copy application files
COPY frequencymonitor.py .
COPY sungrowinverter.py .
COPY webbrowser/ ./webbrowser/
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# set working dir to app (so file paths are consistent)
WORKDIR /app

EXPOSE 5000

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
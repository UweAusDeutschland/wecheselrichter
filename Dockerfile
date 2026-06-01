FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Berlin \
    PIP_EXTRA_INDEX_URL=https://www.piwheels.org/simple

# Install runtime dependencies + build tools for compiling packages on ARM
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential g++ gfortran pkg-config \
      meson ninja-build \
      libopenblas-dev liblapack-dev \
      dos2unix \
      tzdata \
      libjpeg62-turbo libjpeg-dev \
      libpng16-16 libpng-dev \
      libfreetype6 libfreetype6-dev \
      libtiff6 libtiff-dev \
      libwebp7 libwebp-dev \
      liblcms2-2 liblcms2-dev \
      libopenjp2-7 libopenjp2-7-dev \
      libopenblas0-pthread \
      libxcb1 libx11-6 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --prefer-binary --no-build-isolation -r requirements.txt

COPY combined_monitor.py .
COPY monitor_base.py .
COPY sungrowinverter.py .
COPY main.py .
COPY webbrowser/ ./webbrowser/
COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]

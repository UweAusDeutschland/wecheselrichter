#!/usr/bin/env python3
# combined_monitor.py — Unified monitor for all Sungrow inverter data
# Combines frequency, power, and battery monitoring into a single process
# to reduce connection overhead and simplify rate limiting

import os
import logging
import time
import socket
from datetime import datetime
from sungrowinverter import SungrowInverter

# Import shared utilities from monitor_base
from monitor_base import (
    resolve_with_retry,
    test_port,
    cleanup_old_csv_files,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# =============================================================================
# Configuration
# =============================================================================
HOST = os.getenv("INVERTER_HOST", "modbusSungrow.fritz.box")
MODBUS_PORT = int(os.getenv("INVERTER_PORT", "502"))

# Rate limiting: max 1 request per second to avoid Sungrow rejecting connections
MAX_REQUESTS_PER_SECOND = 1.0

# Cleanup old data files (älter als 90 Tage)
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "90"))


def make_sgi(connect_host: str) -> SungrowInverter:
    """Erstellt einen SungrowInverter-Client mit der gegebenen Hostadresse."""
    logging.info("Creating SungrowInverter with host %s", connect_host)
    return SungrowInverter(host=connect_host)


# ensure data dir exists
os.makedirs("data", exist_ok=True)

# Cleanup old data files (älter als 90 Tage)
cleanup_old_csv_files(
    base_dir="data",
    prefix="",
    retention_days=RETENTION_DAYS,
)

# Resolve host and verify port
try:
    ip = resolve_with_retry(HOST)
    if not test_port(ip, MODBUS_PORT, retries=3, delay=2):
        raise SystemExit(f"Cannot reach {HOST}({ip}) port {MODBUS_PORT}")
except Exception as e:
    print("Shutdown: cannot reach inverter host:", e)
    raise SystemExit(1)

# Use resolved IP for the SungrowInverter to avoid repeated DNS lookups
sgi = make_sgi(ip)

last_freq = None
last_power = None
last_battery = None

interval = 1.0  # Alle 1 Sekunde auslesen (rate limiting)
next_call = time.time()
current_day = datetime.now().date()


def _get_time_str():
    """Erzeugt einen Zeitstempel bis Millisekunden."""
    return datetime.now().strftime('%H:%M:%S.%f')[:-3]


try:
    while True:
        # === Rate limiting: ensure we don't exceed requests per second ===
        now = time.time()
        if next_call > now:
            sleep_time = next_call - now
            time.sleep(sleep_time)
        
        # === Update current_day to handle date changes ===
        current_day = datetime.now().date()
        
        try:
            # Read ALL three values in a single Modbus connection
            freq = sgi.get_frequency()
            power = sgi.get_pv_power()
            battery = sgi.get_battery_level()
            
            if freq is not None and freq != last_freq:
                filename = f"data/frequency_{current_day}.csv"
                with open(filename, "a") as f:
                    time_str = _get_time_str()
                    f.write(f"{time_str},{freq:.2f}\n")
                last_freq = freq
            
            if power is not None and power != last_power:
                filename = f"data/pv_power_{current_day}.csv"
                with open(filename, "a") as f:
                    time_str = _get_time_str()
                    f.write(f"{time_str},{power}\n")
                last_power = power
            
            if battery is not None and battery != last_battery:
                filename = f"data/battery_{current_day}.csv"
                with open(filename, "a") as f:
                    time_str = _get_time_str()
                    f.write(f"{time_str},{battery}\n")
                last_battery = battery
                
        except socket.gaierror as e:
            # DNS resolution error during runtime -> try to re-resolve and recreate sgi
            logging.warning("gaierror during read: %s — will re-resolve host", e)
            try:
                ip = resolve_with_retry(HOST, retries=5, delay=2)
                if not test_port(ip, MODBUS_PORT, retries=3, delay=2):
                    logging.error("Port %s not reachable on %s after re-resolve", MODBUS_PORT, ip)
                    next_call += 1.0  # Wait before retrying
                    continue
                sgi = make_sgi(ip)
                time.sleep(0.5)
            except Exception as re:
                logging.error("Re-resolve failed: %s", re)
                next_call += 1.0
                continue
        except Exception as e:
            print("Warning: reading inverter data failed:", type(e).__name__, e)
            next_call += 1.0
            continue

        # Advance the timer for next read
        next_call += interval

except KeyboardInterrupt:
    print("Überwachung beendet.")
except Exception as e:
    print("Shutting down due to error.")
    print(e)

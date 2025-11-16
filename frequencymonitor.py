import os
import socket
import time
import logging
from sungrowinverter import SungrowInverter
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Konfiguration über ENV ermöglichen
HOST = os.getenv("INVERTER_HOST", "modbusSungrow.fritz.box")
MODBUS_PORT = int(os.getenv("INVERTER_PORT", "502"))

def resolve_with_retry(host, retries=5, delay=2):
    for i in range(retries):
        try:
            infos = socket.getaddrinfo(host, None)
            return infos[0][4][0]
        except socket.gaierror:
            print(f"DNS lookup failed for {host}, retry {i+1}/{retries}")
            time.sleep(delay)
    raise RuntimeError(f"Could not resolve host {host}")

def test_port(ip, port, retries=5, delay=2):
    for i in range(retries):
        try:
            socket.create_connection((ip, port), timeout=3).close()
            return True
        except Exception as e:
            print(f"Port {port} on {ip} not reachable ({e}), retry {i+1}/{retries}")
            time.sleep(delay)
    return False

# ensure data dir exists
os.makedirs("data", exist_ok=True)

# Resolve host and verify port
try:
    ip = resolve_with_retry(HOST)
    if not test_port(ip, MODBUS_PORT, retries=3, delay=2):
        raise SystemExit(f"Cannot reach {HOST}({ip}) port {MODBUS_PORT}")
except Exception as e:
    print("Shutdown: cannot reach inverter host:", e)
    raise SystemExit(1)

# Use resolved IP for the SungrowInverter to avoid repeated DNS lookups
def make_sgi(connect_host):
    logging.info("Creating SungrowInverter with host %s", connect_host)
    return SungrowInverter(host=connect_host)

sgi = make_sgi(ip)
last_freq = None
interval = 0.05
next_call = time.time()
current_day = datetime.now().date()
filename = f"data/frequency_{current_day}.csv"

try:
    while True:
        try:
            freq = sgi.get_frequency()
        except socket.gaierror as e:
            # DNS resolution error during runtime -> try to re-resolve and recreate sgi
            logging.warning("gaierror during read: %s — will re-resolve host", e)
            try:
                ip = resolve_with_retry(HOST, retries=5, delay=2)
                if not test_port(ip, MODBUS_PORT, retries=3, delay=2):
                    logging.error("Port %s not reachable on %s after re-resolve", MODBUS_PORT, ip)
                    time.sleep(5)
                    continue
                sgi = make_sgi(ip)
                time.sleep(0.5)
                continue
            except Exception as re:
                logging.error("Re-resolve failed: %s", re)
                time.sleep(5)
                continue
        except Exception as e:
            print("Warning: reading frequency failed:", type(e).__name__, e)
            time.sleep(1)
            continue

        now = datetime.now()
        if freq is not None and freq != last_freq:
            if now.date() != current_day:
                current_day = now.date()
                filename = f"data/frequency_{current_day}.csv"
            with open(filename, "a") as f:
                time_str = now.strftime('%H:%M:%S.%f')[:-3]  # Nur bis Millisekunden
                f.write(f"{time_str},{freq:.2f}\n")
            last_freq = freq
        next_call += interval
        sleep_time = max(0, next_call - time.time())
        time.sleep(sleep_time)  # Intervall in Sekunden
except KeyboardInterrupt:
    print("Überwachung beendet.")
except Exception as e:
    print("Shuting down of error.")
    print(e)

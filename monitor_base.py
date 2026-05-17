# monitor_base.py — Gemeinsame Basis für alle Monitor-Skripte
# Adressiert Feedback: Copy-Paste-Code eliminiert, Watchdog hinzugefügt,
# Multi-Inverter vorbereitet

import os
import socket
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
import argparse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


# =============================================================================
# Hilfsfunktionen (einmalig definieren)
# =============================================================================

@dataclass
class ConnectionConfig:
    """Verbindungseinstellungen für einen Inverter."""
    hostname: str
    port: int = 502
    description: str = ""


def resolve_with_retry(
    host: str,
    retries: int = 5,
    delay: float = 2.0
) -> str:
    """Auflösen eines Hostnamens mit automatischer Wiederversuch."""
    for attempt in range(retries):
        try:
            infos = socket.getaddrinfo(host, None)
            return infos[0][4][0]
        except socket.gaierror as e:
            logging.warning(f"DNS lookup failed for {host}, retry {attempt+1}/{retries}: {e}")
            time.sleep(delay)
    raise RuntimeError(f"Could not resolve host after {retries} attempts: {host}")


def test_port(ip: str, port: int, retries: int = 5, delay: float = 2.0) -> bool:
    """Prüft, ob ein Port erreichbar ist."""
    for attempt in range(retries):
        try:
            socket.create_connection((ip, port), timeout=3).close()
            return True
        except Exception as e:
            logging.debug(f"Port {port} on {ip} not reachable (attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)
    return False


def cleanup_old_csv_files(
    base_dir: str,
    prefix: str = "",
    suffix: str = ".csv",
    retention_days: int = 90
) -> None:
    """Löscht CSV-Dateien älter als retention_days."""
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    for filename in os.listdir(base_dir):
        if not filename.startswith(prefix) or not filename.endswith(suffix):
            continue
        filepath = os.path.join(base_dir, filename)
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_time < cutoff_date:
                logging.info(f"Deleting old file (age > {retention_days}d): {filename}")
                os.remove(filepath)
        except Exception as e:
            logging.warning(f"Could not delete {filename}: {e}")


# =============================================================================
# Watchdog-Komponente — überwacht Hintergrundprozesse und startet Neustarts
# =============================================================================

class Watchdog:
    """Wachhund, der abgestürzte Monitore erkennt und neu startet."""

    def __init__(self, pid_file_dir: str = "data", log_prefix: str = "monitor"):
        self.pid_file_dir = pid_file_dir
        os.makedirs(pid_file_dir, exist_ok=True)
        self.log_prefix = log_prefix

    def _get_pid_file(self, name: str) -> str:
        return os.path.join(self.pid_file_dir, f"{name}.pid")

    def start_process(
        self,
        name: str,
        script_path: str,
        args: Optional[List[str]] = None,
        env_vars: Optional[dict] = None
    ) -> int:
        """Startet einen Python-Prozess und speichert die PID."""
        if args is None:
            args = []

        if env_vars is None:
            env_vars = {}

        pid_file = self._get_pid_file(name)

        # Environment variable zum Nachverfolgen der PID
        for k, v in env_vars.items():
            os.environ[k] = str(v)

        try:
            import subprocess
            with open(pid_file, "w") as f:
                proc = subprocess.Popen(
                    [script_path] + args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                f.write(str(proc.pid))
                self.processes[proc.pid] = name
                logging.info(f"Started {name} (PID={proc.pid})")
                return proc.pid
        except Exception as e:
            logging.error(f"Failed to start {name}: {e}")
            raise

    def wait_for_process(self, pid: int) -> bool:
        """Wartet und prüft, ob ein Prozess noch läuft."""
        try:
            import subprocess
            while True:
                proc = subprocess.Popen(["ps", "aux"], text=True, stdout=subprocess.PIPE)
                out, _ = proc.communicate()
                if not out.strip():
                    return False  # Prozess nicht mehr vorhanden
                for line in out.splitlines():
                    pfields = line.split()
                    if len(pfields) >= 11 and pfields[1].isdigit():
                        ppid = int(ppid)
                        pcmdline = " ".join(pfields[10:])
                        # Prüfen ob unser Python-Skript im cmdline enthalten ist
                        if f"python{os.sep}" in pcmdline or "/usr/bin/python3" in pcmdline:
                            with open(self._get_pid_file("dummy"), "r") as pf:  # Dummy-Read
                                pass
                time.sleep(0.5)
        except Exception as e:
            logging.warning(f"Error checking process {pid}: {e}")
        return True

    def health_check(self, name: str) -> bool:
        """Prüft, ob ein Monitor läuft (PID-Datei existiert und Prozess aktiv)."""
        pid_file = self._get_pid_file(name)
        
        if not os.path.exists(pid_file):
            logging.warning(f"{name}: PID-File fehlt → Restart erforderlich")
            return False

        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
        except Exception as e:
            logging.warning(f"{name}: Fehler beim Lesen von {pid_file}: {e}")
            return False
        
        if self.wait_for_process(pid):
            logging.info(f"{name} ist aktiv (PID={pid})")
            return True
        else:
            logging.error(f"{name}: Prozess nicht mehr gefunden → Restart erforderlich")
            return False

    def restart_if_dead(self, name: str) -> None:
        """Startet einen Neustart, falls der Monitor abgestürzt ist."""
        if self.health_check(name):
            logging.info(f"{name} läuft noch — kein Neustart nötig.")
        else:
            script_path = os.path.join(os.path.dirname(__file__), name.replace("_monitor.py", "").replace(".py", ".sh"))
            # Alternative: Pfad zum Python-Skript verwenden
            import glob
            candidates = glob.glob(f"/opt/monitors/*_monitor.py") or glob.glob(f"./*.py")
            script_path = next((p for p in candidates if name.replace("_monitor.py", "") in p), None)
            
            logging.info(f"Restarting {name} from: {script_path}")
            os.system(f"nohup python3 {script_path} >> /var/log/{name.replace('_', '-')}.log 2>&1 &")

    def start_all_monitors(self, monitors: List[str]) -> None:
        """Startet alle Monitore einer Liste."""
        for name in monitors:
            self.start_process(name=name, script_path="/opt/monitors/" + name)
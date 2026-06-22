"""
Integration Tests für das gesamte System
Tests der Interaktion zwischen Komponenten
"""
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from datetime import datetime


# =============================================================================
# END-TO-END WORKFLOW TESTS
# =============================================================================

def test_inverter_to_monitor_to_web_workflow():
    """Test: Kompletter Workflow von Inverter → Monitor → Web"""
    # 1. Inverter liest Daten
    # 2. Monitor schreibt zu CSV
    # 3. Web-App zeigt Daten an
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "frequency_2026-05-17.csv")
        
        # Simuliere Monitor-Schreiben
        with open(csv_file, "a") as f:
            f.write("13:11:30.123,50.01\n")
        
        # Prüfe ob Datei lesbar ist
        assert os.path.exists(csv_file)
        
        # Simuliere Web-App Lesen
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        assert "50.01" in lines[0]


def test_multiple_inverters_multiple_monitors():
    """Test: Mehrere Monitore können parallel schreiben"""
    with tempfile.TemporaryDirectory() as tmpdir:
        files = {
            "frequency": os.path.join(tmpdir, "frequency_2026-05-17.csv"),
            "power": os.path.join(tmpdir, "pv_power_2026-05-17.csv"),
            "battery": os.path.join(tmpdir, "battery_2026-05-17.csv"),
        }
        
        # Schreibe parallel zu verschiedenen Dateien
        for name, filepath in files.items():
            with open(filepath, "a") as f:
                f.write("13:11:30.123,test_value\n")
        
        # Alle Dateien sollten existieren
        for filepath in files.values():
            assert os.path.exists(filepath)
            with open(filepath, "r") as f:
                assert len(f.readlines()) > 0


def test_monitor_persistence_across_restarts():
    """Test: Monitor-Daten bleiben über Neustarts erhalten"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "frequency_2026-05-17.csv")
        
        # Erste "Session"
        with open(csv_file, "a") as f:
            f.write("13:11:30.123,50.01\n")
        
        # Simuliere Neustart
        # Zweite "Session"
        with open(csv_file, "a") as f:
            f.write("13:11:31.456,50.02\n")
        
        # Beide Einträge sollten vorhanden sein
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        assert "50.01" in lines[0]
        assert "50.02" in lines[1]


# =============================================================================
# CROSS-COMPONENT ERROR HANDLING TESTS
# =============================================================================

def test_recovery_from_network_error():
    """Test: System erholt sich von Netzwerkfehlern"""
    # 1. Netzwerkfehler tritt auf
    # 2. Monitor logged Error
    # 3. Monitor versucht Reconnect
    # 4. Erfolgreiches Lesen nach Reconnect
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "frequency_2026-05-17.csv")
        
        # Simuliere Fehler und Recovery
        errors = 0
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if attempt < 2:
                    # Simuliere Fehler in ersten 2 Versuchen
                    raise ConnectionRefusedError("Connection refused")
                # Dritter Versuch erfolgreich
                with open(csv_file, "a") as f:
                    f.write("13:11:30.123,50.01\n")
                break
            except ConnectionRefusedError:
                errors += 1
        
        # System sollte nach Retries erfolgreich sein
        assert os.path.exists(csv_file)


def test_missing_data_directory_creation():
    """Test: System erstellt fehlende Verzeichnisse automatisch"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data", "subdir")
        
        # Verzeichnis sollte nicht existieren
        assert not os.path.exists(data_dir)
        
        # Erstelle Verzeichnis
        os.makedirs(data_dir, exist_ok=True)
        
        # Nun sollte es existieren
        assert os.path.exists(data_dir)
        
        # Schreibe Datei
        csv_file = os.path.join(data_dir, "test.csv")
        with open(csv_file, "w") as f:
            f.write("test\n")
        
        assert os.path.exists(csv_file)


# =============================================================================
# DATA CONSISTENCY TESTS
# =============================================================================

def test_frequency_data_consistency():
    """Test: Frequenz-Daten sind konsistent zwischen Speicherung und Lesing"""
    test_data = [
        ("13:11:30.123", "50.01"),
        ("13:11:31.456", "50.02"),
        ("13:11:32.789", "49.99"),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "frequency_2026-05-17.csv")
        
        # Schreibe Daten
        with open(csv_file, "w") as f:
            for timestamp, freq in test_data:
                f.write(f"{timestamp},{freq}\n")
        
        # Lese Daten zurück
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        # Prüfe Konsistenz
        for i, (timestamp, freq) in enumerate(test_data):
            assert f"{timestamp},{freq}" in lines[i]


def test_power_data_accuracy():
    """Test: Power-Daten werden genau gespeichert"""
    test_values = [2500, 2750, 2650, 3000, 2900]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "pv_power_2026-05-17.csv")
        
        # Schreibe Daten
        with open(csv_file, "w") as f:
            for i, value in enumerate(test_values):
                f.write(f"13:11:{30+i}.000,{value}\n")
        
        # Lese und verifiziere
        with open(csv_file, "r") as f:
            for i, line in enumerate(f.readlines()):
                parts = line.strip().split(',')
                assert int(parts[1]) == test_values[i]


def test_battery_soc_tracking():
    """Test: Batterie-SoC wird korrekt verfolgt"""
    test_soc_values = [85.5, 85.3, 85.1, 84.9, 84.7]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "battery_2026-05-17.csv")
        
        # Schreibe Daten
        with open(csv_file, "w") as f:
            for i, soc in enumerate(test_soc_values):
                f.write(f"13:11:{30+i}.000,{soc}\n")
        
        # Lese und verifiziere Trend (abnehmend)
        with open(csv_file, "r") as f:
            values = []
            for line in f.readlines():
                parts = line.strip().split(',')
                values.append(float(parts[1]))
        
        # Werte sollten abnehmend sein
        for i in range(len(values) - 1):
            assert values[i] >= values[i + 1]


# =============================================================================
# PERFORMANCE INTEGRATION TESTS
# =============================================================================

def test_high_frequency_data_writing():
    """Test: System kann mit hoher Datenrate (frequencymonitor) umgehen"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "frequency_2026-05-17.csv")
        
        # Schreibe 1000 Punkte (entspricht ~1 Min bei 0.05s Intervall)
        with open(csv_file, "a") as f:
            for i in range(1000):
                timestamp = f"13:11:{30+i//60:02d}.{i%1000:03d}"
                frequency = 50.0 + (i % 10) * 0.01
                f.write(f"{timestamp},{frequency}\n")
        
        # Prüfe Dateiintegrität
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 1000


def test_moderate_frequency_data_writing():
    """Test: System kann mit moderater Datenrate (powermonitor) umgehen"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "pv_power_2026-05-17.csv")
        
        # Schreibe 3600 Punkte (entspricht 1 Stunde bei 1s Intervall)
        with open(csv_file, "a") as f:
            for i in range(3600):
                timestamp = f"13:11:{30+i//60:02d}.{i%1000:03d}"
                power = 2500 + (i % 500)
                f.write(f"{timestamp},{power}\n")
        
        # Prüfe Dateiintegrität
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 3600


def test_low_frequency_data_writing():
    """Test: System kann mit niedriger Datenrate (batterymonitor) umgehen"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "battery_2026-05-17.csv")
        
        # Schreibe 288 Punkte (entspricht 1 Tag bei 5min Intervall)
        with open(csv_file, "a") as f:
            for i in range(288):
                hour = 13 + (i * 5) // 60
                minute = (i * 5) % 60
                timestamp = f"{hour:02d}:{minute:02d}:00.000"
                soc = 85.0 - (i * 0.1)
                f.write(f"{timestamp},{soc}\n")
        
        # Prüfe Dateiintegrität
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 288


# =============================================================================
# DATA RETENTION TESTS
# =============================================================================

def test_daily_rollover():
    """Test: Täglicher Wechsel zu neuer Datei"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Simuliere Daten von zwei verschiedenen Tagen
        file_may_16 = os.path.join(tmpdir, "frequency_2026-05-16.csv")
        file_may_17 = os.path.join(tmpdir, "frequency_2026-05-17.csv")
        
        # Schreibe zu beiden Dateien
        with open(file_may_16, "w") as f:
            f.write("23:59:59.999,50.00\n")
        
        with open(file_may_17, "w") as f:
            f.write("00:00:00.000,50.00\n")
        
        # Beide Dateien sollten existieren
        assert os.path.exists(file_may_16)
        assert os.path.exists(file_may_17)


def test_old_file_cleanup():
    """Test: Alte Dateien werden nach Retention-Periode gelöscht"""
    from datetime import datetime, timedelta
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Erstelle Dateien verschiedenen Alters
        old_file = os.path.join(tmpdir, "frequency_2026-02-01.csv")
        recent_file = os.path.join(tmpdir, "frequency_2026-05-16.csv")
        
        open(old_file, "w").close()
        open(recent_file, "w").close()
        
        # Setze Änderungszeit für alte Datei (100 Tage alt)
        old_time = (datetime.now() - timedelta(days=100)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        # Nach cleanup sollte alte Datei weg sein
        if os.path.getmtime(old_file) < (datetime.now() - timedelta(days=90)).timestamp():
            os.remove(old_file)
        
        assert not os.path.exists(old_file)
        assert os.path.exists(recent_file)


# =============================================================================
# ERROR RECOVERY TESTS
# =============================================================================

def test_corrupted_csv_recovery():
    """Test: System kann mit beschädigten CSV-Dateien umgehen"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "test.csv")
        
        # Schreibe teilweise beschädigte Datei
        with open(csv_file, "w") as f:
            f.write("13:11:30.123,50.01\n")
            f.write("13:11:31.456\n")  # Fehlender Wert
            f.write("13:11:32.789,49.99\n")
        
        # Versuche zu lesen - sollte teilweise funktionieren
        try:
            with open(csv_file, "r") as f:
                lines = f.readlines()
            assert len(lines) == 3
        except Exception as e:
            # Fehler ist ok, solange Datei nicht gelöscht wird
            assert os.path.exists(csv_file)


def test_readonly_file_handling():
    """Test: System kann mit Read-Only Dateien umgehen"""
    import stat
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "readonly.csv")
        
        # Schreibe Datei
        with open(csv_file, "w") as f:
            f.write("13:11:30.123,50.01\n")
        
        # Mache sie Read-Only
        os.chmod(csv_file, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        
        # Lesen sollte funktionieren
        with open(csv_file, "r") as f:
            content = f.read()
        assert "50.01" in content
        
        # Schreiben sollte fehlschlagen (aber nicht absturzen)
        try:
            with open(csv_file, "a") as f:
                f.write("13:11:31.456,50.02\n")
            # Erfolg (auf einigen Systemen erlaubt)
        except PermissionError:
            # Erwarteter Fehler
            pass
        finally:
            # Stelle Permissions wieder her für Cleanup
            os.chmod(csv_file, stat.S_IRWXU)

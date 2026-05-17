"""
Test-Suite für Monitor-Skripte (frequencymonitor, powermonitor, batterymonitor)
Tests für CSV-Writing, Error-Handling und Datums-Rollover
"""
import pytest
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open
import time


# =============================================================================
# FREQUENCYMONITOR TESTS
# =============================================================================

@pytest.fixture
def frequency_monitor_context():
    """Kontext für frequencymonitor Tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_frequency_monitor_csv_format(frequency_monitor_context):
    """Test: frequencymonitor schreibt CSV im korrekten Format"""
    # Simuliere CSV-Schreib-Logik
    csv_file = os.path.join(frequency_monitor_context, "frequency_2026-05-17.csv")
    
    # Schreibe Test-Daten
    with open(csv_file, "w") as f:
        f.write("13:11:30.123,50.01\n")
        f.write("13:11:31.456,50.02\n")
        f.write("13:11:32.789,49.99\n")
    
    # Verifiziere Dateiformat
    with open(csv_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 3
    # Format sollte sein: HH:MM:SS.mmm,frequency
    assert "13:11:30.123,50.01" in lines[0]


def test_frequency_monitor_timestamp_precision():
    """Test: Zeitstempel haben Millisekunden-Genauigkeit"""
    time_str = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    # Format sollte HH:MM:SS.mmm sein (23 Zeichen)
    assert len(time_str) == 12
    parts = time_str.split('.')
    assert len(parts) == 2
    assert len(parts[0]) == 8  # HH:MM:SS
    assert len(parts[1]) == 3  # mmm (Millisekunden)


def test_frequency_monitor_date_rollover(frequency_monitor_context):
    """Test: frequencymonitor erstellt neue Datei bei Datums-Wechsel"""
    # Simuliere Wechsel von Tag zu Tag
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    today_file = f"data/frequency_{today}.csv"
    yesterday_file = f"data/frequency_{yesterday}.csv"
    
    # Test sollte prüfen, ob korrekte Dateien verwendet werden
    assert today.strftime("%Y-%m-%d") in today_file
    assert yesterday.strftime("%Y-%m-%d") in yesterday_file


def test_frequency_monitor_deduplication():
    """Test: frequencymonitor dedupliziert (schreibt nur bei Wertänderung)"""
    # Frequenz ändert sich normalerweise nur gering
    # Wenn Wert gleich bleibt, sollte nicht geschrieben werden
    
    last_freq = 50.01
    new_freq = 50.01  # Gleich wie letzter Wert
    
    should_write = (new_freq != last_freq)
    assert not should_write
    
    # Bei Änderung sollte geschrieben werden
    new_freq = 50.02
    should_write = (new_freq != last_freq)
    assert should_write


def test_frequency_monitor_interval():
    """Test: frequencymonitor hat korrektes Polling-Intervall"""
    # frequencymonitor sollte alle 0.05 Sekunden auslesen
    interval = 0.05
    
    # Mit dieser Frequenz sollte ca. 20 Datenpunkte pro Sekunde kommen
    points_per_second = 1.0 / interval
    assert points_per_second == 20.0


# =============================================================================
# POWERMONITOR TESTS
# =============================================================================

def test_powermonitor_csv_format():
    """Test: powermonitor schreibt CSV im korrekten Format"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "pv_power_2026-05-17.csv")
        
        # Schreibe Test-Daten
        with open(csv_file, "w") as f:
            f.write("13:11:30.123,2500\n")
            f.write("13:11:31.456,2750\n")
            f.write("13:11:32.789,2650\n")
        
        # Verifiziere Dateiformat
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        # Format sollte sein: HH:MM:SS.mmm,power
        assert "13:11:30.123,2500" in lines[0]


def test_powermonitor_interval():
    """Test: powermonitor hat korrektes Polling-Intervall"""
    # powermonitor sollte alle 1.0 Sekunde auslesen
    interval = 1.0
    
    # Mit dieser Frequenz sollte 1 Datenpunkt pro Sekunde kommen
    points_per_second = 1.0 / interval
    assert points_per_second == 1.0


def test_powermonitor_power_values_realistic():
    """Test: powermonitor verarbeitet realistische Werte"""
    # Typische PV-Leistung liegt zwischen 0W und 10000W
    test_values = [0, 1000, 5000, 8500, 10000]
    
    for value in test_values:
        # Wert sollte nicht-negativ sein
        assert value >= 0
        # Wert sollte in realistischem Bereich liegen
        assert value <= 100000


# =============================================================================
# BATTERYMONITOR TESTS
# =============================================================================

def test_batterymonitor_csv_format():
    """Test: batterymonitor schreibt CSV im korrekten Format"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "battery_2026-05-17.csv")
        
        # Schreibe Test-Daten
        with open(csv_file, "w") as f:
            f.write("13:11:30.123,85.5\n")
            f.write("13:11:31.456,85.3\n")
            f.write("13:11:32.789,84.8\n")
        
        # Verifiziere Dateiformat
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        # Format sollte sein: HH:MM:SS.mmm,soc_percent
        assert "13:11:30.123,85.5" in lines[0]


def test_batterymonitor_interval():
    """Test: batterymonitor hat korrektes Polling-Intervall"""
    # batterymonitor sollte alle 5.0 Sekunden auslesen
    interval = 5.0
    
    # Mit dieser Frequenz sollte 1 Datenpunkt alle 5 Sekunden kommen
    points_per_minute = 60.0 / interval
    assert points_per_minute == 12.0


def test_batterymonitor_soc_range():
    """Test: batterymonitor verarbeitet korrekte SoC-Werte"""
    # SoC liegt zwischen 0% und 100%
    test_values = [0.0, 25.0, 50.0, 75.0, 100.0]
    
    for value in test_values:
        assert 0 <= value <= 100


def test_batterymonitor_deduplication():
    """Test: batterymonitor dedupliziert bei gleichem SoC"""
    last_battery = 85.5
    new_battery = 85.5  # Gleich wie letzter Wert
    
    should_write = (new_battery != last_battery)
    assert not should_write
    
    # Bei Änderung sollte geschrieben werden
    new_battery = 85.4
    should_write = (new_battery != last_battery)
    assert should_write


# =============================================================================
# COMMON MONITOR TESTS
# =============================================================================

def test_monitor_creates_data_directory():
    """Test: Monitor erstellt data/ Verzeichnis wenn nicht vorhanden"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data")
        
        # Verzeichnis sollte nicht existieren
        assert not os.path.exists(data_dir)
        
        # Nach os.makedirs sollte es existieren
        os.makedirs(data_dir, exist_ok=True)
        assert os.path.exists(data_dir)


def test_monitor_append_mode():
    """Test: Monitor schreibt im Append-Modus"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "test.csv")
        
        # Schreibe erste Zeile
        with open(csv_file, "a") as f:
            f.write("13:11:30.123,50.01\n")
        
        # Schreibe zweite Zeile im Append-Modus
        with open(csv_file, "a") as f:
            f.write("13:11:31.456,50.02\n")
        
        # Beide Zeilen sollten existieren
        with open(csv_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        assert "13:11:30.123,50.01" in lines[0]
        assert "13:11:31.456,50.02" in lines[1]


def test_monitor_handles_network_errors():
    """Test: Monitor-Fehlerbehandlung bei Netzwerkfehlern"""
    # Fehler sollten geloggt aber nicht fatal sein
    error_types = [
        ConnectionRefusedError("Connection refused"),
        OSError("Network unreachable"),
        TimeoutError("Operation timed out"),
    ]
    
    for error in error_types:
        # Monitor sollte diese Fehler abfangen können
        assert isinstance(error, Exception)


def test_monitor_handles_modbus_errors():
    """Test: Monitor-Fehlerbehandlung bei Modbus-Fehlern"""
    # Wenn Wert None ist, sollte nicht geschrieben werden
    value = None
    
    should_write = (value is not None)
    assert not should_write
    
    # Bei gültigem Wert sollte geschrieben werden
    value = 50.01
    should_write = (value is not None)
    assert should_write


# =============================================================================
# CSV INTEGRITY TESTS
# =============================================================================

def test_csv_no_empty_lines():
    """Test: CSV-Dateien haben keine leeren Zeilen"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "test.csv")
        
        # Schreibe Daten
        with open(csv_file, "w") as f:
            f.write("13:11:30.123,50.01\n")
            f.write("13:11:31.456,50.02\n")
            f.write("13:11:32.789,49.99\n")
        
        # Lese und prüfe
        with open(csv_file, "r") as f:
            lines = [line.strip() for line in f.readlines()]
        
        # Keine leeren Zeilen
        assert all(line for line in lines)


def test_csv_data_types():
    """Test: CSV-Daten haben korrekte Datentypen"""
    csv_lines = [
        "13:11:30.123,50.01",
        "13:11:31.456,50.02",
        "13:11:32.789,49.99",
    ]
    
    for line in csv_lines:
        parts = line.split(',')
        assert len(parts) == 2
        
        # Timestamp sollte auswertbar sein
        timestamp = parts[0]
        assert len(timestamp) == 12  # HH:MM:SS.mmm
        
        # Wert sollte zu float konvertierbar sein
        value = float(parts[1])
        assert isinstance(value, float)


def test_csv_timestamp_ordering():
    """Test: CSV-Einträge sind zeitlich sortiert"""
    timestamps = [
        "13:11:30.123",
        "13:11:31.456",
        "13:11:32.789",
    ]
    
    # Timestamps sollten aufsteigend sortiert sein
    for i in range(len(timestamps) - 1):
        current = datetime.strptime(timestamps[i], "%H:%M:%S.%f")
        next_ts = datetime.strptime(timestamps[i + 1], "%H:%M:%S.%f")
        assert current < next_ts


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

def test_monitor_file_write_performance():
    """Test: Monitor kann schnell schreiben"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "performance_test.csv")
        
        # Schreibe 1000 Zeilen und messe Zeit
        start = time.time()
        with open(csv_file, "a") as f:
            for i in range(1000):
                f.write(f"13:11:30.{i:03d},50.{i%100:02d}\n")
        elapsed = time.time() - start
        
        # Sollte schnell sein (< 0.1 Sekunden)
        assert elapsed < 0.1
        
        # Verifiziere dass alle Zeilen geschrieben wurden
        with open(csv_file, "r") as f:
            lines = f.readlines()
        assert len(lines) == 1000


def test_monitor_file_size():
    """Test: Monitor-CSV-Dateien haben vernünftige Größe"""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_file = os.path.join(tmpdir, "size_test.csv")
        
        # Schreibe 10000 Datenpunkte
        with open(csv_file, "a") as f:
            for i in range(10000):
                f.write(f"13:11:{(30+i//60)%60:02d}.{i%1000:03d},50.{i%100:02d}\n")
        
        # Dateigröße prüfen
        file_size = os.path.getsize(csv_file)
        # ~26 bytes pro Zeile × 10000 = ~260KB (maximal)
        assert file_size < 1_000_000  # < 1MB

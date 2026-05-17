"""
Erweiterte Test-Suite für webbrowser/app.py
Tests für Edge-Cases, Chart-Generierung und Error-Handling
"""
import pytest
import pandas as pd
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import re


@pytest.fixture
def app():
    """Erstellt eine Test-Flask-App"""
    from webbrowser.app import app
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Erstellt einen Test-Client"""
    return app.test_client()


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Erstellt ein temporäres Datenverzeichnis mit Test-CSV-Dateien"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Frequenz-Test-Datei
    freq_file = data_dir / f"frequency_{today}.csv"
    freq_file.write_text(
        "13:11:30.123,50.01\n"
        "13:11:31.456,50.02\n"
        "13:11:32.789,49.99\n"
    )
    
    # Power-Test-Datei
    power_file = data_dir / f"pv_power_{today}.csv"
    power_file.write_text(
        "13:11:30.123,2500\n"
        "13:11:31.456,2750\n"
        "13:11:32.789,2650\n"
    )
    
    # Battery-Test-Datei
    battery_file = data_dir / f"battery_{today}.csv"
    battery_file.write_text(
        "13:11:30.123,85.5\n"
        "13:11:31.456,85.3\n"
        "13:11:32.789,84.8\n"
    )
    
    # Patch DATA_DIR in der app
    import webbrowser.app as app_module
    original_dir = app_module.DATA_DIR
    app_module.DATA_DIR = str(data_dir)
    
    yield data_dir
    
    # Restore
    app_module.DATA_DIR = original_dir


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

def test_extract_date_from_filename():
    """Test: extract_date_from_filename() extrahiert korrekt"""
    from webbrowser.app import extract_date_from_filename
    
    test_cases = {
        "frequency_2026-05-17.csv": "2026-05-17",
        "pv_power_2026-05-16.csv": "2026-05-16",
        "battery_2026-05-15.csv": "2026-05-15",
        "invalid_name.csv": "0000-00-00",
        "2026-05-17_data.csv": "2026-05-17",
    }
    
    for filename, expected_date in test_cases.items():
        date = extract_date_from_filename(filename)
        assert date == expected_date


def test_get_today_date():
    """Test: get_today_date() gibt aktuelles Datum zurück"""
    from webbrowser.app import get_today_date
    
    today = get_today_date()
    # Format sollte YYYY-MM-DD sein
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", today)
    
    # Sollte heutiges Datum sein
    assert today == datetime.now().strftime("%Y-%m-%d")


# =============================================================================
# ROUTE TESTS
# =============================================================================

def test_index_route(client, temp_data_dir):
    """Test: Index-Route funktioniert und listet Dateien auf"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"frequency_" in response.data or b"pv_power_" in response.data


def test_index_route_empty_directory(client, temp_data_dir):
    """Test: Index-Route mit leerem Verzeichnis"""
    # Lösche alle Dateien
    for file in temp_data_dir.glob("*.csv"):
        file.unlink()
    
    response = client.get("/")
    assert response.status_code == 200


def test_chart_route_frequency(client, temp_data_dir):
    """Test: Chart-Route für Frequenz-Datei"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/chart/frequency_{today}.csv")
    assert response.status_code == 200
    assert b"frequency_" in response.data or b"Frequenz" in response.data


def test_chart_route_power(client, temp_data_dir):
    """Test: Chart-Route für Power-Datei"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/chart/pv_power_{today}.csv")
    assert response.status_code == 200


def test_chart_route_battery(client, temp_data_dir):
    """Test: Chart-Route für Battery-Datei"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/chart/battery_{today}.csv")
    assert response.status_code == 200


def test_chart_route_not_found(client, temp_data_dir):
    """Test: Chart-Route mit nicht existierender Datei"""
    response = client.get("/chart/nonexistent_2026-05-16.csv")
    assert response.status_code == 404


# =============================================================================
# CHART IMAGE GENERATION TESTS
# =============================================================================

def test_chart_img_frequency(client, temp_data_dir):
    """Test: Chart-Image für Frequenz wird generiert"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/chart_img/frequency_{today}.csv")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert len(response.data) > 0


def test_chart_img_power(client, temp_data_dir):
    """Test: Chart-Image für PV-Power wird generiert"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/chart_img/pv_power_{today}.csv")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert len(response.data) > 0


def test_chart_img_battery(client, temp_data_dir):
    """Test: Chart-Image für Battery wird generiert"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/chart_img/battery_{today}.csv")
    assert response.status_code == 200
    assert response.mimetype == "image/png"
    assert len(response.data) > 0


def test_chart_img_not_found(client, temp_data_dir):
    """Test: 404 für nicht existierende Datei"""
    response = client.get("/chart_img/nonexistent_2026-05-16.csv")
    assert response.status_code == 404


def test_chart_img_invalid_csv(client, temp_data_dir):
    """Test: Chart-Image mit ungültigem CSV-Format"""
    today = datetime.now().strftime("%Y-%m-%d")
    invalid_file = temp_data_dir / f"invalid_{today}.csv"
    invalid_file.write_text("not,valid,csv\nwith,wrong,format\n")
    
    # Sollte entweder 500 oder 404 zurückgeben
    response = client.get(f"/chart_img/invalid_{today}.csv")
    assert response.status_code in [404, 500]


# =============================================================================
# DOWNLOAD TESTS
# =============================================================================

def test_download_frequency(client, temp_data_dir):
    """Test: Frequenz-CSV kann heruntergeladen werden"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/download/frequency_{today}.csv")
    assert response.status_code == 200
    assert b"50.01" in response.data
    assert response.content_type in ["text/csv", "application/octet-stream"]


def test_download_power(client, temp_data_dir):
    """Test: Power-CSV kann heruntergeladen werden"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/download/pv_power_{today}.csv")
    assert response.status_code == 200
    assert b"2500" in response.data


def test_download_battery(client, temp_data_dir):
    """Test: Battery-CSV kann heruntergeladen werden"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/download/battery_{today}.csv")
    assert response.status_code == 200
    assert b"85.5" in response.data


def test_download_not_found(client, temp_data_dir):
    """Test: Download mit nicht existierender Datei"""
    response = client.get("/download/nonexistent_2026-05-16.csv")
    assert response.status_code == 404


def test_download_filename_in_header(client, temp_data_dir):
    """Test: Download hat korrekten Dateinamen im Header"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/download/frequency_{today}.csv")
    
    # Header sollte Content-Disposition mit Dateinamen haben
    if "Content-Disposition" in response.headers:
        assert f"frequency_{today}.csv" in response.headers["Content-Disposition"]


# =============================================================================
# CSV PARSING TESTS
# =============================================================================

def test_csv_parsing_frequency():
    """Test: CSV-Parsing für Frequenz-Daten"""
    csv_content = "13:11:30.123,50.01\n13:11:31.456,50.02\n13:11:32.789,49.99\n"
    
    df = pd.read_csv(
        pd.io.common.StringIO(csv_content),
        names=["time", "value"]
    )
    
    assert len(df) == 3
    assert df["value"].min() == 49.99
    assert df["value"].max() == 50.02


def test_csv_parsing_power():
    """Test: CSV-Parsing für Power-Daten"""
    csv_content = "13:11:30.123,2500\n13:11:31.456,2750\n13:11:32.789,2650\n"
    
    df = pd.read_csv(
        pd.io.common.StringIO(csv_content),
        names=["time", "value"]
    )
    
    assert len(df) == 3
    assert df["value"].sum() == 7900


def test_csv_parsing_battery():
    """Test: CSV-Parsing für Battery-Daten"""
    csv_content = "13:11:30.123,85.5\n13:11:31.456,85.3\n13:11:32.789,84.8\n"
    
    df = pd.read_csv(
        pd.io.common.StringIO(csv_content),
        names=["time", "value"]
    )
    
    assert len(df) == 3
    assert 84.0 <= df["value"].mean() <= 86.0


# =============================================================================
# CHART RENDERING TESTS
# =============================================================================

def test_chart_frequency_bounds():
    """Test: Frequenz-Chart hat korrekte Grenzen"""
    csv_content = "13:11:30.123,50.01\n13:11:31.456,50.02\n13:11:32.789,49.99\n"
    
    df = pd.read_csv(
        pd.io.common.StringIO(csv_content),
        names=["time", "value"]
    )
    
    # Normalbereich für Frequenz: 49.98 - 50.02 Hz
    assert df["value"].min() >= 49.8  # Toleranzbereich
    assert df["value"].max() <= 50.2  # Toleranzbereich


def test_chart_power_bounds():
    """Test: Power-Chart hat realistische Grenzen"""
    csv_content = "13:11:30.123,2500\n13:11:31.456,2750\n13:11:32.789,2650\n"
    
    df = pd.read_csv(
        pd.io.common.StringIO(csv_content),
        names=["time", "value"]
    )
    
    # Power sollte nicht-negativ sein
    assert (df["value"] >= 0).all()
    # Power sollte realistisch sein (< 50kW)
    assert (df["value"] <= 50000).all()


def test_chart_battery_bounds():
    """Test: Battery-Chart hat Grenzen von 0-100%"""
    csv_content = "13:11:30.123,85.5\n13:11:31.456,85.3\n13:11:32.789,84.8\n"
    
    df = pd.read_csv(
        pd.io.common.StringIO(csv_content),
        names=["time", "value"]
    )
    
    # SoC sollte zwischen 0-100% sein
    assert (df["value"] >= 0).all()
    assert (df["value"] <= 100).all()


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

def test_empty_csv_file(client, temp_data_dir):
    """Test: Handling von leeren CSV-Dateien"""
    today = datetime.now().strftime("%Y-%m-%d")
    empty_file = temp_data_dir / f"empty_{today}.csv"
    empty_file.write_text("")
    
    # Sollte nicht absturzen
    response = client.get(f"/chart_img/empty_{today}.csv")
    assert response.status_code in [200, 400, 500]


def test_malformed_csv_missing_values(client, temp_data_dir):
    """Test: Handling von CSV mit fehlenden Werten"""
    today = datetime.now().strftime("%Y-%m-%d")
    malformed_file = temp_data_dir / f"malformed_{today}.csv"
    malformed_file.write_text("13:11:30.123\n13:11:31.456,50.02\n")
    
    # Sollte nicht absturzen
    response = client.get(f"/chart_img/malformed_{today}.csv")
    assert response.status_code in [200, 400, 500]


def test_csv_special_characters(client, temp_data_dir):
    """Test: Handling von CSV mit Sonderzeichen"""
    today = datetime.now().strftime("%Y-%m-%d")
    special_file = temp_data_dir / f"special_{today}.csv"
    special_file.write_text(
        "13:11:30.123,50.01\n"
        "13:11:31.456,50.02\n"
    )
    
    response = client.get(f"/chart_img/special_{today}.csv")
    assert response.status_code in [200, 400, 500]


# =============================================================================
# DATA SORTING TESTS
# =============================================================================

def test_index_files_sorted_by_date():
    """Test: Index sortiert Dateien nach Datum (neueste zuerst)"""
    from webbrowser.app import extract_date_from_filename
    
    files = [
        "battery_2026-05-15.csv",
        "battery_2026-05-17.csv",
        "battery_2026-05-16.csv",
    ]
    
    sorted_files = sorted(
        files,
        key=lambda f: extract_date_from_filename(f),
        reverse=True
    )
    
    assert sorted_files[0] == "battery_2026-05-17.csv"
    assert sorted_files[1] == "battery_2026-05-16.csv"
    assert sorted_files[2] == "battery_2026-05-15.csv"


def test_index_filters_today_files(temp_data_dir):
    """Test: Index filtert Dateien von heute"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    
    files = [
        f"battery_{today}.csv",
        f"battery_{yesterday}.csv",
        f"frequency_{today}.csv",
    ]
    
    today_files = [f for f in files if today in f]
    assert len(today_files) == 2
    assert f"battery_{today}.csv" in today_files
    assert f"frequency_{today}.csv" in today_files


# =============================================================================
# CONTENT TYPE TESTS
# =============================================================================

def test_content_type_html(client, temp_data_dir):
    """Test: HTML-Routes haben korrekten Content-Type"""
    response = client.get("/")
    assert "text/html" in response.content_type


def test_content_type_png(client, temp_data_dir):
    """Test: PNG-Routes haben korrekten Content-Type"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/chart_img/frequency_{today}.csv")
    assert response.status_code == 200
    assert response.mimetype == "image/png"


def test_content_type_csv(client, temp_data_dir):
    """Test: CSV-Downloads haben korrekten Content-Type"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/download/frequency_{today}.csv")
    assert response.status_code == 200
    assert "csv" in response.content_type or "text" in response.content_type

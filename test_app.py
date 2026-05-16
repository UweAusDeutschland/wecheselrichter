"""
Test-Suite für die Flask-App - prüft Syntax, Routes und Chart-Generierung
"""
import pytest
import pandas as pd
import io
import tempfile
import os
from datetime import datetime
from pathlib import Path


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
    
    # Patch DATA_DIR in der App
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "false")
    
    # Erstelle Test-Dateien
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


def test_app_imports():
    """Test: App kann importiert werden ohne Syntax-Fehler"""
    try:
        from webbrowser.app import app
        assert app is not None
    except SyntaxError as e:
        pytest.fail(f"Syntax-Fehler in app.py: {e}")


def test_index_route(client, temp_data_dir):
    """Test: Index-Route funktioniert"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"frequency_" in response.data or b"pv_power_" in response.data or response.data == b""


def test_chart_route(client, temp_data_dir):
    """Test: Chart-Route funktioniert"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/chart/frequency_{today}.csv")
    assert response.status_code == 200


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


def test_download_frequency(client, temp_data_dir):
    """Test: Frequenz-CSV kann heruntergeladen werden"""
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f"/download/frequency_{today}.csv")
    assert response.status_code == 200
    assert b"50.01" in response.data


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

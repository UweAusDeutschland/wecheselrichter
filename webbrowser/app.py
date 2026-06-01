"""
Flask-Webserver mit Logging für Wecheselrichter
"""
import logging
import sys
from logging.handlers import RotatingFileHandler

# Matplotlib Konfiguration (MUSS vor pyplot stehen!)
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from flask import Flask, render_template, send_file, abort, request
import os
import pandas as pd
from io import BytesIO
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates

# Logging initialisieren
def setup_logging():
    """Logging konfigurieren mit RotatingFileHandler"""
    # Logdatei im Verzeichnis über dem Projekt speichern
    log_dir = os.path.dirname(os.path.dirname(__file__))
    log_file = os.path.join(log_dir, "wecheselrichter_web.log")
    
    # RotatingFileHandler: Logdateien nach Größe rotieren (10MB Limit)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    
    # Console Handler für Debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # DEBUG für mehr Details
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return file_handler, console_handler

setup_logging()


app = Flask(__name__)
DATA_DIR = "data"


@app.before_request
def before_request():
    """Allgemeine Request-Logging"""
    logger.info(f"Request: {request.method} {request.path}")


@app.after_request
def after_request(response):
    """Response-Header hinzufügen (CORS, Cache-Control)"""
    # CORS Header für Web-Oberfläche
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    # Kein Caching von Grafiken
    if request.path.startswith('/chart_img'):
        response.headers['Cache-Control'] = 'no-store'
    
    return response


@app.route("/")
def index():
    """Startseite mit Dateiliste"""
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
        
        logger.info(f"Zeige {len(files)} Dateien auf Startseite")
        
        if not files:
            logger.warning("Keine CSV-Dateien im Datenordner gefunden!")
            
    except PermissionError as e:
        logger.error(f"Lesezugriff verweigert: {e}")
        abort(500)
        
    except Exception as e:
        logger.exception(f"Fehler beim Auflisten von Dateien: {e}")
        abort(500)
    
    return render_template("index.html", files=files)


@app.route("/chart/<filename>")
def show_chart(filename):
    """Zeigt eine Chart-Seite an"""
    filepath = os.path.join(DATA_DIR, filename)
    
    # Existenzprüfung mit Logging
    if not os.path.exists(filepath):
        logger.warning(f"Datei nicht gefunden: {filepath}")
        abort(404)
        
    try:
        df = pd.read_csv(filepath)  # Test ob lesbar
        
    except PermissionError as e:
        logger.error(f"Lesezugriff verweigert für {filename}: {e}")
        abort(503)
        
    except Exception as e:
        logger.exception(f"Fehler beim Lesen von {filename}: {e}")
        abort(500)
    
    return render_template("chart.html", filename=filename)


@app.route("/chart_img/<filename>")
def chart_img(filename):
    """Generiert ein Bild eines Charts"""
    filepath = os.path.join(DATA_DIR, filename)
    
    # Existenzprüfung mit Logging
    if not os.path.exists(filepath):
        logger.warning(f"Datei nicht gefunden: {filepath}")
        abort(404)
        
    try:
        df = pd.read_csv(filepath, names=["time", "value"])
        df["time"] = pd.to_datetime(df["time"], format="%H:%M:%S.%f")
        
    except PermissionError as e:
        logger.error(f"Lesezugriff verweigert für {filename}: {e}")
        abort(503)
        
    except Exception as e:
        logger.exception(f"Fehler beim Lesen von {filename}: {e}")
        # Bei CSV-Fehlern trotzdem ein Bild generieren mit Fehlermeldung
        try:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.text(0.5, 0.5, "Fehler bei Daten-Lesevorgang", 
                    transform=ax.transAxes, ha='center')
            ax.set_title(f"Datei: {filename}")
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format="png")
            plt.close(fig)
            
        except Exception as e2:
            logger.exception(f"Fehler beim Generieren des Fallback-Bildes: {e2}")
            abort(500)
    
    # Bestimme Datentyp basierend auf Dateiname
    is_frequency = filename.startswith("frequency_")
    is_power = filename.startswith("pv_power_")
    is_battery = filename.startswith("battery_")
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    if is_frequency:
        # Frequenzdaten (Hz)
        min_val = df["value"].min() - 0.01
        max_val = df["value"].max() + 0.01
        ax.axhspan(49.98, 50.02, color='green', alpha=0.15, label='Normalbereich (49,98–50,02 Hz)')
        if min_val < 49.98 and max_val >= 49.8:
            lower_limit = 49.8 if min_val < 49.8 else min_val
            ax.axhspan(lower_limit, 49.98, color='orange', alpha=0.15, label='Toleranzbereich (49,8–49,98 Hz)')
        if max_val > 50.02 and min_val <= 50.2:
            upper_limit = 50.2 if max_val > 50.2 else max_val
            ax.axhspan(50.02, upper_limit, color='orange', alpha=0.15, label='Toleranzbereich (50,02–50,2 Hz)')
            ax.text(df["time"].iloc[len(df)//2], 50.04, "Toleranzbereich (49,8 – 50,2 Hz)", color="black",
                fontsize=12, ha="center", va="center", alpha=0.7, weight='bold')
        if min_val < 49.8:
            ax.axhspan(ax.get_ylim()[0], 49.8, color='red', alpha=0.10, label='Kritisch (<49,8 Hz)')
        if max_val > 50.2:
            ax.axhspan(50.2, ax.get_ylim()[1], color='red', alpha=0.10, label='Kritisch (>50,2 Hz)')
            ax.text(df["time"].iloc[len(df)//2], 50.21, "Kritisch", color="red",
                fontsize=12, ha="center", va="center", alpha=0.7, weight='bold')
        plt.plot(df["time"], df["value"], marker='o', linestyle='-', label='Frequenz', markersize=2)
        y_label = "Frequenz (Hz)"
        
    elif is_power:
        # Power-Daten (Watt)
        ax.axhspan(0, df["value"].max() * 0.9, color='green', alpha=0.05)
        plt.plot(df["time"], df["value"], marker='o', linestyle='-', label='PV-Leistung', markersize=2, color='orange')
        y_label = "Leistung (Watt)"
        
    elif is_battery:
        # Battery-Daten (Prozent)
        ax.axhspan(0, 20, color='red', alpha=0.1, label='Kritisch (<20%)')
        ax.axhspan(20, 80, color='yellow', alpha=0.05, label='Normal (20-80%)')
        ax.axhspan(80, 100, color='green', alpha=0.1, label='Gut (80-100%)')
        plt.plot(df["time"], df["value"], marker='o', linestyle='-', label='Batterieladung', markersize=2, color='blue')
        ax.set_ylim(0, 105)
        y_label = "Batterieladung (%)"
    else:
        # Unbekannter Datentyp - Fallback
        plt.plot(df["time"], df["value"], marker='o', linestyle='-', label='Wert', markersize=2)
        y_label = "Wert"
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    basename = filename.split('_', 1)[-1].split('.', 1)[0]
    plt.title(f"{basename}")
    plt.xlabel("Zeit")
    plt.ylabel(y_label)
    plt.grid(True)
    plt.tight_layout()
    
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png")
    img_buffer.seek(0)
    plt.close(fig)
    
    logger.debug(f"Chart-Bild generiert: {filename}")
    
    return send_file(img_buffer, mimetype="image/png")


@app.route("/download/<filename>")
def download_file(filename):
    """Download einer Datei"""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        logger.warning(f"Datei nicht gefunden für Download: {filepath}")
        abort(404)
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Wecheselrichter-Webserver startet...")
    logger.info("=" * 50)
    
    app.run(host="0.0.0.0", port=5000, debug=False)
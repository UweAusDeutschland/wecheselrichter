import matplotlib
matplotlib.use("Agg")  # Muss VOR dem Import von pyplot stehen!
from matplotlib import pyplot as plt
from flask import Flask, render_template, send_file, abort
import os
import pandas as pd
from io import BytesIO
from datetime import datetime
import numpy as np
import matplotlib.dates as mdates
import re

app = Flask(__name__)
DATA_DIR = "data"

def extract_date_from_filename(filename):
    """Extrahiert das Datum aus einem Dateinamen (z.B. battery_2026-05-17.csv)"""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return "0000-00-00"

def get_today_date():
    """Gibt das heutige Datum im Format YYYY-MM-DD zurück"""
    return datetime.now().strftime("%Y-%m-%d")

@app.route("/")
def index():
    # Liste aller CSV-Dateien im Datenordner
    all_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    
    # Nach Datum sortieren (neueste zuerst)
    sorted_files = sorted(all_files, key=lambda f: extract_date_from_filename(f), reverse=True)
    
    # Dateien von heute filtern
    today = get_today_date()
    today_files = [f for f in sorted_files if extract_date_from_filename(f) == today]
    
    return render_template("index.html", files=sorted_files, today_files=today_files)

@app.route("/chart/<filename>")
def show_chart(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    return render_template("chart.html", filename=filename)

@app.route("/chart_img/<filename>")
def chart_img(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    
    # Diagramm erstellen
    df = pd.read_csv(filepath, names=["time", "value"])
    df["time"] = pd.to_datetime(df["time"], format="%H:%M:%S.%f")
    
    # Bestimme Datentyp basierend auf Dateiname
    is_frequency = filename.startswith("frequency_")
    is_power = filename.startswith("pv_power_")
    is_battery = filename.startswith("battery_")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
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
    
    return send_file(img_buffer, mimetype="image/png")

@app.route("/download/<filename>")
def download_file(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

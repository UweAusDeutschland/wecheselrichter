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

app = Flask(__name__)
DATA_DIR = "data"

@app.route("/")
def index():
    # Liste aller CSV-Dateien im Datenordner
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    return render_template("index.html", files=files)

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
    
    # Diagramm erstellen (wie bisher)
    df = pd.read_csv(filepath, names=["time", "freq"])
    df["time"] = pd.to_datetime(df["time"], format="%H:%M:%S.%f")
    min_freq = df["freq"].min() - 0.01
    max_freq = df["freq"].max() + 0.01
    print(f'Min: {min_freq} Hz und Max: {max_freq} Hz')
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axhspan(49.98, 50.02, color='green', alpha=0.15, label='Normalbereich (49,98–50,02 Hz)')
    if min_freq < 49.98 and max_freq >= 49.8:
        lower_limit = 49.8 if min_freq < 49.8 else min_freq
        ax.axhspan( lower_limit, 49.98, color='orange', alpha=0.15, label='Toleranzbereich (49,8–49,98 Hz)')
    if max_freq > 50.02 and min_freq <= 50.2:
        upper_limit =  50.2 if max_freq > 50.2 else max_freq
        ax.axhspan(50.02, upper_limit, color='orange', alpha=0.15, label='Toleranzbereich (50,02–50,2 Hz)')
        ax.text(df["time"].iloc[len(df)//2], 50.04, "Toleranzbereich (49,8 – 50,2 Hz)", color="black",
            fontsize=12, ha="center", va="center", alpha=0.7, weight='bold')
    if min_freq < 49.8:
        ax.axhspan(ax.get_ylim()[0], 49.8, color='red', alpha=0.10, label='Kritisch (<49,8 Hz)')
    
    if max_freq > 50.2:
        ax.axhspan(50.2, ax.get_ylim()[1], color='red', alpha=0.10, label='Kritisch (>50,2 Hz)')
        ax.text(df["time"].iloc[len(df)//2], 50.21, "Kritisch", color="red",
            fontsize=12, ha="center", va="center", alpha=0.7, weight='bold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.plot(df["time"], df["freq"], marker='o', linestyle='-', label='Frequenz', markersize=2)
    basename = filename.split('_', 1)[-1].split('.', 1)[0]
    plt.title(f"Netzfrequenz {basename}")
    plt.xlabel("Zeit")
    plt.ylabel(f"Frequenz in Hz")
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
    app.run(host="0.0.0.0", port=5000, debug=True)

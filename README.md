# Wechselrichter Monitor 🌞

Kontinuierliche Überwachung eines Sungrow SH6.0RT Wechselrichters mit Datensammlung und Web-Visualisierung.

**Features:**
- 📊 Echtzeit-Monitoring von Netzfrequenz, PV-Leistung und Batteriestand
- 📈 Automatische CSV-Datenspeicherung (pro Tag eine Datei)
- 🌐 Web-Dashboard mit interaktiven Diagrammen
- 🐳 Docker-ready (für 24/7 Betrieb)
- ✅ Umfassende Unit-Tests mit CI/CD

## 📋 Übersicht

Das Projekt überwacht einen **Sungrow SH6.0RT Wechselrichter** via Modbus-TCP und visualisiert drei Messwerte:

| Messwert | Bereich | Speicherung | Ziel |
|----------|---------|-------------|------|
| **Netzfrequenz** | 49-51 Hz | `frequency_YYYY-MM-DD.csv` | Stromnetzstabilität |
| **PV-Leistung** | 0-6000W | `pv_power_YYYY-MM-DD.csv` | Solaranlage Performance |
| **Batteriestand** | 0-100% | `battery_YYYY-MM-DD.csv` | Speicherstatus |

## 🚀 Quick Start

### Option 1: Docker (Empfohlen für 24/7 Betrieb)

```bash
# Clone und starten
git clone https://github.com/UweAusDeutschland/wecheselrichter.git
cd wecheselrichter
docker-compose up --build
```

Dann öffnen Sie: **http://localhost:5000**

### Option 2: Lokal (für Entwicklung)

```bash
# Python 3.11+ erforderlich
pip install -r requirements.txt

# Terminal 1: Power Monitor
python powermonitor.py

# Terminal 2: Frequency Monitor
python frequencymonitor.py

# Terminal 3: Battery Monitor
python batterymonitor.py

# Terminal 4: Web App
python -m flask --app webbrowser.app run
```

Web-App öffnet auf: **http://localhost:5000**

## 🔧 Installation & Setup

### Voraussetzungen

- **Python 3.11+** oder **Docker**
- **Netzwerkzugriff** zum Wechselrichter (Modbus TCP Port 502)
- Moderne Browser für Web-Dashboard

### Konfiguration

Der Wechselrichter wird standardmäßig unter `modbusSungrow.fritz.box` erwartet. Sie können die IP/Hostname ändern via:

**Umgebungsvariablen:**
```bash
export INVERTER_HOST=192.168.1.100
python powermonitor.py
```

**Oder in Docker:**
```yaml
# docker-compose.yml
environment:
  - INVERTER_HOST=192.168.1.100
```

### Datenspeicherung

Die Monitore speichern CSV-Dateien in `data/`:

```
data/
├── frequency_2026-05-16.csv    # Pro Tag eine neue Datei
├── pv_power_2026-05-16.csv
├── battery_2026-05-16.csv
└── frequency_sample_data.csv   # Beispiel-Datei
```

**Automatische Bereinigung:** Dateien älter als 90 Tage werden automatisch gelöscht (konfigurierbar via `RETENTION_DAYS`).

## 📊 Web Dashboard

Das Dashboard zeigt alle gesammelten CSV-Dateien an:

- **Dateiübersicht:** Liste aller verfügbaren Dateien
- **Interaktive Diagramme:** Visualisierung mit korrekter Skalierung
- **Download:** CSV-Dateien zur offline Analyse

### Diagramm-Typen

| Dateiname | Darstellung | Bereiche |
|-----------|-------------|----------|
| `frequency_*.csv` | Liniendiagramm | Normal (grün), Toleranz (orange), Kritisch (rot) |
| `pv_power_*.csv` | Liniendiagramm | Power in Watt |
| `battery_*.csv` | Liniendiagramm | Gut 80-100% (grün), Normal 20-80% (gelb), Kritisch 0-20% (rot) |

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │
│  │  frequencymon  │  │   powermonitor │  │ batterymon │ │
│  │   (50ms-inte   │  │   (1s-int)     │  │ (5s-int)   │ │
│  └────────────────┘  └────────────────┘  └────────────┘ │
│           │                   │                 │         │
│           └───────────────────┴─────────────────┘         │
│                        │                                  │
│                   [Modbus TCP]                            │
│                        │                                  │
│              ┌──────────────────────┐                     │
│              │ Sungrow SH6.0RT      │                     │
│              │ Port 502             │                     │
│              └──────────────────────┘                     │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         Flask Web App (Gunicorn)                     │ │
│  │  - Index: Dateiliste                                │ │
│  │  - /chart_img: Chart-Generierung (matplotlib)      │ │
│  │  - /download: CSV-Download                         │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Persistenter Storage                    │ │
│  │  Volumes:                                           │ │
│  │  - data/ → CSV-Dateien (täglich)                   │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │
         └─→ Port 5000 (HTTP)
```

## 📝 CSV-Format

Alle CSV-Dateien folgen einem einheitlichen Format:

```csv
HH:MM:SS.mmm,Wert
13:11:30.123,50.01
13:11:31.456,50.02
13:11:32.789,49.99
```

- **Spalte 1:** Zeit (HH:MM:SS.mmm, Millisekunden-Genauigkeit)
- **Spalte 2:** Messwert (Einheit je nach Datentyp)

## 🧪 Tests & Entwicklung

### Unit Tests starten

```bash
# Alle Tests
python -m pytest -v

# Nur App-Tests
python -m pytest test_app.py -v

# Nur Inverter-Tests
python -m pytest test_sungrowinverter.py -v
```

**Test-Coverage:**
- 10 Tests für Flask-App (Routes, Chart-Generierung, Downloads)
- 7 Tests für SungrowInverter-Klasse (Modbus-Kommunikation)

### CI/CD

Bei jedem Push werden Tests automatisch auf GitHub Actions ausgeführt → `.github/workflows/tests.yml`

## 📦 Projektstruktur

```
wecheselrichter/
├── README.md                      # Diese Datei
├── requirements.txt               # Python-Abhängigkeiten
├── Dockerfile                     # Docker-Image
├── docker-compose.yml             # Docker-Compose Konfiguration
├── entrypoint.sh                  # Container-Startscript
│
├── sungrowinverter.py            # Modbus-Kommunikation (Klasse)
├── frequencymonitor.py           # Netzfrequenz-Sammler
├── powermonitor.py               # PV-Leistungs-Sammler
├── batterymonitor.py             # Batteriestand-Sammler
│
├── webbrowser/
│   ├── __init__.py
│   ├── app.py                    # Flask-App (Hauptlogik)
│   ├── static/
│   │   └── style.css             # Styling
│   └── templates/
│       ├── index.html            # Datei-Liste
│       └── chart.html            # Chart-Seite
│
├── test_app.py                   # Flask-Tests (10 Tests)
├── test_sungrowinverter.py       # Inverter-Tests (7 Tests)
├── pytest.ini                    # Pytest-Konfiguration
│
├── .github/
│   └── workflows/
│       └── tests.yml             # GitHub Actions CI/CD
│
├── data/
│   ├── frequency_YYYY-MM-DD.csv
│   ├── pv_power_YYYY-MM-DD.csv
│   ├── battery_YYYY-MM-DD.csv
│   └── frequency_sample_data.csv # Beispieldaten
│
└── LICENSE
```

## 🔌 API-Referenz

### SungrowInverter Klasse

```python
from sungrowinverter import SungrowInverter

inverter = SungrowInverter(host="modbusSungrow.fritz.box")

# Netzfrequenz (Hz)
freq = inverter.get_frequency()  # z.B. 50.01

# PV-Leistung (Watt)
power = inverter.get_pv_power()  # z.B. 3500

# Batteriestand (%)
battery = inverter.get_battery_level()  # z.B. 85.5
```

### Flask Routes

| Route | Methode | Beschreibung |
|-------|---------|-------------|
| `/` | GET | Dateiübersicht |
| `/chart/<filename>` | GET | Chart-Seite (HTML) |
| `/chart_img/<filename>` | GET | Chart als PNG-Bild |
| `/download/<filename>` | GET | CSV-Download |

## ⚙️ Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|------------|
| `INVERTER_HOST` | `modbusSungrow.fritz.box` | Wechselrichter-Adresse |
| `INVERTER_PORT` | `502` | Modbus TCP Port |
| `RETENTION_DAYS` | `90` | Tage bis automatisches Löschen |

## 🐛 Troubleshooting

### Container startet nicht

```bash
# Logs anschauen
docker-compose logs -f sungrow-monitor-1

# Netzwerk testen
docker exec wecheselrichter-sungrow-monitor-1 ping modbusSungrow.fritz.box
```

### Keine Daten werden gesammelt

- Wechselrichter erreichbar? → `ping modbusSungrow.fritz.box`
- Port 502 offen? → `telnet modbusSungrow.fritz.box 502`
- Modbus-Registers korrekt? → Logs in `frequencymonitor.py`, etc. überprüfen

### Web-App zeigt leere Liste

- `data/` Verzeichnis existiert? → `ls -la data/`
- CSV-Dateien vorhanden? → Monitor-Prozesse laufen?

## 📄 Lizenz

MIT - Siehe [LICENSE](LICENSE)

## 👤 Autor

**Uwe Sülter** (UweAusDeutschland)

## 🤝 Beiträge

Pull Requests sind willkommen! Bitte:
1. Tests schreiben (`pytest`)
2. Code formatieren
3. Dokumentation aktualisieren


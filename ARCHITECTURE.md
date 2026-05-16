# Architektur 🏗️

Technische Übersicht der Systemarchitektur.

## System-Übersicht

```
┌────────────────────────────────────────────────────────────────┐
│                      Docker Container                           │
│  (wecheselrichter-sungrow-monitor-1)                           │
└────────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────────────────────┐
         │                                                 │
         ▼                                                 ▼
    ┌─────────────────────────────┐         ┌──────────────────────────┐
    │  Data Collection Layer      │         │  Web Presentation Layer  │
    ├─────────────────────────────┤         ├──────────────────────────┤
    │ - frequencymonitor.py       │         │ - Flask App (Gunicorn)   │
    │ - powermonitor.py           │         │ - Static Files (CSS)     │
    │ - batterymonitor.py         │         │ - Templates (HTML)       │
    │                             │         │                          │
    │ [Sampling Threads]          │         │ [HTTP Server]            │
    │ 50ms / 1s / 5s              │         │ Port 5000                │
    └─────────────────────────────┘         └──────────────────────────┘
              │                                      │
              │ Modbus TCP                          │ Read
              │ (async)                             │
              ▼                                      ▼
    ┌─────────────────────────────┐         ┌──────────────────────────┐
    │   Device Layer              │         │   Storage Layer          │
    ├─────────────────────────────┤         ├──────────────────────────┤
    │ SungrowInverter Class       │         │ CSV Files (Daily)        │
    │ - Modbus Connection Pool    │         │                          │
    │ - Register Definitions      │         │ data/                    │
    │ - Error Handling            │         │ ├── frequency_YYYY-MM-DD │
    │ - Retry Logic               │         │ ├── pv_power_YYYY-MM-DD  │
    │                             │         │ ├── battery_YYYY-MM-DD   │
    │ [pyModbusTCP Client]        │         │ └── [Sample data]        │
    └─────────────────────────────┘         └──────────────────────────┘
              │
              │ TCP:502
              │
              ▼
    ┌─────────────────────────────┐
    │   Sungrow SH6.0RT           │
    ├─────────────────────────────┤
    │ Modbus Slave                │
    │ - Frequency Register (5241) │
    │ - Power Register (5016)     │
    │ - Battery Register (13022)  │
    └─────────────────────────────┘
```

## Komponenten

### 1. Monitor-Programme (Data Collection)

#### `frequencymonitor.py`
- **Sampling Rate:** 50ms (20 Hz)
- **Daten:** Netzfrequenz (Hz)
- **Speicherung:** `frequency_YYYY-MM-DD.csv`
- **Logik:**
  - DNS resolution + retry
  - Kontinuierliches Polling
  - Change detection (nur änderungen speichern)
  - Automatisches Rollover bei Tageswechsel
  - Automatisches Cleanup alter Dateien (>90 Tage)

#### `powermonitor.py`
- **Sampling Rate:** 1s (1 Hz)
- **Daten:** PV-Leistung (Watt)
- **Speicherung:** `pv_power_YYYY-MM-DD.csv`
- **Logik:** Identisch zu frequencymonitor, aber 32-bit Little-Endian Konversion

#### `batterymonitor.py`
- **Sampling Rate:** 5s (0.2 Hz)
- **Daten:** Batteriestand (%)
- **Speicherung:** `battery_YYYY-MM-DD.csv`
- **Logik:** Identisch zu frequencymonitor, aber 0.1-Skalierung

### 2. Device Layer

#### `SungrowInverter` Class (`sungrowinverter.py`)
```python
class SungrowInverter:
    __init__(host, port=502, unit_id=1)
    _read_register(reg_name, count=1) → raw_values
    get_frequency() → float [Hz]
    get_pv_power() → int [W]
    get_battery_level() → float [%]
```

**Register-Mapping:**
```
Frequency:  Register 5241 (scaled ×0.01)
Power:      Register 5016-5017 (32-bit LE)
Battery:    Register 13022 (scaled ×0.1)
```

**Error Handling:**
- Connection retry mit exponential backoff
- DNS resolution caching
- Modbus timeout handling
- Graceful degradation bei Fehler

### 3. Web Presentation Layer

#### Flask App (`webbrowser/app.py`)

**Routes:**
- `GET /` → Index (Dateiübersicht)
- `GET /chart/<filename>` → Chart-Seite (HTML)
- `GET /chart_img/<filename>` → Chart (PNG)
- `GET /download/<filename>` → CSV-Download

**Chart-Generierung:**
- Dynamische Skalierung basierend auf Datentyp
- Matplotlib-basierte Rendering
- Color-coded Zones (Frequency, Battery)
- Time-axis Formatting

**Performance:**
- Lazy loading (Charts nur bei Anfrage generiert)
- In-memory PNG (kein Temp-File)
- Buffer-based image serving

### 4. Storage Layer

**CSV Format:**
```
HH:MM:SS.mmm,value
13:11:30.123,50.01
13:11:31.456,50.02
...
```

**Dateinamen:**
- `frequency_YYYY-MM-DD.csv` (Netzfrequenz)
- `pv_power_YYYY-MM-DD.csv` (Leistung)
- `battery_YYYY-MM-DD.csv` (Batteriestand)

**Cleanup-Policy:**
- Dateien älter als `RETENTION_DAYS` (default: 90) werden automatisch gelöscht
- Lauft beim Startup jedes Monitors
- Konfigurierbar via Umgebungsvariable

## Datenfluss

### Write-Path (Data Collection)

```
SungrowInverter.get_frequency()
    │
    ├─→ ModbusClient.read_input_registers(5241, 1)
    │       │
    │       └─→ TCP:502 → Wechselrichter
    │
    ├─→ Parse & Scale (×0.01)
    │
    ├─→ Change Detection
    │   │
    │   └─→ Nur wenn Wert ≠ last_value
    │
    └─→ CSV Write (append)
        │
        └─→ data/frequency_2026-05-16.csv
```

**Concurrency:**
- Jeder Monitor läuft in eigenem Prozess (3 Prozesse total)
- Keine Locks erforderlich (separate CSV-Dateien)
- Docker orchestriert via `entrypoint.sh`

### Read-Path (Web Dashboard)

```
GET /chart_img/frequency_2026-05-16.csv
    │
    ├─→ Flask Route Handler
    │
    ├─→ Read CSV File
    │   │
    │   └─→ Pandas.read_csv()
    │
    ├─→ Detect File Type (frequency_/pv_power_/battery_)
    │
    ├─→ Create Matplotlib Figure
    │   │
    │   ├─→ Parse Time + Value
    │   │
    │   ├─→ Add Color Zones (je nach Typ)
    │   │
    │   └─→ Plot Line
    │
    ├─→ Render to PNG (in-memory)
    │
    └─→ HTTP Response (image/png)
```

## Performance-Charakteristiken

### Speichernutzung

**Pro Monitor-Prozess:**
- Baseline: ~50 MB (Python Runtime + Libraries)
- Bei Aktivität: +10-20 MB (Modbus Buffer)
- **Total:** ~150-200 MB für 3 Prozesse

**Pro Datei:**
- Min: ~5 KB/Tag (Battery: 5s Intervall)
- Avg: ~50 KB/Tag (Power: 1s Intervall)
- Max: ~300 KB/Tag (Frequency: 50ms Intervall)
- **90 Tage:** ~5-30 MB pro Datentyp

### Netzwerk

**Modbus Traffic:**
- Read Register: ~12 Bytes/Request
- Response: ~9 Bytes
- **Frequenz:** 20/s × 19 B = 380 B/s
- **Leistung:** 1/s × 27 B = 27 B/s
- **Batterie:** 0.2/s × 19 B = 3.8 B/s
- **Total:** ~410 B/s ≈ 35 KB/min ≈ 50 MB/Tag

### CPU

**Typischer Einsatz:**
- Monitor-Prozesse: ~5-10% CPU (Read + File I/O)
- Flask/Gunicorn: ~0% CPU (idle), ~20-30% bei Chart-Request
- **Summe:** <20% CPU auf Standard-Hardware (Single Core)

## Fehlerbehandlung

### Monitor-Prozesse

**On Modbus Failure:**
1. Log Warning
2. Retry mit exponential backoff
3. Nach 5 Fehlversuchen: Komplette DNS-Neuauflösung
4. Nach 10 Fehlversuchen: Exit + Container Restart

**On File I/O Error:**
1. Log Error
2. Continue mit nächstem Reading
3. File Handle wird automatisch geöffnet

### Flask App

**On CSV Not Found:**
1. Return 404 Not Found

**On Chart Render Error:**
1. Log Exception
2. Return 500 Internal Error

## Skalierbarkeit

### Horizontal

Aktuell: **Single-Container-Design**

Für Multi-Inverter:
- Separate Container pro Inverter
- Shared Volume für Daten
- Load Balancer (nginx) vor Flask

### Vertikal

- CSV → InfluxDB/TimescaleDB für schnellere Queries
- Chart-Cache (Redis) für häufig angeforderte Charts
- Asynchrone Chart-Generierung (Celery)

## Sicherheit

### Aktuell

- Keine Authentication (LAN-only assumed)
- Keine Verschlüsselung (TCP-Modbus unverschlüsselt)

### Empfehlungen

1. **Docker Network:** Nur local (nicht expose zu WAN)
2. **Firewall:** Port 5000 nur im LAN erlauben
3. **HTTPS:** Reverse Proxy (nginx) mit TLS
4. **Auth:** Basic Auth oder OAuth2 via Proxy
5. **Secrets:** Inverter-IP in secrets.yml, nicht in docker-compose.yml

## Testing

### Test-Strategie

**Unit Tests:**
- Mock Modbus Client
- Test Data Parsing
- Test Chart Generation

**Integration Tests:**
- Real CSV Files
- End-to-End HTTP Requests
- Sample Data

**CI/CD:**
- GitHub Actions
- Pre-commit Hooks (lokal)
- Post-deploy Smoke Tests

## Deployment-Varianten

### Docker Compose (Empfohlen)
- Einfach zu deployen
- Automatische Neustart
- Volume-Management

### Kubernetes
- Multi-node Skalierung
- Auto-failover
- Resource Limits

### Bare Metal (systemd)
- Minimale Overhead
- Native Performance
- Komplexeres Setup

---

**Last Updated:** 2026-05-16  
**Version:** 0.3.0

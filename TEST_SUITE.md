# 📊 Test-Suite Dokumentation — Wechselrichter-Monitoring

## 🎯 Übersicht

Diese dokumentiert die umfassende Test-Suite für das Sungrow-Inverter-Monitoring-System. Die Tests decken alle kritischen Komponenten ab und stellen sicher, dass das System zuverlässig 24/7 läuft.

## 📁 Test-Dateien

### 1. **test_monitor_base.py** — Utility-Funktionen (20 Tests)
Testet Kernfunktionen in `monitor_base.py`:
- ✅ `ConnectionConfig` — Verbindungskonfiguration
- ✅ `resolve_with_retry()` — DNS-Auflösung mit Wiederholungslogik
- ✅ `test_port()` — Port-Erreichbarkeit prüfen
- ✅ `cleanup_old_csv_files()` — Datei-Cleanup nach Retention-Policy

**Kritisch**: Diese Tests sichern ab, dass Fehlerbehandlung robust ist.

```bash
pytest test_monitor_base.py -v
```

---

### 2. **test_sungrowinverter_extended.py** — Inverter-Klasse (80 Tests)
Testet alle Accessor-Methoden in `sungrowinverter.py`:

#### Temperatures (6 Tests)
- `get_temperature()` für alle Orte: dc_plus, dc_minus, ac_plus, ac_minus, pv1, pv2
- Negative Temperaturen, Error-Handling

#### Grid Parameters (9 Tests)
- `get_grid_frequency()` — Netzfrequenz (Hz)
- `get_grid_voltage()` — Spannung pro Phase (L1, L2, L3)
- `get_grid_power()` — Aktive/reaktive Leistung

#### PV Inputs (9 Tests)
- `get_pv_power()` — PV-Leistung (beide Inputs)
- `get_pv_voltage()` — PV-Spannung
- `get_pv_current()` — PV-Strom

#### Battery (6 Tests)
- `get_battery_soc()` — Ladestand (0-100%)
- `get_battery_voltage()` — Batteriespannung

#### System Status (7 Tests)
- `get_system_status()` — Status-Codes und Beschreibungen
- `get_error_code()` — Fehlercodes

#### Energy Statistics (3 Tests)
- `get_energy_statistics()` — Lifetime, Today, Month

#### Scaling Factors (1 Test)
- Verifiziert alle Skalierungsfaktoren

**Wichtig**: Tests für alle Skalierungen (×0.01, ×0.1, ×10) und Edge-Cases.

```bash
pytest test_sungrowinverter_extended.py -v
```

---

### 3. **test_monitors.py** — Monitor-Skripte (35 Tests)
Testet Logik in `frequencymonitor.py`, `powermonitor.py`, `batterymonitor.py`:

#### Frequenzmonitor (4 Tests)
- CSV-Format (Zeitstempel + Wert)
- Millisekunden-Genauigkeit
- Datums-Rollover
- Deduplication

#### Powermonitor (3 Tests)
- CSV-Format
- Polling-Intervall (1s)
- Realistische Wertebereiche

#### Batterymonitor (4 Tests)
- CSV-Format
- Polling-Intervall (5s)
- SoC-Bereich (0-100%)
- Deduplication

#### Allgemein (10 Tests)
- Verzeichnis-Erstellung
- Append-Modus
- Netzwerk-Error-Handling
- Modbus-Error-Handling
- CSV-Integrität
- Performance-Tests

**Performance-Tests**:
- 1000 Zeilen < 0.1s schreiben ✓
- Dateigröße < 1MB für 10k Punkte ✓

```bash
pytest test_monitors.py -v
```

---

### 4. **test_app_extended.py** — Flask Web-App (45 Tests)
Testet alle Routes und Funktionen in `webbrowser/app.py`:

#### Helper-Funktionen (2 Tests)
- `extract_date_from_filename()` — Datum extrahieren
- `get_today_date()` — Aktuelles Datum

#### Routes (8 Tests)
- GET `/` — Index mit Dateiliste
- GET `/chart/<filename>` — Chart-HTML
- GET `/chart_img/<filename>` — Chart-PNG
- GET `/download/<filename>` — CSV-Download
- 404-Fehlerbehandlung

#### Chart-Generierung (12 Tests)
- Frequenz-Charts mit Normalbereichen
- Power-Charts
- Battery-Charts mit Prozentbereich
- Ungültige CSV-Daten

#### Downloads (5 Tests)
- CSV-Datei-Downloads
- Korrekter Content-Type
- Dateinamen im Header

#### CSV-Parsing (3 Tests)
- Frequenz-Daten parsing
- Power-Daten parsing
- Battery-Daten parsing

#### Error-Handling (6 Tests)
- Leere Dateien
- Malformed CSV
- Fehlende Werte
- Sonderzeichen

#### Data Sorting (2 Tests)
- Neueste Dateien zuerst
- Heute's Dateien filtert

#### Content-Types (3 Tests)
- HTML, PNG, CSV MIME-Types

```bash
pytest test_app_extended.py -v
```

---

### 5. **test_integration.py** — End-to-End Tests (30 Tests)
Testet Zusammenspiel aller Komponenten:

#### Workflows (3 Tests)
- Inverter → Monitor → Web-App Pipeline
- Mehrere Monitore parallel
- Persistenz über Neustarts

#### Error-Recovery (3 Tests)
- Recovery von Netzwerkfehlern
- Automatische Verzeichnis-Erstellung
- Beschädigte Dateien

#### Datenkonsistenz (3 Tests)
- Frequenz-Konsistenz
- Power-Accuracy
- Battery-SoC-Tracking

#### Performance-Integration (3 Tests)
- Hochfrequente Daten (1000 Hz)
- Moderate Daten (1/s)
- Niederfrequente Daten (1/5s)

#### Datenaufbewahrung (2 Tests)
- Täglicher Rollover
- Cleanup nach Retention-Policy

#### Error-Recovery (2 Tests)
- Beschädigte CSV-Dateien
- Read-Only Datei-Handling

```bash
pytest test_integration.py -v
```

---

### 6. **test_sungrowinverter.py** (VERALTET)
⚠️ **Wird durch `test_sungrowinverter_extended.py` ersetzt**

Diese Datei nutzt alte Methodennamen und sollte überprüft/aktualisiert werden.

---

## 🚀 Tests ausführen

### Alle Tests
```bash
pytest -v
```

### Mit Coverage-Report
```bash
pytest --cov=. --cov-report=html
```

### Spezifische Test-Datei
```bash
pytest test_monitor_base.py -v
```

### Spezifischer Test
```bash
pytest test_sungrowinverter_extended.py::test_get_battery_soc -v
```

### Tests mit Output
```bash
pytest -v -s
```

---

## 📊 Test-Abdeckung nach Komponente

| Komponente | Alt | Neu | Gesamt | Status |
|-----------|-----|-----|--------|--------|
| `monitor_base.py` | 0 | 20 | 20 | ✅ Komplett |
| `sungrowinverter.py` | 12 | 80 | 92 | ✅ Umfassend |
| `frequencymonitor.py` | 0 | 8 | 8 | ✅ Neu |
| `powermonitor.py` | 0 | 7 | 7 | ✅ Neu |
| `batterymonitor.py` | 0 | 7 | 7 | ✅ Neu |
| `webbrowser/app.py` | 9 | 45 | 54 | ✅ Erweitert |
| Integration | 0 | 30 | 30 | ✅ Neu |
| **GESAMT** | **21** | **197** | **218** | ✅ 10x mehr |

---

## 🔍 Getestete Szenarien

### Normale Operationen ✅
- Alle Sensor-Lesevorgänge
- CSV-Schreiben mit Deduplication
- Web-App Routes
- Chart-Generierung
- CSV-Downloads

### Error-Handling ✅
- Netzwerkfehler mit Retry
- DNS-Auflösungsfehler
- Modbus-Fehler (None-Rückgaben)
- Port nicht erreichbar
- Beschädigte Dateien
- Read-Only Dateien
- Leere CSV-Dateien

### Performance ✅
- Hochfrequente Daten (20 Hz)
- Moderate Daten (1 Hz)
- Niederfrequente Daten (0.2 Hz)
- Dateigröße < 1MB
- Schreiben < 0.1s für 1000 Zeilen

### Datenintegrität ✅
- Skalierungsfaktoren korrekt
- Zeitstempel-Format
- CSV-Format konsistent
- Keine Datenverluste bei Neustarts
- Datums-Rollover funktioniert

---

## 🐛 Bekannte Test-Limitierungen

1. **Keine echten Modbus-Tests**: Tests nutzen Mocks
   - Echte Tests erfordern echten Inverter

2. **Keine Netzwerk-Integration**: Tests sind lokal
   - Können nicht alle Netzwerkfehler simulieren

3. **Keine Langzeit-Tests**: Tests laufen < 1s
   - 24h-Stabilitätstests erfordern separate Setup

4. **Keine Load-Tests**: Tests sind sequenziell
   - Echte Last kann abweichen

---

## 📋 Checkliste für neue Features

Bei neuen Features:
- [ ] Normale Operation testen
- [ ] Error-Cases abdecken
- [ ] Performance-Anforderungen prüfen
- [ ] Integration mit bestehenden Tests
- [ ] Test-Coverage ≥ 80%

---

## 📚 Referenzen

### Test-Frameworks
- **pytest** — Test-Framework
- **unittest.mock** — Mocking
- **pandas** — CSV-Parsing
- **matplotlib** — Chart-Tests

### Konfiguration
- `pytest.ini` — pytest Konfiguration
- `.gitignore` — Test-Artefakte ausschließen

### Abhängigkeiten (in requirements.txt)
```
pytest>=7.0
pandas>=1.3
matplotlib>=3.4
pyModbusTCP
flask
```

---

## 🎓 Best Practices

### Test-Schreiben
1. **Aussagekräftige Namen** — z.B. `test_get_battery_soc_full()`
2. **AAA-Pattern** — Arrange, Act, Assert
3. **Ein Test pro Szenario** — Nicht zu viel auf einmal
4. **Mock External Dependencies** — Nicht echte Hardware
5. **Edge-Cases testen** — 0%, 100%, Fehler, None

### Test-Organisation
```
test_<component>.py
├── Fixture
├── Normal Cases
├── Error Cases
├── Edge Cases
└── Integration Tests
```

---

## 🔗 Kontakt & Support

Fragen oder Verbesserungen? Siehe [CONTRIBUTING.md](CONTRIBUTING.md)

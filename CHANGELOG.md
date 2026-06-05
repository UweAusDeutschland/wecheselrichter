## [0.3.1] - 2026-06-05

### ✨ Added
- **Combined Monitor** (`combined_monitor.py`)
  - Unified monitoring process replacing three separate scripts
  - Consolidated sampling: frequency (50ms), power (1s), battery (5s) in single Python process
  - Single entry point for local development and Docker deployments

### 🔧 Fixed
- Replaced `frequencymonitor.py`, `powermonitor.py`, `batterymonitor.py` with `combined_monitor.py`
- Updated all references to old monitor files throughout documentation

Alle wichtigen Änderungen am Projekt werden hier dokumentiert.

## [0.3.0] - 2026-05-16

### ✨ Added
- Battery level monitoring (`batterymonitor.py`)
  - State of charge tracking (0-100%)
  - Automatic data storage with daily files
  - CSV-based persistence
- Comprehensive unit tests (17 total)
  - 10 Flask app tests (routes, chart generation, downloads)
  - 7 SungrowInverter tests (Modbus communication)
- GitHub Actions CI/CD workflow (`.github/workflows/tests.yml`)
- Test dependencies: pytest, pytest-flask, pytest-mock
- Complete documentation
  - README.md with quick start and API reference
  - CONTRIBUTING.md with development guidelines
  - DEPLOYMENT.md with deployment strategies

### 🔧 Fixed
- Docker line ending issues (CRLF → LF conversion)
  - Added `dos2unix` to Dockerfile
  - Fixed `entrypoint.sh` shell script
- Chart rendering for multiple data types
  - Frequency: Hz with tolerance zones
  - Power: Watt with proper scaling
  - Battery: Percentage with status zones

### 📝 Changed
- Enhanced Flask app to handle multiple data types dynamically
- Updated `entrypoint.sh` to run all three monitors
- Updated `docker-compose.yml` for battery monitoring

### 🧹 Cleaned up
- Fixed Dockerfile: added missing `powermonitor.py` in COPY
- Added `.gitignore` entries for pytest cache and test artifacts

---

## [0.2.0] - 2026-05-16

### ✨ Added
- PV Power monitoring (`powermonitor.py`)
  - Real-time power tracking (0-6000W)
  - Automatic data storage with daily files
  - Change detection to reduce file size
- Dynamic chart rendering in web app
  - Separate handling for frequency and power data
  - Proper Y-axis scaling per data type
  - Color-coded zones and annotations

### 🔧 Fixed
- Windows file encoding issues in Docker
- Missing `powermonitor.py` in docker-compose
- Chart image generation syntax errors

### 📝 Changed
- `app.py`: Refactored chart generation to be data-type aware
- `entrypoint.sh`: Now runs both frequency and power monitors

---

## [0.1.0] - 2026-05-16

### ✨ Added
- Initial project structure
- Sungrow SH6.0RT integration via Modbus TCP
- Frequency monitoring (`frequencymonitor.py`)
  - Continuous grid frequency monitoring (Hz)
  - Automatic daily CSV storage
  - Configurable sampling interval
- Web dashboard (Flask app)
  - File listing and browsing
  - Chart visualization with matplotlib
  - CSV download functionality
- Docker support
  - `Dockerfile` for containerization
  - `docker-compose.yml` for easy deployment
  - `entrypoint.sh` for container initialization
- Data persistence
  - Per-day CSV files
  - 90-day automatic retention
  - Configurable via `RETENTION_DAYS` env var

### 📦 Initial Dependencies
- Flask 2.x
- Pandas
- Matplotlib
- NumPy
- pyModbusTCP
- Gunicorn

---

## Format

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Fixed**: Bug fixes
- **Removed**: Removed features
- **Deprecated**: Soon-to-be removed features
- **Security**: Security fixes

## Versioning

Das Projekt folgt [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes (0.x.0)
- **MINOR**: New features, backward-compatible (x.1.0)
- **PATCH**: Bug fixes (x.x.1)

## Future Roadmap

- [ ] Humidity and temperature monitoring
- [ ] Advanced data analytics and trends
- [ ] Email/SMS alerts for critical values
- [ ] InfluxDB integration for time-series database
- [ ] Grafana dashboards
- [ ] REST API for external integrations
- [ ] Mobile app
- [ ] Multi-inverter support
- [ ] Historical data import tool
- [ ] Energy cost calculator

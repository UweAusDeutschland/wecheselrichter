# Beiträge zum Projekt 🚀

Danke, dass du zum Projekt beitragen möchtest! Hier sind die Guidelines.

## Development Setup

### 1. Repository klonen

```bash
git clone https://github.com/UweAusDeutschland/wecheselrichter.git
cd wecheselrichter
```

### 2. Python-Umgebung einrichten

```bash
# Virtuelle Umgebung erstellen (optional, aber empfohlen)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### 3. Tests vor dem Commit

```bash
# Alle Tests ausführen
python -m pytest -v

# Oder nur bestimmte Tests
python -m pytest test_app.py -v
```

## Code-Style Guidelines

### Python

- **Formatter:** Verwende PEP 8 Standard
- **Line Length:** Max. 100 Zeichen
- **Docstrings:** Nutze Google-Style Docstrings

```python
def get_frequency(self):
    """Returns grid frequency in Hz.
    
    Returns:
        float: Frequency in Hz or None on error
    """
    freq_raw = self._read_register('frequency')
    if freq_raw:
        return round(freq_raw[0] * 0.01, 2)
    return None
```

### Naming

- Funktionen/Variablen: `snake_case`
- Klassen: `PascalCase`
- Konstanten: `UPPER_SNAKE_CASE`

## Workflow für neue Features

### 1. Issue erstellen (Optional)

Beschreibe das Feature/Bug und warte auf Feedback.

### 2. Feature-Branch erstellen

```bash
git checkout -b feature/dein-feature-name
# oder
git checkout -b fix/dein-bug-name
```

### 3. Code schreiben + Tests

```bash
# Feature implementieren
# Tests schreiben
python -m pytest -v

# Syntax überprüfen
python -m py_compile deine_datei.py
```

### 4. Commit mit aussagekräftiger Message

```bash
git commit -m "Add feature: XYZ

- Detail 1
- Detail 2
- Detail 3"
```

**Commit-Message Format:**
- **Add:** Neue Features
- **Fix:** Bugfixes
- **Update:** Verbesserungen
- **Remove:** Funktionen entfernen
- **Refactor:** Code-Umstrukturierung
- **Docs:** Dokumentation

### 5. Push und Pull Request

```bash
git push origin feature/dein-feature-name
```

Erstelle einen Pull Request auf GitHub mit:
- Titel: Was wurde gemacht?
- Beschreibung: Warum? Wie wurde es getestet?
- Checklist der durchgeführten Tests

## Test-Standards

### Neues Feature = Neuer Test

Für jede neue Funktion sollte mindestens ein Test existieren:

```python
# test_app.py example
def test_new_feature():
    """Test: Beschreibung des Tests"""
    # Arrange
    test_data = {"key": "value"}
    
    # Act
    result = my_function(test_data)
    
    # Assert
    assert result == expected_value
```

### Test ausführen

```bash
# Einzelner Test
python -m pytest test_app.py::test_new_feature -v

# Mit Coverage
python -m pytest --cov=webbrowser test_app.py
```

## Dokumentation updaten

Bei neuen Features auch die Dokumentation updaten:

- `README.md` - Features/APIs hinzufügen
- `CONTRIBUTING.md` - Diese Datei, falls nötig
- Code-Kommentare - Komplexe Logik erklären

## Common Fixes

### Python Syntax-Fehler vor Commit

```bash
python -m py_compile *.py
python -m py_compile webbrowser/app.py
```

### Zeilenenden-Problem (CRLF vs LF)

```bash
# Git konfigurieren
git config core.autocrlf true  # Windows

# Bestehendes File fixen
git add .gitattributes
echo "*.sh text eol=lf" >> .gitattributes
```

### Docker nach Änderungen

```bash
# Neu bauen
docker-compose down
docker-compose up --build

# Logs anschauen
docker-compose logs -f
```

## Release-Prozess

1. Branch `main` muss alle Tests bestehen
2. Version in `__version__` updaten (falls nötig)
3. CHANGELOG.md aktualisieren
4. Tag erstellen: `git tag v1.0.0`
5. Push: `git push origin main --tags`

## Fragen?

- Erstelle ein Issue auf GitHub
- Schreib einen PR mit deinen Fragen im Description

Vielen Dank für deine Beiträge! 🙏

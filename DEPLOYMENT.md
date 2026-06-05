# Deployment Guide 🚀

Anleitung zum Deployment auf verschiedene Umgebungen.

## Docker (Recommended)

### Lokal mit Docker Compose

```bash
# Clone repo
git clone https://github.com/UweAusDeutschland/wecheselrichter.git
cd wecheselrichter

# Start
docker-compose up -d

# Logs anschauen (combined monitor process)
docker-compose logs -f sungrow-monitor-1

# Stop
docker-compose down
```

**Anmerkungen:**
- Port 5000 wird nach außen exposet
- `data/` Volume wird persistiert
- Container läuft im Hintergrund (`-d` flag)
- Der Monitor-Prozess wurde zu einem **kombinierten Monitor** zusammengefasst, der Frequenz-, Leistungs- und Batteriedaten in einer einzigen Python-Skript verarbeitet

### Auf Docker Hub deployen

```bash
# Login
docker login

# Build
docker build -t dein-username/wecheselrichter:1.0.0 .

# Push
docker push dein-username/wecheselrichter:1.0.0
```

## Linux/Debian (Bare Metal)

### Systemd Service

Erstelle `/etc/systemd/system/wecheselrichter.service`:

```ini
[Unit]
Description=Wechselrichter Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wecheselrichter
ExecStart=/usr/bin/python3 /home/pi/wecheselrichter/entrypoint.sh
Restart=always
RestartSec=10
Environment="INVERTER_HOST=modbusSungrow.fritz.box"

[Install]
WantedBy=multi-user.target
```

Start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wecheselrichter
sudo systemctl start wecheselrichter
sudo systemctl status wecheselrichter
```

### Cron für tägliches Backup

```bash
# Backup täglich um 23:55 Uhr
55 23 * * * tar -czf /backup/wecheselrichter-data-$(date +\%Y-\%m-\%d).tar.gz /home/pi/wecheselrichter/data/
```

## Kubernetes

### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wecheselrichter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wecheselrichter
  template:
    metadata:
      labels:
        app: wecheselrichter
    spec:
      containers:
      - name: wecheselrichter
        image: dein-username/wecheselrichter:1.0.0
        ports:
        - containerPort: 5000
        env:
        - name: INVERTER_HOST
          value: "192.168.1.100"
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: wecheselrichter-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: wecheselrichter-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: wecheselrichter
spec:
  selector:
    app: wecheselrichter
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl get pods
```

## Monitoring & Logging

### Container-Logs

```bash
# Live-Logs (combined monitor)
docker-compose logs -f sungrow-monitor-1

# Letzte 100 Zeilen
docker-compose logs --tail=100 sungrow-monitor-1

# Nur Errors
docker-compose logs | grep ERROR sungrow-monitor-1
```

### Health-Check

```bash
# Web-App antwortet?
curl http://localhost:5000

# CSV-Dateien werden erstellt? (alle Monitor-Daten)
ls -la data/
tail -f data/frequency_*.csv  # Frequenzdaten
tail -f data/power_*.csv    # Leistungsdaten
tail -f data/battery_*.csv  # Batteriedaten

# Combined Monitor läuft?
docker exec wecheselrichter-sungrow-monitor-1 ps aux | grep combined_monitor.py

# Modbus-Verbindung?
docker exec wecheselrichter-sungrow-monitor-1 nc -zv modbusSungrow.fritz.box 502
```

### Disk-Space-Management

```bash
# Große Dateien anzeigen
du -sh data/*

# Alte Dateien löschen (manuell)
find data/ -name "*.csv" -mtime +90 -delete

# Oder automatisch via RETENTION_DAYS
docker-compose.yml:
  environment:
    - RETENTION_DAYS=60
```

## Backup-Strategie

### Täglich

```bash
# Backup alle 24h
cp -r data/ /backup/data-$(date +%Y-%m-%d)/
```

### Automatisch mit Docker

```yaml
# docker-compose.yml - backup service hinzufügen
services:
  backup:
    image: alpine
    volumes:
      - ./data:/data
      - ./backups:/backups
    command: /bin/sh -c 'while true; do tar -czf /backups/backup-$(date +%Y-%m-%d-%H).tar.gz /data; sleep 86400; done'
```

## Update-Prozess

### Neue Version deployen

```bash
# Repo updaten
git pull origin main

# Neu bauen
docker-compose down
docker-compose up --build -d

# Logs überprüfen
docker-compose logs -f
```

### Rollback bei Fehlern

```bash
# Alte Version starten
git checkout v1.0.0
docker-compose up --build -d

# Oder mit Tag direkt
docker run -p 5000:5000 dein-username/wecheselrichter:1.0.0
```

## Performance-Tipps

### CPU-Limits

```yaml
# docker-compose.yml
services:
  sungrow-monitor:
    cpu_shares: 512
    mem_limit: 256m
```

### Sampling-Frequenz reduzieren

```bash
# Weniger oft auslesen → weniger CPU
# combined_monitor.py (alle Intervalle zusammen)
# frequency_interval, power_interval, battery_interval anpassen
```

### Datenbank statt CSV

Für größere Deployments: CSV → InfluxDB/Prometheus

## Troubleshooting

### Container crasht sofort

```bash
docker-compose logs
# Checken: INVERTER_HOST erreichbar?
# Checken: Port 502 offen?
```

### Web-App nicht erreichbar

```bash
# Port gemappt?
docker ps | grep 5000

# Firewall?
ufw allow 5000

# Container laufen?
docker-compose ps
```

### Speicher voll

```bash
# Disk-Usage
df -h

# Alte Dateien löschen
find data/ -mtime +90 -delete

# Oder erhöhen in RETENTION_DAYS
```

## Support

Probleme beim Deployment? Öffne ein Issue:
https://github.com/UweAusDeutschland/wecheselrichter/issues

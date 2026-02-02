# InfluxDB + Grafana Setup Guide

This guide walks through setting up InfluxDB and Grafana for real-time monitoring of Pico voltage data.

## Prerequisites

- Python 3.7+
- Docker (recommended) or local InfluxDB installation

## Option 1: Docker Setup (Recommended)

### 1. Install Docker Desktop
Download from: https://www.docker.com/products/docker-desktop/

### 2. Start InfluxDB Container

```powershell
docker run -d -p 8086:8086 `
  --name influxdb `
  -v influxdb-data:/var/lib/influxdb2 `
  -e DOCKER_INFLUXDB_INIT_MODE=setup `
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin `
  -e DOCKER_INFLUXDB_INIT_PASSWORD=adminpass123 `
  -e DOCKER_INFLUXDB_INIT_ORG=pico `
  -e DOCKER_INFLUXDB_INIT_BUCKET=pico_voltage `
  -e DOCKER_INFLUXDB_INIT_RETENTION=0 `
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-token `
  influxdb:2.7
```

### 3. Start Grafana Container

```powershell
docker run -d -p 3000:3000 `
  --name grafana `
  -v grafana-data:/var/lib/grafana `
  grafana/grafana:latest
```

### 4. Verify Containers Running

```powershell
docker ps
```

You should see both `influxdb` and `grafana` running.

---

## Option 2: Local Installation

### 1. Install InfluxDB

Download from: https://www.influxdata.com/downloads/

Windows installer will set up InfluxDB as a service.

### 2. Configure InfluxDB

Open http://localhost:8086 and complete setup:
- Username: `admin`
- Password: `adminpass123`
- Organization: `pico`
- Bucket: `pico_voltage`

### 3. Install Grafana

Download from: https://grafana.com/grafana/download

Windows installer available.

---

## Configure Grafana

### 1. Access Grafana

Open: http://localhost:3000

Default login:
- Username: `admin`
- Password: `admin`

Change password when prompted.

### 2. Add InfluxDB Data Source

1. Go to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **InfluxDB**
4. Configure:
   - **Name**: `InfluxDB`
   - **Query Language**: `Flux`
   - **URL**: `http://localhost:8086`
   - **Organization**: `pico`
   - **Token**: `my-super-secret-token` (or your token)
   - **Default Bucket**: `pico_voltage`
5. Click **Save & Test**

### 3. Import Dashboard

1. Go to **Dashboards** → **Import**
2. Click **Upload JSON file**
3. Select: `tools/grafana_dashboard.json`
4. Select data source: `InfluxDB`
5. Click **Import**

---

## Install Python Dependencies

```powershell
pip install influxdb-client pyserial
```

---

## Start Live Monitoring

### 1. Configure Pico for USB Streaming

Edit `src/config.py`:

```python
LOGGING_MODE = "USB_STREAM"
```

Upload to Pico and run `src/main.py`.

### 2. Find Pico COM Port

**Windows:**
```powershell
# Check Device Manager → Ports (COM & LPT)
# Or use:
Get-CimInstance -ClassName Win32_SerialPort | Select Name,DeviceID
```

Pico typically appears as `COM9`, `COM4`, etc.

**Linux:**
```bash
ls /dev/ttyACM*
```

### 3. Start Live Monitor

```powershell
python tools/live_monitor.py --port COM9
```

Options:
```powershell
python tools/live_monitor.py `
  --port COM9 `
  --influx-url http://localhost:8086 `
  --token my-super-secret-token `
  --org pico `
  --bucket pico_voltage
```

### 4. View Dashboard

Open Grafana: http://localhost:3000

Navigate to **Pico Voltage Dip Monitor** dashboard.

You should see:
- Real-time voltage graphs
- Baseline tracking
- Dip events
- Statistics

---

## Dashboard Features

### Panels

1. **Voltage Medians (All Channels)** - Real-time voltage over time with statistics
2. **Baseline Tracking** - Reference voltage for each channel
3. **Voltage Dip Events** - Bar chart of dip drops
4. **Current Voltage** - Gauge showing latest readings
5. **Dip Count by Channel** - Pie chart of dip distribution
6. **Dip Statistics** - Summary metrics (avg drop, max drop, duration)

### Time Ranges

- Default: Last 15 minutes
- Adjustable in top-right corner
- Auto-refresh every 5 seconds

### Filters

Click on channel legends to show/hide specific channels.

---

## Troubleshooting

### InfluxDB Connection Failed

Check containers:
```powershell
docker logs influxdb
docker logs grafana
```

Restart if needed:
```powershell
docker restart influxdb grafana
```

### No Data in Grafana

1. Verify live_monitor.py is running without errors
2. Check InfluxDB data:
   - Open http://localhost:8086
   - Go to **Data Explorer**
   - Query: `from(bucket: "pico_voltage") |> range(start: -1h)`
3. Verify Pico is in USB_STREAM mode
4. Check serial connection (correct COM port)

### Serial Port Busy

Close other programs using the port (Thonny, Arduino IDE, etc.)

---

## Data Retention

Default: Forever (retention = 0)

To change retention:
```powershell
docker exec influxdb influx bucket update `
  --name pico_voltage `
  --retention 7d `
  --org pico
```

Retention options:
- `1h` = 1 hour
- `24h` = 24 hours
- `7d` = 7 days
- `30d` = 30 days
- `0` = forever

---

## Stopping Services

```powershell
# Stop containers
docker stop influxdb grafana

# Start again later
docker start influxdb grafana

# Remove completely
docker rm -f influxdb grafana
docker volume rm influxdb-data grafana-data
```

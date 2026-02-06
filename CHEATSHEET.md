# Pico Voltage Dip Monitor - Quick Reference Card

## 🚀 Getting Started (5 Minutes)

**Using Thonny?** See detailed guide: [docs/THONNY_SETUP.md](docs/THONNY_SETUP.md)

1. **Upload to Pico:** Copy all `src/*.py` files to Pico (via Thonny: right-click → Upload to /)
2. **Edit config:** Set `LOGGING_MODE` in `src/config.py` on Pico
3. **Connect:** PLC/MODEM/BATTERY to GP26/27/28, GND common
4. **Run:** Press F5 in Thonny (or `python main.py` via terminal)

## 📊 Logging Modes

| Mode | Best For | Flash Wear | Storage |
|------|----------|------------|---------|
| `USB_STREAM` | Development | None | Unlimited (InfluxDB) |
| `EVENT_ONLY` | Production | Minimal | Months |
| `FULL_LOCAL` | Testing | Moderate | 1 hour buffer |

## ⚙️ Key Configuration (`src/config.py`)

```python
LOGGING_MODE = "USB_STREAM"      # Choose mode
DIP_THRESHOLD_V = 0.10           # Dip detection (100mV drop)
MIN_V = 0.6                      # Voltage range start
MAX_V = 1.8                      # Voltage range end
STABLE_SPAN_V = 0.03             # Noise tolerance (30mV)
```

## 🔌 Hardware Connections

```
PLC (+)     → GP26 (ADC0)
MODEM (+)   → GP27 (ADC1)
BATTERY (+) → GP28 (ADC2)
All GND     → Pico GND

⚠️ Max 3.3V on ADC pins!
```

## 🛠️ PC Tools Cheat Sheet

**⚠️ IMPORTANT:** Close Thonny before using PC tools (serial port conflict!)

### Install Dependencies

**Minimal (Grafana users only):**
```powershell
pip install influxdb-client pyserial
```

**Full (with matplotlib plotting):**
```powershell
pip install -r requirements.txt
pip install matplotlib
```

### Download Data from Pico

```powershell
# Download all CSV files from Pico flash
python tools/download_from_pico.py --port COM9 --output ./data
```

**Note:** Only works with EVENT_ONLY or FULL_LOCAL modes (USB_STREAM doesn't save to flash)

### Validate CSV Files

```powershell
python tools/validate_csv.py data/pico_medians.csv
python tools/validate_csv.py data/pico_dips.csv
```

### Visualize Data (Matplotlib)

**Quick test with sample data:**
```powershell
python tools/plot_medians.py examples/pico_medians_sample.csv
python tools/plot_dips.py examples/pico_dips_sample.csv
```

**Plot real data:**
```powershell
python tools/plot_medians.py data/pico_medians.csv
python tools/plot_dips.py data/pico_dips.csv
```

**Create sample dips for testing:**
```powershell
# Create CSV only (no InfluxDB)
python tools/create_sample_dips.py --csv-only

# Then plot it
python tools/plot_dips.py "$env:TEMP\sample_dips.csv"
```

### Data Quality Report

```powershell
python tools/data_quality_report.py data/pico_medians.csv
```

### Test Without Hardware

```powershell
# Simulate 60 seconds with 10 dips
python tools/simulate_dips.py --duration 60 --dips 10

# Plot the simulated data
python tools/plot_medians.py "$env:TEMP\sim_medians.csv"
```

### Live InfluxDB Streaming (USB_STREAM mode)

**Start InfluxDB + Grafana (Docker):**
```powershell
# First time setup
docker run -d -p 8086:8086 --name influxdb influxdb:2.7
docker run -d -p 3000:3000 --name grafana grafana/grafana:latest

# Subsequent starts
docker start influxdb
docker start grafana
```

**Stream Pico data to InfluxDB:**
```powershell
python tools/live_monitor.py --port COM9 \
  --influx-url http://localhost:8086 \
  --token YOUR_INFLUX_TOKEN \
  --org pico \
  --bucket pico_voltage
```

**Access dashboards:**
- InfluxDB: http://localhost:8086
- Grafana: http://localhost:3000 (admin/admin)

**Import dashboard:**
- Import `tools/grafana_dashboard.json` in Grafana UI

### Upload Sample Data to InfluxDB

```powershell
# Upload sample dips for testing Grafana
python tools/create_sample_dips.py \
  --influx-url http://localhost:8086 \
  --token YOUR_TOKEN \
  --org pico \
  --bucket pico_voltage
```

### Find Serial Ports

```powershell
python -m serial.tools.list_ports
```

### Debug Probe (Advanced)

**Stream via Debug Probe (eliminates serial conflicts):**
```powershell
# Set USE_DEBUG_PROBE = True in config.py first

# Find ports
python -m serial.tools.list_ports
# Example output:
#   COM9 - Pico USB (use for Thonny)
#   COM8 - Debug Probe (use for live_monitor)

# Stream via Debug Probe
python tools/live_monitor.py --port COM8 --token YOUR_TOKEN

# Upload code via Thonny on COM9 - no conflicts!
```

**See:** [docs/DEBUG_PROBE.md](docs/DEBUG_PROBE.md)

## 📁 Output Files (on Pico)

| File | Mode | Content |
|------|------|---------|
| `/pico_dips.csv` | All | Dip events (immediate write) |
| `/pico_medians.csv` | FULL_LOCAL | Voltage history (1 hr buffer) |
| `/pico_baseline_snapshots.csv` | EVENT_ONLY | Baseline every 10 min |

## 📈 Expected Output

### Console Status (Every 60s)
```
60.0s  PLC: stable=1 base=1.274 dip=0  MODEM: stable=1 base=1.281 dip=0
```

### Stats Summary
```
STATS SUMMARY @ 120.0s uptime
Samples:         36,000 (300.0/s)
Medians:         1,200 computed, 1,200 logged
Dips detected:   2 total
Memory:          123,456 bytes free
```

### Dip Detection
```
18.420s  DIP START  BATTERY  baseline=1.274V  now=1.112V
18.470s  DIP END    BATTERY  dur=50ms  min=1.112V  drop=0.162V
```

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Random values" | Normal when disconnected. Add batteries or pulldown resistor |
| "No files on Pico" | View → Files → Raspberry Pi Pico in Thonny |
| "Device busy" | Run → Stop/Restart backend, or unplug/replug |
| "Configuration errors" | Check `config.py` values (MIN_V < MAX_V, etc.) |
| Serial port not found | Check Device Manager (Windows) or `ls /dev/ttyACM*` (Linux) |

## 🎯 Pre-Dip Hardware Testing Checklist

- [ ] Upload all files to Pico
- [ ] Configure logging mode
- [ ] Run with stable batteries overnight
- [ ] Download and validate CSVs
- [ ] Generate data quality report
- [ ] Test simulator with various dip patterns
- [ ] Set up InfluxDB + Grafana (optional)
- [ ] Verify stats tracking works
- [ ] Check file size limits in FULL_LOCAL mode
- [ ] Test all three logging modes

## 📚 Documentation

| Doc | Purpose |
|-----|---------|
| [QUICKSTART.md](docs/QUICKSTART.md) | 5-minute setup |
| [SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md) | InfluxDB guide |
| [README.md](README.md) | Full overview |
| [architecture.md](docs/architecture.md) | System design |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | What was built |

## 🐛 Debug Commands

```powershell
# Check syntax errors
python -m py_compile tools/live_monitor.py

# Test simulator
python tools/simulate_dips.py --duration 30 --dips 5

# Validate simulated output
python tools/validate_csv.py /tmp/sim_dips.csv
python tools/plot_dips.py /tmp/sim_dips.csv
```

## ⚡ Performance

- **Sampling:** 100 Hz (10 ms)
- **Latency:** 10-20 ms dip detection
- **Channels:** 3 simultaneous
- **Memory:** ~40 KB
- **Flash (EVENT_ONLY):** <100 writes/day
- **Flash (FULL_LOCAL):** ~86,400 writes/day

## 🎓 Advanced Usage

### Custom Dip Thresholds per Channel
Edit `dip_detector.py` to use channel-specific thresholds

### Export to Different Formats
Parse CSV to JSON/SQLite/Parquet for analysis tools

### Continuous Integration
Use simulator in CI to validate detector logic changes

### Multi-Pico Setup
Run multiple Picos with different serial ports

## 📞 Getting Help

1. Check [troubleshooting.md](docs/troubleshooting.md)
2. Run data quality report
3. Validate CSVs for corruption
4. Test with simulator
5. Check stats output for anomalies

---

**Quick Links:**
- Setup: [QUICKSTART.md](docs/QUICKSTART.md)
- InfluxDB: [SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)
- Issues: [troubleshooting.md](docs/troubleshooting.md)

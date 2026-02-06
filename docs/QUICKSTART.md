# Quick Start Guide

Get your Pico voltage monitoring system running in minutes.

**Using Thonny IDE?** Skip to the comprehensive: [THONNY_SETUP.md](THONNY_SETUP.md)

## Prerequisites

- Raspberry Pi Pico 2 with MicroPython installed
- Thonny IDE (or similar)
- 3 AAA batteries for testing (optional)

---

## Step 1: Upload Code to Pico

### Copy All Files from `src/` Folder

Using Thonny:

1. Open Thonny
2. Connect Pico via USB
3. Select interpreter: **MicroPython (Raspberry Pi Pico)**
4. For each file in `src/`:
   - Open the file in Thonny
   - **File** → **Save as...**
   - Select **Raspberry Pi Pico**
   - Save with same filename

Files to upload:
- `main.py`
- `config.py`
- `adc_sampler.py`
- `channel_state.py`
- `dip_detector.py`
- `median_logger.py`
- `storage.py`
- `stats_tracker.py`
- `utils.py`

### Or Use Command Line

```powershell
# Install ampy
pip install adafruit-ampy

# Upload all files (replace COM3 with your port)
Get-ChildItem src\*.py | ForEach-Object {
    ampy --port COM3 put $_.FullName
}
```

---

## Step 2: Choose Logging Mode

Edit `config.py` on the Pico:

### Option A: USB Streaming (For InfluxDB + Grafana)

```python
LOGGING_MODE = "USB_STREAM"
```

**Pros:** Real-time dashboards, unlimited storage
**Cons:** Requires PC connected

### Option B: Full Local Logging

```python
LOGGING_MODE = "FULL_LOCAL"
```

**Pros:** Standalone operation
**Cons:** Limited flash storage (~1 hour of data)

### Option C: Event-Only Logging (Recommended for Production)

```python
LOGGING_MODE = "EVENT_ONLY"
```

**Pros:** Minimal flash wear, captures important events
**Cons:** No continuous voltage history

---

## Step 3: Connect Hardware

### Basic Test (No Batteries)

Just connect Pico to USB. ADC pins will float (normal).

### With Batteries (Recommended)

```
PLC (+)     → GP26
MODEM (+)   → GP27  
BATTERY (+) → GP28
All GND     → Pico GND
```

**⚠️ WARNING:** Never exceed 3.3V on ADC pins!

For fresh AAA (1.5V): Use voltage divider or rechargeable NiMH (1.2V).

See: [docs/wiring.md](docs/wiring.md)

---

## Step 4: Run

### In Thonny

1. Open `main.py`
2. Press **F5** (Run)
3. Watch output in console

Expected output:
```
Configuration validated successfully.
============================================================
PICO VOLTAGE DIP MONITOR
============================================================
Logging mode:    USB_STREAM
Sampling:        10 ms (100 Hz)
Channels:        PLC, MODEM, BATTERY
...
```

### Auto-Run on Boot

Rename `main.py` to `main.py` (already correct).

Pico will auto-run on power-up.

---

## Step 5: Verify It's Working

### Check Status Messages

Every 60 seconds you'll see:
```
60.0s  PLC: stable=1 base=1.274 dip=0  MODEM: stable=1 base=1.281 dip=0  ...
```

- `stable=1`: Channel is stable ✓
- `base=X.XXX`: Baseline voltage established
- `dip=0`: No active dip

### View Statistics

Every 60 seconds:
```
============================================================
STATS SUMMARY @ 120.5s uptime
============================================================
Samples:         12000 (100.0/s)
Medians:         400 computed, 400 logged
Memory:          123456 bytes free
...
```

---

## Step 6: View Data

### USB Streaming Mode

Setup InfluxDB + Grafana: [docs/SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)

Then:
```powershell
python tools/live_monitor.py --port COM3
```

View dashboard: http://localhost:3000

### Local Logging Mode

Download CSV files:
```powershell
python tools/download_from_pico.py --port COM3 --output ./data
```

Visualize:
```powershell
python tools/plot_medians.py data/pico_medians.csv
python tools/plot_dips.py data/pico_dips.csv
```

---

## Testing Without Hardware

Simulate dips on your PC:

```powershell
python tools/simulate_dips.py --duration 60 --dips 10
```

This creates synthetic data in `/tmp/` for testing analysis tools.

---

## Troubleshooting

### "Configuration errors"

Check `config.py` values are valid:
- `MIN_V < MAX_V`
- `VREF = 3.3`
- Valid `LOGGING_MODE`

### "Random values when disconnected"

This is normal - ADC pins float without load.

Solutions:
- Connect batteries
- Add 100kΩ pulldown resistor to GND
- Ignore until hardware connected

### "No files appear on Pico"

View files in Thonny:
**View** → **Files** → **Raspberry Pi Pico**

### "Device is busy"

In Thonny:
**Run** → **Stop/Restart backend**

Or unplug and replug Pico.

---

## Next Steps

1. **Run overnight test** - Verify 24h stability
2. **Build dip hardware** - Voltage divider + controllable load
3. **Set up InfluxDB** - Real-time monitoring
4. **Tune parameters** - Adjust thresholds in `config.py`

---

## Quick Reference

### File Locations (on Pico)

- `/pico_medians.csv` - Voltage history (FULL_LOCAL mode)
- `/pico_dips.csv` - Dip events (all modes)
- `/pico_baseline_snapshots.csv` - Baseline log (EVENT_ONLY mode)

### Key Configuration

Edit `src/config.py`:

```python
LOGGING_MODE = "USB_STREAM"      # or EVENT_ONLY, FULL_LOCAL
DIP_THRESHOLD_V = 0.10           # Dip detection threshold
TICK_MS = 10                     # Sampling rate (don't change)
```

### Tools

```powershell
# Download data
python tools/download_from_pico.py --port COM3

# Validate CSV
python tools/validate_csv.py data/pico_medians.csv

# Plot data
python tools/plot_medians.py data/pico_medians.csv
python tools/plot_dips.py data/pico_dips.csv

# Data quality report
python tools/data_quality_report.py data/pico_medians.csv

# Simulate dips
python tools/simulate_dips.py --duration 30 --dips 5

# Live monitor to InfluxDB
python tools/live_monitor.py --port COM3
```

---

## Support

See full documentation:
- [README.md](../README.md) - Overview
- [docs/architecture.md](docs/architecture.md) - System design
- [docs/troubleshooting.md](docs/troubleshooting.md) - Common issues
- [docs/SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md) - InfluxDB guide

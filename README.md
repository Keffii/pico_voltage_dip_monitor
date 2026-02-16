# Pico Voltage Dip Monitor (Pico 2)

**High-frequency battery voltage monitoring system** for detecting fast voltage dips with MicroPython on Raspberry Pi Pico 2.

Samples PLC, MODEM, BATTERY channels every 10 ms (100 Hz), computes 100 ms medians, tracks baseline stability, and detects voltage dips with millisecond precision.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Logging Modes](#logging-modes)
- [Hardware Setup](#hardware)
- [Configuration](#configuration)
- [PC Tools](#tools)
- [Output Files](#output-files)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

---

## Features

✅ **100 Hz sampling** - 10 ms tick rate for low-latency dip detection  
✅ **Multi-channel** - Monitor 3 independent voltage sources simultaneously  
✅ **Stability gating** - Only logs stable, valid readings  
✅ **Baseline tracking** - Adaptive baseline from stable median history  
✅ **Dip detection** - Sub-second dip start/end events with hysteresis  
✅ **Three logging modes:**
  - **USB_STREAM** - Real-time streaming to InfluxDB + Grafana
  - **EVENT_ONLY** - Minimal flash wear, event-based logging
  - **FULL_LOCAL** - Complete local CSV logging with circular buffer  
✅ **Statistics tracking** - Uptime, memory, sample counts, file sizes  
✅ **Data validation** - CSV validation and quality reporting tools  
✅ **Simulation** - Test dip detection without hardware  
✅ **Professional dashboards** - Pre-built Grafana visualization

---

## Prerequisites

### Hardware
- **Raspberry Pi Pico 2** (RP2350 microcontroller)
- **USB cable** (micro-USB for Pico 2)
- **Voltage sources** (0.6V - 3.3V range for default config)
  - AAA batteries (1.0-1.5V) work great for testing
  - Or any DC source within safe range
- **Jumper wires** for connections
- **Optional:** Battery holder, capacitors (100nF), pull-down resistors (100kΩ)

### Pico Software
- **MicroPython** firmware (v1.20+ with RP2350 support)
- Install via Thonny IDE (easiest) or download from micropython.org

### PC Software (Windows/Mac/Linux)
- **Thonny IDE** (recommended) - https://thonny.org/
- **Python 3.7+** (for analysis tools)
- **Git** (optional, for cloning repository)

### Optional (for InfluxDB/Grafana mode)
- **Docker Desktop** - https://www.docker.com/products/docker-desktop/
- Or standalone InfluxDB 2.x and Grafana installations

### Optional (for offline CSV plotting)
- **matplotlib** - Only needed if analyzing CSV files offline
- Not required if using Grafana for all visualization

### Optional (for improved development workflow)
- **Raspberry Pi Debug Probe** (~$12) - Eliminates serial port conflicts during development
- See [docs/DEBUG_PROBE.md](docs/DEBUG_PROBE.md) for setup

### Optional (for OLED display)
- **SSD1351 MicroPython driver (nano-gui)**:
  https://github.com/peterhinch/micropython-nano-gui/tree/master/drivers/ssd1351

---

## Quick Start

### 🚀 5-Minute Setup with Thonny (Recommended)

**Complete step-by-step guide:** [docs/THONNY_SETUP.md](docs/THONNY_SETUP.md)

1. **Install Thonny IDE** - Download from https://thonny.org/
2. **Install MicroPython on Pico:**
   - Hold BOOTSEL button, plug USB
   - In Thonny: Tools → Options → Interpreter → Install MicroPython
3. **Upload code:**
   - View → Files (shows Pico files)
   - Drag all files from `src/` folder to Pico
4. **Edit config.py on Pico:**
   - Set `LOGGING_MODE = "EVENT_ONLY"` (standalone) or `"USB_STREAM"` (with PC)
5. **Connect hardware:**
   - Battery (+) → GP26, GP27, GP28
   - Battery (-) → Pico GND
6. **Run:** Press F5 in Thonny

✅ Done! Pico starts monitoring and logging dips.

### 📊 Advanced: InfluxDB + Grafana Setup

For real-time dashboards with unlimited storage:

**Complete guide:** [docs/SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)

1. Install Docker Desktop
2. Start InfluxDB container
3. Start Grafana container
4. Configure Pico: `LOGGING_MODE = "USB_STREAM"`
5. Run: `python tools/live_monitor.py --port COM3 --bucket pico_voltage`
6. Import Grafana dashboard from `tools/grafana_dashboard.json`

---

## Installation

### Option 1: Clone Repository (Recommended)

```powershell
git clone https://github.com/yourusername/pico-voltage-dip-monitor.git
cd pico-voltage-dip-monitor
```

### Option 2: Download ZIP

Download from GitHub → Extract → Open in Thonny

### Install PC Tool Dependencies

**For Grafana users (minimal install):**
```powershell
pip install influxdb-client pyserial
```

**For offline CSV analysis (full install):**
```powershell
pip install -r requirements.txt
pip install matplotlib
```

This installs:
- `influxdb-client` - InfluxDB integration (required for USB_STREAM mode)
- `pyserial` - USB serial communication (required for live_monitor.py)
- `matplotlib` - Data visualization (optional, only for offline CSV plotting)

---

## Hardware Setup

### Wiring Diagram

```
┌─────────────────────────────────────────┐
│  Raspberry Pi Pico 2                    │
│                                         │
│  GP26 (ADC0) ←─── PLC (+)              │
│  GP27 (ADC1) ←─── MODEM (+)            │
│  GP28 (ADC2) ←─── BATTERY (+)          │
│                                         │
│  GND ←────────┬─── PLC (-)              │
│               ├─── MODEM (-)            │
│               └─── BATTERY (-)          │
│                                         │
│  VBUS ←─────── USB Power               │
└─────────────────────────────────────────┘

⚠️ CRITICAL: Max 3.3V on ADC pins!
⚠️ Common ground required for all sources
```

### Prototype Setup (AAA Batteries)

1. **PLC:** Connect (+) to GP26, (-) to GND
2. **MODEM:** Connect (+) to GP27, (-) to GND  
3. **BATTERY:** Connect (+) to GP28, (-) to GND

**Recommendations:**
- Use battery holder for stable connections
- Add 100nF capacitor from each ADC pin to GND (reduces noise)
- Optional: 100kΩ pull-down resistor to prevent floating when disconnected

**Higher Voltages:** For 5V, 12V, etc., use voltage dividers. See [docs/wiring.md](docs/wiring.md)

**⚠️ Safety:** Never exceed 3.3V on ADC pins or you'll damage the Pico!

---

## Logging Modes

Choose the mode that fits your use case. Edit `LOGGING_MODE` in `src/config.py` on the Pico.

### USB_STREAM - Real-Time Dashboards (Recommended for Development)

```python
LOGGING_MODE = "USB_STREAM"
```

**What it does:**  
Streams all data over USB serial → PC → InfluxDB → Grafana dashboard

**Benefits:**
- ✅ Real-time visualization with professional dashboards
- ✅ Unlimited storage (time-series database)
- ✅ Zero flash wear on Pico
- ✅ Advanced queries and analysis

**Drawbacks:**
- ❌ Requires PC connected 24/7
- ❌ Needs InfluxDB setup (Docker recommended)

**Setup guide:** [docs/SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)

**Use when:** Development, testing, research, or when PC is always available

---

### EVENT_ONLY - Standalone Operation (Recommended for Production)

```python
LOGGING_MODE = "EVENT_ONLY"
```

**What it does:**  
Logs only critical events to Pico flash:
- Voltage dips (when detected)
- Baseline snapshots (every 10 minutes)

**Benefits:**
- ✅ Minimal flash wear (~500 lines/day = months of runtime)
- ✅ Standalone operation (no PC needed)
- ✅ Captures all critical events
- ✅ Perfect for long-term monitoring

**Drawbacks:**
- ❌ No continuous voltage history
- ❌ Must download CSVs manually from Pico

**Use when:** Production deployments, battery aging studies, remote monitoring

---

### FULL_LOCAL - Complete History (Debug/Testing)

```python
LOGGING_MODE = "FULL_LOCAL"
```

**What it does:**  
Logs ALL 100ms voltage medians to Pico flash with circular buffer

**Benefits:**
- ✅ Standalone operation
- ✅ Complete voltage history
- ✅ Fixed storage (1 hour = ~3600 lines = 100KB)
- ✅ Automatic old data removal

**Drawbacks:**
- ❌ Moderate flash wear (~86,400 writes/day)
- ❌ Limited to 1 hour of history

**Use when:** Short-term testing, debugging, verification

---

### Comparison Table

| Feature | USB_STREAM | EVENT_ONLY | FULL_LOCAL |
|---------|------------|------------|------------|
| Storage | Unlimited (InfluxDB) | Months (flash) | 1 hour (flash) |
| Flash wear | None | Minimal | Moderate |
| Standalone | ❌ (needs PC) | ✅ | ✅ |
| Real-time viz | ✅ (Grafana) | ❌ | ❌ |
| Data resolution | Full (100ms) | Events only | Full (100ms) |
| Setup complexity | High | Low | Low |

---

## Hardware

### Requirements

- **Raspberry Pi Pico 2** (RP2350)
- **MicroPython** firmware
- **Voltage sources** (0-3.3V)

### Prototype Setup

```
PLC (+)     → GP26 (ADC0)
MODEM (+)   → GP27 (ADC1)
BATTERY (+) → GP28 (ADC2)
All GND     → Pico GND (common ground)
```

**Full wiring guide:** [docs/wiring.md](docs/wiring.md)

---

## Output Files

### Files Created on Pico Flash

**All modes create:**
- `/pico_dips.csv` - Dip events with complete details
  - Columns: `channel`, `dip_start_s`, `dip_end_s`, `duration_ms`, `baseline_V`, `min_V`, `drop_V`
  - Example: `BATTERY,18.420,18.470,50,1.274,1.112,0.162`

**EVENT_ONLY and FULL_LOCAL modes also create:**
- `/pico_baseline_snapshots.csv` - Baseline snapshots (every 10 minutes by default)
  - Columns: `time_s`, `channel`, `baseline_V`
  - Tracks baseline drift over time

**FULL_LOCAL mode also creates:**
- `/pico_medians.csv` - 100ms voltage medians (circular buffer)
  - Columns: `time_s`, `channel`, `median_V`
  - Example: `12.300,PLC,1.274`
  - Automatically rotates when file exceeds 100KB or 3600 lines

### Downloading Files from Pico

**Method 1: Using Thonny (Easiest)**
1. View → Files (Ctrl+3)
2. Right-click CSV file on Pico (right panel)
3. Download to /your/computer/

**Method 2: Command Line Tool**
```powershell
python tools/download_from_pico.py --port COM3 --output ./data
```

**⚠️ Important:** Close Thonny before using command-line tools (serial port conflict)

### File Formats

Complete CSV schemas: [docs/data-formats.md](docs/data-formats.md)

---

## Tools

All PC-side tools are in the `tools/` directory.

**⚠️ IMPORTANT:** Close Thonny IDE before running tools that use serial port!

### Installation

```powershell
pip install -r requirements.txt
```

### Data Download & Analysis

**Note:** These tools require matplotlib. Skip if using Grafana exclusively.

**Complete plotting guide:** [docs/PLOTTING.md](docs/PLOTTING.md)

```powershell
# Download all CSV files from Pico to your PC
python tools/download_from_pico.py --port COM3 --output ./data

# Validate CSV file integrity (no matplotlib needed)
python tools/validate_csv.py data/pico_medians.csv
python tools/validate_csv.py data/pico_dips.csv

# Plot voltage over time with statistics (requires matplotlib)
python tools/plot_medians.py data/pico_medians.csv

# Plot and analyze dip events (requires matplotlib)
python tools/plot_dips.py data/pico_dips.csv

# Generate comprehensive data quality report (requires matplotlib)
python tools/data_quality_report.py data/pico_medians.csv
```

**Quick test with sample data:**
```powershell
pip install matplotlib
python tools/plot_medians.py examples/pico_medians_sample.csv
python tools/plot_dips.py examples/pico_dips_sample.csv
```

**For Grafana users:** Use Grafana dashboards instead of matplotlib plotting.

### Live Monitoring (USB_STREAM mode)

**Prerequisites:** InfluxDB and Grafana running (see [SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md))

```powershell
# Stream Pico data to InfluxDB
python tools/live_monitor.py --port COM3 \
  --influx-url http://localhost:8086 \
  --token YOUR_INFLUX_TOKEN \
  --org pico \
  --bucket pico_voltage
```

**Then:**
1. Open Grafana at http://localhost:3000
2. Import `tools/grafana_dashboard.json`
3. View real-time voltage, baselines, and dips

**Dashboard includes:**
- Voltage medians (time series, all channels)
- Baseline tracking (step chart)
- Voltage dip events (bar chart with duration/magnitude)
- Current voltage gauges (live readout)
- Dip count by channel (pie chart)
- Dip statistics (min/max/avg drops)

### Testing Without Hardware

```powershell
# Simulate voltage data with controllable dips
python tools/simulate_dips.py --duration 60 --dips 10

# Creates synthetic CSV files in temp directory with:
# - Realistic noise (5mV std dev)
# - Configurable dip injection
# - Full detector logic validation
```

**Use cases:**
- Test configuration changes
- Validate thresholds
- Development without hardware
- Demonstrate functionality

### Creating Sample Data for Grafana

```powershell
# Upload realistic sample dips to InfluxDB
python tools/create_sample_dips.py \
  --influx-url http://localhost:8086 \
  --token YOUR_TOKEN \
  --org pico \
  --bucket pico_voltage
```

---

## Configuration

All tunable parameters in `src/config.py`:

### Logging Mode

```python
LOGGING_MODE = "USB_STREAM"  # or EVENT_ONLY, FULL_LOCAL
```

### Sampling

```python
TICK_MS = 10            # 10 ms sampling (100 Hz)
MEDIAN_BLOCK = 10       # Median of 10 samples (100 ms window)
```

### Stability Gating

```python
MIN_V = 0.6             # Minimum valid voltage
MAX_V = 1.8             # Maximum valid voltage  
STABLE_SPAN_V = 0.03    # Max noise span (30 mV)
```

### Dip Detection

```python
DIP_THRESHOLD_V = 0.10      # Dip starts at baseline - 100 mV
RECOVERY_MARGIN_V = 0.04    # Hysteresis (40 mV)
DIP_START_HOLD = 2          # Must persist 2 ticks (20 ms)
DIP_END_HOLD = 2            # Recovery must persist 2 ticks
DIP_COOLDOWN_MS = 300       # Ignore new dips for 300 ms after recovery
```

### Statistics & Reporting

```python
STATS_REPORT_EVERY_S = 60.0      # Print stats every 60 seconds
SHELL_STATUS_EVERY_S = 60.0      # Status line interval
BASELINE_SNAPSHOT_EVERY_S = 600  # Baseline snapshot (EVENT_ONLY mode)
```

---

## Architecture

```
┌─────────────────────────────────────────────┐
│  10 ms Tick                                 │
│  ├─ Read PLC, MODEM, BATTERY (ADC)         │
│  ├─ Update raw window (stability check)     │
│  ├─ Dip detection (raw samples)             │
│  └─ Update median block                     │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  Every 100 ms (10 samples)                  │
│  ├─ Compute median                          │
│  ├─ Update baseline (if stable)             │
│  └─ Log/stream median                       │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  Logging (mode-dependent)                   │
│  ├─ USB_STREAM: Serial → InfluxDB          │
│  ├─ FULL_LOCAL: Flash (batched, 1/sec)     │
│  └─ EVENT_ONLY: Dips + baseline snapshots   │
└─────────────────────────────────────────────┘
```

See: [docs/architecture.md](docs/architecture.md)

---

## Project Structure

```
pico-voltage-dip-monitor/
├── src/                      # MicroPython source (upload to Pico)
│   ├── main.py              # Main loop + mode switching
│   ├── config.py            # All configuration parameters
│   ├── adc_sampler.py       # ADC reading
│   ├── channel_state.py     # Per-channel buffers and state
│   ├── dip_detector.py      # Dip detection logic
│   ├── median_logger.py     # Median buffering
│   ├── storage.py           # Flash I/O + circular buffer
│   ├── stats_tracker.py     # Runtime statistics
│   └── utils.py             # Median calculation
│
├── tools/                    # PC-side analysis tools
│   ├── live_monitor.py      # USB serial → InfluxDB
│   ├── download_from_pico.py # Download CSVs via REPL
│   ├── validate_csv.py      # Data integrity checks
│   ├── plot_medians.py      # Voltage visualization
│   ├── plot_dips.py         # Dip event analysis
│   ├── data_quality_report.py # Comprehensive analysis
│   ├── simulate_dips.py     # Synthetic dip generator
│   └── grafana_dashboard.json # Pre-built dashboard
│
├── docs/
│   ├── QUICKSTART.md        # 5-minute setup guide
│   ├── SETUP_INFLUXDB.md    # InfluxDB + Grafana guide
│   ├── architecture.md      # System design
│   ├── data-formats.md      # CSV schemas
│   ├── wiring.md            # Hardware connections
│   └── troubleshooting.md   # Common issues
│
└── examples/
    ├── pico_medians_sample.csv
    └── pico_dips_sample.csv
```

---

## Troubleshooting

### Common Issues

#### "No files appear on the Pico"
- **Solution:** Files are there, just need to refresh Thonny file view
  1. View → Files (Ctrl+3)
  2. Right-click on Raspberry Pi Pico panel
  3. Click "Refresh"
- **Or:** Check Pico is running and stable readings achieved

#### "AttributeError: 'module' object has no attribute 'stdout'"
- **Cause:** MicroPython doesn't support `sys.stdout.flush()`
- **Solution:** Already fixed in current code (removed flush calls)

#### "Device busy" or "Thonny can't connect"
- Unplug Pico, wait 3 seconds, plug back in
- In Thonny: Run → Stop/Restart backend (Ctrl+F2)
- Check MicroPython is installed (not in BOOTSEL mode)

#### "Random voltage values when batteries disconnected"
- **Normal behavior:** ADC pins float without connection
- **Solutions:**
  - Use battery holder for stable contacts
  - Add 100kΩ pull-down resistor (ADC pins → GND)
  - Add 100nF capacitor (ADC pins → GND)

#### "Pico not detecting dips when I disconnect wires"
- **Issue:** Disconnecting wires drops voltage to 0V (outside valid range 0.6-1.8V)
- **Solution:** Real dips require voltage SAG (not disconnection):
  - Add load resistor (100Ω-1kΩ) between battery+ and ADC pin
  - Or wait for natural battery aging/current draw
  - Dips = temporary voltage drop while connected, not disconnection

#### "Serial port not found" (live_monitor.py)
- **Windows:** Check port in Device Manager (COM3, COM9, etc.)
  - Run: `python -m serial.tools.list_ports`
- **Mac/Linux:** Usually `/dev/ttyACM0` or `/dev/cu.usbmodem*`
- **Solution:** Use correct `--port` argument

#### "ValueError: unknown format code 'f' for object of type 'str'"
- **Cause:** Type conversion bug in older version
- **Solution:** Update to latest code (fixed in `main.py` dip_append function)

#### "InfluxDB connection refused"
- Check Docker containers running: `docker ps`
- Start containers:
  ```powershell
  docker start influxdb
  docker start grafana
  ```
- Verify InfluxDB URL: http://localhost:8086
- Check API token is correct

#### "Grafana shows no data"
- Verify InfluxDB data source configured correctly
- Check bucket name matches (`pico_voltage`)
- Ensure `live_monitor.py` is running and streaming
- Check time range in Grafana (use "Last 15 minutes")

#### "Low stability percentage (< 50%)"
- **Cause:** Manual jumper wire connections, noisy environment
- **Solutions:**
  - Use battery holder for stable contacts
  - Add 100nF capacitor to each ADC pin
  - Check batteries are good (> 1.0V for AAA)
  - Adjust `STABLE_SPAN_V` in config (increase tolerance)

### Getting Help

1. Check detailed troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)
2. Review architecture: [docs/architecture.md](docs/architecture.md)
3. Validate CSV files: `python tools/validate_csv.py your_file.csv`
4. Run simulation to verify logic: `python tools/simulate_dips.py`
5. Open GitHub issue with:
   - Pico output log
   - `config.py` settings
   - Hardware setup description

---

- **[THONNY_SETUP.md](docs/THONNY_SETUP.md)** - Complete Thonny IDE setup guide ⭐ (Start here!)
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Command line setup
- **[SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)** - InfluxDB + Grafana setup
- **[DEBUG_PROBE.md](docs/DEBUG_PROBE.md)** - Raspberry Pi Debug Probe setup (eliminates serial port conflicts)
- **[PLOTTING.md](docs/PLOTTING.md)** - Matplotlib plotting guide (offline CSV analysis)
- **[architecture.md](docs/architecture.md)** - Technical design
- **[data-formats.md](docs/data-formats.md)** - CSV schemas
- **[wiring.md](docs/wiring.md)** - Hardware connections
- **[troubleshooting.md](docs/troubleshooting.md)** - Common issues

---

## Example Output

### Console (USB_STREAM mode)

```
============================================================
PICO VOLTAGE DIP MONITOR
============================================================
Logging mode:    USB_STREAM
Sampling:        10 ms (100 Hz)
Channels:        PLC, MODEM, BATTERY
Dip threshold:   0.100 V
Free flash:      1,887,232 bytes
============================================================

Starting sampling loop...
Press Ctrl+C to stop.

MEDIAN,0.100,PLC,1.274
MEDIAN,0.100,MODEM,1.281
MEDIAN,0.100,BATTERY,1.268
...

  18.420s  DIP START  BATTERY  baseline=1.274V  now=1.112V
  18.470s  DIP END    BATTERY  dur=50ms  min=1.112V  drop=0.162V
DIP,BATTERY,18.420,18.470,50,1.274,1.112,0.162

============================================================
STATS SUMMARY @ 120.0s uptime
============================================================
Samples:         36,000 (300.0/s)
Medians:         1,200 computed, 1,200 logged
Dips detected:   1 total
  BATTERY: 1
Flash writes:    1
Memory:          123,456 bytes free / 45,678 allocated
============================================================
```

### Grafana Dashboard

Real-time visualization:
- Voltage trends (all channels)
- Baseline tracking
- Dip events timeline
- Live statistics

---

## Requirements

### Hardware
- Raspberry Pi Pico 2 (RP2350)
- USB cable
- Voltage sources (0-3.3V)

### Pico Software
- MicroPython 1.20+ (RP2350 build)

### PC Software (for tools)
- Python 3.7+
- `pip install matplotlib` (for plotting)
- `pip install influxdb-client pyserial` (for InfluxDB streaming)

---

---

## Use Cases

### Battery Testing & Validation
- ✅ Detect voltage dips under load (motor start, high current draw)
- ✅ Quality control for battery manufacturing
- ✅ Automated cell testing and sorting
- ✅ Verify battery performance specifications

### Power Supply Monitoring
- ✅ Monitor power supply stability and transients
- ✅ Detect voltage sag during high load
- ✅ Validate regulator performance
- ✅ Identify power quality issues

### Long-Term Health Monitoring
- ✅ Track battery degradation over weeks/months
- ✅ Solar battery bank monitoring
- ✅ UPS battery health tracking
- ✅ Car battery condition monitoring

### Research & Development
- ✅ High-frequency voltage data collection (100 Hz)
- ✅ Baseline drift analysis
- ✅ Noise characterization
- ✅ Multi-channel correlation studies

---

## Performance Specifications

| Specification | Value |
|---------------|-------|
| **Sampling rate** | 100 Hz (10 ms per sample) |
| **Channels** | 3 simultaneous (PLC, MODEM, BATTERY) |
| **Voltage range** | 0-3.3V (configurable safe range: 0.6-1.8V) |
| **ADC resolution** | 12-bit (RP2350) |
| **Dip detection latency** | 10-20 ms (1-2 samples) |
| **Median resolution** | 100 ms (10-sample median) |
| **Memory usage** | ~40 KB (472 KB free typical) |
| **Flash writes** | <100/day (EVENT_ONLY) to ~86,400/day (FULL_LOCAL) |
| **Uptime tested** | 24+ hours continuous |
| **Stability** | >90% with good connections, ~8% with jumper wires |

---

## Real-World Results

### Typical Console Output (USB_STREAM mode)

```
============================================================
PICO VOLTAGE DIP MONITOR
============================================================
Logging mode:    USB_STREAM
Sampling:        10 ms (100 Hz)
Channels:        PLC, MODEM, BATTERY
Dip threshold:   0.100 V
Free flash:      1,887,232 bytes
============================================================

Starting sampling loop...
Press Ctrl+C to stop.

MEDIAN,0.100,PLC,1.274
MEDIAN,0.100,MODEM,1.281
MEDIAN,0.100,BATTERY,1.268
...

  18.420s  DIP START  BATTERY  baseline=1.274V  now=1.112V
  18.470s  DIP END    BATTERY  dur=50ms  min=1.112V  drop=0.162V
DIP,BATTERY,18.420,18.470,50,1.274,1.112,0.162

============================================================
STATS SUMMARY @ 120.0s uptime
============================================================
Samples:         12,000 (100.0/s)
Medians:         1,200 computed, 1,200 logged
Baselines:
  PLC: 1.274V (converged @ 21.5s)
  MODEM: 1.281V (converged @ 409.7s)
  BATTERY: 1.268V (converged @ 116.5s)
Dips detected:   1 total
  BATTERY: 1
Flash writes:    1
Memory:          472,064 bytes free / 24,320 allocated
Stability:       PLC=92%, MODEM=8%, BATTERY=100%
============================================================
```

### Actual Dip Detection Example

Real dip detected during testing:
```
MODEM: 1.470V → 1.278V
Drop: 192 mV (0.192V)
Duration: ~50-150ms
Baseline: 1.470V
```

This proves the detector works when proper electrical conditions are met (voltage sag within valid range, not disconnection).

---

## Safety & Limitations

### ⚠️ Critical Safety Information

**NEVER exceed 3.3V on any ADC pin** - This will permanently damage the Pico!

**For higher voltages:**
- Use voltage dividers (resistor network)
- For 5V: 4.7kΩ and 10kΩ divider → 3.18V at ADC
- For 12V: 12kΩ and 5.6kΩ divider → 3.24V at ADC
- Calculate: V_out = V_in × (R2 / (R1 + R2))

**For series battery packs:**
- Each cell needs isolated measurement
- Or use differential measurement circuits
- Direct connection only works for parallel batteries with common ground

**Full wiring guide:** [docs/wiring.md](docs/wiring.md)

### Known Limitations

- **ADC accuracy:** RP2350 ADC has ~±10mV typical error (consider in threshold settings)
- **Dip detection:** Requires voltage sag (0.6-1.8V range), not disconnection (0V)
- **Flash endurance:** ~100,000 write cycles per sector (FULL_LOCAL wears faster)
- **Timing jitter:** MicroPython has ~1-2ms jitter (acceptable for 10ms sampling)
- **No isolation:** Common ground required (not suitable for high-voltage isolated systems)

---

## Future Enhancements

**Reliability:**
- [ ] Watchdog timer for unattended operation  
- [ ] LED status indicators (heartbeat, dip, error)  
- [ ] Auto-recovery from crashes  

**Connectivity:**
- [ ] WiFi streaming (Pico W support)  
- [ ] MQTT publishing  
- [ ] Web dashboard on Pico  

**Analysis:**
- [ ] Battery health prediction algorithms  
- [ ] Multi-event correlation (simultaneous dips)  
- [ ] Trend analysis and alerts  

**Performance:**
- [ ] C SDK port for <1ms latency  
- [ ] External ADC support (16-bit, 24-bit for higher precision)  
- [ ] Higher sampling rates (1 kHz+)  

**User Experience:**
- [ ] Configuration via web interface  
- [ ] Mobile app for monitoring  
- [ ] Email/SMS alerts on dip detection  

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Contributing

Contributions welcome! Please:

1. **Test changes:** Run simulation before hardware testing
   ```powershell
   python tools/simulate_dips.py --duration 60 --dips 10
   ```

2. **Validate code:** Ensure MicroPython compatibility
   - No `sys.stdout.flush()`
   - Use `time.ticks_ms()` not `time.time()`
   - Test on actual Pico 2 hardware

3. **Document:** Update relevant docs in `docs/` folder

4. **Open issues:** For bugs, feature requests, or questions

**Development workflow:**
- Fork repository
- Create feature branch
- Test thoroughly (simulation + hardware)
- Submit pull request with description

---

## Authors & Acknowledgments

**Built for:** High-frequency battery monitoring and voltage dip detection

**Focus areas:**
- ⏱️ Timing correctness (100 Hz sampling, low-latency detection)
- 💾 Data integrity (checksums, validation, circular buffers)
- 🏭 Production readiness (error handling, statistics, multiple modes)
- 🛠️ Developer experience (comprehensive docs, tools, examples)

**Special thanks to:**
- MicroPython community for excellent RP2350 support
- InfluxDB/Grafana for powerful time-series visualization
- Battery testing community for real-world use case validation

---

## Changelog

**Version 1.0.0** (February 2026)
- ✅ Initial release
- ✅ Three logging modes (USB_STREAM, EVENT_ONLY, FULL_LOCAL)
- ✅ 100 Hz sampling with dip detection
- ✅ InfluxDB + Grafana integration
- ✅ Comprehensive documentation
- ✅ PC analysis tools (10 utilities)
- ✅ Validated on Pico 2 hardware (24+ hour uptime)

---

## Support

**Documentation:**
- Quick start: [THONNY_SETUP.md](docs/THONNY_SETUP.md)
- InfluxDB setup: [SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)
- Troubleshooting: [troubleshooting.md](docs/troubleshooting.md)
- Cheat sheet: [CHEATSHEET.md](CHEATSHEET.md)

**Getting help:**
1. Check [troubleshooting.md](docs/troubleshooting.md)
2. Review [architecture.md](docs/architecture.md)
3. Run `python tools/validate_csv.py` on your data
4. Open GitHub issue with logs and config

**Reporting bugs:**
- Include Pico console output
- Attach `config.py` settings
- Describe hardware setup
- Mention MicroPython version

---

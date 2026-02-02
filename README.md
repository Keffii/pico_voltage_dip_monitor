# Pico Voltage Dip Monitor (Pico 2)

**High-frequency battery voltage monitoring system** for detecting fast voltage dips with MicroPython on Raspberry Pi Pico 2.

Samples GP26, GP27, GP28 every 10 ms (100 Hz), computes 100 ms medians, tracks baseline stability, and detects voltage dips with millisecond precision.

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

---

## Quick Start

**Using Thonny IDE?** See: [docs/THONNY_SETUP.md](docs/THONNY_SETUP.md) (recommended for beginners)

**Command line users:** See: [docs/QUICKSTART.md](docs/QUICKSTART.md)

### Quick Steps

1. Install MicroPython on Pico 2
2. Upload all files from `src/` to Pico
3. Edit `config.py` - choose logging mode
4. Connect batteries to GP26, GP27, GP28 (GND common)
5. Run `main.py`

---

## Logging Modes

### USB_STREAM (Recommended for Development)

```python
LOGGING_MODE = "USB_STREAM"
```

Streams all data over USB serial → PC → InfluxDB → Grafana dashboard

**Benefits:**
- Real-time visualization
- Unlimited storage
- Professional time-series analysis
- No flash wear

**Setup:** [docs/SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)

### EVENT_ONLY (Recommended for Production)

```python
LOGGING_MODE = "EVENT_ONLY"
```

Logs only important events: dips, baseline snapshots (every 10 min)

**Benefits:**
- Minimal flash wear (~500 lines/day)
- Standalone operation
- Months of runtime
- Captures critical events

### FULL_LOCAL (Debug/Testing)

```python
LOGGING_MODE = "FULL_LOCAL"
```

Logs all medians to flash with 1-hour circular buffer

**Benefits:**
- Standalone operation
- Full voltage history
- Fixed storage footprint (100 KB)

---

## Hardware

### Requirements

- **Raspberry Pi Pico 2** (RP2350)
- **MicroPython** firmware
- **Voltage sources** (0-3.3V)

### Prototype Setup

```
Battery A (+) → GP26 (ADC0)
Battery B (+) → GP27 (ADC1)
Battery C (+) → GP28 (ADC2)
All GND       → Pico GND (common ground)
```

**⚠️ SAFETY:** Never exceed 3.3V on ADC pins!

For higher voltages, use voltage dividers. See: [docs/wiring.md](docs/wiring.md)

---

## Output Files

### On Pico Flash

**All modes:**
- `/pico_dips.csv` - Dip events (channel, start, end, duration, baseline, min_V, drop_V)

**EVENT_ONLY and FULL_LOCAL:**
- `/pico_baseline_snapshots.csv` - Baseline snapshots every 10 minutes

**FULL_LOCAL only:**
- `/pico_medians.csv` - 100 ms medians (circular buffer, last 1 hour)

See: [docs/data-formats.md](docs/data-formats.md)

---

## Tools

### Data Analysis (PC-side)

```powershell
# Download CSV files from Pico
python tools/download_from_pico.py --port COM3 --output ./data

# Validate CSV integrity
python tools/validate_csv.py data/pico_medians.csv

# Plot voltage over time
python tools/plot_medians.py data/pico_medians.csv

# Plot dip events
python tools/plot_dips.py data/pico_dips.csv

# Generate data quality report
python tools/data_quality_report.py data/pico_medians.csv
```

### Live Monitoring (USB_STREAM mode)

```powershell
# Stream to InfluxDB + Grafana
python tools/live_monitor.py --port COM3 --bucket pico_voltage
```

Setup guide: [docs/SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)

### Testing Without Hardware

```powershell
# Simulate voltage dips for testing detector logic
python tools/simulate_dips.py --duration 60 --dips 10
```

Generates synthetic data with realistic noise and configurable dip injection.

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
│  ├─ Read GP26, GP27, GP28 (ADC)            │
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

## Documentation

- **[THONNY_SETUP.md](docs/THONNY_SETUP.md)** - Complete Thonny IDE setup guide ⭐ (Start here!)
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Command line setup
- **[SETUP_INFLUXDB.md](docs/SETUP_INFLUXDB.md)** - InfluxDB + Grafana setup
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
Channels:        GP26, GP27, GP28
Dip threshold:   0.100 V
Free flash:      1,887,232 bytes
============================================================

Starting sampling loop...
Press Ctrl+C to stop.

MEDIAN,0.100,GP26,1.274
MEDIAN,0.100,GP27,1.281
MEDIAN,0.100,GP28,1.268
...

  18.420s  DIP START  GP28  baseline=1.274V  now=1.112V
  18.470s  DIP END    GP28  dur=50ms  min=1.112V  drop=0.162V
DIP,GP28,18.420,18.470,50,1.274,1.112,0.162

============================================================
STATS SUMMARY @ 120.0s uptime
============================================================
Samples:         36,000 (300.0/s)
Medians:         1,200 computed, 1,200 logged
Dips detected:   1 total
  GP28: 1
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

![Grafana Dashboard Preview](https://via.placeholder.com/800x400.png?text=Grafana+Dashboard)

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

## Use Cases

✅ **Battery testing** - Detect voltage dips under load  
✅ **Power supply validation** - Monitor stability and transients  
✅ **Battery health monitoring** - Track degradation over time  
✅ **Quality control** - Automated cell testing  
✅ **Research** - High-frequency voltage data collection  

---

## Safety

⚠️ **CRITICAL:** Never exceed 3.3V on any ADC pin  
⚠️ For higher voltages, use proper voltage dividers  
⚠️ For series battery packs, use isolated measurement  

See: [docs/wiring.md](docs/wiring.md) for safe connections

---

## Performance

| Metric | Value |
|--------|-------|
| Sampling rate | 100 Hz (10 ms) |
| Latency | 10-20 ms (dip start detection) |
| Channels | 3 simultaneous |
| Flash writes | <100/day (EVENT_ONLY mode) |
| Flash writes | ~86,400/day (FULL_LOCAL mode) |
| Memory usage | ~40 KB |
| Uptime tested | 24+ hours |

---

## Roadmap

- [ ] Watchdog timer for unattended operation  
- [ ] LED status indicators (heartbeat, dip, error)  
- [ ] WiFi streaming (Pico W support)  
- [ ] Battery health prediction algorithms  
- [ ] Multi-event correlation (simultaneous dips)  
- [ ] C SDK port for <1ms latency  
- [ ] External ADC support (higher precision)  

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Contributing

Issues and pull requests welcome!

**Before hardware testing:** Run simulation to validate changes:
```powershell
python tools/simulate_dips.py --duration 60 --dips 10
```

---

## Acknowledgments

Built for high-frequency battery monitoring with focus on:
- Timing correctness
- Data integrity
- Production readiness
- Developer experience

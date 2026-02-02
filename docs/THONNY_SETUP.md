# Thonny Setup Guide for Pico 2

Complete guide for setting up and running the Pico Voltage Dip Monitor using Thonny IDE.

---

## Prerequisites

- **Thonny IDE** - Download from: https://thonny.org/
- **Raspberry Pi Pico 2** (RP2350)
- **USB cable**
- **Batteries** (optional, for testing)

---

## Step 1: Install MicroPython on Pico 2

### 1.1 Open Thonny

Launch Thonny IDE.

### 1.2 Connect Pico in BOOTSEL Mode

1. **Hold the BOOTSEL button** on Pico 2
2. **Plug in USB** while holding BOOTSEL
3. Release BOOTSEL
4. Pico appears as USB drive (RPI-RP2)

### 1.3 Install MicroPython

1. In Thonny: **Tools** → **Options** → **Interpreter**
2. Select: **MicroPython (Raspberry Pi Pico)**
3. Click: **Install or update MicroPython**
4. Select:
   - **Target volume**: RPI-RP2 (your Pico drive)
   - **MicroPython variant**: Raspberry Pi Pico / Pico H (RP2350)
   - **Version**: Latest stable
5. Click: **Install**
6. Wait for installation (~30 seconds)
7. Click: **Close**

### 1.4 Verify Installation

1. **Unplug Pico** from USB
2. **Plug back in normally** (don't hold BOOTSEL)
3. In Thonny bottom-right, you should see: **MicroPython (Raspberry Pi Pico)**
4. In the Shell panel, you should see:
   ```
   MicroPython v1.x.x on 2024-xx-xx; Raspberry Pi Pico 2 with RP2350
   Type "help()" for more information.
   >>>
   ```

✅ MicroPython is now installed!

---

## Step 2: Upload Project Files to Pico

### 2.1 Open File Explorer in Thonny

1. **View** → **Files** (or press Ctrl+3)
2. You'll see two panels:
   - **Left**: Your PC files
   - **Right**: Raspberry Pi Pico files

### 2.2 Upload All Files from `src/` Folder

Navigate to your project folder on the **left panel**:

For **each file** in the src/ folder, do the following:

1. **Right-click** the file in the left panel
2. Select: **Upload to /**
3. Confirm the upload

**Files to upload (9 total):**
- ✅ `main.py`
- ✅ `config.py`
- ✅ `adc_sampler.py`
- ✅ `channel_state.py`
- ✅ `dip_detector.py`
- ✅ `median_logger.py`
- ✅ `storage.py`
- ✅ `stats_tracker.py`
- ✅ `utils.py`

### Alternative: Upload via Shell Commands

Or, select all files in left panel, right-click → **Upload to /**

### 2.3 Verify Files on Pico

In the **right panel** (Raspberry Pi Pico), you should see all 9 files:

```
/
├── main.py
├── config.py
├── adc_sampler.py
├── channel_state.py
├── dip_detector.py
├── median_logger.py
├── storage.py
├── stats_tracker.py
└── utils.py
```

✅ All files uploaded!

---

## Step 3: Configure Logging Mode

### 3.1 Open config.py on Pico

1. In the **right panel** (Raspberry Pi Pico files)
2. **Double-click** `config.py`
3. It opens in the editor

### 3.2 Choose Logging Mode

Find this line near the top:
```python
LOGGING_MODE = "USB_STREAM"
```

Change it to your desired mode:

#### Option A: USB_STREAM (For InfluxDB - requires PC tools)
```python
LOGGING_MODE = "USB_STREAM"
```
**Note:** You'll need to close Thonny and run PC tools separately (see Step 5)

#### Option B: FULL_LOCAL (Standalone, saves to Pico flash)
```python
LOGGING_MODE = "FULL_LOCAL"
```
**Recommended for initial testing in Thonny**

#### Option C: EVENT_ONLY (Production, minimal flash)
```python
LOGGING_MODE = "EVENT_ONLY"
```

### 3.3 Save config.py

1. **File** → **Save** (or Ctrl+S)
2. Confirm it's saving to the **Raspberry Pi Pico** (not your PC)

✅ Configuration set!

---

## Step 4: Connect Hardware (Optional)

### For Testing with Batteries

```
Battery A (+) → GP26 (Pin 31)
Battery B (+) → GP27 (Pin 32)
Battery C (+) → GP28 (Pin 34)
All GND       → Any GND pin on Pico
```

**⚠️ IMPORTANT:** Use AAA NiMH (1.2V) or add voltage dividers for alkaline (1.5V+)

### For Testing Without Batteries

You can run without batteries - ADC pins will show random values (this is normal, they're floating).

---

## Step 5: Run the Project

### 5.1 Open main.py

In the **right panel** (Pico files), **double-click** `main.py`

### 5.2 Run

Click the **green Run button** (or press F5)

### 5.3 Expected Output in Shell

You should see:

```
Configuration validated successfully.
============================================================
PICO VOLTAGE DIP MONITOR
============================================================
Logging mode:    FULL_LOCAL
Sampling:        10 ms (100 Hz)
Channels:        GP26, GP27, GP28
Dip threshold:   0.100 V
Free flash:      1,887,232 bytes
============================================================

Starting sampling loop...
Press Ctrl+C to stop.

    60.0s  GP26: stable=1 base=1.274 dip=0  GP27: stable=1 base=1.281 dip=0  GP28: stable=1 base=1.268 dip=0
============================================================
STATS SUMMARY @ 60.5s uptime
============================================================
Samples:         18,000 (297.5/s)
Medians:         600 computed, 600 logged
Dips detected:   0 total
Flash writes:    60
Memory:          123,456 bytes free / 45,678 allocated
File sizes:
  medians.csv:   15,234 bytes
  dips.csv:      89 bytes
Baseline convergence:
  GP26: 3.2s
  GP27: 3.2s
  GP28: 3.2s
============================================================
```

✅ Project is running!

### 5.4 Stop the Program

Press **Ctrl+C** in Thonny to stop gracefully. You'll see:

```
Shutdown requested. Flushing buffers...
Flushed 15 median lines to flash

Final statistics:
[stats summary]

Shutdown complete.
```

---

## Step 6: View Data Files

### 6.1 Check Files on Pico

In the **right panel** (Pico files), you should now see new CSV files:

```
/
├── main.py
├── config.py
├── ...
├── pico_medians.csv        ← New!
├── pico_dips.csv           ← New!
└── pico_baseline_snapshots.csv  ← New (if EVENT_ONLY mode)
```

### 6.2 View CSV Content in Thonny

1. **Double-click** `pico_medians.csv` in right panel
2. You'll see the CSV data in the editor:
   ```csv
   time_s,channel,median_V
   0.100,GP26,1.274
   0.100,GP27,1.281
   0.100,GP28,1.268
   ...
   ```

### 6.3 Download CSV to PC

To analyze data with PC tools:

1. **Right-click** `pico_medians.csv` in right panel
2. Select: **Download to C:\Users\kevin\Documents\Python\pico-voltage-dip-monitor\data**
3. Create `data/` folder if it doesn't exist
4. Repeat for `pico_dips.csv`

---

## Step 7: Using PC Tools (Important!)

### ⚠️ Serial Port Conflict

**You CANNOT use PC tools while Thonny is connected!**

Both Thonny and PC tools (like `live_monitor.py`) need exclusive access to the serial port.

### Workflow A: Use Thonny for Development

**For initial testing and debugging:**

1. ✅ Use Thonny to run code
2. ✅ View output in Thonny Shell
3. ✅ Edit files on Pico
4. ✅ Download CSVs when done
5. ✅ Close Thonny
6. ✅ Then run PC analysis tools:
   ```powershell
   python tools/plot_medians.py data/pico_medians.csv
   python tools/validate_csv.py data/pico_medians.csv
   ```

### Workflow B: Use PC Tools for Production Monitoring

**For InfluxDB streaming or advanced analysis:**

1. ✅ Configure `LOGGING_MODE = "USB_STREAM"` in config.py
2. ✅ Run main.py in Thonny once to verify it works
3. ✅ **Close Thonny completely**
4. ✅ Pico will auto-run main.py on power-up (it's already uploaded)
5. ✅ Run PC tool:
   ```powershell
   python tools/live_monitor.py --port COM9
   ```
6. ✅ View Grafana dashboard: http://localhost:3000

### How to Switch Modes

**From Thonny → PC Tools:**
1. Stop program (Ctrl+C)
2. Close Thonny
3. Run PC tool

**From PC Tools → Thonny:**
1. Stop PC tool (Ctrl+C)
2. Unplug Pico (optional)
3. Open Thonny
4. Plug in Pico
5. Run → Stop/Restart backend (if needed)

---

## Step 8: Auto-Run on Boot (Optional)

Files named `main.py` on Pico automatically run when powered up.

Since you already uploaded `main.py`, the Pico will auto-start monitoring when:
- Powered via USB (without Thonny)
- Powered via VSYS pin (battery/external power)

**To disable auto-run:** Rename `main.py` to something else (like `main_disabled.py`)

---

## Common Workflows

### Workflow 1: Development in Thonny (Recommended for Beginners)

```
1. Set LOGGING_MODE = "FULL_LOCAL"
2. Run in Thonny (F5)
3. Watch Shell output for status
4. Let run for a few minutes
5. Stop (Ctrl+C)
6. Download CSVs (right-click → Download)
7. Close Thonny
8. Analyze with PC tools:
   python tools/plot_medians.py data/pico_medians.csv
```

### Workflow 2: InfluxDB Streaming (Advanced)

```
1. Upload all files in Thonny
2. Set LOGGING_MODE = "USB_STREAM"
3. Test run in Thonny (verify no errors)
4. Close Thonny completely
5. Setup InfluxDB (docs/SETUP_INFLUXDB.md)
6. Run: python tools/live_monitor.py --port COM9
7. View Grafana: http://localhost:3000
```

### Workflow 3: Overnight Stability Test

```
1. Set LOGGING_MODE = "FULL_LOCAL"
2. Run in Thonny, verify it starts
3. Close Thonny (Pico continues running)
4. Leave overnight
5. Next day: Open Thonny
6. Download CSVs
7. Analyze:
   python tools/data_quality_report.py data/pico_medians.csv
```

### Workflow 4: Simulation Testing (No Pico Needed!)

```
1. Close Thonny
2. Run on PC:
   python tools/simulate_dips.py --duration 60 --dips 10
3. Analyze simulated data:
   python tools/validate_csv.py /tmp/sim_dips.csv
   python tools/plot_dips.py /tmp/sim_dips.csv
```

---

## Troubleshooting

### "Backend is already running"

**Solution:**
1. **Run** → **Stop/Restart backend**
2. Or: Unplug Pico, replug, try again

### "Device is busy" or "Could not connect"

**Causes:**
- Another program is using the serial port
- PC tool is running

**Solution:**
1. Close all programs using the port (other Python scripts, Arduino IDE, etc.)
2. **Run** → **Stop/Restart backend**
3. Unplug/replug Pico

### "No files appear in right panel"

**Solution:**
1. Check bottom-right shows: "MicroPython (Raspberry Pi Pico)"
2. Click **View** → **Files** to show file panel
3. Try: **Run** → **Stop/Restart backend**

### "Random voltage values"

**This is normal when ADC pins are disconnected** (floating inputs).

**Solutions:**
- Connect batteries
- Add 100kΩ pulldown resistors to GND
- Ignore until hardware is connected

### "Configuration errors" on startup

**Solution:**
1. Open `config.py` on Pico (right panel)
2. Check values:
   - `MIN_V < MAX_V`
   - `LOGGING_MODE` is one of: "USB_STREAM", "EVENT_ONLY", "FULL_LOCAL"
   - `DIP_THRESHOLD_V > 0`
3. Save and run again

### Can't use PC tools

**Remember:** Close Thonny first!

The serial port can only be used by one program at a time.

---

## Tips for Thonny Users

### Editing Files

- **Edit on Pico:** Double-click file in right panel → edit → save
- **Edit on PC:** Double-click file in left panel → edit → save → upload

### Viewing Real-Time Output

Shell panel shows all `print()` statements in real-time - perfect for monitoring.

### Debugging

Add print statements in your code:
```python
print(f"Debug: voltage={v:.3f}, baseline={baseline:.3f}")
```

### Stopping Gracefully

Always use **Ctrl+C** instead of clicking the red Stop button - this ensures buffers are flushed.

### File Size Monitoring

Watch the stats output every 60s to see file sizes growing.

### Testing Different Modes

Edit `config.py`, save, run again - easy to test all three modes!

---

## Quick Reference

### Thonny Shortcuts

| Action | Shortcut |
|--------|----------|
| Run current file | F5 |
| Stop program | Ctrl+C |
| Show Files panel | Ctrl+3 |
| Save file | Ctrl+S |
| Stop/Restart backend | Ctrl+F2 |

### File Locations

| Location | Purpose |
|----------|---------|
| Left panel (PC) | `C:\Users\kevin\Documents\Python\pico-voltage-dip-monitor\src\` |
| Right panel (Pico) | `/` (root of Pico filesystem) |

### When to Use What

| Task | Use |
|------|-----|
| Upload files | Thonny (right-click → Upload) |
| Edit config | Thonny (double-click on Pico) |
| Run/debug | Thonny (F5) |
| Quick tests | Thonny Shell |
| Download data | Thonny (right-click → Download) |
| Plot graphs | PC tools (close Thonny first!) |
| InfluxDB stream | PC tools (close Thonny first!) |
| Simulate dips | PC tools (Pico not needed) |

---

## Next Steps

1. ✅ **Upload all files** (Step 2)
2. ✅ **Set logging mode** (Step 3) - Start with `FULL_LOCAL`
3. ✅ **Run in Thonny** (Step 5) - Verify it works
4. ✅ **Let it run 5-10 minutes** - Watch stats output
5. ✅ **Download CSVs** (Step 6)
6. ✅ **Close Thonny, analyze data:**
   ```powershell
   python tools/plot_medians.py data/pico_medians.csv
   python tools/data_quality_report.py data/pico_medians.csv
   ```
7. ✅ **Optional: Setup InfluxDB** - See [docs/SETUP_INFLUXDB.md](SETUP_INFLUXDB.md)

---

## Summary

**Thonny is perfect for:**
- ✅ Uploading files
- ✅ Editing configuration
- ✅ Development and debugging
- ✅ Quick tests
- ✅ Viewing real-time status

**PC tools are needed for:**
- ✅ Advanced plotting
- ✅ Data quality reports
- ✅ CSV validation
- ✅ InfluxDB streaming
- ✅ Grafana dashboards
- ✅ Simulation

**Remember:** Close Thonny before using PC tools!

---

**You're ready to go! Start with Workflow 1 above and work your way up.**

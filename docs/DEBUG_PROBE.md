# Raspberry Pi Debug Probe Setup Guide

This guide shows how to use the Raspberry Pi Debug Probe with the Pico Voltage Dip Monitor for improved development workflow and debugging.

**Debug Probe Product Page:** https://www.raspberrypi.com/documentation/microcontrollers/debug-probe.html

---

## Benefits

### 1. **Eliminate Serial Port Conflicts**
- **Before:** Stop `live_monitor.py` → Upload code in Thonny → Restart `live_monitor.py`
- **After:** Keep `live_monitor.py` running while uploading code via Thonny
- No more disconnecting and reconnecting!

### 2. **Dual Connection Workflow**
- **Debug Probe UART** → `live_monitor.py` (always streaming to InfluxDB)
- **Pico USB** → Thonny (code upload, REPL, debugging)
- Work simultaneously without interference

### 3. **Soft Breakpoints for MicroPython**
- MicroPython does **not** support true hardware breakpoints on the Pico
- This project adds a **UART soft-breakpoint** so you can pause/resume the main loop and query status
- Useful for inspecting state without stopping UART streaming

### 4. **More Reliable Serial Communication**
- Dedicated UART hardware (not USB CDC)
- No buffer overruns during code uploads
- Consistent baud rates
- Industrial-grade FTDI chip

---

## Hardware Requirements

- **Raspberry Pi Debug Probe** (includes cables)
- **Raspberry Pi Pico 2**
- **3 female-to-female jumper wires** (for UART connection)
- Optional: USB extension cable for Debug Probe

---

## Wiring Connections

### UART Connection (for Serial Streaming)

```
Debug Probe              Pico 2
-----------              ------
GND (black wire)    →    GND (any ground pin)
UART TX (orange)    →    GP1 (UART0 RX, pin 2)
UART RX (yellow)    →    GP0 (UART0 TX, pin 1)
```

**Pin Layout Reference:**
```
Pico 2 Pins:
┌─────────────┐
│ GP0  1  40  │ VBUS
│ GP1  2  39  │ VSYS
│ GND  3  38  │ GND
│ ...         │ ...
└─────────────┘
```

### Debug Connection (Optional - for Hardware Debugging)

If you want to use hardware debugging (breakpoints, stepping):

```
Debug Probe         Pico 2 Debug Header
-----------         -------------------
SWCLK          →    SWCLK
SWDIO          →    SWDIO
GND            →    GND
```

**Note:** The Pico 2 has a 3-pin debug header near the USB connector.

---

## Software Setup

### Step 1: Enable Debug Probe in Config

Edit `src/config.py` on your Pico:

```python
# Serial output configuration
USE_DEBUG_PROBE = True  # Set to True when using Debug Probe UART
```

### Step 2: Upload Updated Code

1. Open Thonny
2. Connect Pico via USB
3. Upload all files from `src/` folder (including updated `config.py` and `main.py`)
4. The Pico will now output to both USB (for Thonny REPL) and UART (for Debug Probe)

### Step 2b: Soft Breakpoint Commands (UART)

Send these commands over the Debug Probe UART (e.g., from `live_monitor.py`, a serial terminal, or any script):

- `PAUSE` / `BREAK` / `B` → pause the sampling loop
- `RESUME` / `CONT` / `C` → resume the loop
- `STATUS` / `S` → print a one-line status (stable/baseline/dip per channel)
- `HELP` / `H` / `?` → print command list

### Step 3: Identify Serial Ports

Connect both Debug Probe and Pico USB to your PC, then check ports:

```powershell
python -m serial.tools.list_ports
```

**Example output:**
```
COM9 - USB Serial Device (Pico USB CDC)
COM8 - USB Serial Port (Debug Probe FTDI)
```

- **COM9** = Pico USB (use for Thonny)
- **COM8** = Debug Probe (use for `live_monitor.py`)

**Note:** Port numbers vary by system. On Mac/Linux: `/dev/ttyACM0`, `/dev/ttyUSB0`, etc.

### Step 4: Run Live Monitor on Debug Probe Port

```powershell
# Use the Debug Probe port (COM8 in this example)
python tools/live_monitor.py --port COM8 --token YOUR_INFLUX_TOKEN
```

### Step 5: Develop in Thonny on Pico USB Port

1. In Thonny: Tools → Options → Interpreter
2. Port: Select the Pico USB port (COM9 in example)
3. Upload code, run REPL, debug as usual
4. `live_monitor.py` keeps running without interruption!

---

## Workflow Example

### Traditional Workflow (Without Debug Probe)

```
1. Start: python tools/live_monitor.py --port COM9
2. [Streaming data to InfluxDB...]
3. Need to update code
4. Stop live_monitor.py (Ctrl+C)
5. Close Thonny (if open)
6. Open Thonny
7. Upload new code
8. Close Thonny
9. Restart: python tools/live_monitor.py --port COM9
10. [Streaming resumes...]
```

### Debug Probe Workflow (With Debug Probe)

```
1. Start ONCE: python tools/live_monitor.py --port COM8
2. [Streaming continuously to InfluxDB...]
3. Need to update code
4. Open Thonny (on COM9)
5. Upload new code
6. Close Thonny
7. [Streaming never stopped!]
```

**Time saved:** ~30-60 seconds per iteration, no interruption to data collection.

---

## Configuration Options

### Dual Output (Recommended)

```python
USE_DEBUG_PROBE = True
```

**Behavior:**
- Outputs to both USB CDC (Thonny) AND UART (Debug Probe)
- Works even if Debug Probe is disconnected
- Maximum flexibility

### USB Only (Default)

```python
USE_DEBUG_PROBE = False
```

**Behavior:**
- Outputs only to USB CDC
- Original behavior, no UART usage
- Use when Debug Probe not available

---

## Troubleshooting

### "No data in InfluxDB" after connecting Debug Probe

**Check:**
1. Is `USE_DEBUG_PROBE = True` in `config.py` on Pico?
2. Did you upload the updated `main.py`?
3. Is `live_monitor.py` using the Debug Probe port (e.g., COM10)?

**Test UART output:**
```powershell
# Simple serial monitor
python -m serial.tools.miniterm COM10 115200
```

You should see: `MEDIAN,...`, `DIP,...`, `BASELINE,...` messages

### "Wiring is correct but no output on Debug Probe"

**Common issues:**
- TX/RX swapped: Debug Probe TX goes to Pico RX (GP1), Debug Probe RX goes to Pico TX (GP0)
- Wrong ground: Ensure GND is connected
- Wrong pins: GP0 = pin 1, GP1 = pin 2 (not GP26/27/28!)

**Test with simple script:**
```python
# Test UART output (upload via Thonny)
from machine import UART
import time

uart = UART(0, baudrate=115200, tx=0, rx=1)

while True:
    uart.write("Test message\n")
    time.sleep(1)
```

### "live_monitor.py shows garbage characters"

**Baud rate mismatch:**
- Check `live_monitor.py` is using 115200 baud
- Check Pico `main.py` initializes UART with 115200

### "Thonny can't connect after enabling Debug Probe"

**Debug Probe doesn't affect USB connection:**
- Debug Probe uses GP0/GP1 (UART0)
- USB CDC is separate hardware
- Both work simultaneously
- Check Thonny port selection (should be Pico USB, not Debug Probe)

### "Debug Probe port disappears after Pico reset"

**This is normal:**
- Debug Probe port is independent
- Only Pico USB resets
- Debug Probe stays connected
- No need to restart `live_monitor.py`

---

## Advanced: Hardware Debugging

### OpenOCD Setup (for breakpoints and stepping)

**Windows:**
```powershell
# Install OpenOCD
choco install openocd

# Connect to Pico
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg
```

**Mac/Linux:**
```bash
# Install OpenOCD
brew install openocd  # Mac
sudo apt install openocd  # Linux

# Connect to Pico
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg
```

### VS Code Debugging

Install extensions:
- Cortex-Debug
- Pico-Go or MicroPico

Configure `launch.json` for hardware debugging with Debug Probe.

**Note:** Hardware debugging is advanced and primarily useful for C/C++ development. For MicroPython, UART serial output is usually sufficient.

---

## Pin Reference

### Debug Probe Connector Pinout

```
Debug Probe UART Cable (JST connector):
┌──────────────────┐
│ 1: GND (black)   │
│ 2: TX  (orange)  │  → Pico GP1 (RX)
│ 3: RX  (yellow)  │  → Pico GP0 (TX)
└──────────────────┘
```

### Pico 2 UART0 Pins

```
GP0 (Pin 1)  = UART0 TX
GP1 (Pin 2)  = UART0 RX
GP2 (Pin 4)  = UART0 CTS (not used)
GP3 (Pin 5)  = UART0 RTS (not used)
```

**Note:** We only use GP0 (TX) and GP1 (RX). Hardware flow control (CTS/RTS) not needed.

---

## Cost-Benefit Analysis

### Investment
- **Debug Probe:** ~$12 USD
- **Jumper wires:** ~$2 USD (if not included)
- **Total:** ~$14 USD

### Time Savings
- **Per code update:** 30-60 seconds saved
- **Typical development session:** 10-20 updates
- **Time saved per session:** 5-20 minutes
- **ROI:** Pays for itself in a few development sessions

### Additional Benefits
- No data gaps during code updates
- Continuous InfluxDB logging
- Professional debugging capability
- Cleaner desk setup (fewer cable swaps)

---

## Alternatives

### Without Debug Probe

**Option 1: Accept the workflow**
- Stop/restart `live_monitor.py` each time
- Brief data gaps acceptable

**Option 2: Use EVENT_ONLY or FULL_LOCAL mode**
- No `live_monitor.py` needed
- Standalone Pico operation
- Download CSVs later for analysis

**Option 3: Second Pico as USB-UART bridge**
- Use another Pico as serial bridge
- More complex wiring
- Debug Probe is cleaner solution

---

## Related Documentation

- [USB_STREAM mode setup](SETUP_INFLUXDB.md)
- [Thonny setup guide](THONNY_SETUP.md)
- [Troubleshooting](troubleshooting.md)
- [Main configuration](../src/config.py)

---

## Summary

The Raspberry Pi Debug Probe is a **highly recommended** addition for development workflows:

✅ Eliminates serial port conflicts  
✅ Continuous data streaming during development  
✅ Professional debugging capability  
✅ Minimal cost (~$12)  
✅ Easy to set up (3 wire connections)  

**Verdict:** Worth it if you're actively developing and using USB_STREAM mode.

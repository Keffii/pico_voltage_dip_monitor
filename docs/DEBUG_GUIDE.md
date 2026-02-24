# Soft Breakpoint Debugging Guide

Complete guide for debugging MicroPython on Pico 2 using soft breakpoints.

**Why soft breakpoints?** Hardware breakpoints (via SWD/GDB) don't work with MicroPython. Soft breakpoints are manual pause points coded into your program that give you similar debugging capabilities.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Configuration](#configuration)
- [Breakpoint Types](#breakpoint-types)
- [Test Instructions](#test-instructions)
- [Usage Examples](#usage-examples)
- [Advanced Techniques](#advanced-techniques)
- [Performance Impact](#performance-impact)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Enable Debugging

Edit [src/config.py](../src/config.py):

```python
DEBUG_BREAKPOINTS = True   # Enable breakpoints
DEBUG_TRACE = True         # Enable tracepoints
```

### 2. Add Breakpoints to Your Code

```python
from debug import debug

# Simple breakpoint
voltage = 1.112
baseline = 1.274
debug.bp("voltage_check", 
         voltage=voltage, 
         baseline=baseline, 
         drop_mV=(baseline - voltage) * 1000)
```

### 3. Run and Observe Output

```
============================================================
BREAKPOINT #1: voltage_check
Time: 18420ms
Variables:
  voltage              = 1.112000
  baseline             = 1.274000
  drop_mV              = 162.000000
============================================================
```

---

## Features

### ✅ Available Features

| Feature | Description | Use Case |
|---------|-------------|----------|
| **Breakpoints** | Pause and print variables | Inspect state at specific locations |
| **Conditional Breakpoints** | Only break when condition is true | Debug specific scenarios |
| **Watchpoints** | Auto-break on variable change | Track state machine transitions |
| **Tracepoints** | Log without pausing | High-frequency event logging |

### ❌ NOT Available (MicroPython Limitations)

- Hardware breakpoints (CPU halt)
- Step-through line-by-line
- External debugger (GDB)
- Memory/register inspection
- Stack unwinding

---

## Configuration

### Config Flags ([src/config.py](../src/config.py))

```python
# Enable/disable debugging features
DEBUG_BREAKPOINTS = False    # Breakpoints and watchpoints
DEBUG_TRACE = False          # Tracepoint logging
```

**Performance tip:** Set all to `False` in production for maximum performance.

---

## Breakpoint Types

### 1. Simple Breakpoint

**Pause execution and print variables:**

```python
from debug import debug

debug.bp("location_name", 
         var1=value1, 
         var2=value2, 
         var3=value3)
```

**Example:**
```python
# In dip_detector.py
def process_sample(...):
    if st.below_count >= self.start_hold:
        debug.bp("dip_started",
                 channel=channel_name,
                 voltage_V=v,
                 baseline_V=baseline,
                 drop_mV=(baseline - v) * 1000)
```

**Output:**
```
============================================================
BREAKPOINT #1: dip_started
Time: 18420ms
Variables:
  channel              = PLC
  voltage_V            = 1.112000
  baseline_V           = 1.274000
  drop_mV              = 162.000000
============================================================
```

---

### 2. Conditional Breakpoint

**Only break when a condition is true:**

```python
debug.bp_if(condition, "name", var1=val1, var2=val2)
```

**Example:**
```python
# Only break on large voltage drops
drop = baseline - v
debug.bp_if(drop > 0.200,  # Condition: drop > 200mV
            "large_drop",
            channel=channel_name,
            drop_mV=drop * 1000,
            threshold_mV=200.0)
```

**Use cases:**
- Debug rare events (only break when drop > threshold)
- Catch edge cases (only break when count reaches limit)
- Filter noise (only break on unexpected values)

---

### 3. Watchpoint

**Auto-break when a variable changes:**

```python
# Create watchpoint
watch = debug.watch("variable_name", break_on_change=True)

# Check value (breaks if changed)
watch.check(current_value, extra_var=extra_value)
```

**Example:**
```python
# In channel_state.py
class ChannelState:
    def __init__(self, ...):
        self._dip_watch = debug.watch("dip_active")
    
    def set_dip_active(self, active):
        # Auto-breaks when dip_active changes
        self._dip_watch.check(active, 
                              channel=self.channel_name,
                              time_s=current_time)
        self.dip_active = active
```

**Output when value changes:**
```
============================================================
WATCHPOINT: dip_active changed! (#1)
  Old value: False
  New value: True
  channel            = PLC
  time_s             = 18.420
============================================================
```

---

### 4. Tracepoint

**Log events without pausing (high-frequency logging):**

```python
debug.trace("event_name", var1=val1, var2=val2)
```

**Example:**
```python
# Log every sample (doesn't pause)
def process_sample(...):
    debug.trace("sample",
                ch=channel_name,
                v=v,
                stable=st.stable,
                baseline=baseline)
```

**View trace log:**
```python
# In REPL or code
debug.dump_trace(last_n=20)  # Show last 20 events
```

**Output:**
```
============================================================
TRACE LOG (last 20 events):
============================================================
    18100ms | sample                    | ch=PLC, v=1.274, stable=True, baseline=1.273
    18110ms | sample                    | ch=MODEM, v=1.281, stable=True, baseline=1.280
    18120ms | sample                    | ch=BATTERY, v=1.268, stable=True, baseline=1.267
    ...
============================================================
```

---

## Test Instructions

### Running the Test Suite

1. **Upload files to Pico:**
   - [src/debug.py](../src/debug.py)
   - [src/test_breakpoints.py](../src/test_breakpoints.py)

2. **Enable debugging in config:**
   ```python
   # In src/config.py
   DEBUG_BREAKPOINTS = True
   DEBUG_TRACE = True
   ```

3. **Run tests in Thonny REPL:**
   ```python
   >>> import test_breakpoints
   >>> test_breakpoints.run_all_tests()
   ```

4. **Expected output:**
   - Test 1: Simple breakpoint example
   - Test 2: Conditional breakpoint (only triggers once)
   - Test 3: Watchpoint (triggers on state change)
   - Test 4: Tracepoint log dump
   - Test 5: Debug status summary

### Manual Testing

**Test simple breakpoint:**
```python
>>> from debug import debug
>>> import config
>>> config.DEBUG_BREAKPOINTS = True
>>> debug.bp("test", voltage=1.274, stable=True)
```

**Test conditional breakpoint:**
```python
>>> for i in range(10):
...     debug.bp_if(i == 5, "found_five", value=i)
```

**Test tracepoint:**
```python
>>> config.DEBUG_TRACE = True
>>> for i in range(5):
...     debug.trace("loop", iteration=i)
>>> debug.dump_trace()
```

---

## Usage Examples

### Example 1: Debug Dip Detection

```python
# In dip_detector.py
def process_sample(...):
    # Trace every sample
    debug.trace("sample", ch=channel_name, v=v, stable=st.stable)
    
    # Break when approaching dip trigger
    if v <= start_thresh:
        st.below_count += 1
        debug.bp_if(
            st.below_count == self.start_hold - 1,
            "dip_about_to_trigger",
            channel=channel_name,
            below_count=st.below_count,
            threshold_V=start_thresh
        )
    
    # Break when dip starts
    if st.below_count >= self.start_hold:
        debug.bp("dip_started",
                 channel=channel_name,
                 voltage_V=v,
                 baseline_V=baseline,
                 drop_mV=(baseline - v) * 1000)
```

### Example 2: Track Baseline Convergence

```python
# In channel_state.py
def update_baseline_with_median(self, med_v):
    old_baseline = self.baseline
    
    self.baseline_buf.append(med_v)
    if len(self.baseline_buf) > self._baseline_len:
        self.baseline_buf.pop(0)
    
    if len(self.baseline_buf) >= 3:
        self.baseline = median(self.baseline_buf)
        
        # Break when baseline first becomes valid
        if old_baseline is None and self.baseline is not None:
            debug.bp("baseline_converged",
                     channel=self.channel_name,
                     baseline_V=self.baseline,
                     samples_used=len(self.baseline_buf))
```

### Example 3: Monitor Stability State

```python
# In main loop
watch_stable = debug.watch("PLC_stable", break_on_change=True)

for channel_name, st in states.items():
    if channel_name == "PLC":
        watch_stable.check(st.stable, 
                          time_s=t_s,
                          span_V=max(st.raw_win) - min(st.raw_win) if st.raw_win else 0)
```

## Advanced Techniques

### Technique 1: Performance Profiling

**Track execution time:**
```python
start_ms = time.ticks_ms()
# ... code to profile ...
duration_ms = time.ticks_ms() - start_ms

debug.bp_if(duration_ms > 50, 
            "slow_execution",
            duration_ms=duration_ms,
            threshold_ms=50)
```

### Technique 2: State Machine Visualization

**Log all state transitions:**
```python
state_watch = debug.watch("state", break_on_change=False)

# In state machine
for new_state in state_sequence:
    state_watch.check(new_state)
    debug.trace("state_change", 
                old=state_watch.last_value,
                new=new_state)
```

Then dump trace to see full state history.

### Technique 3: Conditional Trace

**Only trace when condition is met:**
```python
def process_sample(...):
    # Only trace when unstable
    if not st.stable:
        debug.trace("unstable_sample",
                    ch=channel_name,
                    v=v,
                    span=max(st.raw_win) - min(st.raw_win))
```

### Technique 4: Breakpoint Batching

**Break after N occurrences:**
```python
counter = 0

def process(...):
    global counter
    counter += 1
    debug.bp_if(counter % 100 == 0,  # Every 100th call
                "periodic_check",
                call_count=counter)
```

### Technique 5: Exception Tracking

**Break on errors:**
```python
try:
    risky_operation()
except Exception as e:
    debug.bp("exception_caught",
             error_type=type(e).__name__,
             error_msg=str(e))
    raise
```

---

## Performance Impact

### Overhead Analysis

| Feature | Overhead (when disabled) | Overhead (when enabled) |
|---------|--------------------------|-------------------------|
| `debug.bp()` | ~0.001ms | ~1-5ms (print time) |
| `debug.bp_if()` | ~0.002ms | 0.002ms (false) / 1-5ms (true) |
| `debug.trace()` | ~0.001ms | ~0.1ms (list append) |
| `debug.watch.check()` | ~0.002ms | ~0.003ms (no change) / 1-5ms (changed) |

**Impact on 10ms tick:**
- Disabled: Negligible (<1% of tick)
- Enabled with tracing only: ~1% of tick
- Enabled with frequent breakpoints: Can pause execution

**Recommendations:**
- **Development:** All features enabled
- **Testing:** Tracepoints only (no breakpoints)
- **Production:** All disabled (`DEBUG_* = False`)

### Minimizing Impact

```python
# Bad: Check flag every time
if config.DEBUG_BREAKPOINTS:
    debug.bp("location", v=v)

# Good: Import check (once per module load)
try:
    from debug import debug
    HAS_DEBUG = True
except ImportError:
    HAS_DEBUG = False

# Then use HAS_DEBUG flag
if HAS_DEBUG:
    debug.bp("location", v=v)
```

---

## Troubleshooting

### Issue: Breakpoints Not Triggering

**Symptoms:** No breakpoint output

**Solutions:**
1. Check `DEBUG_BREAKPOINTS = True` in [config.py](../src/config.py)
2. Verify `debug.py` is uploaded to Pico
3. Check import: `from debug import debug` (no errors?)
4. Test manually: `debug.bp("test", value=123)`

### Issue: Too Much Output

**Symptoms:** Console flooded with breakpoint messages

**Solutions:**
1. Use conditional breakpoints: `debug.bp_if(rare_condition, ...)`
2. Replace breakpoints with tracepoints: `debug.trace(...)`
3. Disable breakpoints, view trace later: `debug.dump_trace()`
4. Adjust frequency: Only break every Nth time

### Issue: Trace Buffer Full

**Symptoms:** Old events getting dropped

**Solutions:**
1. Increase buffer size in `debug.py`:
   ```python
   if len(self.trace_log) > 100:  # Change to 500
   ```
2. Dump trace more frequently:
   ```python
   if len(debug.trace_log) > 80:
       debug.dump_trace()
       debug.clear_trace()
   ```

### Issue: Program Pauses Unexpectedly

**Symptoms:** Execution stops at breakpoints you don't want

**Solutions:**
1. Remove or comment out breakpoints
2. Make breakpoints conditional:
   ```python
   debug.bp_if(False, "disabled", ...)  # Never triggers
   ```
3. Disable globally:
   ```python
   config.DEBUG_BREAKPOINTS = False
   ```

---

## Further Possibilities

### Future Enhancements

**1. Remote Debugging**
- Send breakpoint data over WiFi (Pico W)
- View breakpoints in web dashboard
- Real-time variable inspection

**2. Graphical Trace Viewer**
- Export trace log to CSV
- Visualize state transitions in matplotlib
- Timeline view of events

**3. Conditional Trace Filters**
```python
debug.trace_if(condition, "event", ...)  # Only trace when true
```

**4. Statistical Breakpoints**
```python
debug.bp_every_n(100, "periodic", ...)  # Every 100th call
debug.bp_random(0.01, "rare", ...)      # 1% probability
```

**5. Memory Profiling**
```python
import gc
debug.bp("memory_check",
         free_bytes=gc.mem_free(),
         allocated_bytes=gc.mem_alloc())
```

**6. Call Stack Tracing**
```python
import sys
debug.bp("location",
         caller=sys._getframe(1).f_code.co_name)
```

---

## Summary

**Soft breakpoints provide:**
- ✅ Variable inspection at specific locations
- ✅ Conditional debugging (only when needed)
- ✅ State change monitoring (watchpoints)
- ✅ Event logging without pausing (tracepoints)

**They don't provide:**
- ❌ CPU-level breakpoints (hardware limitation)
- ❌ Step-through execution (MicroPython interpreter)
- ❌ Memory/register inspection (no debugger access)

**For MicroPython embedded development, soft breakpoints are the practical solution.**

---

## Quick Reference

```python
from debug import debug

# Simple breakpoint
debug.bp("name", var1=val1, var2=val2)

# Conditional breakpoint
debug.bp_if(condition, "name", var1=val1)

# Tracepoint
debug.trace("event", var1=val1)

# Watchpoint
watch = debug.watch("var_name")
watch.check(current_value)

# View trace
debug.dump_trace(last_n=20)

# Status
debug.status()

# Control
debug.enable()
debug.disable()
debug.reset()
```

---

## Related Documentation

- [Architecture](architecture.md) - System design
- [Troubleshooting](troubleshooting.md) - Common issues

---

**Happy debugging! 🐛**

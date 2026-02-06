# Matplotlib Plotting Guide

Quick guide for visualizing Pico voltage data using matplotlib offline plotting tools.

**Note:** If you're using Grafana exclusively, you don't need matplotlib. This guide is for offline CSV analysis.

---

## Installation

```powershell
pip install matplotlib
```

---

## Quick Test with Sample Data

The easiest way to see what the plotting tools do:

```powershell
# Plot sample median data (voltage over time)
python tools/plot_medians.py examples/pico_medians_sample.csv

# Plot sample dip events
python tools/plot_dips.py examples/pico_dips_sample.csv
```

A matplotlib window will pop up showing the plots. Close it to continue.

---

## Plotting Real Data from Pico

### Step 1: Download CSV Files

**⚠️ Important:** Close Thonny before downloading (serial port conflict)

```powershell
# Download all CSV files from Pico
python tools/download_from_pico.py --port COM9 --output ./data
```

Replace `COM9` with your Pico's serial port.

### Step 2: Plot the Data

```powershell
# Plot voltage medians
python tools/plot_medians.py data/pico_medians.csv

# Plot dip events (if any dips were detected)
python tools/plot_dips.py data/pico_dips.csv

# Generate comprehensive data quality report
python tools/data_quality_report.py data/pico_medians.csv
```

---

## What Each Tool Shows

### plot_medians.py - Voltage Trends

Creates **2 subplots:**

1. **Voltage Over Time (top chart)**
   - Line plot for each channel (PLC, MODEM, BATTERY)
   - Shows voltage trends and stability
   - Legend includes:
     - Mean voltage per channel
     - Standard deviation (noise level)
     - Min/max values

2. **Baseline Noise (bottom chart)**
   - Rolling standard deviation (30-sample window)
   - Shows noise characteristics over time
   - Helps identify noisy periods or unstable connections

**Use cases:**
- Verify stable voltage readings
- Identify baseline drift over time
- Measure noise levels
- Compare channel stability

### plot_dips.py - Dip Event Analysis

Creates **6 subplots:**

1. **Baseline vs Minimum Voltage**
   - **Bars:** Baseline voltage (stable voltage before dip)
   - **Triangles:** Minimum voltage reached during dip
   - **Red lines:** Visual representation of the drop
   - Shows each dip numbered sequentially
   - **Purpose:** See the absolute voltage context - not just drop magnitude, but where the voltage actually was
   - **Example:** PLC baseline at 1.250V dropped to 1.080V

2. **Dip Drops Over Time**
   - **X-axis:** When the dip happened (seconds since start)
   - **Y-axis:** Drop magnitude (mV)
   - **Purpose:** Identify if dips get worse over time or happen randomly
   - **Use case:** Battery degradation might show increasing drops over days/weeks
   - **Example:** If all large drops happen late in the timeline, battery is degrading

3. **Dip Durations Over Time**
   - **X-axis:** When the dip happened (seconds since start)
   - **Y-axis:** How long the dip lasted (milliseconds)
   - **Purpose:** See if dips get longer/shorter over time
   - **Use case:** Aging batteries might have longer recovery times
   - **Example:** Consistent duration = stable system, increasing = degradation

4. **Drop vs Duration Correlation**
   - **X-axis:** Dip duration (milliseconds)
   - **Y-axis:** Drop magnitude (mV)
   - **Purpose:** Determine if bigger drops last longer
   - **Pattern interpretation:**
     - Diagonal cluster: Bigger drops correlate with longer duration
     - Random scatter: Drop size and duration are independent
     - Horizontal cluster: All drops are similar magnitude regardless of duration
   - **Example:** If points form diagonal line, severe dips also last longer

5. **Distribution of Dip Drops**
   - **Histogram** showing how many dips fall into each magnitude range
   - **X-axis:** Drop magnitude buckets (e.g., 170-180mV, 180-190mV)
   - **Y-axis:** Count of dips in each bucket
   - **Purpose:** Show typical range and variability of dips
   - **Pattern interpretation:**
     - Narrow peak: Consistent, predictable dips (e.g., all ~170mV)
     - Wide spread: Variable dips (e.g., 100-300mV range)
     - Multiple peaks: Different failure modes or conditions
   - **Example:** All dips in one bucket = very consistent behavior

6. **Dip Statistics Summary**
   - **Table** with comprehensive statistics per channel
   - Columns: Channel, Count, Avg Drop, Max Drop, Avg Duration, Max Duration, Avg Baseline
   - Includes "Overall" row for all channels combined
   - **Purpose:** Quick reference for numerical analysis and comparison

**Real-world interpretation example:**

Monitoring a car battery over a month:
- **Drops Over Time:** Shows if voltage sags are getting worse (battery aging)
- **Durations Over Time:** Shows if recovery takes longer (internal resistance increasing)
- **Correlation:** Reveals if severe drops also take longer to recover (capacity loss)
- **Distribution:** Shows if the battery behaves consistently or erratically

**Note:** With small datasets (5 dips over 30 seconds), patterns aren't obvious. Long-term monitoring (days/weeks) reveals meaningful trends like degradation, temperature effects, or load-related patterns.

**Use cases:**
- Analyze dip severity
- Find patterns in dip events
- Compare channels
- Identify worst-case scenarios

### data_quality_report.py - Comprehensive Analysis

Generates **text report** with:

1. **Data Coverage**
   - Total runtime
   - Samples per channel
   - Sample rate
   - Data gaps (if any)

2. **Baseline Stability**
   - Mean voltage per channel
   - Standard deviation
   - Voltage range (min to max)
   - Drift analysis

3. **Noise Characteristics**
   - Noise histogram
   - Percentiles (P50, P90, P95, P99)
   - High-noise periods

4. **Channel Health**
   - Stability percentage
   - Outlier detection
   - Comparison across channels

**Use cases:**
- Long-term data validation
- Identify data quality issues
- Generate reports for documentation
- Compare different test runs

---

## Examples

### Example 1: Verify Data After Download

```powershell
# Download data
python tools/download_from_pico.py --port COM9 --output ./data

# Validate integrity
python tools/validate_csv.py data/pico_medians.csv

# Plot to visualize
python tools/plot_medians.py data/pico_medians.csv
```

### Example 2: Analyze Dip Events

```powershell
# Check if dips were detected
python tools/validate_csv.py data/pico_dips.csv

# Plot dip analysis
python tools/plot_dips.py data/pico_dips.csv
```

### Example 3: Generate Quality Report

```powershell
# Comprehensive analysis
python tools/data_quality_report.py data/pico_medians.csv
```

---

## Tips

### Saving Plots to Files

Matplotlib plots open in interactive windows by default. To save as images, modify the script or:

1. Open the plot window
2. Click the save icon (💾) in the toolbar
3. Choose PNG, PDF, or SVG format
4. Save to your desired location

### Customizing Plots

The plotting scripts are in `tools/` and easy to modify:

- **Change colors:** Edit the `color=` parameter in plot calls
- **Adjust window size:** Modify `figsize=(12, 8)` values
- **Change time range:** Slice the data before plotting
- **Add annotations:** Use matplotlib's `annotate()` function

### Batch Processing

Plot multiple files:

```powershell
# Windows PowerShell
Get-ChildItem data\*.csv | ForEach-Object {
    python tools/plot_medians.py $_.FullName
}
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'matplotlib'"

Install matplotlib:
```powershell
pip install matplotlib
```

### "FileNotFoundError: [Errno 2] No such file or directory"

Check the file path:
```powershell
# List files in data directory
ls data

# Use correct path
python tools/plot_medians.py data/pico_medians.csv
```

### "No data to plot" or Empty Plots

- Check CSV file has data (not just headers)
- For `plot_dips.py`: Requires actual dip events in CSV
- Validate CSV first: `python tools/validate_csv.py your_file.csv`

### Plot Window Doesn't Appear

- Check if matplotlib backend is configured
- Try non-interactive mode: add `--no-show` flag (if implemented)
- Or use Jupyter notebook for inline plotting

### "UserWarning: No artists with labels found to put in legend"

**Cause:** Sample file too small for rolling statistics

The noise analysis chart uses a 30-sample rolling window. The sample files only have 2 data points, so the bottom chart is empty.

**This is expected and harmless.** The warning just means "no data in that subplot."

**To see full plots:**
- Use real data (download from Pico after running for 30+ seconds)
- Or use the simulator: `python tools/simulate_dips.py --duration 60`

**To suppress the warning:**
Ignore it - doesn't affect the main voltage plot (top chart), which displays correctly.

---

## Matplotlib vs Grafana

| Feature | Matplotlib | Grafana |
|---------|------------|---------|
| **Real-time** | ❌ (static files only) | ✅ |
| **Storage** | CSV files | InfluxDB |
| **Setup** | `pip install matplotlib` | Docker + InfluxDB |
| **Use case** | Offline analysis | Live monitoring |
| **Customization** | Full Python control | Dashboard JSON |
| **Best for** | Reports, analysis | Production monitoring |

**Recommendation:** Use Grafana for live monitoring, matplotlib for offline analysis and report generation.

---

## Related Documentation

- [Download data from Pico](QUICKSTART.md#downloading-data)
- [CSV file formats](data-formats.md)
- [Data validation](../tools/validate_csv.py)
- [Grafana setup](SETUP_INFLUXDB.md)

---

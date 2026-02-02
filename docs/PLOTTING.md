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
   - Line plot for each channel (GP26, GP27, GP28)
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

Creates **4 subplots:**

1. **Dip Drops Over Time**
   - Bar chart showing voltage drop magnitude (mV)
   - X-axis: Time when dip occurred
   - Y-axis: Drop magnitude
   - Color-coded by channel

2. **Dip Durations Over Time**
   - Bar chart showing how long each dip lasted (ms)
   - Identifies short glitches vs sustained dips

3. **Drop vs Duration Correlation**
   - Scatter plot
   - Shows relationship between dip depth and duration
   - Helps identify dip patterns

4. **Summary Statistics**
   - Table with per-channel statistics:
     - Count (number of dips)
     - Mean drop (average magnitude)
     - Max drop (worst case)
     - Mean duration (average length)
     - Max duration (longest dip)

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

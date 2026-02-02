"""Plot medians CSV with enhanced statistics (host-side).

Displays voltage over time with baseline statistics and drift analysis.

Usage: python tools/plot_medians.py examples/pico_medians_sample.csv
"""
import sys
import csv
from collections import defaultdict
import statistics


def plot(path):
    import matplotlib.pyplot as plt
    
    data = defaultdict(list)
    with open(path, newline='') as f:
        r = csv.reader(f)
        next(r)
        for t, ch, v in r:
            data[ch].append((float(t), float(v)))
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot voltage over time
    for ch, arr in data.items():
        times = [a for a, _ in arr]
        vals = [b for _, b in arr]
        ax1.plot(times, vals, label=ch, alpha=0.7)
        
        # Calculate statistics
        mean_v = statistics.mean(vals)
        stdev_v = statistics.stdev(vals) if len(vals) > 1 else 0
        
        print(f"\n{ch} Statistics:")
        print(f"  Mean:     {mean_v:.4f} V")
        print(f"  Std Dev:  {stdev_v*1000:.2f} mV")
        print(f"  Range:    {min(vals):.4f} - {max(vals):.4f} V")
        print(f"  Samples:  {len(vals)}")
    
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_title('Voltage Medians Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot baseline stability (rolling std dev)
    window_size = 30  # 30-point window
    for ch, arr in data.items():
        vals = [b for _, b in arr]
        times = [a for a, _ in arr]
        
        if len(vals) < window_size:
            continue
        
        rolling_std = []
        rolling_times = []
        
        for i in range(window_size, len(vals)):
            window = vals[i-window_size:i]
            rolling_std.append(statistics.stdev(window) * 1000)  # Convert to mV
            rolling_times.append(times[i])
        
        ax2.plot(rolling_times, rolling_std, label=f'{ch} noise', alpha=0.7)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Noise (mV, rolling std dev)')
    ax2.set_title(f'Baseline Noise ({window_size}-sample window)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools/plot_medians.py <medians.csv>')
    else:
        plot(sys.argv[1])

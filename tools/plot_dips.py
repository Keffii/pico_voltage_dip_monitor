"""Plot dip events CSV with statistics (host-side).

Displays dip drops over time and analyzes dip patterns.

Usage: python tools/plot_dips.py examples/pico_dips_sample.csv
"""
import sys
import csv
import matplotlib.pyplot as plt
from collections import defaultdict
import statistics


def plot(path):
    # Load dip data
    dips_by_channel = defaultdict(list)
    all_dips = []
    
    with open(path, newline='') as f:
        r = csv.reader(f)
        next(r)
        for ch, start, end, dur, base, mn, drop in r:
            dip = {
                'channel': ch,
                'start': float(start),
                'end': float(end),
                'duration_ms': int(dur),
                'baseline': float(base),
                'min_v': float(mn),
                'drop': float(drop)
            }
            dips_by_channel[ch].append(dip)
            all_dips.append(dip)
    
    if not all_dips:
        print("No dips found in file")
        return
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Dip drops over time
    for ch, dips in dips_by_channel.items():
        times = [d['start'] for d in dips]
        drops = [d['drop'] * 1000 for d in dips]  # Convert to mV
        ax1.scatter(times, drops, label=ch, s=100, alpha=0.6)
    
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Voltage Drop (mV)')
    ax1.set_title('Dip Drops Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Dip durations
    for ch, dips in dips_by_channel.items():
        times = [d['start'] for d in dips]
        durations = [d['duration_ms'] for d in dips]
        ax2.scatter(times, durations, label=ch, s=100, alpha=0.6)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Duration (ms)')
    ax2.set_title('Dip Durations Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Drop vs Duration scatter
    for ch, dips in dips_by_channel.items():
        drops = [d['drop'] * 1000 for d in dips]
        durations = [d['duration_ms'] for d in dips]
        ax3.scatter(durations, drops, label=ch, s=100, alpha=0.6)
    
    ax3.set_xlabel('Duration (ms)')
    ax3.set_ylabel('Voltage Drop (mV)')
    ax3.set_title('Drop vs Duration Correlation')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Histogram of drops
    for ch, dips in dips_by_channel.items():
        drops = [d['drop'] * 1000 for d in dips]
        ax4.hist(drops, bins=20, label=ch, alpha=0.6)
    
    ax4.set_xlabel('Voltage Drop (mV)')
    ax4.set_ylabel('Count')
    ax4.set_title('Distribution of Dip Drops')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Print statistics
    print(f"\n{'='*60}")
    print("DIP STATISTICS")
    print(f"{'='*60}\n")
    
    for ch in sorted(dips_by_channel.keys()):
        dips = dips_by_channel[ch]
        drops = [d['drop'] * 1000 for d in dips]
        durations = [d['duration_ms'] for d in dips]
        
        print(f"{ch}:")
        print(f"  Total dips:       {len(dips)}")
        print(f"  Avg drop:         {statistics.mean(drops):.2f} mV")
        print(f"  Max drop:         {max(drops):.2f} mV")
        print(f"  Avg duration:     {statistics.mean(durations):.1f} ms")
        print(f"  Max duration:     {max(durations)} ms")
        print()
    
    print(f"Overall:")
    all_drops = [d['drop'] * 1000 for d in all_dips]
    all_durations = [d['duration_ms'] for d in all_dips]
    print(f"  Total dips:       {len(all_dips)}")
    print(f"  Avg drop:         {statistics.mean(all_drops):.2f} mV")
    print(f"  Avg duration:     {statistics.mean(all_durations):.1f} ms")
    print(f"{'='*60}\n")
    
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools/plot_dips.py <dips.csv>')
    else:
        plot(sys.argv[1])

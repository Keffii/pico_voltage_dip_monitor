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
    
    # Create subplots - now 6 panels (3x2)
    fig = plt.figure(figsize=(16, 12))
    ax1 = plt.subplot(2, 3, 1)  # Baseline + Min voltages
    ax2 = plt.subplot(2, 3, 2)  # Drop magnitude
    ax3 = plt.subplot(2, 3, 3)  # Duration
    ax4 = plt.subplot(2, 3, 4)  # Drop vs Duration
    ax5 = plt.subplot(2, 3, 5)  # Drop distribution
    ax6 = plt.subplot(2, 3, 6)  # Statistics table
    
    # Plot 1: Baseline and Minimum Voltages (NEW - shows context!)
    x_pos = range(len(all_dips))
    baselines = [d['baseline'] for d in all_dips]
    min_vs = [d['min_v'] for d in all_dips]
    channels = [d['channel'] for d in all_dips]
    
    # Color map for channels
    colors = {'GP26': 'tab:blue', 'GP27': 'tab:orange', 'GP28': 'tab:green'}
    bar_colors = [colors.get(ch, 'gray') for ch in channels]
    
    # Plot baselines as bars
    ax1.bar(x_pos, baselines, alpha=0.3, color=bar_colors, label='Baseline', edgecolor='black')
    # Plot minimum voltages as markers
    ax1.scatter(x_pos, min_vs, c=bar_colors, s=100, marker='v', label='Minimum', zorder=5, edgecolors='black')
    
    # Draw lines showing the drop
    for i, dip in enumerate(all_dips):
        ax1.plot([i, i], [dip['baseline'], dip['min_v']], 'r-', alpha=0.5, linewidth=2)
    
    ax1.set_xlabel('Dip Event #')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_title('Baseline vs Minimum Voltage')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([f"{i+1}" for i in x_pos])
    
    # Add legend with channel colors
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=colors[ch], alpha=0.6, label=ch) 
                       for ch in sorted(dips_by_channel.keys())]
    ax1.legend(handles=legend_elements, loc='best')
    
    # Plot 2: Dip drops over time
    for ch, dips in dips_by_channel.items():
        times = [d['start'] for d in dips]
        drops = [d['drop'] * 1000 for d in dips]  # Convert to mV
        ax2.scatter(times, drops, label=ch, s=100, alpha=0.6)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage Drop (mV)')
    ax2.set_title('Dip Drops Over Time')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Dip durations
    for ch, dips in dips_by_channel.items():
        times = [d['start'] for d in dips]
        durations = [d['duration_ms'] for d in dips]
        ax3.scatter(times, durations, label=ch, s=100, alpha=0.6)
    
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Duration (ms)')
    ax3.set_title('Dip Durations Over Time')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Drop vs Duration scatter
    for ch, dips in dips_by_channel.items():
        drops = [d['drop'] * 1000 for d in dips]
        durations = [d['duration_ms'] for d in dips]
        ax4.scatter(durations, drops, label=ch, s=100, alpha=0.6)
    
    ax4.set_xlabel('Duration (ms)')
    ax4.set_ylabel('Voltage Drop (mV)')
    ax4.set_title('Drop vs Duration Correlation')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Histogram of drops
    for ch, dips in dips_by_channel.items():
        drops = [d['drop'] * 1000 for d in dips]
        ax5.hist(drops, bins=20, label=ch, alpha=0.6)
    
    ax5.set_xlabel('Voltage Drop (mV)')
    ax5.set_ylabel('Count')
    ax5.set_title('Distribution of Dip Drops')
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Plot 6: Statistics Table
    ax6.axis('tight')
    ax6.axis('off')
    
    # Build statistics table
    table_data = [['Channel', 'Count', 'Avg Drop\n(mV)', 'Max Drop\n(mV)', 'Avg Dur\n(ms)', 'Max Dur\n(ms)', 'Avg Base\n(V)']]
    
    for ch in sorted(dips_by_channel.keys()):
        dips = dips_by_channel[ch]
        drops = [d['drop'] * 1000 for d in dips]
        durations = [d['duration_ms'] for d in dips]
        baselines = [d['baseline'] for d in dips]
        
        row = [
            ch,
            str(len(dips)),
            f"{statistics.mean(drops):.1f}",
            f"{max(drops):.1f}",
            f"{statistics.mean(durations):.1f}",
            str(max(durations)),
            f"{statistics.mean(baselines):.3f}"
        ]
        table_data.append(row)
    
    # Add overall row
    all_drops = [d['drop'] * 1000 for d in all_dips]
    all_durations = [d['duration_ms'] for d in all_dips]
    all_baselines = [d['baseline'] for d in all_dips]
    table_data.append([
        'Overall',
        str(len(all_dips)),
        f"{statistics.mean(all_drops):.1f}",
        f"{max(all_drops):.1f}",
        f"{statistics.mean(all_durations):.1f}",
        str(max(all_durations)),
        f"{statistics.mean(all_baselines):.3f}"
    ])
    
    table = ax6.table(cellText=table_data, cellLoc='center', loc='center',
                      colWidths=[0.14, 0.11, 0.16, 0.16, 0.16, 0.16, 0.16])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 2.5)
    
    # Style header row
    for i in range(7):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Style overall row
    for i in range(7):
        table[(len(table_data)-1, i)].set_facecolor('#E0E0E0')
        table[(len(table_data)-1, i)].set_text_props(weight='bold')
    
    ax6.set_title('Dip Statistics Summary', fontsize=12, weight='bold', pad=20)
    
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

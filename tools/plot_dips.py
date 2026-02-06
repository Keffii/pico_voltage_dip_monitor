"""Plot dip events CSV with statistics (host-side).

Displays dip drops over time and analyzes dip patterns.

Usage: python tools/plot_dips.py examples/pico_dips_sample.csv
"""
import sys
import csv
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
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
    
    # Create subplots - 2x2 dashboard layout
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.2], height_ratios=[1, 1])
    ax1 = fig.add_subplot(gs[0, 0])  # Baseline vs Minimum Voltage (keep)
    ax2 = fig.add_subplot(gs[0, 1])  # Voltage Dip Events (new graph)
    ax3 = fig.add_subplot(gs[1, 0])  # Baseline Tracking (new graph)
    ax6 = fig.add_subplot(gs[1, 1])  # Statistics table (keep)
    
    # Plot 1: Baseline and Minimum Voltages (NEW - shows context!)
    x_pos = range(len(all_dips))
    baselines = [d['baseline'] for d in all_dips]
    min_vs = [d['min_v'] for d in all_dips]
    channels = [d['channel'] for d in all_dips]
    
    # Color map for channels
    colors = {'PLC': 'tab:blue', 'MODEM': 'tab:orange', 'BATTERY': 'tab:green'}
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
    
    # Plot 2: Voltage Dip Events (baseline + shaded dip blocks)
    for ch, dips in dips_by_channel.items():
        times = [d['start'] for d in dips]
        baselines = [d['baseline'] for d in dips]
        ax2.plot(times, baselines, marker='o', markersize=3, linewidth=1.2,
                 color=colors.get(ch, 'gray'), label=ch, alpha=0.9)
    
    for dip in all_dips:
        start = dip['start']
        end = dip['end']
        baseline = dip['baseline']
        min_v = dip['min_v']
        ch = dip['channel']
        width = max(0.001, end - start)
        height = max(0.001, baseline - min_v)
        ax2.add_patch(
            Rectangle(
                (start, min_v),
                width,
                height,
                facecolor=colors.get(ch, 'gray'),
                alpha=0.25,
                edgecolor='none'
            )
        )
        ax2.plot([start, end], [min_v, min_v], color=colors.get(ch, 'gray'), alpha=0.6, linewidth=1)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Voltage (V)')
    ax2.set_title('Voltage Dip Events')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Baseline Tracking (from dips)
    for ch, dips in dips_by_channel.items():
        times = [d['start'] for d in dips]
        baselines = [d['baseline'] for d in dips]
        ax3.plot(times, baselines, marker='o', markersize=4, linewidth=1.5, label=ch, color=colors.get(ch, 'gray'))
    
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Baseline (V)')
    ax3.set_title('Baseline Tracking')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
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

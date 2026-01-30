"""Plot dip events CSV (host-side).

Usage: python tools/plot_dips.py examples/pico_dips_sample.csv
"""
import sys
import csv
import matplotlib.pyplot as plt

def plot(path):
    times = []
    drops = []
    with open(path, newline='') as f:
        r = csv.reader(f)
        next(r)
        for ch, start, end, dur, base, mn, drop in r:
            times.append(float(start))
            drops.append(float(drop))
    plt.bar(times, drops, width=0.02)
    plt.xlabel('dip_start_s')
    plt.ylabel('drop_V')
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools/plot_dips.py <dips.csv>')
    else:
        plot(sys.argv[1])

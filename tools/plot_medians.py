"""Small helper to plot medians CSV (host-side).

Usage: python tools/plot_medians.py examples/pico_medians_sample.csv
"""
import sys
import csv
from collections import defaultdict

def plot(path):
    import matplotlib.pyplot as plt
    data = defaultdict(list)
    with open(path, newline='') as f:
        r = csv.reader(f)
        next(r)
        for t, ch, v in r:
            data[ch].append((float(t), float(v)))
    for ch, arr in data.items():
        times = [a for a,_ in arr]
        vals = [b for _,b in arr]
        plt.plot(times, vals, label=ch)
    plt.xlabel('time_s')
    plt.ylabel('median_V')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python tools/plot_medians.py <medians.csv>')
    else:
        plot(sys.argv[1])

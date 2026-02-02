"""Generate comprehensive data quality report from CSV files.

Analyzes:
- Uptime and data coverage
- Baseline stability and drift
- Noise characteristics
- Data gaps
- Channel health

Usage:
    python tools/data_quality_report.py data/pico_medians.csv
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import statistics


class DataQualityAnalyzer:
    def __init__(self, medians_file):
        self.medians_file = Path(medians_file)
        self.data = defaultdict(list)  # channel -> [(time, voltage), ...]
    
    def load_data(self):
        """Load median data from CSV."""
        print(f"Loading data from {self.medians_file}...")
        
        with open(self.medians_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                time_s = float(row['time_s'])
                channel = row['channel']
                voltage = float(row['median_V'])
                self.data[channel].append((time_s, voltage))
        
        # Sort by time
        for channel in self.data:
            self.data[channel].sort(key=lambda x: x[0])
        
        print(f"Loaded {sum(len(v) for v in self.data.values())} data points across {len(self.data)} channels\n")
    
    def analyze_coverage(self):
        """Analyze time coverage and gaps."""
        print(f"{'='*60}")
        print("TIME COVERAGE ANALYSIS")
        print(f"{'='*60}\n")
        
        for channel in sorted(self.data.keys()):
            points = self.data[channel]
            if not points:
                continue
            
            times = [t for t, _ in points]
            start_time = times[0]
            end_time = times[-1]
            duration = end_time - start_time
            
            # Find gaps
            gaps = []
            for i in range(1, len(times)):
                dt = times[i] - times[i-1]
                if dt > 0.5:  # Gap larger than 500ms
                    gaps.append((times[i-1], times[i], dt))
            
            print(f"{channel}:")
            print(f"  Data points:  {len(points):,}")
            print(f"  Start time:   {start_time:.3f}s")
            print(f"  End time:     {end_time:.3f}s")
            print(f"  Duration:     {duration:.1f}s ({duration/60:.1f} min)")
            print(f"  Sample rate:  {len(points)/duration:.2f} Hz (expected: 10 Hz)")
            
            if gaps:
                print(f"  Data gaps:    {len(gaps)}")
                for t1, t2, dt in gaps[:5]:  # Show first 5 gaps
                    print(f"    {t1:.3f}s -> {t2:.3f}s ({dt:.3f}s gap)")
                if len(gaps) > 5:
                    print(f"    ... and {len(gaps)-5} more")
            else:
                print(f"  Data gaps:    None ✓")
            
            print()
    
    def analyze_baseline_stability(self):
        """Analyze baseline stability and drift."""
        print(f"{'='*60}")
        print("BASELINE STABILITY ANALYSIS")
        print(f"{'='*60}\n")
        
        for channel in sorted(self.data.keys()):
            points = self.data[channel]
            if not points:
                continue
            
            voltages = [v for _, v in points]
            
            mean_v = statistics.mean(voltages)
            stdev_v = statistics.stdev(voltages) if len(voltages) > 1 else 0
            min_v = min(voltages)
            max_v = max(voltages)
            span_v = max_v - min_v
            
            # Compute drift (first 10% vs last 10%)
            n = len(voltages)
            first_10pct = voltages[:n//10] if n >= 10 else voltages[:n//2]
            last_10pct = voltages[-n//10:] if n >= 10 else voltages[-n//2:]
            
            drift_v = statistics.mean(last_10pct) - statistics.mean(first_10pct)
            drift_pct = (drift_v / mean_v) * 100 if mean_v > 0 else 0
            
            print(f"{channel}:")
            print(f"  Mean voltage:     {mean_v:.4f} V")
            print(f"  Std deviation:    {stdev_v*1000:.2f} mV")
            print(f"  Range:            {min_v:.4f} - {max_v:.4f} V (span: {span_v*1000:.2f} mV)")
            print(f"  Baseline drift:   {drift_v*1000:+.2f} mV ({drift_pct:+.2f}%)")
            
            # Stability rating
            if stdev_v < 0.005:
                rating = "Excellent ✓✓✓"
            elif stdev_v < 0.010:
                rating = "Good ✓✓"
            elif stdev_v < 0.020:
                rating = "Fair ✓"
            else:
                rating = "Poor ✗"
            
            print(f"  Stability:        {rating}")
            print()
    
    def analyze_noise(self):
        """Analyze noise characteristics."""
        print(f"{'='*60}")
        print("NOISE ANALYSIS")
        print(f"{'='*60}\n")
        
        for channel in sorted(self.data.keys()):
            points = self.data[channel]
            if len(points) < 10:
                continue
            
            # Compute sample-to-sample differences (noise proxy)
            diffs = []
            for i in range(1, len(points)):
                v1 = points[i-1][1]
                v2 = points[i][1]
                diffs.append(abs(v2 - v1))
            
            avg_noise = statistics.mean(diffs)
            max_noise = max(diffs)
            
            # Count large jumps
            large_jumps = sum(1 for d in diffs if d > 0.05)  # > 50mV
            
            print(f"{channel}:")
            print(f"  Avg noise (∆V):   {avg_noise*1000:.2f} mV")
            print(f"  Max noise (∆V):   {max_noise*1000:.2f} mV")
            print(f"  Large jumps:      {large_jumps} (>{50}mV)")
            
            if avg_noise < 0.005:
                quality = "Low noise ✓"
            elif avg_noise < 0.015:
                quality = "Moderate"
            else:
                quality = "High noise ✗"
            
            print(f"  Noise level:      {quality}")
            print()
    
    def generate_summary(self):
        """Generate overall summary."""
        print(f"{'='*60}")
        print("OVERALL SUMMARY")
        print(f"{'='*60}\n")
        
        total_points = sum(len(v) for v in self.data.values())
        
        if not self.data:
            print("No data found")
            return
        
        # Get time range
        all_times = []
        for points in self.data.values():
            all_times.extend([t for t, _ in points])
        
        duration = max(all_times) - min(all_times)
        
        print(f"Total data points:  {total_points:,}")
        print(f"Total duration:     {duration:.1f}s ({duration/60:.1f} min, {duration/3600:.1f} hr)")
        print(f"Channels:           {len(self.data)}")
        print(f"\nData quality:       Check individual sections above")
        print(f"{'='*60}\n")
    
    def run(self):
        """Run full analysis."""
        self.load_data()
        self.analyze_coverage()
        self.analyze_baseline_stability()
        self.analyze_noise()
        self.generate_summary()


def main():
    parser = argparse.ArgumentParser(description='Generate data quality report')
    parser.add_argument('medians_file', help='Path to pico_medians.csv')
    
    args = parser.parse_args()
    
    analyzer = DataQualityAnalyzer(args.medians_file)
    analyzer.run()


if __name__ == '__main__':
    main()

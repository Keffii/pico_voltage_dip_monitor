"""Validate CSV files from Pico for data quality issues.

Checks for:
- Missing data / gaps in timestamps
- Timestamp anomalies (backwards time, large jumps)
- Voltage out of range
- Corrupted lines
- File integrity

Usage:
    python tools/validate_csv.py data/pico_medians.csv
    python tools/validate_csv.py data/pico_dips.csv
"""

import argparse
import csv
import sys
from pathlib import Path


class CSVValidator:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.errors = []
        self.warnings = []
        self.stats = {}
    
    def error(self, msg):
        self.errors.append(msg)
        print(f"ERROR: {msg}")
    
    def warning(self, msg):
        self.warnings.append(msg)
        print(f"WARNING: {msg}")
    
    def info(self, msg):
        print(f"INFO: {msg}")
    
    def validate_medians(self):
        """Validate pico_medians.csv format."""
        print(f"\nValidating medians file: {self.filepath}")
        print("="*60)
        
        if not self.filepath.exists():
            self.error(f"File not found: {self.filepath}")
            return
        
        try:
            with open(self.filepath, 'r') as f:
                reader = csv.DictReader(f)
                
                # Check header
                if reader.fieldnames != ['time_s', 'channel', 'median_V']:
                    self.error(f"Invalid header: {reader.fieldnames}")
                    return
                
                prev_time = {}
                line_count = 0
                voltage_range = {'min': float('inf'), 'max': float('-inf')}
                channels = set()
                
                for i, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                    line_count += 1
                    
                    try:
                        time_s = float(row['time_s'])
                        channel = row['channel']
                        voltage = float(row['median_V'])
                        
                        channels.add(channel)
                        
                        # Track voltage range
                        voltage_range['min'] = min(voltage_range['min'], voltage)
                        voltage_range['max'] = max(voltage_range['max'], voltage)
                        
                        # Check voltage range
                        if voltage < 0 or voltage > 3.3:
                            self.warning(f"Line {i}: Voltage {voltage}V out of expected range [0, 3.3]")
                        
                        # Check time sequence per channel
                        if channel in prev_time:
                            dt = time_s - prev_time[channel]
                            
                            if dt < 0:
                                self.error(f"Line {i}: Time went backwards for {channel} ({prev_time[channel]} -> {time_s})")
                            elif dt == 0:
                                self.warning(f"Line {i}: Duplicate timestamp {time_s} for {channel}")
                            elif dt > 1.0:  # Gap larger than 1 second
                                self.warning(f"Line {i}: Large time gap {dt:.3f}s for {channel}")
                        
                        prev_time[channel] = time_s
                    
                    except ValueError as e:
                        self.error(f"Line {i}: Invalid data format: {e}")
                    except KeyError as e:
                        self.error(f"Line {i}: Missing column: {e}")
                
                self.stats = {
                    'lines': line_count,
                    'channels': sorted(channels),
                    'voltage_range': voltage_range,
                    'duration_s': max(prev_time.values()) - min(prev_time.values()) if prev_time else 0
                }
        
        except Exception as e:
            self.error(f"Failed to read file: {e}")
    
    def validate_dips(self):
        """Validate pico_dips.csv format."""
        print(f"\nValidating dips file: {self.filepath}")
        print("="*60)
        
        if not self.filepath.exists():
            self.error(f"File not found: {self.filepath}")
            return
        
        try:
            with open(self.filepath, 'r') as f:
                reader = csv.DictReader(f)
                
                # Check header
                expected_header = ['channel', 'dip_start_s', 'dip_end_s', 'duration_ms', 'baseline_V', 'min_V', 'drop_V']
                if reader.fieldnames != expected_header:
                    self.error(f"Invalid header: {reader.fieldnames}")
                    return
                
                line_count = 0
                channels = set()
                durations = []
                drops = []
                
                for i, row in enumerate(reader, start=2):
                    line_count += 1
                    
                    try:
                        channel = row['channel']
                        start_s = float(row['dip_start_s'])
                        end_s = float(row['dip_end_s'])
                        duration_ms = int(row['duration_ms'])
                        baseline_v = float(row['baseline_V'])
                        min_v = float(row['min_V'])
                        drop_v = float(row['drop_V'])
                        
                        channels.add(channel)
                        durations.append(duration_ms)
                        drops.append(drop_v)
                        
                        # Validate consistency
                        if end_s <= start_s:
                            self.error(f"Line {i}: End time {end_s} <= start time {start_s}")
                        
                        expected_duration = int((end_s - start_s) * 1000)
                        if abs(expected_duration - duration_ms) > 1:
                            self.warning(f"Line {i}: Duration mismatch (calculated {expected_duration}ms, logged {duration_ms}ms)")
                        
                        expected_drop = baseline_v - min_v
                        if abs(expected_drop - drop_v) > 0.001:
                            self.warning(f"Line {i}: Drop mismatch (calculated {expected_drop:.3f}V, logged {drop_v:.3f}V)")
                        
                        if min_v > baseline_v:
                            self.error(f"Line {i}: Min voltage {min_v} > baseline {baseline_v}")
                        
                        if drop_v < 0:
                            self.error(f"Line {i}: Negative drop {drop_v}V")
                    
                    except ValueError as e:
                        self.error(f"Line {i}: Invalid data format: {e}")
                    except KeyError as e:
                        self.error(f"Line {i}: Missing column: {e}")
                
                self.stats = {
                    'dips': line_count,
                    'channels': sorted(channels),
                    'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
                    'max_duration_ms': max(durations) if durations else 0,
                    'avg_drop_v': sum(drops) / len(drops) if drops else 0,
                    'max_drop_v': max(drops) if drops else 0
                }
        
        except Exception as e:
            self.error(f"Failed to read file: {e}")
    
    def print_summary(self):
        """Print validation summary."""
        print(f"\n{'='*60}")
        print(f"VALIDATION SUMMARY")
        print(f"{'='*60}")
        
        if self.stats:
            print("\nStatistics:")
            for key, value in self.stats.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        
        print(f"\nResults:")
        print(f"  Errors:   {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n{'='*60}")
            print("ERRORS FOUND - DATA MAY BE CORRUPTED")
            print(f"{'='*60}")
            return False
        elif self.warnings:
            print(f"\n{'='*60}")
            print("WARNINGS FOUND - DATA USABLE BUT CHECK ISSUES")
            print(f"{'='*60}")
            return True
        else:
            print(f"\n{'='*60}")
            print("✓ VALIDATION PASSED - DATA OK")
            print(f"{'='*60}")
            return True


def main():
    parser = argparse.ArgumentParser(description='Validate Pico CSV files')
    parser.add_argument('file', help='CSV file to validate')
    
    args = parser.parse_args()
    
    filepath = Path(args.file)
    validator = CSVValidator(filepath)
    
    # Detect file type from name
    if 'median' in filepath.name.lower():
        validator.validate_medians()
    elif 'dip' in filepath.name.lower():
        validator.validate_dips()
    else:
        print(f"ERROR: Unknown file type: {filepath.name}")
        print("Expected 'medians' or 'dips' in filename")
        return 1
    
    success = validator.print_summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

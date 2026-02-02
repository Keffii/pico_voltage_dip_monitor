"""Create sample dip data for testing Grafana dashboards.

This creates realistic dip events without needing the full simulator.
"""

import tempfile
import os
import csv
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import argparse


def create_sample_dips():
    """Create sample dip CSV data."""
    temp_dir = tempfile.gettempdir()
    dips_file = os.path.join(temp_dir, 'sample_dips.csv')
    
    # Sample dip events with realistic values
    dips = [
        # channel, start_s, end_s, duration_ms, baseline_V, min_V, drop_V
        ('GP26', 5.123, 5.245, 122, 1.250, 1.080, 0.170),
        ('GP27', 12.456, 12.589, 133, 1.270, 1.095, 0.175),
        ('GP28', 18.789, 18.920, 131, 1.290, 1.075, 0.215),
        ('GP26', 25.234, 25.389, 155, 1.250, 1.050, 0.200),
        ('GP27', 32.567, 32.712, 145, 1.270, 1.090, 0.180),
    ]
    
    with open(dips_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['channel', 'dip_start_s', 'dip_end_s', 'duration_ms', 'baseline_V', 'min_V', 'drop_V'])
        for dip in dips:
            writer.writerow(dip)
    
    print(f"Created sample dips file: {dips_file}")
    print(f"  {len(dips)} dip events")
    return dips_file


def upload_to_influxdb(dips_file, args):
    """Upload dip data to InfluxDB."""
    client = InfluxDBClient(url=args.influx_url, token=args.token, org=args.org)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    count = 0
    with open(dips_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            channel = row['channel']
            start_s = float(row['dip_start_s'])
            end_s = float(row['dip_end_s'])
            duration_ms = float(row['duration_ms'])
            baseline_V = float(row['baseline_V'])
            min_V = float(row['min_V'])
            drop_V = float(row['drop_V'])
            
            # Create point with current timestamp
            timestamp = datetime.now(timezone.utc)
            
            point = Point("voltage_dip") \
                .tag("channel", channel) \
                .field("drop_V", drop_V) \
                .field("min_V", min_V) \
                .field("baseline_V", baseline_V) \
                .field("duration_ms", duration_ms) \
                .field("start_s", start_s) \
                .field("end_s", end_s) \
                .time(timestamp)
            
            write_api.write(bucket=args.bucket, record=point)
            count += 1
            print(f"  Uploaded: {channel} - {drop_V:.3f}V drop, {duration_ms:.0f}ms")
    
    client.close()
    return count


def main():
    parser = argparse.ArgumentParser(description='Create and upload sample dip data')
    parser.add_argument('--influx-url', default='http://localhost:8086')
    parser.add_argument('--token', required=True)
    parser.add_argument('--org', default='pico')
    parser.add_argument('--bucket', default='pico_voltage')
    
    args = parser.parse_args()
    
    print("="*60)
    print("CREATE SAMPLE DIP DATA FOR GRAFANA")
    print("="*60)
    
    # Create sample dips
    dips_file = create_sample_dips()
    
    # Upload to InfluxDB
    print(f"\nUploading to InfluxDB...")
    print(f"  URL: {args.influx_url}")
    print(f"  Org: {args.org}")
    print(f"  Bucket: {args.bucket}")
    print()
    
    count = upload_to_influxdb(dips_file, args)
    
    print(f"\n{'='*60}")
    print(f"COMPLETE - Uploaded {count} dip events")
    print(f"{'='*60}")
    print(f"\nView in Grafana: http://localhost:3000")
    print(f"Check the 'Voltage Dip Events' panel!")


if __name__ == '__main__':
    main()

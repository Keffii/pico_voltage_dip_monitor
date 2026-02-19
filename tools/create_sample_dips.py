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
    parser.add_argument('--csv-only', action='store_true', 
                        help='Only create CSV file, skip InfluxDB upload')
    parser.add_argument('--output', default=None,
                        help='Output directory for CSV file (default: temp directory)')
    parser.add_argument('--influx-url', default='http://localhost:8086')
    parser.add_argument('--token', required=False)
    parser.add_argument('--org', default='pico')
    parser.add_argument('--bucket', default='pico_voltage')
    
    args = parser.parse_args()
    
    # Check if token is required
    if not args.csv_only and not args.token:
        parser.error('--token is required when uploading to InfluxDB (use --csv-only to skip upload)')
    
    print("="*60)
    if args.csv_only:
        print("CREATE SAMPLE DIP DATA (CSV ONLY)")
    else:
        print("CREATE SAMPLE DIP DATA FOR GRAFANA")
    print("="*60)
    
    # Create sample dips
    if args.output:
        # Use custom output directory
        os.makedirs(args.output, exist_ok=True)
        dips_file = os.path.join(args.output, 'sample_dips.csv')
        temp_dir = args.output
    else:
        temp_dir = tempfile.gettempdir()
        dips_file = os.path.join(temp_dir, 'sample_dips.csv')
    
    # Sample dip events with realistic values
    dips = [
        # channel, start_s, end_s, duration_ms, baseline_V, min_V, drop_V
        ('BLUE', 5.123, 5.245, 122, 1.250, 1.080, 0.170),
        ('YELLOW', 12.456, 12.589, 133, 1.270, 1.095, 0.175),
        ('GREEN', 18.789, 18.920, 131, 1.290, 1.075, 0.215),
        ('BLUE', 25.234, 25.389, 155, 1.250, 1.050, 0.200),
        ('YELLOW', 32.567, 32.712, 145, 1.270, 1.090, 0.180),
    ]
    
    with open(dips_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['channel', 'dip_start_s', 'dip_end_s', 'duration_ms', 'baseline_V', 'min_V', 'drop_V'])
        for dip in dips:
            writer.writerow(dip)
    
    print(f"Created sample dips file: {dips_file}")
    print(f"  {len(dips)} dip events")
    
    if args.csv_only:
        print(f"\n{'='*60}")
        print(f"COMPLETE - CSV file created")
        print(f"{'='*60}")
        print(f"\nVisualize with:")
        print(f'  python tools/plot_dips.py "{dips_file}"')
        return
    
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

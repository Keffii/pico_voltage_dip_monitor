"""Upload simulated CSV data to InfluxDB for Grafana visualization.

Usage:
    python tools/upload_sim_to_influx.py
"""

import argparse
import csv
import tempfile
import os
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


def upload_medians(write_api, bucket, medians_file):
    """Upload median data to InfluxDB."""
    count = 0
    print(f"\nUploading medians from {medians_file}...")
    
    with open(medians_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_s = float(row['time_s'])
            channel = row['channel']
            voltage = float(row['median_V'])
            
            # Create point with timestamp
            timestamp = datetime.now(timezone.utc)
            
            point = Point("voltage_median") \
                .tag("channel", channel) \
                .field("voltage", voltage) \
                .time(timestamp)
            
            write_api.write(bucket=bucket, record=point)
            count += 1
    
    print(f"  ✓ Uploaded {count} median points")
    return count


def upload_dips(write_api, bucket, dips_file):
    """Upload dip data to InfluxDB."""
    if not os.path.exists(dips_file):
        print(f"\nNo dips file found: {dips_file}")
        return 0
    
    count = 0
    print(f"\nUploading dips from {dips_file}...")
    
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
            
            # Create point with timestamp
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
            
            write_api.write(bucket=bucket, record=point)
            count += 1
    
    print(f"  ✓ Uploaded {count} dip events")
    return count


def upload_baselines(write_api, bucket):
    """Upload baseline snapshots to InfluxDB."""
    print(f"\nUploading baseline snapshots...")
    
    # Create baseline points for each channel
    baselines = {
        'BLUE': 1.25,
        'YELLOW': 1.25, 
        'GREEN': 1.25
    }
    
    count = 0
    for channel, baseline in baselines.items():
        timestamp = datetime.now(timezone.utc)
        
        point = Point("voltage_baseline") \
            .tag("channel", channel) \
            .field("baseline", baseline) \
            .time(timestamp)
        
        write_api.write(bucket=bucket, record=point)
        count += 1
    
    print(f"  ✓ Uploaded {count} baseline points")
    return count


def main():
    parser = argparse.ArgumentParser(description='Upload simulated data to InfluxDB')
    parser.add_argument('--influx-url', default='http://localhost:8086',
                        help='InfluxDB URL (default: http://localhost:8086)')
    parser.add_argument('--token', required=True,
                        help='InfluxDB API token')
    parser.add_argument('--org', default='pico',
                        help='InfluxDB organization (default: pico)')
    parser.add_argument('--bucket', default='pico_voltage',
                        help='InfluxDB bucket (default: pico_voltage)')
    
    args = parser.parse_args()
    
    # Find simulated files in temp directory
    temp_dir = tempfile.gettempdir()
    medians_file = os.path.join(temp_dir, 'sim_medians.csv')
    dips_file = os.path.join(temp_dir, 'sim_dips.csv')
    
    if not os.path.exists(medians_file):
        print(f"ERROR: Simulated data not found at {medians_file}")
        print(f"\nRun this first: python tools/simulate_dips.py")
        return 1
    
    print(f"{'='*60}")
    print(f"UPLOAD SIMULATED DATA TO INFLUXDB")
    print(f"{'='*60}")
    print(f"InfluxDB URL:     {args.influx_url}")
    print(f"Organization:     {args.org}")
    print(f"Bucket:           {args.bucket}")
    print(f"Medians file:     {medians_file}")
    print(f"Dips file:        {dips_file}")
    print(f"{'='*60}")
    
    # Connect to InfluxDB
    client = InfluxDBClient(url=args.influx_url, token=args.token, org=args.org)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    try:
        # Upload data
        median_count = upload_medians(write_api, args.bucket, medians_file)
        dip_count = upload_dips(write_api, args.bucket, dips_file)
        baseline_count = upload_baselines(write_api, args.bucket)
        
        print(f"\n{'='*60}")
        print(f"UPLOAD COMPLETE")
        print(f"{'='*60}")
        print(f"Total medians:    {median_count}")
        print(f"Total dips:       {dip_count}")
        print(f"Total baselines:  {baseline_count}")
        print(f"{'='*60}\n")
        print(f"View in Grafana: http://localhost:3000")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1
    finally:
        client.close()
    
    return 0


if __name__ == '__main__':
    exit(main())

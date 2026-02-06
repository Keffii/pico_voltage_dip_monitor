"""Live monitor for Pico voltage data streaming to InfluxDB.

Reads serial output from Pico and writes to InfluxDB.
Supports real-time Grafana visualization.

Prerequisites:
    pip install influxdb-client pyserial

Usage:
    python tools/live_monitor.py --port COM9 --influx-url http://localhost:8086 --bucket pico_voltage

Stream format from Pico:
    MEDIAN,<time_s>,<channel>,<voltage>
    DIP,<channel>,<start_s>,<end_s>,<duration_ms>,<baseline_V>,<min_V>,<drop_V>
    BASELINE,<time_s>,<channel>,<baseline_V>
"""

import argparse
import sys
import time
from datetime import datetime, timezone
import serial
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


class PicoInfluxLogger:
    def __init__(self, influx_url, token, org, bucket, serial_port, baudrate=115200):
        self.serial_port = serial_port
        self.baudrate = baudrate
        
        # InfluxDB setup
        self.client = InfluxDBClient(url=influx_url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.bucket = bucket
        
        self.ser = None
        self.running = False
        
        # Statistics
        self.stats = {
            'medians': 0,
            'dips': 0,
            'baselines': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    def connect_serial(self):
        """Connect to Pico serial port."""
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            print(f"Connected to {self.serial_port} at {self.baudrate} baud")
            # Wait for port to stabilize
            time.sleep(2)
            # Flush any initial garbage
            self.ser.reset_input_buffer()
            return True
        except Exception as e:
            print(f"ERROR: Failed to connect to serial port: {e}")
            return False
    
    def parse_median(self, parts):
        """Parse MEDIAN line: MEDIAN,<time_s>,<channel>,<voltage>"""
        if len(parts) != 4:
            raise ValueError(f"Invalid MEDIAN format: expected 4 parts, got {len(parts)}")
        
        _, time_s, channel, voltage = parts
        
        point = Point("voltage_median") \
            .tag("channel", channel) \
            .field("voltage", float(voltage)) \
            .time(datetime.now(timezone.utc))
        
        self.write_api.write(bucket=self.bucket, record=point)
        self.stats['medians'] += 1
    
    def parse_dip(self, parts):
        """Parse DIP line: DIP,<channel>,<start_s>,<end_s>,<duration_ms>,<baseline_V>,<min_V>,<drop_V>"""
        if len(parts) != 8:
            raise ValueError(f"Invalid DIP format: expected 8 parts, got {len(parts)}")
        
        _, channel, start_s, end_s, duration_ms, baseline_v, min_v, drop_v = parts
        
        point = Point("voltage_dip") \
            .tag("channel", channel) \
            .field("dip_start_s", float(start_s)) \
            .field("dip_end_s", float(end_s)) \
            .field("duration_ms", float(duration_ms)) \
            .field("baseline_V", float(baseline_v)) \
            .field("min_V", float(min_v)) \
            .field("drop_V", float(drop_v)) \
            .time(datetime.now(timezone.utc))
        
        self.write_api.write(bucket=self.bucket, record=point)
        self.stats['dips'] += 1
        
        print(f"[DIP] {channel}: {drop_v}V drop, {duration_ms}ms duration")
    
    def parse_baseline(self, parts):
        """Parse BASELINE line: BASELINE,<time_s>,<channel>,<baseline_V>"""
        if len(parts) != 4:
            raise ValueError(f"Invalid BASELINE format: expected 4 parts, got {len(parts)}")
        
        _, time_s, channel, baseline_v = parts
        
        point = Point("voltage_baseline") \
            .tag("channel", channel) \
            .field("baseline", float(baseline_v)) \
            .time(datetime.now(timezone.utc))
        
        self.write_api.write(bucket=self.bucket, record=point)
        self.stats['baselines'] += 1
    
    def parse_line(self, line):
        """Parse a line from serial stream."""
        line = line.strip()
        if not line:
            return
        
        # Skip non-data lines (status messages, etc.)
        if not line.startswith(('MEDIAN,', 'DIP,', 'BASELINE,')):
            # Print status/info messages
            if not line.startswith('='):  # Skip separator lines
                print(f"[PICO] {line}")
            return
        
        try:
            parts = line.split(',')
            msg_type = parts[0]
            
            if msg_type == 'MEDIAN':
                self.parse_median(parts)
            elif msg_type == 'DIP':
                self.parse_dip(parts)
            elif msg_type == 'BASELINE':
                self.parse_baseline(parts)
            else:
                print(f"Unknown message type: {msg_type}")
        
        except Exception as e:
            print(f"ERROR parsing line '{line}': {e}")
            self.stats['errors'] += 1
    
    def print_stats(self):
        """Print statistics summary."""
        uptime = time.time() - self.stats['start_time']
        print(f"\n{'='*60}")
        print(f"STATS @ {uptime:.0f}s uptime")
        print(f"{'='*60}")
        print(f"Medians logged:   {self.stats['medians']:,}")
        print(f"Dips logged:      {self.stats['dips']}")
        print(f"Baselines logged: {self.stats['baselines']}")
        print(f"Parse errors:     {self.stats['errors']}")
        print(f"Rate:             {self.stats['medians']/uptime:.1f} medians/sec")
        print(f"{'='*60}\n")
    
    def run(self):
        """Main monitoring loop."""
        if not self.connect_serial():
            return
        
        self.running = True
        print("\nMonitoring Pico data stream. Press Ctrl+C to stop.\n")
        
        last_stats_time = time.time()
        stats_interval = 60  # Print stats every 60 seconds
        
        buf = ""
        try:
            while self.running:
                try:
                    if self.ser.in_waiting:
                        chunk = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                        if chunk:
                            buf += chunk
                            while '\n' in buf:
                                line, buf = buf.split('\n', 1)
                                self.parse_line(line)
                    
                    # Periodic stats
                    if time.time() - last_stats_time >= stats_interval:
                        self.print_stats()
                        last_stats_time = time.time()
                
                except UnicodeDecodeError:
                    # Skip malformed serial data
                    pass
                except Exception as e:
                    print(f"ERROR in main loop: {e}")
                    self.stats['errors'] += 1
        
        except KeyboardInterrupt:
            print("\n\nShutdown requested...")
        
        finally:
            self.running = False
            if self.ser:
                self.ser.close()
            self.client.close()
            
            print("\nFinal statistics:")
            self.print_stats()
            print("Disconnected.")


def main():
    parser = argparse.ArgumentParser(
        description='Stream Pico voltage data to InfluxDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python tools/live_monitor.py --port COM9
  
  # Custom InfluxDB settings
  python tools/live_monitor.py --port COM9 --influx-url http://localhost:8086 \\
      --token my-token --org my-org --bucket pico_voltage
  
  # Linux serial port
  python tools/live_monitor.py --port /dev/ttyACM0
        """
    )
    
    parser.add_argument('--port', required=True,
                        help='Serial port (e.g., COM9 or /dev/ttyACM0)')
    parser.add_argument('--baudrate', type=int, default=115200,
                        help='Serial baudrate (default: 115200)')
    parser.add_argument('--influx-url', default='http://localhost:8086',
                        help='InfluxDB URL (default: http://localhost:8086)')
    parser.add_argument('--token', default='',
                        help='InfluxDB token (default: empty for no auth)')
    parser.add_argument('--org', default='pico',
                        help='InfluxDB organization (default: pico)')
    parser.add_argument('--bucket', default='pico_voltage',
                        help='InfluxDB bucket (default: pico_voltage)')
    
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print(f"PICO VOLTAGE MONITOR -> INFLUXDB")
    print(f"{'='*60}")
    print(f"Serial port:      {args.port}")
    print(f"Baudrate:         {args.baudrate}")
    print(f"InfluxDB URL:     {args.influx_url}")
    print(f"Organization:     {args.org}")
    print(f"Bucket:           {args.bucket}")
    print(f"{'='*60}\n")
    
    logger = PicoInfluxLogger(
        influx_url=args.influx_url,
        token=args.token,
        org=args.org,
        bucket=args.bucket,
        serial_port=args.port,
        baudrate=args.baudrate
    )
    
    logger.run()


if __name__ == '__main__':
    main()

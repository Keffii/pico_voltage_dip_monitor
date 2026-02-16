"""Live monitor for Pico voltage data over serial.

Reads serial output from Pico and prints parsed values.
Can optionally write parsed values to InfluxDB.

Prerequisites:
    pip install pyserial

Optional InfluxDB support:
    pip install influxdb-client

Usage:
    # Serial-only monitor (no token or InfluxDB required)
    python tools/live_monitor.py --port COM9

    # Serial + InfluxDB
    python tools/live_monitor.py --port COM9 --write-influx --influx-url http://localhost:8086 --bucket pico_voltage

Stream format from Pico:
    MEDIAN,<time_s>,<channel>,<voltage>
    DIP,<channel>,<start_s>,<end_s>,<duration_ms>,<baseline_V>,<min_V>,<drop_V>
    BASELINE,<time_s>,<channel>,<baseline_V>
"""

import argparse
import time
from datetime import datetime, timezone
import serial


class PicoInfluxLogger:
    def __init__(
        self,
        serial_port,
        baudrate=115200,
        write_influx=False,
        influx_url='http://localhost:8086',
        token='',
        org='pico',
        bucket='pico_voltage'
    ):
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.write_influx = write_influx
        self.influx_url = influx_url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.write_api = None
        self.point_cls = None
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

    def connect_influx(self):
        """Initialize InfluxDB client when enabled."""
        if not self.write_influx:
            return True

        try:
            from influxdb_client import InfluxDBClient, Point
            from influxdb_client.client.write_api import SYNCHRONOUS
        except ImportError:
            print("ERROR: InfluxDB output requested, but influxdb-client is not installed.")
            print("Install it with: pip install influxdb-client")
            return False

        try:
            self.client = InfluxDBClient(url=self.influx_url, token=self.token, org=self.org)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.point_cls = Point
            print(f"InfluxDB enabled: {self.influx_url} (org={self.org}, bucket={self.bucket})")
            return True
        except Exception as e:
            print(f"ERROR: Failed to connect to InfluxDB: {e}")
            return False

    def write_point(self, measurement, channel, fields):
        """Write a measurement point to InfluxDB if enabled."""
        if not self.write_influx or self.write_api is None or self.point_cls is None:
            return

        point = self.point_cls(measurement).tag("channel", channel)
        for key, value in fields.items():
            point = point.field(key, value)
        point = point.time(datetime.now(timezone.utc))
        self.write_api.write(bucket=self.bucket, record=point)
    
    def parse_median(self, parts):
        """Parse MEDIAN line: MEDIAN,<time_s>,<channel>,<voltage>"""
        if len(parts) != 4:
            raise ValueError(f"Invalid MEDIAN format: expected 4 parts, got {len(parts)}")
        
        _, time_s, channel, voltage = parts
        time_s_f = float(time_s)
        voltage_f = float(voltage)

        self.write_point(
            measurement="voltage_median",
            channel=channel,
            fields={"voltage": voltage_f}
        )

        self.stats['medians'] += 1
        print(f"[MEDIAN] {time_s_f:8.3f}s {channel}: {voltage_f:.3f}V")
    
    def parse_dip(self, parts):
        """Parse DIP line: DIP,<channel>,<start_s>,<end_s>,<duration_ms>,<baseline_V>,<min_V>,<drop_V>"""
        if len(parts) != 8:
            raise ValueError(f"Invalid DIP format: expected 8 parts, got {len(parts)}")
        
        _, channel, start_s, end_s, duration_ms, baseline_v, min_v, drop_v = parts
        baseline_v_f = float(baseline_v)
        min_v_f = float(min_v)
        drop_v_f = float(drop_v)
        drop_pct = (-(drop_v_f / baseline_v_f) * 100.0) if baseline_v_f > 0 else 0.0

        self.write_point(
            measurement="voltage_dip",
            channel=channel,
            fields={
                "dip_start_s": float(start_s),
                "dip_end_s": float(end_s),
                "duration_ms": float(duration_ms),
                "baseline_V": baseline_v_f,
                "min_V": min_v_f,
                "drop_V": drop_v_f,
                "drop_pct": drop_pct,
            }
        )

        self.stats['dips'] += 1
        
        print(f"[DIP] {channel}: {drop_v_f:.3f}V drop ({drop_pct:.1f}%), {duration_ms}ms duration")
    
    def parse_baseline(self, parts):
        """Parse BASELINE line: BASELINE,<time_s>,<channel>,<baseline_V>"""
        if len(parts) != 4:
            raise ValueError(f"Invalid BASELINE format: expected 4 parts, got {len(parts)}")
        
        _, time_s, channel, baseline_v = parts
        time_s_f = float(time_s)
        baseline_v_f = float(baseline_v)

        self.write_point(
            measurement="voltage_baseline",
            channel=channel,
            fields={"baseline": baseline_v_f}
        )

        self.stats['baselines'] += 1
        print(f"[BASELINE] {time_s_f:8.3f}s {channel}: {baseline_v_f:.3f}V")
    
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
        rate = self.stats['medians'] / uptime if uptime > 0 else 0.0
        print(f"Rate:             {rate:.1f} medians/sec")
        print(f"{'='*60}\n")
    
    def run(self):
        """Main monitoring loop."""
        if not self.connect_serial():
            return
        if not self.connect_influx():
            return
        
        self.running = True
        mode = "serial + InfluxDB" if self.write_influx else "serial-only"
        print(f"\nMonitoring Pico data stream ({mode}). Press Ctrl+C to stop.\n")
        
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
            if self.client:
                self.client.close()
            
            print("\nFinal statistics:")
            self.print_stats()
            print("Disconnected.")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor Pico serial stream with optional InfluxDB output',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Serial-only monitor (no token required)
  python tools/live_monitor.py --port COM9
  
  # Enable InfluxDB output
  python tools/live_monitor.py --port COM9 --write-influx --influx-url http://localhost:8086 \\
      --token my-token --org my-org --bucket pico_voltage
  
  # Linux serial port
  python tools/live_monitor.py --port /dev/ttyACM0
        """
    )
    
    parser.add_argument('--port', required=True,
                        help='Serial port (e.g., COM9 or /dev/ttyACM0)')
    parser.add_argument('--baudrate', type=int, default=115200,
                        help='Serial baudrate (default: 115200)')
    parser.add_argument('--write-influx', action='store_true',
                        help='Write parsed values to InfluxDB (default: disabled)')
    parser.add_argument('--influx-url', default='http://localhost:8086',
                        help='InfluxDB URL (default: http://localhost:8086)')
    parser.add_argument('--token', default='',
                        help='InfluxDB token (only used with --write-influx)')
    parser.add_argument('--org', default='pico',
                        help='InfluxDB organization (only used with --write-influx)')
    parser.add_argument('--bucket', default='pico_voltage',
                        help='InfluxDB bucket (only used with --write-influx)')
    
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print(f"PICO VOLTAGE MONITOR")
    print(f"{'='*60}")
    print(f"Serial port:      {args.port}")
    print(f"Baudrate:         {args.baudrate}")
    print(f"Mode:             {'Serial + InfluxDB' if args.write_influx else 'Serial only'}")
    if args.write_influx:
        print(f"InfluxDB URL:     {args.influx_url}")
        print(f"Organization:     {args.org}")
        print(f"Bucket:           {args.bucket}")
    else:
        print(f"InfluxDB:         Disabled")
    print(f"{'='*60}\n")
    
    logger = PicoInfluxLogger(
        serial_port=args.port,
        baudrate=args.baudrate,
        write_influx=args.write_influx,
        influx_url=args.influx_url,
        token=args.token,
        org=args.org,
        bucket=args.bucket
    )
    
    logger.run()


if __name__ == '__main__':
    main()

"""Download CSV files from Pico via serial/REPL.

Usage:
    python tools/download_from_pico.py --port COM9 --output ./data/
"""

import argparse
import os
import time
import serial


class PicoDownloader:
    def __init__(self, port, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
    
    def connect(self):
        """Connect to Pico."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=2)
            print(f"Connected to {self.port}")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"ERROR: Failed to connect: {e}")
            return False
    
    def send_interrupt(self):
        """Send Ctrl+C to stop running program."""
        self.ser.write(b'\x03')
        time.sleep(0.5)
        self.ser.reset_input_buffer()
    
    def enter_repl(self):
        """Enter REPL mode."""
        print("Entering REPL...")
        self.send_interrupt()
        self.send_interrupt()  # Send twice to be sure
        
        # Send Enter to get prompt
        self.ser.write(b'\r\n')
        time.sleep(0.5)
        
        # Clear buffer
        self.ser.reset_input_buffer()
        print("REPL ready")
    
    def execute_command(self, cmd):
        """Execute Python command in REPL and return output."""
        self.ser.write((cmd + '\r\n').encode())
        time.sleep(0.1)
        
        output = []
        timeout = time.time() + 5
        
        while time.time() < timeout:
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line and not line.startswith('>>>'):
                    output.append(line)
            else:
                time.sleep(0.05)
        
        return '\n'.join(output)
    
    def read_file(self, filepath):
        """Read file content from Pico."""
        print(f"Reading {filepath}...")
        
        cmd = f"""
with open('{filepath}', 'r') as f:
    print(f.read())
"""
        
        self.ser.write(cmd.encode())
        time.sleep(0.5)
        
        content = []
        timeout = time.time() + 10
        
        while time.time() < timeout:
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8', errors='ignore')
                if '>>>' not in line and line.strip():
                    content.append(line.rstrip('\r\n'))
            else:
                if content:  # Got some content, wait a bit more
                    time.sleep(0.1)
                else:
                    time.sleep(0.05)
        
        # Remove echo of command and prompt
        filtered = []
        in_content = False
        for line in content:
            if line.strip().startswith('with open'):
                in_content = True
                continue
            if in_content and '>>>' not in line:
                filtered.append(line)
        
        return '\n'.join(filtered)
    
    def list_files(self):
        """List all files on Pico."""
        print("Listing files on Pico...")
        
        cmd = """import os
for f in os.listdir('/'):
    print(f)
"""
        
        self.ser.write(cmd.encode())
        time.sleep(0.5)
        
        files = []
        while self.ser.in_waiting:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line and not line.startswith('>>>') and 'import os' not in line and 'for f' not in line and 'print' not in line:
                files.append(line)
        
        return files
    
    def download_file(self, filename, output_dir):
        """Download a single file."""
        content = self.read_file(f'/{filename}')
        
        if not content:
            print(f"WARNING: {filename} is empty or failed to read")
            return False
        
        output_path = os.path.join(output_dir, filename)
        
        try:
            with open(output_path, 'w') as f:
                f.write(content)
            print(f"✓ Downloaded {filename} ({len(content)} bytes)")
            return True
        except Exception as e:
            print(f"ERROR: Failed to write {output_path}: {e}")
            return False
    
    def download_all_csv(self, output_dir):
        """Download all CSV files from Pico."""
        os.makedirs(output_dir, exist_ok=True)
        
        files = self.list_files()
        csv_files = [f for f in files if f.endswith('.csv')]
        
        if not csv_files:
            print("No CSV files found on Pico")
            return
        
        print(f"\nFound {len(csv_files)} CSV files:")
        for f in csv_files:
            print(f"  - {f}")
        print()
        
        success = 0
        for filename in csv_files:
            if self.download_file(filename, output_dir):
                success += 1
        
        print(f"\n{'='*60}")
        print(f"Download complete: {success}/{len(csv_files)} files")
        print(f"Output directory: {os.path.abspath(output_dir)}")
        print(f"{'='*60}")
    
    def close(self):
        """Close serial connection."""
        if self.ser:
            self.ser.close()
            print("Disconnected")


def main():
    parser = argparse.ArgumentParser(description='Download CSV files from Pico')
    parser.add_argument('--port', required=True, help='Serial port (e.g., COM9)')
    parser.add_argument('--output', default='./data', help='Output directory (default: ./data)')
    parser.add_argument('--baudrate', type=int, default=115200, help='Baudrate (default: 115200)')
    
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print(f"PICO CSV DOWNLOADER")
    print(f"{'='*60}")
    print(f"Port:   {args.port}")
    print(f"Output: {os.path.abspath(args.output)}")
    print(f"{'='*60}\n")
    
    downloader = PicoDownloader(args.port, args.baudrate)
    
    try:
        if downloader.connect():
            downloader.enter_repl()
            downloader.download_all_csv(args.output)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        downloader.close()


if __name__ == '__main__':
    main()

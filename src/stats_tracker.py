# stats_tracker.py

import time
import gc
import os

class StatsTracker:
    def __init__(self):
        self.start_ms = time.ticks_ms()
        self.total_samples = 0
        self.total_medians_computed = 0
        self.total_medians_logged = 0
        self.dips_detected = {}
        self.flash_writes = 0
        self.baseline_first_valid_ms = {}
        
    def record_sample(self):
        self.total_samples += 1
    
    def record_median_computed(self):
        self.total_medians_computed += 1
        
    def record_median_logged(self):
        self.total_medians_logged += 1
        
    def record_dip(self, channel_name):
        if channel_name not in self.dips_detected:
            self.dips_detected[channel_name] = 0
        self.dips_detected[channel_name] += 1
        
    def record_flash_write(self, lines_written=1):
        self.flash_writes += lines_written
        
    def record_baseline_valid(self, channel_name):
        if channel_name not in self.baseline_first_valid_ms:
            self.baseline_first_valid_ms[channel_name] = time.ticks_ms()
    
    def get_uptime_s(self):
        return time.ticks_diff(time.ticks_ms(), self.start_ms) / 1000.0
    
    def get_baseline_convergence_time_s(self, channel_name):
        if channel_name not in self.baseline_first_valid_ms:
            return None
        return time.ticks_diff(self.baseline_first_valid_ms[channel_name], self.start_ms) / 1000.0
    
    def get_file_size(self, filepath):
        try:
            stat = os.stat(filepath)
            return stat[6]  # Size in bytes
        except OSError:
            return 0
    
    def get_memory_stats(self):
        gc.collect()
        return {
            'free': gc.mem_free(),
            'allocated': gc.mem_alloc()
        }
    
    def print_summary(self, medians_file, dips_file):
        uptime = self.get_uptime_s()
        mem = self.get_memory_stats()
        
        medians_size = self.get_file_size(medians_file)
        dips_size = self.get_file_size(dips_file)
        
        print(f"\n{'='*60}")
        print(f"STATS SUMMARY @ {uptime:.1f}s uptime")
        print(f"{'='*60}")
        print(f"Samples:         {self.total_samples:,} ({self.total_samples/uptime:.1f}/s)")
        print(f"Medians:         {self.total_medians_computed} computed, {self.total_medians_logged} logged")
        print(f"Dips detected:   {sum(self.dips_detected.values())} total")
        for ch, count in sorted(self.dips_detected.items()):
            print(f"  {ch}: {count}")
        print(f"Flash writes:    {self.flash_writes}")
        print(f"Memory:          {mem['free']:,} bytes free / {mem['allocated']:,} allocated")
        print(f"File sizes:")
        print(f"  medians.csv:   {medians_size:,} bytes")
        print(f"  dips.csv:      {dips_size:,} bytes")
        
        print(f"Baseline convergence:")
        for ch in sorted(self.baseline_first_valid_ms.keys()):
            conv_time = self.get_baseline_convergence_time_s(ch)
            print(f"  {ch}: {conv_time:.1f}s")
        print(f"{'='*60}\n")

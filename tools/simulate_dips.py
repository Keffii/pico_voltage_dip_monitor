"""Simulate voltage dips for testing dip detector logic without hardware.

This script provides a mock ADC sampler that generates realistic voltage
readings with controllable noise and synthetic dip injection.

Usage:
    python tools/simulate_dips.py --duration 60 --dips 5
"""

import sys
import time
import random
import argparse
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import config
from channel_state import ChannelState
from dip_detector import DipDetector
from median_logger import MedianLogger
from storage import ensure_file, append_lines, append_line
from stats_tracker import StatsTracker


class MockADC:
    """Mock ADC that generates synthetic voltage readings."""
    
    def __init__(self, baseline_v=1.25, noise_v=0.005):
        self.baseline_v = baseline_v
        self.noise_v = noise_v
        self.dip_active = False
        self.dip_progress = 0
        self.dip_depth_v = 0
        self.dip_duration_ticks = 0
        self.dip_ticks_elapsed = 0
    
    def inject_dip(self, depth_v, duration_ms):
        """Inject a synthetic dip."""
        self.dip_active = True
        self.dip_progress = 0
        self.dip_depth_v = depth_v
        self.dip_duration_ticks = duration_ms // config.TICK_MS
        self.dip_ticks_elapsed = 0
        print(f"\n>>> INJECTING DIP: {depth_v:.3f}V drop for {duration_ms}ms\n")
    
    def read_u16(self):
        """Simulate ADC reading with noise and dips."""
        voltage = self.baseline_v
        
        # Add noise
        voltage += random.gauss(0, self.noise_v)
        
        # Apply dip if active
        if self.dip_active:
            # Dip shape: ramp down -> hold -> ramp up
            progress = self.dip_ticks_elapsed / self.dip_duration_ticks
            
            if progress < 0.2:  # Ramp down (20%)
                dip_factor = progress / 0.2
            elif progress < 0.8:  # Hold (60%)
                dip_factor = 1.0
            else:  # Ramp up (20%)
                dip_factor = (1.0 - progress) / 0.2
            
            voltage -= self.dip_depth_v * dip_factor
            
            self.dip_ticks_elapsed += 1
            if self.dip_ticks_elapsed >= self.dip_duration_ticks:
                self.dip_active = False
                self.dip_ticks_elapsed = 0
        
        # Convert to 16-bit ADC value
        raw = int((voltage / config.VREF) * 65535)
        return max(0, min(65535, raw))


class MockAdcSampler:
    """Mock sampler that generates readings for multiple channels."""
    
    def __init__(self, channel_pins, vref):
        self.vref = vref
        self.channels = []
        
        # Create mock ADCs with slight baseline variation
        for i, (name, gp) in enumerate(channel_pins):
            baseline = 1.25 + (i * 0.02)  # Slightly different baselines
            adc = MockADC(baseline_v=baseline, noise_v=0.003)
            self.channels.append((name, adc))
    
    def read_all_volts(self):
        """Read all channels."""
        readings = []
        for name, adc in self.channels:
            raw = adc.read_u16()
            v = (raw / 65535.0) * self.vref
            readings.append((name, v))
        return readings
    
    def inject_dip(self, channel_name, depth_v, duration_ms):
        """Inject dip on specific channel."""
        for name, adc in self.channels:
            if name == channel_name:
                adc.inject_dip(depth_v, duration_ms)
                return
        print(f"ERROR: Channel {channel_name} not found")


def run_simulation(duration_s, num_dips):
    """Run simulation with synthetic dips."""
    
    print(f"\n{'='*60}")
    print(f"VOLTAGE DIP SIMULATOR")
    print(f"{'='*60}")
    print(f"Duration:      {duration_s}s")
    print(f"Dips to inject: {num_dips}")
    print(f"Tick rate:     {config.TICK_MS}ms")
    print(f"Channels:      {', '.join(ch for ch, _ in config.CHANNEL_PINS)}")
    print(f"{'='*60}\n")
    
    # Initialize files
    ensure_file("/tmp/sim_medians.csv", "time_s,channel,median_V")
    ensure_file("/tmp/sim_dips.csv", "channel,dip_start_s,dip_end_s,duration_ms,baseline_V,min_V,drop_V")
    
    # Create mock sampler
    sampler = MockAdcSampler(config.CHANNEL_PINS, config.VREF)
    stats = StatsTracker()
    
    # Initialize channel states
    states = {}
    for name, _gp in config.CHANNEL_PINS:
        states[name] = ChannelState(
            stable_window=config.STABLE_WINDOW,
            median_block=config.MEDIAN_BLOCK,
            baseline_len=config.BASELINE_LEN
        )
    
    # Initialize dip detector
    dip = DipDetector(
        threshold_v=config.DIP_THRESHOLD_V,
        recovery_margin_v=config.RECOVERY_MARGIN_V,
        start_hold=config.DIP_START_HOLD,
        end_hold=config.DIP_END_HOLD,
        cooldown_ms=config.DIP_COOLDOWN_MS
    )
    
    medlog = MedianLogger("/tmp/sim_medians.csv")
    
    # Schedule dips
    total_ticks = duration_s * 1000 // config.TICK_MS
    dip_schedule = []
    
    if num_dips > 0:
        # Space dips evenly, starting after baseline stabilizes
        start_tick = 500  # Wait 5 seconds for baseline
        dip_interval = (total_ticks - start_tick) // num_dips
        
        for i in range(num_dips):
            tick = start_tick + (i * dip_interval)
            channel = config.CHANNEL_PINS[i % len(config.CHANNEL_PINS)][0]
            
            # Vary dip characteristics
            depth = 0.08 + random.uniform(0, 0.15)  # 80-230 mV
            duration = random.randint(30, 150)  # 30-150 ms
            
            dip_schedule.append((tick, channel, depth, duration))
        
        print("Dip schedule:")
        for tick, ch, depth, dur in dip_schedule:
            t_s = tick * config.TICK_MS / 1000.0
            print(f"  {t_s:6.1f}s - {ch}: {depth:.3f}V drop, {dur}ms duration")
        print()
    
    # Simulation loop
    tick_count = 0
    last_flush_tick = 0
    next_dip_idx = 0
    
    print("Starting simulation...\n")
    
    start_time = time.time()
    
    try:
        while tick_count < total_ticks:
            # Check for scheduled dips
            if next_dip_idx < len(dip_schedule):
                tick, channel, depth, duration = dip_schedule[next_dip_idx]
                if tick_count >= tick:
                    sampler.inject_dip(channel, depth, duration)
                    next_dip_idx += 1
            
            # Simulate tick timing
            now_ms = tick_count * config.TICK_MS
            t_s = now_ms / 1000.0
            
            # Read all channels
            readings = sampler.read_all_volts()
            stats.record_sample()
            
            # Process each channel
            for name, v in readings:
                st = states[name]
                
                st.update_raw_window(v)
                st.update_median_block(v)
                
                # Stability check
                stable = False
                if len(st.raw_win) == config.STABLE_WINDOW:
                    vmin = min(st.raw_win)
                    vmax = max(st.raw_win)
                    span = vmax - vmin
                    stable = (vmin >= config.MIN_V) and (vmax <= config.MAX_V) and (span <= config.STABLE_SPAN_V)
                st.stable = stable
                
                # Dip detection
                def dip_callback(msg):
                    print(msg)
                    if "DIP END" in msg:
                        stats.record_dip(name)
                
                dip.process_sample(
                    now_ms=now_ms,
                    t_s=t_s,
                    channel_name=name,
                    v=v,
                    st=st,
                    print_fn=dip_callback,
                    append_line_fn=lambda path, line: append_line(path, line),
                    dips_file="/tmp/sim_dips.csv"
                )
            
            # Compute medians
            if (tick_count % config.MEDIAN_BLOCK) == 0:
                for name, _gp in config.CHANNEL_PINS:
                    st = states[name]
                    med_v = st.compute_block_median_and_clear()
                    if med_v is None:
                        continue
                    
                    stats.record_median_computed()
                    
                    if st.stable and (not st.dip_active):
                        st.update_baseline_with_median(med_v)
                        
                        if st.baseline is not None:
                            stats.record_baseline_valid(name)
                    
                    if st.stable:
                        medlog.add(t_s, name, med_v)
                        stats.record_median_logged()
            
            # Flush medians periodically
            if tick_count - last_flush_tick >= 100:  # Every 1 second
                medlog.flush_to_file(append_lines)
                last_flush_tick = tick_count
            
            tick_count += 1
        
        # Final flush
        medlog.flush_to_file(append_lines)
    
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted\n")
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"Simulated time:  {tick_count * config.TICK_MS / 1000.0:.1f}s")
    print(f"Real time:       {elapsed:.1f}s")
    print(f"Speed factor:    {(tick_count * config.TICK_MS / 1000.0) / elapsed:.1f}x")
    print(f"\nOutput files:")
    print(f"  /tmp/sim_medians.csv")
    print(f"  /tmp/sim_dips.csv")
    print(f"{'='*60}\n")
    
    stats.print_summary("/tmp/sim_medians.csv", "/tmp/sim_dips.csv")
    
    print(f"\nValidate results with:")
    print(f"  python tools/validate_csv.py /tmp/sim_medians.csv")
    print(f"  python tools/validate_csv.py /tmp/sim_dips.csv")
    print(f"\nVisualize with:")
    print(f"  python tools/plot_medians.py /tmp/sim_medians.csv")
    print(f"  python tools/plot_dips.py /tmp/sim_dips.csv")


def main():
    parser = argparse.ArgumentParser(description='Simulate voltage dips for testing')
    parser.add_argument('--duration', type=int, default=30,
                        help='Simulation duration in seconds (default: 30)')
    parser.add_argument('--dips', type=int, default=3,
                        help='Number of dips to inject (default: 3)')
    
    args = parser.parse_args()
    
    run_simulation(args.duration, args.dips)


if __name__ == '__main__':
    main()

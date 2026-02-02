# main.py

import time
import sys

import config
from adc_sampler import AdcSampler
from channel_state import ChannelState
from dip_detector import DipDetector
from median_logger import MedianLogger
from storage import ensure_file, append_lines, append_line, check_file_size_limit, get_free_space
from stats_tracker import StatsTracker

def usb_stream_median(t_s, channel_name, median_v):
    """Stream median to USB serial for InfluxDB."""
    print(f"MEDIAN,{t_s:.3f},{channel_name},{median_v:.3f}")

def usb_stream_dip(channel, dip_start_s, dip_end_s, duration_ms, baseline_v, min_v, drop_v):
    """Stream dip event to USB serial for InfluxDB."""
    print(f"DIP,{channel},{dip_start_s:.3f},{dip_end_s:.3f},{duration_ms},{baseline_v:.3f},{min_v:.3f},{drop_v:.3f}")

def usb_stream_baseline(t_s, channel_name, baseline_v):
    """Stream baseline snapshot to USB serial."""
    print(f"BASELINE,{t_s:.3f},{channel_name},{baseline_v:.3f}")

def run():
    # Validate configuration
    try:
        config.validate_config()
        print("Configuration validated successfully.")
    except ValueError as e:
        print(f"FATAL: {e}")
        return
    
    # Print configuration summary
    print(f"\n{'='*60}")
    print(f"PICO VOLTAGE DIP MONITOR")
    print(f"{'='*60}")
    print(f"Logging mode:    {config.LOGGING_MODE}")
    print(f"Sampling:        {config.TICK_MS} ms ({1000/config.TICK_MS:.0f} Hz)")
    print(f"Channels:        {', '.join(ch for ch, _ in config.CHANNEL_PINS)}")
    print(f"Dip threshold:   {config.DIP_THRESHOLD_V:.3f} V")
    print(f"Free flash:      {get_free_space():,} bytes")
    print(f"{'='*60}\n")
    
    # Initialize files based on logging mode
    try:
        ensure_file(config.DIPS_FILE, "channel,dip_start_s,dip_end_s,duration_ms,baseline_V,min_V,drop_V")
        
        if config.LOGGING_MODE in ["FULL_LOCAL", "EVENT_ONLY"]:
            ensure_file(config.BASELINE_SNAPSHOTS_FILE, "time_s,channel,baseline_V")
        
        if config.LOGGING_MODE == "FULL_LOCAL":
            ensure_file(config.MEDIANS_FILE, "time_s,channel,median_V")
    except Exception as e:
        print(f"FATAL: Failed to initialize files: {e}")
        return

    sampler = AdcSampler(config.CHANNEL_PINS, config.VREF)
    stats = StatsTracker()

    states = {}
    for name, _gp in config.CHANNEL_PINS:
        states[name] = ChannelState(
            stable_window=config.STABLE_WINDOW,
            median_block=config.MEDIAN_BLOCK,
            baseline_len=config.BASELINE_LEN
        )

    dip = DipDetector(
        threshold_v=config.DIP_THRESHOLD_V,
        recovery_margin_v=config.RECOVERY_MARGIN_V,
        start_hold=config.DIP_START_HOLD,
        end_hold=config.DIP_END_HOLD,
        cooldown_ms=config.DIP_COOLDOWN_MS
    )

    medlog = MedianLogger(config.MEDIANS_FILE)

    next_tick_ms = time.ticks_add(time.ticks_ms(), config.TICK_MS)
    last_flush_ms = time.ticks_ms()
    last_status_ms = time.ticks_ms()
    last_stats_ms = time.ticks_ms()
    last_baseline_snapshot_ms = time.ticks_ms()
    tick_count = 0

    print("Starting sampling loop...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            now_ms = time.ticks_ms()
            wait = time.ticks_diff(next_tick_ms, now_ms)
            if wait > 0:
                time.sleep_ms(wait)

            now_ms = time.ticks_ms()
            t_s = now_ms / 1000.0
            next_tick_ms = time.ticks_add(next_tick_ms, config.TICK_MS)
            tick_count += 1

            readings = sampler.read_all_volts()
            stats.record_sample()

            # Per-tick processing
            for name, v in readings:
                st = states[name]

                st.update_raw_window(v)
                st.update_median_block(v)

                # Stability
                stable = False
                if len(st.raw_win) == config.STABLE_WINDOW:
                    vmin = min(st.raw_win)
                    vmax = max(st.raw_win)
                    span = vmax - vmin
                    stable = (vmin >= config.MIN_V) and (vmax <= config.MAX_V) and (span <= config.STABLE_SPAN_V)
                st.stable = stable

                # Dip detection (raw samples)
                # Custom wrapper to track dips and stream to USB
                def dip_callback(msg):
                    print(msg)
                    if "DIP END" in msg:
                        stats.record_dip(name)
                
                def dip_append(path, line):
                    # Parse dip line for USB streaming
                    if config.LOGGING_MODE == "USB_STREAM":
                        parts = line.strip().split(',')
                        if len(parts) == 7:
                            usb_stream_dip(*parts)
                    
                    # Always write to flash
                    if append_line(path, line):
                        stats.record_flash_write()

                dip.process_sample(
                    now_ms=now_ms,
                    t_s=t_s,
                    channel_name=name,
                    v=v,
                    st=st,
                    print_fn=dip_callback,
                    append_line_fn=dip_append,
                    dips_file=config.DIPS_FILE
                )

            # Every 100 ms: compute median + baseline + enqueue logging
            if (tick_count % config.MEDIAN_BLOCK) == 0:
                for name, _gp in config.CHANNEL_PINS:
                    st = states[name]
                    med_v = st.compute_block_median_and_clear()
                    if med_v is None:
                        continue
                    
                    stats.record_median_computed()

                    # Baseline update
                    if st.stable and (not st.dip_active):
                        st.update_baseline_with_median(med_v)
                        
                        # Track first valid baseline
                        if st.baseline is not None:
                            stats.record_baseline_valid(name)

                    # Log medians based on mode
                    if st.stable:
                        if config.LOGGING_MODE == "USB_STREAM":
                            # Stream to USB
                            usb_stream_median(t_s, name, med_v)
                            stats.record_median_logged()
                        elif config.LOGGING_MODE == "FULL_LOCAL":
                            # Log to flash
                            medlog.add(t_s, name, med_v)
                            stats.record_median_logged()
                        # EVENT_ONLY mode: don't log medians

            # Flush medians in batches (FULL_LOCAL mode only)
            if config.LOGGING_MODE == "FULL_LOCAL":
                if time.ticks_diff(now_ms, last_flush_ms) >= int(config.MEDIAN_FLUSH_EVERY_S * 1000):
                    lines_written = medlog.flush_to_file(append_lines)
                    stats.record_flash_write(lines_written)
                    
                    # Check file size and truncate if needed
                    check_file_size_limit(
                        config.MEDIANS_FILE,
                        config.MAX_MEDIANS_SIZE_BYTES,
                        "time_s,channel,median_V",
                        config.MAX_MEDIANS_LINES
                    )
                    
                    last_flush_ms = now_ms

            # Baseline snapshots (EVENT_ONLY and FULL_LOCAL modes)
            if config.LOGGING_MODE in ["EVENT_ONLY", "FULL_LOCAL"]:
                if time.ticks_diff(now_ms, last_baseline_snapshot_ms) >= int(config.BASELINE_SNAPSHOT_EVERY_S * 1000):
                    for name, _gp in config.CHANNEL_PINS:
                        st = states[name]
                        if st.baseline is not None:
                            line = f"{t_s:.3f},{name},{st.baseline:.3f}\n"
                            if append_line(config.BASELINE_SNAPSHOTS_FILE, line):
                                stats.record_flash_write()
                    last_baseline_snapshot_ms = now_ms
            
            # USB baseline snapshots
            if config.LOGGING_MODE == "USB_STREAM":
                if time.ticks_diff(now_ms, last_baseline_snapshot_ms) >= int(config.BASELINE_SNAPSHOT_EVERY_S * 1000):
                    for name, _gp in config.CHANNEL_PINS:
                        st = states[name]
                        if st.baseline is not None:
                            usb_stream_baseline(t_s, name, st.baseline)
                    last_baseline_snapshot_ms = now_ms

            # Status line
            if time.ticks_diff(now_ms, last_status_ms) >= int(config.SHELL_STATUS_EVERY_S * 1000):
                parts = []
                for name, _gp in config.CHANNEL_PINS:
                    st = states[name]
                    b = st.baseline
                    btxt = "None" if b is None else f"{b:.3f}"
                    parts.append(f"{name}: stable={1 if st.stable else 0} base={btxt} dip={1 if st.dip_active else 0}")
                print(f"{t_s:8.1f}s  " + "  ".join(parts))
                last_status_ms = now_ms
            
            # Stats report
            if time.ticks_diff(now_ms, last_stats_ms) >= int(config.STATS_REPORT_EVERY_S * 1000):
                stats.print_summary(config.MEDIANS_FILE, config.DIPS_FILE)
                last_stats_ms = now_ms

    except KeyboardInterrupt:
        print("\n\nShutdown requested. Flushing buffers...")
        
        # Flush any pending medians
        if config.LOGGING_MODE == "FULL_LOCAL" and medlog.buffer:
            lines_written = medlog.flush_to_file(append_lines)
            print(f"Flushed {lines_written} median lines to flash")
        
        # Final stats report
        print("\nFinal statistics:")
        stats.print_summary(config.MEDIANS_FILE, config.DIPS_FILE)
        
        print("\nShutdown complete.")
    
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import sys
        sys.print_exception(e)

# Auto-run
run()
# main.py

import time

import config
from adc_sampler import AdcSampler
from channel_state import ChannelState
from dip_detector import DipDetector
from median_logger import MedianLogger
from storage import ensure_file, append_lines, append_line

def run():
    ensure_file(config.MEDIANS_FILE, "time_s,channel,median_V")
    ensure_file(config.DIPS_FILE, "channel,dip_start_s,dip_end_s,duration_ms,baseline_V,min_V,drop_V")

    sampler = AdcSampler(config.CHANNEL_PINS, config.VREF)

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
    tick_count = 0

    print("Running 10ms sampling on GP26/GP27/GP28.")
    print("Logging 100ms medians to pico_medians.csv (batched) and dip events to pico_dips.csv (immediate).")

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
            dip.process_sample(
                now_ms=now_ms,
                t_s=t_s,
                channel_name=name,
                v=v,
                st=st,
                print_fn=print,
                append_line_fn=append_line,
                dips_file=config.DIPS_FILE
            )

        # Every 100 ms: compute median + baseline + enqueue logging
        if (tick_count % config.MEDIAN_BLOCK) == 0:
            for name, _gp in config.CHANNEL_PINS:
                st = states[name]
                med_v = st.compute_block_median_and_clear()
                if med_v is None:
                    continue

                # Baseline update
                if st.stable and (not st.dip_active):
                    st.update_baseline_with_median(med_v)

                # Log medians only when stable
                if st.stable:
                    medlog.add(t_s, name, med_v)

        # Flush medians in batches
        if time.ticks_diff(now_ms, last_flush_ms) >= int(config.MEDIAN_FLUSH_EVERY_S * 1000):
            medlog.flush_to_file(append_lines)
            last_flush_ms = now_ms

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

# Auto-run
run()

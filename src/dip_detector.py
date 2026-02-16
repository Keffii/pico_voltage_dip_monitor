# dip_detector.py

import time
import config

try:
    from debug import debug
except ImportError:
    debug = None

try:
    from machine import Pin
except ImportError:
    Pin = None


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _ticks_add(a, b):
    if hasattr(time, "ticks_add"):
        return time.ticks_add(a, b)
    return a + b


class DipDetector:
    def __init__(self, threshold_v, recovery_margin_v, start_hold, end_hold, cooldown_ms):
        self.threshold_v = threshold_v
        self.recovery_margin_v = recovery_margin_v
        self.start_hold = start_hold
        self.end_hold = end_hold
        self.cooldown_ms = cooldown_ms
        self.tick_ms = int(config.TICK_MS) if config.TICK_MS > 0 else 1
        self.marker_pin = None
        self.marker_off_ms = None
        self.marker_pulse_ms = int(config.DIP_DETECT_MARKER_PULSE_MS)
        self._init_marker()

    def _init_marker(self):
        pin_num = config.DIP_DETECT_MARKER_PIN
        if pin_num is None or Pin is None:
            return
        try:
            self.marker_pin = Pin(pin_num, Pin.OUT)
            self.marker_pin.value(0)
        except Exception:
            self.marker_pin = None

    def _update_marker(self, now_ms):
        if self.marker_pin is None or self.marker_off_ms is None:
            return
        if _ticks_diff(now_ms, self.marker_off_ms) >= 0:
            self.marker_pin.value(0)
            self.marker_off_ms = None

    def _pulse_marker(self, now_ms):
        if self.marker_pin is None:
            return
        self.marker_pin.value(1)
        self.marker_off_ms = _ticks_add(now_ms, self.marker_pulse_ms)

    def process_sample(self, now_ms, t_s, channel_name, v, st, print_fn, append_line_fn, dips_file):
        debug_available = debug is not None
        baseline = st.baseline
        self._update_marker(now_ms)

        # Trace every sample (lightweight, non-blocking)
        if debug_available:
            debug.trace("sample", ch=channel_name, v=round(v, 3), stable=st.stable)

        # During an active dip, use baseline captured at dip start for recovery threshold.
        active_baseline = st.dip_baseline_v if st.dip_active else baseline
        if active_baseline is None:
            st.below_count = 0
            st.first_below_ms = None
            st.above_count = 0
            return

        # Cooldown check
        in_cooldown = _ticks_diff(st.cooldown_until_ms, now_ms) > 0

        recently_stable = (
            st.stable or
            (st.last_stable_ms is not None and
             _ticks_diff(now_ms, st.last_stable_ms) <= config.STABLE_GRACE_MS)
        )

        # Gate dip start by stability/cooldown, but allow active dips to recover/end.
        if (not st.dip_active) and ((not recently_stable) or in_cooldown):
            st.below_count = 0
            st.first_below_ms = None
            st.above_count = 0
            return

        if not st.dip_active:
            start_thresh = baseline - self.threshold_v
            if v <= start_thresh:
                if st.below_count == 0:
                    st.first_below_ms = now_ms
                st.below_count += 1
                
                # Conditional breakpoint: only when approaching trigger
                if debug_available:
                    debug.bp_if(
                        st.below_count == self.start_hold - 1,
                        "dip_about_to_trigger",
                        channel=channel_name,
                        below_count=st.below_count,
                        voltage_V=round(v, 3),
                        threshold_V=round(start_thresh, 3),
                        need_count=self.start_hold
                    )
            else:
                st.below_count = 0
                st.first_below_ms = None

            if st.below_count >= self.start_hold:
                latency_ms = 0 if st.first_below_ms is None else _ticks_diff(now_ms, st.first_below_ms)
                if latency_ms < 0:
                    latency_ms = 0
                latency_ticks = int(round(latency_ms / self.tick_ms))
                st.dip_active = True
                st.dip_start_s = t_s
                st.dip_min_v = v
                st.dip_baseline_v = baseline
                st.above_count = 0
                st.first_below_ms = None
                self._pulse_marker(now_ms)
                
                # Breakpoint when dip starts
                if debug_available:
                    drop_mV = (baseline - v) * 1000
                    debug.bp("dip_started",
                             channel=channel_name,
                             time_s=round(t_s, 3),
                             voltage_V=round(v, 3),
                             baseline_V=round(baseline, 3),
                             drop_mV=round(drop_mV, 1))
                
                print_fn(f"{t_s:8.3f}s  DIP START  {channel_name}  baseline={baseline:.3f}V  now={v:.3f}V")
                print_fn(f"DETECT_LATENCY_TICKS,{channel_name},{latency_ticks},{self.tick_ms}")
        else:
            # Dip ongoing
            end_thresh = active_baseline - (self.threshold_v - self.recovery_margin_v)
            if st.dip_min_v is None or v < st.dip_min_v:
                st.dip_min_v = v

            # Recovery check with hysteresis
            if v >= end_thresh:
                st.above_count += 1
            else:
                st.above_count = 0

            if st.above_count >= self.end_hold:
                dip_end_s = t_s
                dip_start_s = st.dip_start_s
                base_at_start = st.dip_baseline_v
                min_v = st.dip_min_v

                duration_ms = int(round((dip_end_s - dip_start_s) * 1000.0))
                drop_v = base_at_start - min_v
                drop_pct = (-(drop_v / base_at_start) * 100.0) if base_at_start > 0 else 0.0

                append_line_fn(
                    dips_file,
                    f"{channel_name},{dip_start_s:.3f},{dip_end_s:.3f},{duration_ms},{base_at_start:.3f},{min_v:.3f},{drop_v:.3f}\n"
                )

                print_fn(
                    f"{t_s:8.3f}s  DIP END    {channel_name}  dur={duration_ms}ms  "
                    f"min={min_v:.3f}V  drop={drop_v:.3f}V ({drop_pct:.1f}%)"
                )

                # Reset + cooldown
                st.dip_active = False
                st.dip_start_s = None
                st.dip_min_v = None
                st.dip_baseline_v = None
                st.below_count = 0
                st.first_below_ms = None
                st.above_count = 0
                st.cooldown_until_ms = now_ms + self.cooldown_ms

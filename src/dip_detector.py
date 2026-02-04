# dip_detector.py

class DipDetector:
    def __init__(self, threshold_v, recovery_margin_v, start_hold, end_hold, cooldown_ms):
        self.threshold_v = threshold_v
        self.recovery_margin_v = recovery_margin_v
        self.start_hold = start_hold
        self.end_hold = end_hold
        self.cooldown_ms = cooldown_ms

    def process_sample(self, now_ms, t_s, channel_name, v, st, print_fn, append_line_fn, dips_file):
        # Optional: Import debug utilities (only if DEBUG_* flags are enabled)
        try:
            from debug import debug
            debug_available = True
        except ImportError:
            debug_available = False
        
        baseline = st.baseline
        
        # Trace every sample (lightweight, non-blocking)
        if debug_available:
            debug.trace("sample", ch=channel_name, v=round(v, 3), stable=st.stable)
        
        if baseline is None:
            st.below_count = 0
            st.above_count = 0
            return

        # Cooldown check
        in_cooldown = (st.cooldown_until_ms - now_ms) > 0

        # Only detect dips when stable and not in cooldown
        if (not st.stable) or in_cooldown:
            st.below_count = 0
            st.above_count = 0
            return

        start_thresh = baseline - self.threshold_v
        end_thresh = baseline - (self.threshold_v - self.recovery_margin_v)

        if not st.dip_active:
            if v <= start_thresh:
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

            if st.below_count >= self.start_hold:
                st.dip_active = True
                st.dip_start_s = t_s
                st.dip_min_v = v
                st.dip_baseline_v = baseline
                st.above_count = 0
                
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
        else:
            # Dip ongoing
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

                append_line_fn(
                    dips_file,
                    f"{channel_name},{dip_start_s:.3f},{dip_end_s:.3f},{duration_ms},{base_at_start:.3f},{min_v:.3f},{drop_v:.3f}\n"
                )

                print_fn(f"{t_s:8.3f}s  DIP END    {channel_name}  dur={duration_ms}ms  min={min_v:.3f}V  drop={drop_v:.3f}V")

                # Reset + cooldown
                st.dip_active = False
                st.dip_start_s = None
                st.dip_min_v = None
                st.dip_baseline_v = None
                st.below_count = 0
                st.above_count = 0
                st.cooldown_until_ms = now_ms + self.cooldown_ms

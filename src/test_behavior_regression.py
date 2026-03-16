# test_behavior_regression.py

import config
from channel_state import ChannelState
from dip_detector import DipDetector


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def _new_state():
    return ChannelState(
        stable_window=config.STABLE_WINDOW,
        median_block=config.MEDIAN_BLOCK,
        baseline_init_samples=10,
        baseline_alpha=config.BASELINE_ALPHA,
    )


def _new_detector():
    return DipDetector(
        threshold_v=config.DIP_THRESHOLD_V,
        recovery_margin_v=config.RECOVERY_MARGIN_V,
        start_hold=config.DIP_START_HOLD,
        end_hold=config.DIP_END_HOLD,
        cooldown_ms=config.DIP_COOLDOWN_MS,
    )


def _run_sequence(values, allow_start=True):
    st = _new_state()
    dip = _new_detector()
    now_ms = 0
    events = []
    lines = []

    def _print_fn(msg):
        events.append(msg)

    def _append_fn(_path, line):
        lines.append(line)

    for v in values:
        st.update_raw_window(v)
        st.update_median_block(v)

        stable = False
        if st.raw_window_ready():
            vmin, vmax = st.raw_window_bounds()
            span = vmax - vmin
            stable = (vmin >= config.MIN_V) and (vmax <= config.MAX_V) and (span <= config.STABLE_SPAN_V)
        st.stable = stable

        if st.stable:
            st.last_stable_ms = now_ms
            if not st.dip_active:
                st.update_baseline_with_raw(v)

        dip.process_sample(
            now_ms=now_ms,
            t_s=now_ms / 1000.0,
            channel_name="BLUE",
            v=v,
            st=st,
            print_fn=_print_fn,
            append_line_fn=_append_fn,
            dips_file=config.DIPS_FILE,
            allow_start=allow_start,
        )
        now_ms += config.TICK_MS

    return events, lines, st


def test_median_block_consistency():
    st = _new_state()
    values = [1.2, 0.9, 1.1, 1.4, 1.0, 1.3, 0.8, 1.5, 1.6, 1.7]
    for v in values:
        st.update_median_block(v)
    median_v = st.compute_block_median_and_clear()
    _assert(median_v is not None, "Expected median after 10 samples")
    _assert(abs(median_v - 1.25) < 0.0001, "Median value mismatch for deterministic block")


def test_single_dip_detected():
    values = [1.00] * 24 + [0.72] * 3 + [1.00] * 8
    _events, lines, _st = _run_sequence(values)
    _assert(len(lines) == 1, "Expected exactly one dip event line")
    parts = lines[0].strip().split(",")
    _assert(len(parts) == 7, "Dip line format mismatch")
    drop_v = float(parts[6])
    _assert(drop_v > 0.0, "Dip drop must be positive")


def test_cooldown_blocks_immediate_redetection():
    values = [1.00] * 24 + [0.72] * 3 + [1.00] * 8 + [0.72] * 3 + [1.00] * 8
    _events, lines, _st = _run_sequence(values)
    _assert(len(lines) == 1, "Cooldown should prevent immediate second dip")


def test_baseline_arms_with_intermittent_stability():
    # Each stable window burst is intentionally short; baseline should still arm
    # by accumulating stable samples across bursts without seed reset.
    values = (
        [1.00] * 14 +
        [1.20] +
        [1.00] * 14 +
        [1.20] +
        [1.00] * 14 +
        [0.78] * 3 +
        [1.00] * 8
    )
    _events, lines, st = _run_sequence(values)
    _assert(st.baseline is not None, "Baseline should initialize from cumulative stable seeds")
    _assert(len(lines) >= 1, "Expected at least one dip after baseline initialization")


def test_allow_start_false_suppresses_dip_start():
    values = [1.00] * 24 + [0.72] * 3 + [1.00] * 8
    _events, lines, st = _run_sequence(values, allow_start=False)
    _assert(st.baseline is not None, "Baseline should still initialize when starts are suppressed")
    _assert(len(lines) == 0, "No dip should be appended when allow_start=False")
    _assert(st.dip_active is False, "Dip state should remain inactive when allow_start=False")


def test_detects_about_1p5v_real_drop():
    # 1.5V real across the current divider is about 0.081V in ADC domain.
    # This sequence should become a real dip event once the threshold is lowered
    # from the old 0.15V ADC setting.
    values = [0.662] * 24 + [0.575] * 3 + [0.662] * 8
    _events, lines, _st = _run_sequence(values)
    _assert(len(lines) == 1, "Expected a ~1.5V real drop to be detected as a dip")
    parts = lines[0].strip().split(",")
    _assert(len(parts) == 7, "Dip line format mismatch for ~1.5V real drop")
    drop_v = float(parts[6])
    _assert(drop_v >= 0.081, "Expected dip drop to reflect the lower real-domain threshold target")


def run_all():
    tests = (
        test_median_block_consistency,
        test_single_dip_detected,
        test_cooldown_blocks_immediate_redetection,
        test_baseline_arms_with_intermittent_stability,
        test_allow_start_false_suppresses_dip_start,
        test_detects_about_1p5v_real_drop,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("Behavior regression tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

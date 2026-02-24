# test_performance_runtime.py

import gc
import time

import config
from perf_metrics import PerfMetrics


def _ticks_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def _ticks_us():
    if hasattr(time, "ticks_us"):
        return time.ticks_us()
    return int(time.time() * 1000000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _ticks_add(a, b):
    if hasattr(time, "ticks_add"):
        return time.ticks_add(a, b)
    return a + b


def _sleep_ms(delay_ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(delay_ms)
    else:
        time.sleep(delay_ms / 1000.0)


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def run_tick_probe(duration_s=3, tick_ms=None, ring_size=None):
    if tick_ms is None:
        tick_ms = int(config.TICK_MS)
    if ring_size is None:
        ring_size = int(getattr(config, "PERF_RING_SIZE", 1024))

    perf = PerfMetrics(ring_size=ring_size)
    next_tick_ms = _ticks_add(_ticks_ms(), tick_ms)
    end_ms = _ticks_add(_ticks_ms(), int(duration_s * 1000))

    while _ticks_diff(end_ms, _ticks_ms()) > 0:
        loop_start_us = _ticks_us()
        now_ms = _ticks_ms()
        wait_ms = _ticks_diff(next_tick_ms, now_ms)
        if wait_ms > 0:
            _sleep_ms(wait_ms)
        else:
            backlog_ticks = int((-wait_ms) // tick_ms)
            perf.observe_backlog(backlog_ticks)
            perf.add_missed_ticks(backlog_ticks)
        processing_start_us = _ticks_us()

        stage_start_us = _ticks_us()
        # Synthetic low-work stage measurements to exercise the counters.
        perf.add_timing("adc_us", _ticks_diff(_ticks_us(), stage_start_us))
        perf.add_timing("state_us", 0)
        perf.add_timing("dip_us", 0)
        perf.add_timing("median_us", 0)
        perf.add_timing("ui_frame_us", 0)
        perf.add_timing("usb_write_us", 0)
        perf.add_timing("flash_write_us", 0)
        perf.add_timing("processing_us", _ticks_diff(_ticks_us(), processing_start_us))

        perf.add_timing("loop_us", _ticks_diff(_ticks_us(), loop_start_us))
        next_tick_ms = _ticks_add(next_tick_ms, tick_ms)

    gc_start_us = _ticks_us()
    gc.collect()
    perf.record_gc(_ticks_diff(_ticks_us(), gc_start_us))
    return perf.snapshot()


def test_perf_snapshot_shape():
    snap = run_tick_probe(duration_s=1)
    if "processing_us" not in snap:
        raise AssertionError(
            "Missing metric key: processing_us. "
            "Copy updated perf_metrics.py to Pico and soft reboot (Ctrl+D), then rerun."
        )
    for key in ("loop_us", "processing_us", "adc_us", "state_us", "dip_us", "median_us", "ui_frame_us", "usb_write_us", "flash_write_us"):
        _assert(key in snap, "Missing metric key: {}".format(key))
        _assert("p95" in snap[key], "Missing p95 in {}".format(key))
        _assert("p99" in snap[key], "Missing p99 in {}".format(key))
    _assert(snap["gc_count"] >= 1, "Expected at least one GC sample")


def test_perf_probe_thresholds():
    snap = run_tick_probe(duration_s=2)
    if hasattr(time, "ticks_us"):
        max_allowed_missed = int(getattr(config, "TEST_MAX_MISSED_TICKS", 0))
        p99_budget_pct = int(getattr(config, "TEST_PROCESSING_P99_BUDGET_PCT", getattr(config, "TEST_LOOP_P99_BUDGET_PCT", 70)))
    else:
        # CPython timer granularity is much coarser; keep host checks looser.
        max_allowed_missed = int(getattr(config, "TEST_MAX_MISSED_TICKS_HOST", 5))
        p99_budget_pct = int(
            getattr(
                config,
                "TEST_PROCESSING_P99_BUDGET_PCT_HOST",
                getattr(config, "TEST_LOOP_P99_BUDGET_PCT_HOST", 120)
            )
        )
    _assert(snap["missed_ticks"] <= max_allowed_missed, "missed_ticks exceeded threshold")
    tick_budget_us = int(config.TICK_MS * 1000)
    p99_limit_us = int((tick_budget_us * p99_budget_pct) // 100)
    _assert(snap["processing_us"]["p99"] <= p99_limit_us, "processing p99 exceeds configured tick budget")


def run_all():
    tests = (
        test_perf_snapshot_shape,
        test_perf_probe_thresholds,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("Performance runtime tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

# test_breakpoints.py
"""
Test script for soft breakpoint debugging utilities.

This demonstrates:
- Simple breakpoints
- Conditional breakpoints
- Watchpoints
- Tracepoints
"""

import time
import config

# Test if debug module is available
try:
    from debug import debug
    DEBUG_AVAILABLE = True
except ImportError:
    print("ERROR: debug.py not found!")
    print("Please upload debug.py to the Pico first.")
    DEBUG_AVAILABLE = False


def test_simple_breakpoint():
    """Test basic breakpoint functionality."""
    print("\n" + "=" * 60)
    print("TEST 1: Simple Breakpoint")
    print("=" * 60)

    if not DEBUG_AVAILABLE:
        return

    original_bp = getattr(config, "DEBUG_BREAKPOINTS", False)
    config.DEBUG_BREAKPOINTS = True

    voltage = 1.274
    baseline = 1.300
    channel = "BLUE"

    debug.bp(
        "test_simple",
        channel=channel,
        voltage_V=voltage,
        baseline_V=baseline,
        drop_mV=(baseline - voltage) * 1000,
    )

    config.DEBUG_BREAKPOINTS = original_bp
    print("✓ Simple breakpoint test complete\n")


def test_conditional_breakpoint():
    """Test conditional breakpoints."""
    print("\n" + "=" * 60)
    print("TEST 2: Conditional Breakpoint")
    print("=" * 60)

    if not DEBUG_AVAILABLE:
        return

    original_bp = getattr(config, "DEBUG_BREAKPOINTS", False)
    config.DEBUG_BREAKPOINTS = True

    print("Testing with 5 voltage readings...")
    print("Breakpoint should only trigger when drop > 100mV\n")

    baseline = 1.300
    test_voltages = [1.290, 1.250, 1.180, 1.295, 1.270]

    for index, value in enumerate(test_voltages):
        drop = baseline - value
        drop_millivolts = drop * 1000
        print("Sample {}: {:.3f}V (drop: {:.1f}mV)".format(index + 1, value, drop_millivolts))
        debug.bp_if(
            drop > 0.100,
            "large_voltage_drop",
            sample=index + 1,
            voltage_V=value,
            baseline_V=baseline,
            drop_mV=drop_millivolts,
            threshold_mV=100.0,
        )
        time.sleep(0.1)

    config.DEBUG_BREAKPOINTS = original_bp
    print("\n✓ Conditional breakpoint test complete\n")


def test_watchpoint():
    """Test watchpoint (auto-break on value change)."""
    print("\n" + "=" * 60)
    print("TEST 3: Watchpoint")
    print("=" * 60)

    if not DEBUG_AVAILABLE:
        return

    original_bp = getattr(config, "DEBUG_BREAKPOINTS", False)
    config.DEBUG_BREAKPOINTS = True

    watch = debug.watch("dip_active", break_on_change=True)

    print("Simulating dip state machine...")
    print("Watchpoint should trigger when dip_active changes\n")

    states = [False, False, True, True, False]
    for index, state in enumerate(states):
        print("Step {}: Setting dip_active = {}".format(index + 1, state))
        watch.check(state, step=index + 1, channel="BLUE")
        time.sleep(0.1)

    config.DEBUG_BREAKPOINTS = original_bp
    print("\n✓ Watchpoint test complete\n")


def test_tracepoint():
    """Test tracepoints (non-blocking log)."""
    print("\n" + "=" * 60)
    print("TEST 4: Tracepoint")
    print("=" * 60)

    if not DEBUG_AVAILABLE:
        return

    original_trace = getattr(config, "DEBUG_TRACE", False)
    config.DEBUG_TRACE = True

    debug.clear_trace()

    print("Logging 10 sample events to trace buffer...")
    print("(These don't pause execution)\n")

    for index in range(10):
        voltage = 1.250 + (index % 3) * 0.010
        stable = index > 2
        debug.trace("sample", sample_num=index + 1, ch="BLUE", v=voltage, stable=stable)
        print("  Sample {}: {:.3f}V stable={}".format(index + 1, voltage, stable))
        time.sleep(0.05)

    print("\nDumping trace log:")
    debug.dump_trace(last_n=10)

    config.DEBUG_TRACE = original_trace
    print("✓ Tracepoint test complete\n")


def test_debug_status():
    """Test debug status reporting."""
    print("\n" + "=" * 60)
    print("TEST 5: Debug Status")
    print("=" * 60)

    if not DEBUG_AVAILABLE:
        return

    print("Showing debug status after previous tests:\n")
    debug.status()
    print("✓ Status test complete\n")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "#" * 60)
    print("# SOFT BREAKPOINT TEST SUITE")
    print("#" * 60)

    if not DEBUG_AVAILABLE:
        print("\n✗ Cannot run tests: debug.py not found")
        print("Please upload debug.py to the Pico first.")
        return

    print("\nThis demonstrates available soft breakpoint features.\n")

    test_simple_breakpoint()
    test_conditional_breakpoint()
    test_watchpoint()
    test_tracepoint()
    test_debug_status()

    print("\n" + "#" * 60)
    print("# ALL TESTS COMPLETE")
    print("#" * 60)
    print("\nYou can now use these debugging features in your code:")
    print("  from debug import debug")
    print("  debug.bp('location_name', variable1=value1, variable2=value2)")
    print("\nSee docs/DEBUG_GUIDE.md for complete documentation.")


if __name__ == "__main__":
    run_all_tests()

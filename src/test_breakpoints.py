# test_breakpoints.py
"""
Test script for soft breakpoint debugging system.

This demonstrates all soft breakpoint features:
- Simple breakpoints
- Conditional breakpoints
- Watchpoints
- Tracepoints
- Interactive debugging

Upload this to your Pico and run it to see debugging in action.

Usage:
    1. Upload debug.py and this file to Pico
    2. In Thonny REPL:
       >>> import test_breakpoints
       >>> test_breakpoints.run_tests()
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
    print("\n" + "="*60)
    print("TEST 1: Simple Breakpoint")
    print("="*60)
    
    if not DEBUG_AVAILABLE:
        return
    
    # Enable breakpoints
    original_bp = getattr(config, 'DEBUG_BREAKPOINTS', False)
    config.DEBUG_BREAKPOINTS = True
    
    # Simulate voltage reading
    voltage = 1.274
    baseline = 1.300
    channel = "PLC"
    
    # Simple breakpoint
    debug.bp("test_simple",
             channel=channel,
             voltage_V=voltage,
             baseline_V=baseline,
             drop_mV=(baseline - voltage) * 1000)
    
    # Restore config
    config.DEBUG_BREAKPOINTS = original_bp
    print("✓ Simple breakpoint test complete\n")


def test_conditional_breakpoint():
    """Test conditional breakpoints."""
    print("\n" + "="*60)
    print("TEST 2: Conditional Breakpoint")
    print("="*60)
    
    if not DEBUG_AVAILABLE:
        return
    
    original_bp = getattr(config, 'DEBUG_BREAKPOINTS', False)
    config.DEBUG_BREAKPOINTS = True
    
    print("Testing with 5 voltage readings...")
    print("Breakpoint should only trigger when drop > 100mV\n")
    
    baseline = 1.300
    test_voltages = [1.290, 1.250, 1.180, 1.295, 1.270]  # Only 1.180 triggers
    
    for i, v in enumerate(test_voltages):
        drop = baseline - v
        drop_mV = drop * 1000
        
        print(f"Sample {i+1}: {v:.3f}V (drop: {drop_mV:.1f}mV)")
        
        # Conditional breakpoint: only when drop > 100mV
        debug.bp_if(
            drop > 0.100,
            "large_voltage_drop",
            sample=i+1,
            voltage_V=v,
            baseline_V=baseline,
            drop_mV=drop_mV,
            threshold_mV=100.0
        )
        
        time.sleep(0.1)
    
    config.DEBUG_BREAKPOINTS = original_bp
    print("\n✓ Conditional breakpoint test complete\n")


def test_watchpoint():
    """Test watchpoint (auto-break on value change)."""
    print("\n" + "="*60)
    print("TEST 3: Watchpoint")
    print("="*60)
    
    if not DEBUG_AVAILABLE:
        return
    
    original_bp = getattr(config, 'DEBUG_BREAKPOINTS', False)
    config.DEBUG_BREAKPOINTS = True
    
    # Create watchpoint for dip_active state
    watch = debug.watch("dip_active", break_on_change=True)
    
    print("Simulating dip state machine...")
    print("Watchpoint should trigger when dip_active changes\n")
    
    # Simulate state changes
    states = [False, False, True, True, False]
    
    for i, state in enumerate(states):
        print(f"Step {i+1}: Setting dip_active = {state}")
        watch.check(state, step=i+1, channel="PLC")
        time.sleep(0.1)
    
    config.DEBUG_BREAKPOINTS = original_bp
    print("\n✓ Watchpoint test complete\n")


def test_tracepoint():
    """Test tracepoints (non-blocking log)."""
    print("\n" + "="*60)
    print("TEST 4: Tracepoint")
    print("="*60)
    
    if not DEBUG_AVAILABLE:
        return
    
    original_trace = getattr(config, 'DEBUG_TRACE', False)
    config.DEBUG_TRACE = True
    
    debug.clear_trace()
    
    print("Logging 10 sample events to trace buffer...")
    print("(These don't pause execution)\n")
    
    # Simulate voltage sampling
    for i in range(10):
        voltage = 1.250 + (i % 3) * 0.010  # Vary voltage slightly
        stable = i > 2  # Becomes stable after 3 samples
        
        debug.trace("sample",
                    sample_num=i+1,
                    ch="PLC",
                    v=voltage,
                    stable=stable)
        
        print(f"  Sample {i+1}: {voltage:.3f}V stable={stable}")
        time.sleep(0.05)
    
    print("\nDumping trace log:")
    debug.dump_trace(last_n=10)
    
    config.DEBUG_TRACE = original_trace
    print("✓ Tracepoint test complete\n")


def test_debug_status():
    """Test debug status reporting."""
    print("\n" + "="*60)
    print("TEST 5: Debug Status")
    print("="*60)
    
    if not DEBUG_AVAILABLE:
        return
    
    print("Showing debug status after previous tests:\n")
    debug.status()
    
    print("✓ Status test complete\n")


def test_interactive_help():
    """Show interactive debug commands."""
    print("\n" + "="*60)
    print("TEST 6: Interactive Debug Commands")
    print("="*60)
    
    if not DEBUG_AVAILABLE:
        return
    
    print("\nTo use interactive debugging:")
    print("1. Enable DEBUG_INTERACTIVE = True in config.py")
    print("2. Connect via Debug Probe UART (or USB serial)")
    print("3. Press these keys during execution:")
    print("   p - Pause")
    print("   c - Continue")
    print("   s - Show channel status")
    print("   v - Dump all variables")
    print("   t - Show trace log")
    print("   b - Show breakpoint stats")
    print("   r - Reset debug state")
    print("   h - Help")
    print("\nThis allows you to inspect program state without modifying code!")
    print("\n✓ Interactive help shown\n")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "#"*60)
    print("# SOFT BREAKPOINT TEST SUITE")
    print("#"*60)
    
    if not DEBUG_AVAILABLE:
        print("\n✗ Cannot run tests: debug.py not found")
        print("Please upload debug.py to the Pico first.")
        return
    
    print("\nThis will demonstrate all soft breakpoint features.")
    print("Watch for breakpoint messages in the output.\n")
    
    test_simple_breakpoint()
    test_conditional_breakpoint()
    test_watchpoint()
    test_tracepoint()
    test_debug_status()
    test_interactive_help()
    
    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETE")
    print("#"*60)
    print("\nYou can now use these debugging features in your code:")
    print("  from debug import debug")
    print("  debug.bp('location_name', variable1=value1, variable2=value2)")
    print("\nSee docs/DEBUG_GUIDE.md for complete documentation.")


# Allow running from command line or import
if __name__ == "__main__":
    run_all_tests()

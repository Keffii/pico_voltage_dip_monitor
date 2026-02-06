# debug.py
"""
Soft breakpoint debugging utilities for MicroPython.

Hardware breakpoints (via SWD/GDB) don't work with MicroPython.
These "soft breakpoints" are manually coded pause/inspect points.

Features:
- Breakpoints: Pause and print variable state
- Conditional breakpoints: Only break when condition is true
- Watchpoints: Monitor variable changes
- Tracepoints: Log events without pausing
- Interactive debug mode: UART command shell

Usage:
    from debug import debug
    
    # Simple breakpoint
    debug.bp("dip_started", voltage=v, baseline=baseline)
    
    # Conditional breakpoint
    debug.bp_if(drop > 0.2, "large_drop", drop_mV=drop*1000)
    
    # Tracepoint (non-blocking log)
    debug.trace("sample_processed", ch=channel, v=v)
    
    # Watchpoint (auto-break on value change)
    watch = debug.watch("dip_active")
    watch.check(st.dip_active)
"""

import time

class Watchpoint:
    """Monitor a variable and optionally break when it changes."""
    
    def __init__(self, name, break_on_change=True):
        self.name = name
        self.last_value = None
        self.break_on_change = break_on_change
        self.changes = 0
    
    def check(self, current_value, **extra_vars):
        """Check if value changed and optionally break."""
        if self.last_value is not None and self.last_value != current_value:
            self.changes += 1
            
            # Import here to avoid circular dependency
            import config
            if config.DEBUG_BREAKPOINTS and self.break_on_change:
                print(f"\n{'='*60}")
                print(f"WATCHPOINT: {self.name} changed! (#{self.changes})")
                print(f"  Old value: {self.last_value}")
                print(f"  New value: {current_value}")
                for k, v in extra_vars.items():
                    print(f"  {k:15s} = {v}")
                print(f"{'='*60}\n")
        
        self.last_value = current_value
        return current_value


class DebugHelper:
    """Main debug helper with breakpoints, traces, and interactive mode."""
    
    def __init__(self):
        self.breakpoints_hit = 0
        self.trace_log = []
        self.watchpoints = {}
        self.paused = False
        self.enabled = True
    
    def bp(self, name, **variables):
        """Soft breakpoint - pause and print variables.
        
        Example:
            debug.bp("dip_detected", 
                     channel="PLC", 
                     voltage=1.112, 
                     baseline=1.274)
        """
        import config
        if not config.DEBUG_BREAKPOINTS or not self.enabled:
            return
        
        self.breakpoints_hit += 1
        print(f"\n{'='*60}")
        print(f"BREAKPOINT #{self.breakpoints_hit}: {name}")
        print(f"Time: {time.ticks_ms()}ms")
        
        if variables:
            print(f"Variables:")
            for k, v in variables.items():
                # Format nicely
                if isinstance(v, float):
                    print(f"  {k:20s} = {v:.6f}")
                else:
                    print(f"  {k:20s} = {v}")
        
        print(f"{'='*60}\n")
    
    def bp_if(self, condition, name, **variables):
        """Conditional breakpoint - only break if condition is True.
        
        Example:
            debug.bp_if(drop > 0.2, "large_drop", 
                        drop_V=drop, 
                        threshold=0.2)
        """
        if condition:
            self.bp(name, **variables)
    
    def trace(self, event, **data):
        """Tracepoint - log event without pausing (non-blocking).
        
        Example:
            debug.trace("sample", ch="PLC", v=1.274, stable=True)
        """
        import config
        if not config.DEBUG_TRACE or not self.enabled:
            return
        
        entry = {
            'ms': time.ticks_ms(),
            'event': event,
            'data': data
        }
        self.trace_log.append(entry)
        
        # Keep last 100 events (circular buffer)
        if len(self.trace_log) > 100:
            self.trace_log.pop(0)
    
    def dump_trace(self, last_n=20):
        """Print recent trace events.
        
        Args:
            last_n: Number of recent events to show (default 20)
        """
        print(f"\n{'='*60}")
        print(f"TRACE LOG (last {last_n} events):")
        print(f"{'='*60}")
        
        for entry in self.trace_log[-last_n:]:
            data_str = ', '.join(f"{k}={v}" for k, v in entry['data'].items())
            print(f"  {entry['ms']:8d}ms | {entry['event']:25s} | {data_str}")
        
        print(f"{'='*60}\n")
    
    def clear_trace(self):
        """Clear trace log."""
        self.trace_log.clear()
        print("Trace log cleared")
    
    def watch(self, name, break_on_change=True):
        """Create or retrieve a watchpoint.
        
        Args:
            name: Variable name to watch
            break_on_change: If True, trigger breakpoint on change
        
        Returns:
            Watchpoint object
        
        Example:
            watch = debug.watch("dip_active")
            watch.check(st.dip_active, channel="PLC")
        """
        if name not in self.watchpoints:
            self.watchpoints[name] = Watchpoint(name, break_on_change)
        return self.watchpoints[name]
    
    def status(self):
        """Print debug status summary."""
        print(f"\n{'='*60}")
        print(f"DEBUG STATUS")
        print(f"{'='*60}")
        print(f"  Breakpoints hit:  {self.breakpoints_hit}")
        print(f"  Trace events:     {len(self.trace_log)}")
        print(f"  Watchpoints:      {len(self.watchpoints)}")
        print(f"  Enabled:          {self.enabled}")
        print(f"  Paused:           {self.paused}")
        print(f"{'='*60}\n")
    
    def enable(self):
        """Enable debugging."""
        self.enabled = True
        print("Debug enabled")
    
    def disable(self):
        """Disable all debugging (for performance)."""
        self.enabled = False
        print("Debug disabled")
    
    def reset(self):
        """Reset all debug state."""
        self.breakpoints_hit = 0
        self.trace_log.clear()
        self.watchpoints.clear()
        self.paused = False
        print("Debug state reset")


# Global debug instance
debug = DebugHelper()


def process_debug_uart_commands(uart, states):
    """Process interactive debug commands via UART.
    
    Commands:
        p - pause execution
        c - continue execution
        s - show status (channels, baselines, etc.)
        v - dump all variables for all channels
        t - dump trace log
        b - show breakpoint count
        r - reset debug state
        h - help
    
    Args:
        uart: UART object (or None)
        states: Dictionary of channel states {name: ChannelState}
    
    Returns:
        True if paused, False if running
    """
    if not uart or not uart.any():
        return debug.paused
    
    import config
    if not config.DEBUG_INTERACTIVE:
        return False
    
    try:
        cmd = uart.read(1)
        
        if cmd == b'p':  # Pause
            debug.paused = True
            print("\nDEBUG: PAUSED")
            print("Commands: c=continue, s=status, v=variables, t=trace, b=breakpoints, r=reset, h=help")
        
        elif cmd == b'c':  # Continue
            debug.paused = False
            print("\nDEBUG: RESUMED\n")
        
        elif cmd == b's':  # Status
            print("\n" + "="*60)
            print("CHANNEL STATUS")
            print("="*60)
            for ch_name, st in states.items():
                baseline_str = f"{st.baseline:.3f}V" if st.baseline else "None"
                print(f"  {ch_name}: stable={st.stable:5s} baseline={baseline_str:8s} dip={st.dip_active}")
            print("="*60 + "\n")
        
        elif cmd == b'v':  # Variables
            print("\n" + "="*60)
            print("CHANNEL VARIABLES")
            print("="*60)
            for ch_name, st in states.items():
                print(f"\n{ch_name}:")
                for attr, value in st.__dict__.items():
                    # Skip large lists
                    if isinstance(value, list) and len(value) > 5:
                        print(f"  {attr:20s} = {type(value).__name__}[{len(value)}]")
                    else:
                        print(f"  {attr:20s} = {value}")
            print("="*60 + "\n")
        
        elif cmd == b't':  # Trace
            debug.dump_trace(last_n=15)
        
        elif cmd == b'b':  # Breakpoints
            debug.status()
        
        elif cmd == b'r':  # Reset
            debug.reset()
        
        elif cmd == b'h':  # Help
            print("\nDEBUG COMMANDS:")
            print("  p - Pause execution")
            print("  c - Continue/resume")
            print("  s - Show channel status")
            print("  v - Dump all variables")
            print("  t - Show trace log")
            print("  b - Show breakpoint stats")
            print("  r - Reset debug state")
            print("  h - This help\n")
    
    except Exception as e:
        print(f"Debug command error: {e}")
    
    return debug.paused

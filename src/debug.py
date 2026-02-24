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
    """Main debug helper with breakpoints, traces, and watchpoints."""
    
    def __init__(self):
        self.breakpoints_hit = 0
        self.trace_log = []
        self.watchpoints = {}
        self.enabled = True
    
    def bp(self, name, **variables):
        """Soft breakpoint - pause and print variables.
        
        Example:
            debug.bp("dip_detected", 
                     channel="BLUE", 
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
            debug.trace("sample", ch="BLUE", v=1.274, stable=True)
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
            watch.check(st.dip_active, channel="BLUE")
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
        print("Debug state reset")


# Global debug instance
debug = DebugHelper()

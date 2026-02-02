# config.py

# ============================================================
# LOGGING MODE
# ============================================================
# "USB_STREAM" - Stream all data to USB serial for InfluxDB logging
# "EVENT_ONLY" - Log only dips and baseline snapshots to flash
# "FULL_LOCAL" - Log all medians to flash (with circular buffer)
LOGGING_MODE = "USB_STREAM"

# ============================================================
# Serial output configuration (for USB_STREAM mode)
# ============================================================
# Set to True when using Raspberry Pi Debug Probe UART connection
# Enables dual output: USB CDC (for Thonny) + UART (for Debug Probe)
# See docs/DEBUG_PROBE.md for setup instructions
USE_DEBUG_PROBE = False

# ============================================================
# ADC conversion
# ============================================================
VREF = 3.3

# ============================================================
# Sampling
# ============================================================
TICK_MS = 10                 # 10 ms tick
STABLE_WINDOW = 10           # last 10 raw samples (100 ms)
MEDIAN_BLOCK = 10            # median of 10 samples (100 ms)

# ============================================================
# Stability definition (AAA-like inputs)
# ============================================================
MIN_V = 0.6
MAX_V = 1.8
STABLE_SPAN_V = 0.03         # max-min allowed in raw stable window

# ============================================================
# Baseline (built from stable medians)
# ============================================================
BASELINE_SECONDS = 3.0       # baseline history length
MEDIAN_PERIOD_S = (TICK_MS * MEDIAN_BLOCK) / 1000.0
BASELINE_LEN = int(BASELINE_SECONDS / MEDIAN_PERIOD_S)  # ~30 medians

# ============================================================
# Dip detection (raw samples, low latency)
# ============================================================
DIP_THRESHOLD_V = 0.10       # dip starts if value <= baseline - threshold
RECOVERY_MARGIN_V = 0.04     # hysteresis margin
DIP_START_HOLD = 2           # consecutive ticks below start threshold
DIP_END_HOLD = 2             # consecutive ticks above end threshold
DIP_COOLDOWN_MS = 300        # ignore new dips after dip ends

# ============================================================
# Logging / shell
# ============================================================
MEDIANS_FILE = "/pico_medians.csv"
DIPS_FILE = "/pico_dips.csv"
BASELINE_SNAPSHOTS_FILE = "/pico_baseline_snapshots.csv"

MEDIAN_FLUSH_EVERY_S = 1.0
SHELL_STATUS_EVERY_S = 60.0  # Less frequent when streaming to USB
STATS_REPORT_EVERY_S = 60.0

# ============================================================
# File size limits (circular buffer)
# ============================================================
# Keep last 1 hour of medians: 3 channels * 10 samples/sec = 30 lines/sec
# 1 hour = 3600 lines, ~90 KB
MAX_MEDIANS_LINES = 3600
MAX_MEDIANS_SIZE_BYTES = 100 * 1024  # 100 KB

# Baseline snapshots: every 10 minutes
BASELINE_SNAPSHOT_EVERY_S = 600.0

# ============================================================
# Channels
# ============================================================
CHANNEL_PINS = [
    ("GP26", 26),
    ("GP27", 27),
    ("GP28", 28),
]

# ============================================================
# Configuration validation
# ============================================================
def validate_config():
    """Validate configuration parameters. Raises ValueError if invalid."""
    errors = []
    
    # Voltage range checks
    if MIN_V < 0 or MIN_V >= VREF:
        errors.append(f"MIN_V={MIN_V} must be 0 <= MIN_V < VREF={VREF}")
    if MAX_V <= MIN_V or MAX_V > VREF:
        errors.append(f"MAX_V={MAX_V} must be MIN_V < MAX_V <= VREF={VREF}")
    if STABLE_SPAN_V <= 0:
        errors.append(f"STABLE_SPAN_V={STABLE_SPAN_V} must be positive")
    
    # Timing checks
    if TICK_MS <= 0:
        errors.append(f"TICK_MS={TICK_MS} must be positive")
    if MEDIAN_BLOCK <= 0:
        errors.append(f"MEDIAN_BLOCK={MEDIAN_BLOCK} must be positive")
    if STABLE_WINDOW < MEDIAN_BLOCK:
        errors.append(f"STABLE_WINDOW={STABLE_WINDOW} should be >= MEDIAN_BLOCK={MEDIAN_BLOCK}")
    
    # Dip detection checks
    if DIP_THRESHOLD_V <= 0:
        errors.append(f"DIP_THRESHOLD_V={DIP_THRESHOLD_V} must be positive")
    if RECOVERY_MARGIN_V < 0 or RECOVERY_MARGIN_V >= DIP_THRESHOLD_V:
        errors.append(f"RECOVERY_MARGIN_V={RECOVERY_MARGIN_V} must be 0 <= margin < DIP_THRESHOLD_V={DIP_THRESHOLD_V}")
    if DIP_START_HOLD <= 0:
        errors.append(f"DIP_START_HOLD={DIP_START_HOLD} must be positive")
    if DIP_END_HOLD <= 0:
        errors.append(f"DIP_END_HOLD={DIP_END_HOLD} must be positive")
    
    # Logging mode check
    valid_modes = ["USB_STREAM", "EVENT_ONLY", "FULL_LOCAL"]
    if LOGGING_MODE not in valid_modes:
        errors.append(f"LOGGING_MODE={LOGGING_MODE} must be one of {valid_modes}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True

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
USE_DEBUG_PROBE = False

# ============================================================
# Debug / Development (Soft Breakpoints)
# ============================================================
DEBUG_BREAKPOINTS = False
DEBUG_TRACE = False
DEBUG_INTERACTIVE = False

# ============================================================
# ADC conversion (ADC PIN domain)
# ============================================================
VREF = 3.3

# ============================================================
# Sampling
# ============================================================
TICK_MS = 10                 # 10 ms tick
STABLE_WINDOW = 10           # last 10 raw samples (100 ms)
MEDIAN_BLOCK = 10            # median of 10 samples (100 ms)

# ============================================================
# Stability definition (ADC PIN volts)
# ============================================================
MIN_V = 0.6
MAX_V = 3.3
STABLE_SPAN_V = 0.03         # max-min allowed in raw stable window
STABLE_GRACE_MS = 200        # allow dip detection shortly after stability breaks

# ============================================================
# Baseline (built from stable raw samples)
# ============================================================
BASELINE_SECONDS = 3.0
BASELINE_INIT_SAMPLES = int((BASELINE_SECONDS * 1000) / TICK_MS) if TICK_MS > 0 else 0
BASELINE_ALPHA = (TICK_MS / (BASELINE_SECONDS * 1000.0)) if BASELINE_SECONDS > 0 else 1.0

# ============================================================
# Dip detection (ADC PIN volts, low latency)
# ============================================================
# From your log, drops were ~0.45V at ADC pin.
# 0.15V is a good starting threshold for catching smaller dips without constant triggering.
DIP_THRESHOLD_V = 0.15       # dip starts if v <= baseline - threshold
RECOVERY_MARGIN_V = 0.05     # hysteresis
DIP_START_HOLD = 1
DIP_END_HOLD = 2
DIP_COOLDOWN_MS = 300

# Optional marker pin
DIP_DETECT_MARKER_PIN = None
DIP_DETECT_MARKER_PULSE_MS = 2

# ============================================================
# Logging / shell
# ============================================================
MEDIANS_FILE = "/pico_medians.csv"
DIPS_FILE = "/pico_dips.csv"
BASELINE_SNAPSHOTS_FILE = "/pico_baseline_snapshots.csv"

MEDIAN_FLUSH_EVERY_S = 1.0
SHELL_STATUS_EVERY_S = 60.0
STATS_REPORT_EVERY_S = 60.0

# ============================================================
# File size limits (circular buffer)
# ============================================================
MAX_MEDIANS_LINES = 3600
MAX_MEDIANS_SIZE_BYTES = 100 * 1024  # 100 KB

BASELINE_SNAPSHOT_EVERY_S = 600.0

# ============================================================
# Channels
# ============================================================
CHANNEL_PINS = [
    ("PLC", 26),
    ("MODEM", 27),
    ("BATTERY", 28),
]

# ============================================================
# Divider scaling (ONLY for display/logging)
# ============================================================
DIVIDER_RTOP_OHM = 82_000
DIVIDER_RBOT_OHM = 10_000
DIVIDER_SCALE = (DIVIDER_RTOP_OHM + DIVIDER_RBOT_OHM) / DIVIDER_RBOT_OHM  # 9.2

CHANNEL_SCALE = {
    "PLC": DIVIDER_SCALE,
    "MODEM": DIVIDER_SCALE,
    "BATTERY": DIVIDER_SCALE,
}

# ============================================================
# OLED UI (SSD1351 128x96)
# ============================================================
ENABLE_OLED = True

OLED_SPI_ID = 0
OLED_SCK = 18
OLED_MOSI = 19
OLED_CS = 17
OLED_DC = 20
OLED_RST = 21

# Graph range in REAL volts (scaled for display only)
UI_V_MIN = 0.0
UI_V_MAX = 12.5

# Start with no DIP display for 1.5s
UI_NO_DIP_MS = 1500

# Display dip as negative (example: -3.97)
UI_DIP_NEGATIVE = True

# ============================================================
# Configuration validation
# ============================================================
def validate_config():
    errors = []

    # ADC range checks
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
    if BASELINE_SECONDS <= 0:
        errors.append(f"BASELINE_SECONDS={BASELINE_SECONDS} must be positive")
    if BASELINE_INIT_SAMPLES < 3:
        errors.append(f"BASELINE_INIT_SAMPLES={BASELINE_INIT_SAMPLES} is too small (need >= 3)")
    if BASELINE_ALPHA <= 0 or BASELINE_ALPHA > 1.0:
        errors.append(f"BASELINE_ALPHA={BASELINE_ALPHA} must be in (0, 1]")

    # Dip checks
    if DIP_THRESHOLD_V <= 0:
        errors.append(f"DIP_THRESHOLD_V={DIP_THRESHOLD_V} must be positive")
    if RECOVERY_MARGIN_V < 0 or RECOVERY_MARGIN_V >= DIP_THRESHOLD_V:
        errors.append(f"RECOVERY_MARGIN_V={RECOVERY_MARGIN_V} must be 0 <= margin < DIP_THRESHOLD_V={DIP_THRESHOLD_V}")
    if DIP_START_HOLD <= 0:
        errors.append(f"DIP_START_HOLD={DIP_START_HOLD} must be positive")
    if DIP_END_HOLD <= 0:
        errors.append(f"DIP_END_HOLD={DIP_END_HOLD} must be positive")
    if DIP_DETECT_MARKER_PULSE_MS <= 0:
        errors.append(f"DIP_DETECT_MARKER_PULSE_MS={DIP_DETECT_MARKER_PULSE_MS} must be positive")

    valid_modes = ["USB_STREAM", "EVENT_ONLY", "FULL_LOCAL"]
    if LOGGING_MODE not in valid_modes:
        errors.append(f"LOGGING_MODE={LOGGING_MODE} must be one of {valid_modes}")

    if ENABLE_OLED and UI_V_MAX <= UI_V_MIN:
        errors.append("UI_V_MAX must be > UI_V_MIN")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True
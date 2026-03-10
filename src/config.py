# config.py

# ============================================================
# LOGGING MODE
# ============================================================
# "USB_STREAM" - Stream all data to USB serial for InfluxDB logging
# "EVENT_ONLY" - Log only dips and baseline snapshots to flash
# "FULL_LOCAL" - Log all medians to flash (with circular buffer)
# "DISPLAY_ONLY" - No runtime USB/CSV I/O; keep sampling + detection + OLED
LOGGING_MODE = "DISPLAY_ONLY"

# ============================================================
# Debug / Development (Soft Breakpoints)
# ============================================================
DEBUG_BREAKPOINTS = False
DEBUG_TRACE = False

# ============================================================
# ADC conversion (ADC PIN domain)
# ============================================================
VREF = 3.3

# ADC precision / calibration:
# - Settling discards mitigate channel-to-channel crosstalk in the ADC mux.
# - Oversample + trim mean reduces random conversion noise.
# - Gain/offset maps allow per-channel calibration against a known DMM value.
ADC_SETTLE_DISCARDS = 1
ADC_OVERSAMPLE_COUNT = 9
ADC_TRIM_COUNT = 2
ADC_SETTLE_US = 2

ADC_CHANNEL_GAIN = {
    "BLUE": 1.0,
    "YELLOW": 1.0,
    "GREEN": 1.0,
}
ADC_CHANNEL_OFFSET_V = {
    "BLUE": 0.0,
    "YELLOW": 0.0,
    "GREEN": 0.0,
}

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

# Runtime status LED
# Use "LED" board alias for compatibility across MicroPython builds.
# On Pico 2 this maps to the onboard status LED.
ENABLE_STATUS_LED = True
STATUS_LED_PIN = "LED"  # "LED" or integer GPIO (0..29)
STATUS_LED_ACTIVE_LOW = False
STATUS_LED_OFF_ON_EXIT = True

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
# ADC terminal debug (runtime diagnostics)
# ============================================================
# Prints live ADC-domain detector context to terminal for troubleshooting.
ADC_DEBUG_TERMINAL_ENABLED = False
ADC_DEBUG_TERMINAL_INTERVAL_MS = 100
ADC_DEBUG_TERMINAL_SHOW_UI_EVENTS = True
ADC_DEBUG_TERMINAL_CHANNEL_FILTER = "ALL"  # "ALL", "BLUE", "YELLOW", "GREEN"

# ============================================================
# Source-off handling (supply removed / floating input)
# ============================================================
SOURCE_OFF_ENABLED = True
SOURCE_OFF_ADC_V = 0.08
SOURCE_OFF_HOLD_MS = 250
SOURCE_OFF_RELEASE_ADC_V = 0.12
SOURCE_OFF_RELEASE_MS = 400
SOURCE_OFF_DIP_CANCEL_WINDOW_MS = 2500
UI_SOURCE_OFF_OVERLAY_ENABLED = True
UI_SOURCE_OFF_OVERLAY_TEXT = "NO SIGNAL"

# ============================================================
# Runtime performance metrics
# ============================================================
PERF_METRICS_ENABLED = False
PERF_REPORT_EVERY_S = 30.0
PERF_RING_SIZE = 1024

# Dual-core runtime split (RP2350 / RP2040)
DUAL_CORE_ENABLED = True
# Strict policy: when enabled, Core0 never performs OLED draw/event writes.
# If Core1 is unavailable and strict is enabled, UI runs headless.
UI_CORE1_STRICT = False
CORE1_QUEUE_SIZE = 256
CORE1_IDLE_SLEEP_MS = 1

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
    ("BLUE", 26),
    ("YELLOW", 27),
    ("GREEN", 28),
]

# ============================================================
# Divider scaling (ONLY for display/logging)
# ============================================================
DIVIDER_RTOP_OHM = 820_000
DIVIDER_RBOT_OHM = 47_000
DIVIDER_SCALE = (DIVIDER_RTOP_OHM + DIVIDER_RBOT_OHM) / DIVIDER_RBOT_OHM  # 18.447

CHANNEL_SCALE = {
    "BLUE": DIVIDER_SCALE,
    "YELLOW": DIVIDER_SCALE,
    "GREEN": DIVIDER_SCALE,
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

# OLED UI toggle button (optional)
# Set UI_TOGGLE_BTN_PIN=None to disable.
UI_TOGGLE_BTN_PIN = 15
UI_TOGGLE_ACTIVE_LOW = True
UI_TOGGLE_PULL = "UP"          # "UP" or "DOWN"
UI_TOGGLE_DEBOUNCE_MS = 80

# Dedicated channel-select button (optional)
# Tap to cycle visible channels: ALL -> BLUE -> YELLOW -> GREEN.
# Set UI_CHANNEL_BTN_PIN=None to disable.
UI_CHANNEL_BTN_PIN = 13
UI_CHANNEL_BTN_ACTIVE_LOW = True
UI_CHANNEL_BTN_PULL = "UP"     # "UP" or "DOWN"
UI_CHANNEL_BTN_DEBOUNCE_MS = 30
UI_CHANNEL_BADGE_MS = 1000     # temporary CH: mode badge visibility

# OLED stats view
UI_STATS_MAX_EVENTS = 6
UI_STATS_DEFAULT_VIEW = "GRAPH"  # "GRAPH" or "STATS"
UI_STATS_DOUBLE_HEIGHT = True
UI_STATS_BOLD = True
UI_STATS_ACTIVE_BLINK_ENABLED = True
UI_STATS_ACTIVE_BLINK_MS = 500

# Graph layout / axis overlay
UI_HUD_H = 0
UI_Y_AXIS_ENABLED = False
UI_Y_AXIS_STRIP_W = 36
UI_Y_AXIS_DECIMALS = 1
UI_Y_AXIS_SHOW_MID = False
UI_GRAPH_LEGEND_ENABLED = False
UI_GRAPH_READOUTS_ENABLED = True
UI_GRAPH_READOUT_DECIMALS = 1
UI_GRAPH_READOUT_SHOW_UNITS = False
UI_GRAPH_READOUT_TOP_MODE = "LIVE_VISIBLE_MAX"  # "LIVE_VISIBLE_MAX" or "RANGE_MAX"
UI_GRAPH_STARTUP_SPAN_V = 6.0
UI_GRAPH_STARTUP_HOLD_MS = 2000
UI_GRAPH_MAX_EVENTS = 24
# Baseline overlay draws a horizontal reference line that can overlap top-of-graph data.
UI_GRAPH_BASELINE_ENABLED = False
UI_GRAPH_BASELINE_ALPHA_UP = 0.25
UI_GRAPH_BASELINE_ALPHA_DOWN = 0.03
UI_GRAPH_CHANNEL_FILTER = "ALL"   # "ALL", "BLUE", "YELLOW", "GREEN"
# Graph-only real-voltage calibration:
# v_real = (v_adc * UI_GRAPH_REAL_GAIN[channel]) + UI_GRAPH_REAL_OFFSET_V[channel]
UI_GRAPH_REAL_GAIN = {
    "BLUE": DIVIDER_SCALE,
    "YELLOW": DIVIDER_SCALE,
    "GREEN": DIVIDER_SCALE,
}
UI_GRAPH_REAL_OFFSET_V = {
    "BLUE": 0.0,
    "YELLOW": 0.0,
    "GREEN": 0.0,
}
UI_GRAPH_REAL_CLAMP_MIN_V = 0.0
UI_GRAPH_REAL_CLAMP_MAX_V = 60.0
# Main-loop OLED plot gate:
# - True: require fresh medians from all channels before drawing.
# - False: render every frame using last-known or default ADC volts per channel.
UI_MAIN_PLOT_REQUIRE_ALL_CHANNELS = False
UI_MAIN_PLOT_DEFAULT_ADC_V = 0.0

# Dip callouts (graph overlay from left axis to dip column)
UI_DIP_CALLOUTS_ENABLED = True
UI_DIP_CALLOUT_INCLUDE_ACTIVE = False
UI_DIP_CALLOUT_SCOPE = "ALL_FINISHED_IN_WINDOW"  # show all finished dip labels in view
UI_DIP_LABEL_OVERLAP_MODE = "DRAW_ALL"  # "DRAW_ALL", "PRIORITY_SKIP"
UI_DIP_LABEL_PRIORITY = "LARGEST_DROP"       # "LARGEST_DROP", "NEWEST"

# Graph event markers (for correlating graph and stats events)
UI_GRAPH_EVENT_MARKERS_ENABLED = False
UI_GRAPH_EVENT_MARKER_Y = 0
UI_GRAPH_EVENT_MARKER_H = 3
UI_GRAPH_EVENT_MARKER_W = 3
UI_GRAPH_EVENT_MARKER_ACTIVE_HOLLOW = True
UI_GRAPH_EVENT_MARKER_ACTIVE_FORCE_MIN_SIZE = True

# Graph range in REAL volts (scaled for display only)
UI_V_MIN = 0.0
UI_V_MAX = 60.0

# Auto-zoom for OLED plot.
# True: adapt Y-range to recent visible values (good for emphasizing dips).
# False: fixed UI_V_MIN/UI_V_MAX range.
UI_AUTO_ZOOM = True
UI_AUTO_WINDOW = 128        # points considered for dynamic range
UI_AUTO_MIN_SPAN_V = 6.0    # minimum displayed Y span (REAL volts)
UI_AUTO_PAD_FRAC = 0.20     # top headroom as fraction of current span
UI_AUTO_BOTTOM_PAD_FRAC = 0.35  # extra room below dips so troughs stay above the floor
UI_AUTO_RANGE_ALPHA = 0.35  # smoothing (0..1): higher reacts faster
UI_AUTO_RANGE_UPDATE_EVERY = 4  # update auto-range every N frames (speed/quality tradeoff)
UI_AUTO_RANGE_EPSILON_V = 0.03  # redraw only if range changed by this much
UI_AUTO_ZOOMOUT_HOLD_SCREENS = 3  # hold widened range for N plot widths before shrinking
UI_AUTO_ZOOMIN_COOLDOWN_SCREENS = 1  # keep zoom-in blocked after expansion
UI_AUTO_RANGE_MAX_STEP_V = 0.20  # max range edge movement per auto-range update

# Auto-zoom startup bootstrap:
# During bootstrap, collect live values before graph trace draw starts, then
# initialize range from percentile-clamped data.
UI_AUTO_ZOOM_BOOTSTRAP_ENABLE = True
UI_AUTO_ZOOM_BOOTSTRAP_FRAMES = 20
UI_AUTO_ZOOM_BOOTSTRAP_VIEW = "CALIBRATE"  # "CALIBRATE", "FIXED", "BLANK"
UI_AUTO_ZOOM_BOOTSTRAP_PCTL_LOW = 5
UI_AUTO_ZOOM_BOOTSTRAP_PCTL_HIGH = 95
UI_AUTO_ZOOM_BOOTSTRAP_SKIP_STARTUP_LOCK = True

# Keep traces away from plot edges so they never touch HUD/text boundary.
UI_PLOT_TOP_PAD_PX = 1
UI_PLOT_BOTTOM_PAD_PX = 2

# Visual demo refresh pacing:
# 0 = uncapped (fastest possible, limited by OLED/SPI throughput)
UI_DEMO_FRAME_MS = 0
UI_DEMO_PRINT_EVENTS = False

# Start with no DIP display for 1.5s
UI_NO_DIP_MS = 1500

# Display dip as negative (example: -3.97)
UI_DIP_NEGATIVE = True

# Global MIN DIP badge (plot overlay)
UI_MIN_DIP_ENABLED = False
UI_MIN_DIP_X = 0
UI_MIN_DIP_Y = 64
UI_MIN_DIP_W = 60
UI_MIN_DIP_H = 8
UI_MIN_DIP_SHOW_CHANNEL = True
UI_MIN_DIP_RESET_ON_START = True
UI_MIN_DIP_EPS_V = 0.01      # Ignore tiny updates

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
    if (not isinstance(ADC_SETTLE_DISCARDS, int)) or isinstance(ADC_SETTLE_DISCARDS, bool) or ADC_SETTLE_DISCARDS < 0:
        errors.append("ADC_SETTLE_DISCARDS must be an integer >= 0")
    if (not isinstance(ADC_OVERSAMPLE_COUNT, int)) or isinstance(ADC_OVERSAMPLE_COUNT, bool) or ADC_OVERSAMPLE_COUNT < 1:
        errors.append("ADC_OVERSAMPLE_COUNT must be an integer >= 1")
    if (not isinstance(ADC_TRIM_COUNT, int)) or isinstance(ADC_TRIM_COUNT, bool) or ADC_TRIM_COUNT < 0:
        errors.append("ADC_TRIM_COUNT must be an integer >= 0")
    if (not isinstance(ADC_SETTLE_US, int)) or isinstance(ADC_SETTLE_US, bool) or ADC_SETTLE_US < 0:
        errors.append("ADC_SETTLE_US must be an integer >= 0")
    if isinstance(ADC_OVERSAMPLE_COUNT, int) and not isinstance(ADC_OVERSAMPLE_COUNT, bool):
        if isinstance(ADC_TRIM_COUNT, int) and not isinstance(ADC_TRIM_COUNT, bool):
            max_trim = (ADC_OVERSAMPLE_COUNT - 1) // 2
            if ADC_TRIM_COUNT > max_trim:
                errors.append(f"ADC_TRIM_COUNT={ADC_TRIM_COUNT} is too large for ADC_OVERSAMPLE_COUNT={ADC_OVERSAMPLE_COUNT} (max {max_trim})")
    if not isinstance(ADC_CHANNEL_GAIN, dict):
        errors.append("ADC_CHANNEL_GAIN must be a dict of channel->gain")
    if not isinstance(ADC_CHANNEL_OFFSET_V, dict):
        errors.append("ADC_CHANNEL_OFFSET_V must be a dict of channel->offset volts")
    if isinstance(ADC_CHANNEL_GAIN, dict):
        for ch_name, _ in CHANNEL_PINS:
            if ch_name in ADC_CHANNEL_GAIN:
                gain = ADC_CHANNEL_GAIN[ch_name]
                if isinstance(gain, bool) or (not isinstance(gain, (int, float))) or gain <= 0:
                    errors.append(f"ADC_CHANNEL_GAIN['{ch_name}'] must be numeric > 0")
    if isinstance(ADC_CHANNEL_OFFSET_V, dict):
        for ch_name, _ in CHANNEL_PINS:
            if ch_name in ADC_CHANNEL_OFFSET_V:
                offset = ADC_CHANNEL_OFFSET_V[ch_name]
                if isinstance(offset, bool) or (not isinstance(offset, (int, float))):
                    errors.append(f"ADC_CHANNEL_OFFSET_V['{ch_name}'] must be numeric")

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
    if ENABLE_STATUS_LED not in (True, False, 0, 1):
        errors.append("ENABLE_STATUS_LED must be boolean-like")
    if STATUS_LED_ACTIVE_LOW not in (True, False, 0, 1):
        errors.append("STATUS_LED_ACTIVE_LOW must be boolean-like")
    if STATUS_LED_OFF_ON_EXIT not in (True, False, 0, 1):
        errors.append("STATUS_LED_OFF_ON_EXIT must be boolean-like")
    pin_is_int = isinstance(STATUS_LED_PIN, int) and not isinstance(STATUS_LED_PIN, bool)
    pin_is_led_alias = isinstance(STATUS_LED_PIN, str) and STATUS_LED_PIN.upper() == "LED"
    if pin_is_int:
        if STATUS_LED_PIN < 0 or STATUS_LED_PIN > 29:
            errors.append("STATUS_LED_PIN must be in [0, 29] when integer")
    elif not pin_is_led_alias:
        errors.append("STATUS_LED_PIN must be 'LED' or an integer GPIO in [0, 29]")
    if pin_is_int and DIP_DETECT_MARKER_PIN is not None and DIP_DETECT_MARKER_PIN == STATUS_LED_PIN:
        errors.append("DIP_DETECT_MARKER_PIN must not use STATUS_LED_PIN")

    valid_modes = ["USB_STREAM", "EVENT_ONLY", "FULL_LOCAL", "DISPLAY_ONLY"]
    if LOGGING_MODE not in valid_modes:
        errors.append(f"LOGGING_MODE={LOGGING_MODE} must be one of {valid_modes}")
    if PERF_METRICS_ENABLED not in (True, False, 0, 1):
        errors.append("PERF_METRICS_ENABLED must be boolean-like")
    if isinstance(PERF_REPORT_EVERY_S, bool) or (not isinstance(PERF_REPORT_EVERY_S, (int, float))) or PERF_REPORT_EVERY_S <= 0:
        errors.append("PERF_REPORT_EVERY_S must be numeric > 0")
    if (not isinstance(PERF_RING_SIZE, int)) or isinstance(PERF_RING_SIZE, bool) or PERF_RING_SIZE < 32:
        errors.append("PERF_RING_SIZE must be an integer >= 32")
    if ADC_DEBUG_TERMINAL_ENABLED not in (True, False, 0, 1):
        errors.append("ADC_DEBUG_TERMINAL_ENABLED must be boolean-like")
    if ADC_DEBUG_TERMINAL_SHOW_UI_EVENTS not in (True, False, 0, 1):
        errors.append("ADC_DEBUG_TERMINAL_SHOW_UI_EVENTS must be boolean-like")
    if (not isinstance(ADC_DEBUG_TERMINAL_INTERVAL_MS, int)) or isinstance(ADC_DEBUG_TERMINAL_INTERVAL_MS, bool):
        errors.append("ADC_DEBUG_TERMINAL_INTERVAL_MS must be an integer >= 50")
    elif ADC_DEBUG_TERMINAL_INTERVAL_MS < 50:
        errors.append("ADC_DEBUG_TERMINAL_INTERVAL_MS must be >= 50")
    if ADC_DEBUG_TERMINAL_CHANNEL_FILTER not in ("ALL", "BLUE", "YELLOW", "GREEN"):
        errors.append("ADC_DEBUG_TERMINAL_CHANNEL_FILTER must be 'ALL', 'BLUE', 'YELLOW', or 'GREEN'")
    if SOURCE_OFF_ENABLED not in (True, False, 0, 1):
        errors.append("SOURCE_OFF_ENABLED must be boolean-like")
    if UI_SOURCE_OFF_OVERLAY_ENABLED not in (True, False, 0, 1):
        errors.append("UI_SOURCE_OFF_OVERLAY_ENABLED must be boolean-like")
    if isinstance(SOURCE_OFF_ADC_V, bool) or (not isinstance(SOURCE_OFF_ADC_V, (int, float))) or SOURCE_OFF_ADC_V < 0:
        errors.append("SOURCE_OFF_ADC_V must be numeric >= 0")
    if isinstance(SOURCE_OFF_RELEASE_ADC_V, bool) or (not isinstance(SOURCE_OFF_RELEASE_ADC_V, (int, float))) or SOURCE_OFF_RELEASE_ADC_V < 0:
        errors.append("SOURCE_OFF_RELEASE_ADC_V must be numeric >= 0")
    if (
        (not isinstance(SOURCE_OFF_ADC_V, bool))
        and isinstance(SOURCE_OFF_ADC_V, (int, float))
        and (not isinstance(SOURCE_OFF_RELEASE_ADC_V, bool))
        and isinstance(SOURCE_OFF_RELEASE_ADC_V, (int, float))
        and SOURCE_OFF_RELEASE_ADC_V < SOURCE_OFF_ADC_V
    ):
        errors.append("SOURCE_OFF_RELEASE_ADC_V must be >= SOURCE_OFF_ADC_V")
    if (not isinstance(SOURCE_OFF_HOLD_MS, int)) or isinstance(SOURCE_OFF_HOLD_MS, bool) or SOURCE_OFF_HOLD_MS < 0:
        errors.append("SOURCE_OFF_HOLD_MS must be an integer >= 0")
    if (not isinstance(SOURCE_OFF_RELEASE_MS, int)) or isinstance(SOURCE_OFF_RELEASE_MS, bool) or SOURCE_OFF_RELEASE_MS < 0:
        errors.append("SOURCE_OFF_RELEASE_MS must be an integer >= 0")
    if (not isinstance(SOURCE_OFF_DIP_CANCEL_WINDOW_MS, int)) or isinstance(SOURCE_OFF_DIP_CANCEL_WINDOW_MS, bool) or SOURCE_OFF_DIP_CANCEL_WINDOW_MS < 0:
        errors.append("SOURCE_OFF_DIP_CANCEL_WINDOW_MS must be an integer >= 0")
    if (not isinstance(UI_SOURCE_OFF_OVERLAY_TEXT, str)) or (len(UI_SOURCE_OFF_OVERLAY_TEXT.strip()) == 0):
        errors.append("UI_SOURCE_OFF_OVERLAY_TEXT must be a non-empty string")
    if DUAL_CORE_ENABLED not in (True, False, 0, 1):
        errors.append("DUAL_CORE_ENABLED must be boolean-like")
    if UI_CORE1_STRICT not in (True, False, 0, 1):
        errors.append("UI_CORE1_STRICT must be boolean-like")
    if (not isinstance(CORE1_QUEUE_SIZE, int)) or isinstance(CORE1_QUEUE_SIZE, bool) or CORE1_QUEUE_SIZE < 32:
        errors.append("CORE1_QUEUE_SIZE must be an integer >= 32")
    if (not isinstance(CORE1_IDLE_SLEEP_MS, int)) or isinstance(CORE1_IDLE_SLEEP_MS, bool) or CORE1_IDLE_SLEEP_MS < 0:
        errors.append("CORE1_IDLE_SLEEP_MS must be an integer >= 0")

    if ENABLE_OLED and UI_V_MAX <= UI_V_MIN:
        errors.append("UI_V_MAX must be > UI_V_MIN")
    if ENABLE_OLED:
        if UI_AUTO_WINDOW < 4:
            errors.append("UI_AUTO_WINDOW must be >= 4")
        if UI_AUTO_MIN_SPAN_V <= 0:
            errors.append("UI_AUTO_MIN_SPAN_V must be positive")
        if UI_AUTO_PAD_FRAC < 0:
            errors.append("UI_AUTO_PAD_FRAC must be >= 0")
        if UI_AUTO_BOTTOM_PAD_FRAC < UI_AUTO_PAD_FRAC:
            errors.append("UI_AUTO_BOTTOM_PAD_FRAC must be >= UI_AUTO_PAD_FRAC")
        if UI_AUTO_RANGE_ALPHA <= 0 or UI_AUTO_RANGE_ALPHA > 1.0:
            errors.append("UI_AUTO_RANGE_ALPHA must be in (0, 1]")
        if UI_AUTO_RANGE_UPDATE_EVERY < 1:
            errors.append("UI_AUTO_RANGE_UPDATE_EVERY must be >= 1")
        if UI_AUTO_RANGE_EPSILON_V < 0:
            errors.append("UI_AUTO_RANGE_EPSILON_V must be >= 0")
        if UI_AUTO_ZOOMOUT_HOLD_SCREENS < 0:
            errors.append("UI_AUTO_ZOOMOUT_HOLD_SCREENS must be >= 0")
        if UI_AUTO_ZOOMIN_COOLDOWN_SCREENS < 0:
            errors.append("UI_AUTO_ZOOMIN_COOLDOWN_SCREENS must be >= 0")
        if UI_AUTO_RANGE_MAX_STEP_V <= 0:
            errors.append("UI_AUTO_RANGE_MAX_STEP_V must be > 0")
        if UI_AUTO_ZOOM_BOOTSTRAP_ENABLE not in (True, False, 0, 1):
            errors.append("UI_AUTO_ZOOM_BOOTSTRAP_ENABLE must be boolean-like")
        if (not isinstance(UI_AUTO_ZOOM_BOOTSTRAP_FRAMES, int)) or isinstance(UI_AUTO_ZOOM_BOOTSTRAP_FRAMES, bool) or UI_AUTO_ZOOM_BOOTSTRAP_FRAMES < 1:
            errors.append("UI_AUTO_ZOOM_BOOTSTRAP_FRAMES must be an integer >= 1")
        if UI_AUTO_ZOOM_BOOTSTRAP_VIEW not in ("CALIBRATE", "FIXED", "BLANK"):
            errors.append("UI_AUTO_ZOOM_BOOTSTRAP_VIEW must be 'CALIBRATE', 'FIXED', or 'BLANK'")
        low_ok = (not isinstance(UI_AUTO_ZOOM_BOOTSTRAP_PCTL_LOW, bool)) and isinstance(UI_AUTO_ZOOM_BOOTSTRAP_PCTL_LOW, (int, float))
        high_ok = (not isinstance(UI_AUTO_ZOOM_BOOTSTRAP_PCTL_HIGH, bool)) and isinstance(UI_AUTO_ZOOM_BOOTSTRAP_PCTL_HIGH, (int, float))
        if not low_ok:
            errors.append("UI_AUTO_ZOOM_BOOTSTRAP_PCTL_LOW must be numeric")
        if not high_ok:
            errors.append("UI_AUTO_ZOOM_BOOTSTRAP_PCTL_HIGH must be numeric")
        if low_ok and high_ok:
            if UI_AUTO_ZOOM_BOOTSTRAP_PCTL_LOW < 0 or UI_AUTO_ZOOM_BOOTSTRAP_PCTL_HIGH > 100 or UI_AUTO_ZOOM_BOOTSTRAP_PCTL_LOW >= UI_AUTO_ZOOM_BOOTSTRAP_PCTL_HIGH:
                errors.append("UI_AUTO_ZOOM_BOOTSTRAP_PCTL_LOW/UI_AUTO_ZOOM_BOOTSTRAP_PCTL_HIGH must satisfy 0 <= low < high <= 100")
        if UI_AUTO_ZOOM_BOOTSTRAP_SKIP_STARTUP_LOCK not in (True, False, 0, 1):
            errors.append("UI_AUTO_ZOOM_BOOTSTRAP_SKIP_STARTUP_LOCK must be boolean-like")
        if UI_PLOT_TOP_PAD_PX < 0 or UI_PLOT_BOTTOM_PAD_PX < 0:
            errors.append("UI_PLOT_TOP_PAD_PX/UI_PLOT_BOTTOM_PAD_PX must be >= 0")
        if UI_HUD_H < 0 or UI_HUD_H >= 96:
            errors.append("UI_HUD_H must be in [0, 95]")
        if UI_Y_AXIS_ENABLED not in (True, False, 0, 1):
            errors.append("UI_Y_AXIS_ENABLED must be boolean-like")
        if UI_Y_AXIS_STRIP_W < 16 or UI_Y_AXIS_STRIP_W >= 128:
            errors.append("UI_Y_AXIS_STRIP_W must be in [16, 127]")
        if UI_Y_AXIS_DECIMALS not in (0, 1):
            errors.append("UI_Y_AXIS_DECIMALS must be 0 or 1")
        if UI_Y_AXIS_SHOW_MID not in (True, False, 0, 1):
            errors.append("UI_Y_AXIS_SHOW_MID must be boolean-like")
        if UI_GRAPH_LEGEND_ENABLED not in (True, False, 0, 1):
            errors.append("UI_GRAPH_LEGEND_ENABLED must be boolean-like")
        if UI_GRAPH_READOUTS_ENABLED not in (True, False, 0, 1):
            errors.append("UI_GRAPH_READOUTS_ENABLED must be boolean-like")
        if UI_GRAPH_READOUT_DECIMALS not in (0, 1):
            errors.append("UI_GRAPH_READOUT_DECIMALS must be 0 or 1")
        if UI_GRAPH_READOUT_SHOW_UNITS not in (True, False, 0, 1):
            errors.append("UI_GRAPH_READOUT_SHOW_UNITS must be boolean-like")
        if UI_GRAPH_READOUT_TOP_MODE not in ("LIVE_VISIBLE_MAX", "RANGE_MAX"):
            errors.append("UI_GRAPH_READOUT_TOP_MODE must be 'LIVE_VISIBLE_MAX' or 'RANGE_MAX'")
        if UI_GRAPH_STARTUP_SPAN_V <= 0:
            errors.append("UI_GRAPH_STARTUP_SPAN_V must be > 0")
        if UI_GRAPH_STARTUP_HOLD_MS < 0:
            errors.append("UI_GRAPH_STARTUP_HOLD_MS must be >= 0")
        if UI_GRAPH_MAX_EVENTS < 1:
            errors.append("UI_GRAPH_MAX_EVENTS must be >= 1")
        if UI_GRAPH_BASELINE_ENABLED not in (True, False, 0, 1):
            errors.append("UI_GRAPH_BASELINE_ENABLED must be boolean-like")
        if UI_GRAPH_BASELINE_ALPHA_UP <= 0 or UI_GRAPH_BASELINE_ALPHA_UP > 1.0:
            errors.append("UI_GRAPH_BASELINE_ALPHA_UP must be in (0, 1]")
        if UI_GRAPH_BASELINE_ALPHA_DOWN <= 0 or UI_GRAPH_BASELINE_ALPHA_DOWN > 1.0:
            errors.append("UI_GRAPH_BASELINE_ALPHA_DOWN must be in (0, 1]")
        if UI_GRAPH_CHANNEL_FILTER not in ("ALL", "BLUE", "YELLOW", "GREEN"):
            errors.append("UI_GRAPH_CHANNEL_FILTER must be 'ALL', 'BLUE', 'YELLOW', or 'GREEN'")
        if not isinstance(UI_GRAPH_REAL_GAIN, dict):
            errors.append("UI_GRAPH_REAL_GAIN must be a dict of channel->gain")
        if not isinstance(UI_GRAPH_REAL_OFFSET_V, dict):
            errors.append("UI_GRAPH_REAL_OFFSET_V must be a dict of channel->offset volts")
        if isinstance(UI_GRAPH_REAL_GAIN, dict):
            for ch_name, _ in CHANNEL_PINS:
                if ch_name in UI_GRAPH_REAL_GAIN:
                    gain = UI_GRAPH_REAL_GAIN[ch_name]
                    if isinstance(gain, bool) or (not isinstance(gain, (int, float))) or gain <= 0:
                        errors.append(f"UI_GRAPH_REAL_GAIN['{ch_name}'] must be numeric > 0")
        if isinstance(UI_GRAPH_REAL_OFFSET_V, dict):
            for ch_name, _ in CHANNEL_PINS:
                if ch_name in UI_GRAPH_REAL_OFFSET_V:
                    offset = UI_GRAPH_REAL_OFFSET_V[ch_name]
                    if isinstance(offset, bool) or (not isinstance(offset, (int, float))):
                        errors.append(f"UI_GRAPH_REAL_OFFSET_V['{ch_name}'] must be numeric")
        clamp_min_ok = not isinstance(UI_GRAPH_REAL_CLAMP_MIN_V, bool) and isinstance(UI_GRAPH_REAL_CLAMP_MIN_V, (int, float))
        clamp_max_ok = not isinstance(UI_GRAPH_REAL_CLAMP_MAX_V, bool) and isinstance(UI_GRAPH_REAL_CLAMP_MAX_V, (int, float))
        if not clamp_min_ok:
            errors.append("UI_GRAPH_REAL_CLAMP_MIN_V must be numeric")
        if not clamp_max_ok:
            errors.append("UI_GRAPH_REAL_CLAMP_MAX_V must be numeric")
        if clamp_min_ok and clamp_max_ok and UI_GRAPH_REAL_CLAMP_MAX_V <= UI_GRAPH_REAL_CLAMP_MIN_V:
            errors.append("UI_GRAPH_REAL_CLAMP_MAX_V must be > UI_GRAPH_REAL_CLAMP_MIN_V")
        if UI_MAIN_PLOT_REQUIRE_ALL_CHANNELS not in (True, False, 0, 1):
            errors.append("UI_MAIN_PLOT_REQUIRE_ALL_CHANNELS must be boolean-like")
        if isinstance(UI_MAIN_PLOT_DEFAULT_ADC_V, bool) or (not isinstance(UI_MAIN_PLOT_DEFAULT_ADC_V, (int, float))):
            errors.append("UI_MAIN_PLOT_DEFAULT_ADC_V must be numeric >= 0")
        elif UI_MAIN_PLOT_DEFAULT_ADC_V < 0:
            errors.append("UI_MAIN_PLOT_DEFAULT_ADC_V must be >= 0")
        if UI_DIP_CALLOUTS_ENABLED not in (True, False, 0, 1):
            errors.append("UI_DIP_CALLOUTS_ENABLED must be boolean-like")
        if UI_DIP_CALLOUT_INCLUDE_ACTIVE not in (True, False, 0, 1):
            errors.append("UI_DIP_CALLOUT_INCLUDE_ACTIVE must be boolean-like")
        if UI_DIP_CALLOUT_SCOPE not in ("LATEST_PER_CHANNEL", "ALL_FINISHED_IN_WINDOW"):
            errors.append("UI_DIP_CALLOUT_SCOPE must be 'LATEST_PER_CHANNEL' or 'ALL_FINISHED_IN_WINDOW'")
        if UI_DIP_LABEL_OVERLAP_MODE not in ("DRAW_ALL", "PRIORITY_SKIP"):
            errors.append("UI_DIP_LABEL_OVERLAP_MODE must be 'DRAW_ALL' or 'PRIORITY_SKIP'")
        if UI_DIP_LABEL_PRIORITY not in ("LARGEST_DROP", "NEWEST"):
            errors.append("UI_DIP_LABEL_PRIORITY must be 'LARGEST_DROP' or 'NEWEST'")
        if UI_DEMO_FRAME_MS < 0:
            errors.append("UI_DEMO_FRAME_MS must be >= 0")
        if UI_MIN_DIP_W <= 0 or UI_MIN_DIP_H <= 0:
            errors.append("UI_MIN_DIP_W/UI_MIN_DIP_H must be > 0")
        if UI_MIN_DIP_EPS_V < 0:
            errors.append("UI_MIN_DIP_EPS_V must be >= 0")
        if UI_GRAPH_EVENT_MARKER_H <= 0 or UI_GRAPH_EVENT_MARKER_W <= 0:
            errors.append("UI_GRAPH_EVENT_MARKER_H/UI_GRAPH_EVENT_MARKER_W must be > 0")
        if UI_GRAPH_EVENT_MARKER_Y < 0:
            errors.append("UI_GRAPH_EVENT_MARKER_Y must be >= 0")
        if UI_GRAPH_EVENT_MARKER_ACTIVE_HOLLOW not in (True, False, 0, 1):
            errors.append("UI_GRAPH_EVENT_MARKER_ACTIVE_HOLLOW must be boolean-like")
        if UI_GRAPH_EVENT_MARKER_ACTIVE_FORCE_MIN_SIZE not in (True, False, 0, 1):
            errors.append("UI_GRAPH_EVENT_MARKER_ACTIVE_FORCE_MIN_SIZE must be boolean-like")
        if UI_TOGGLE_BTN_PIN is not None and UI_TOGGLE_BTN_PIN < 0:
            errors.append("UI_TOGGLE_BTN_PIN must be >= 0 or None")
        if UI_TOGGLE_PULL not in ("UP", "DOWN"):
            errors.append("UI_TOGGLE_PULL must be 'UP' or 'DOWN'")
        if UI_TOGGLE_DEBOUNCE_MS < 0:
            errors.append("UI_TOGGLE_DEBOUNCE_MS must be >= 0")
        if UI_CHANNEL_BTN_PIN is not None:
            if isinstance(UI_CHANNEL_BTN_PIN, bool) or (not isinstance(UI_CHANNEL_BTN_PIN, int)):
                errors.append("UI_CHANNEL_BTN_PIN must be None or an integer >= 0")
            elif UI_CHANNEL_BTN_PIN < 0:
                errors.append("UI_CHANNEL_BTN_PIN must be None or an integer >= 0")
        if UI_CHANNEL_BTN_ACTIVE_LOW not in (True, False, 0, 1):
            errors.append("UI_CHANNEL_BTN_ACTIVE_LOW must be boolean-like")
        if UI_CHANNEL_BTN_PULL not in ("UP", "DOWN"):
            errors.append("UI_CHANNEL_BTN_PULL must be 'UP' or 'DOWN'")
        if UI_CHANNEL_BTN_DEBOUNCE_MS < 0:
            errors.append("UI_CHANNEL_BTN_DEBOUNCE_MS must be >= 0")
        if UI_CHANNEL_BADGE_MS < 0:
            errors.append("UI_CHANNEL_BADGE_MS must be >= 0")
        if (
            UI_TOGGLE_BTN_PIN is not None
            and UI_CHANNEL_BTN_PIN is not None
            and UI_TOGGLE_BTN_PIN == UI_CHANNEL_BTN_PIN
        ):
            errors.append("UI_CHANNEL_BTN_PIN must not equal UI_TOGGLE_BTN_PIN")
        if UI_STATS_MAX_EVENTS < 1:
            errors.append("UI_STATS_MAX_EVENTS must be >= 1")
        if UI_STATS_DEFAULT_VIEW not in ("GRAPH", "STATS"):
            errors.append("UI_STATS_DEFAULT_VIEW must be 'GRAPH' or 'STATS'")
        if UI_STATS_ACTIVE_BLINK_ENABLED not in (True, False, 0, 1):
            errors.append("UI_STATS_ACTIVE_BLINK_ENABLED must be boolean-like")
        if UI_STATS_ACTIVE_BLINK_MS < 100:
            errors.append("UI_STATS_ACTIVE_BLINK_MS must be >= 100")

        # OLED plot area width is fixed and height depends on UI_HUD_H.
        plot_w = 128
        plot_h = 96 - UI_HUD_H
        if plot_h < 1:
            plot_h = 1
        if UI_MIN_DIP_X < 0 or UI_MIN_DIP_Y < 0:
            errors.append("UI_MIN_DIP_X/UI_MIN_DIP_Y must be >= 0")
        if (UI_MIN_DIP_X + UI_MIN_DIP_W) > plot_w or (UI_MIN_DIP_Y + UI_MIN_DIP_H) > plot_h:
            errors.append("MIN DIP badge rectangle must fit inside plot area")
        if UI_GRAPH_EVENT_MARKER_Y >= plot_h:
            errors.append("UI_GRAPH_EVENT_MARKER_Y must be inside plot area")
        if (UI_GRAPH_EVENT_MARKER_Y + UI_GRAPH_EVENT_MARKER_H) > plot_h:
            errors.append("Graph event marker height must fit inside plot area")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True

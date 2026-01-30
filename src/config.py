# config.py

# ADC conversion
VREF = 3.3

# Sampling
TICK_MS = 10                 # 10 ms tick
STABLE_WINDOW = 10           # last 10 raw samples (100 ms)
MEDIAN_BLOCK = 10            # median of 10 samples (100 ms)

# Stability definition (AAA-like inputs)
MIN_V = 0.6
MAX_V = 1.8
STABLE_SPAN_V = 0.03         # max-min allowed in raw stable window

# Baseline (built from stable medians)
BASELINE_SECONDS = 3.0       # baseline history length
MEDIAN_PERIOD_S = (TICK_MS * MEDIAN_BLOCK) / 1000.0
BASELINE_LEN = int(BASELINE_SECONDS / MEDIAN_PERIOD_S)  # ~30 medians

# Dip detection (raw samples, low latency)
DIP_THRESHOLD_V = 0.10       # dip starts if value <= baseline - threshold
RECOVERY_MARGIN_V = 0.04     # hysteresis margin
DIP_START_HOLD = 2           # consecutive ticks below start threshold
DIP_END_HOLD = 2             # consecutive ticks above end threshold
DIP_COOLDOWN_MS = 300        # ignore new dips after dip ends

# Logging / shell
MEDIANS_FILE = "/pico_medians.csv"
DIPS_FILE = "/pico_dips.csv"
MEDIAN_FLUSH_EVERY_S = 1.0
SHELL_STATUS_EVERY_S = 1.0

# Channels
CHANNEL_PINS = [
    ("GP26", 26),
    ("GP27", 27),
    ("GP28", 28),
]

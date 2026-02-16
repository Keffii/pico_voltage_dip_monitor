# visual_dip_demo.py
#
# OLED-only visual test mode:
# - No CSV writes
# - No dip detector/filesystem pipeline
# - Random dip timing and random dip strength for zoom testing

import time
import config
from oled_ui import OledUI

try:
    import random
except ImportError:
    import urandom as random


CHANNELS = ("PLC", "MODEM", "BATTERY")

# Real-voltage baselines for each channel (display domain).
BASELINE_REAL = {
    "PLC": 11.9,
    "MODEM": 11.8,
    "BATTERY": 12.0,
}

# Frame pacing:
# 0 means uncapped (fastest possible for your OLED/SPI setup).
FRAME_MS = int(getattr(config, "UI_DEMO_FRAME_MS", 0))
PRINT_EVENTS = bool(getattr(config, "UI_DEMO_PRINT_EVENTS", False))

# Random dip scheduling.
DIP_INTERVAL_MIN_MS = 500
DIP_INTERVAL_MAX_MS = 3500
DIP_DEPTH_MIN_V = 0.2
DIP_DEPTH_MAX_V = 2.2
DIP_DURATION_MIN_MS = 80
DIP_DURATION_MAX_MS = 1200

# Add light baseline noise so traces are not perfectly flat between dips.
NOISE_V = 0.03


def _sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


def _ticks_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def _ticks_add(a, b):
    if hasattr(time, "ticks_add"):
        return time.ticks_add(a, b)
    return a + b


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _rand_unit():
    if hasattr(random, "random"):
        return random.random()
    if hasattr(random, "getrandbits"):
        return random.getrandbits(24) / 16777215.0
    # Last-resort fallback.
    return (_ticks_ms() % 1000) / 999.0


def _randf(lo, hi):
    if hi < lo:
        lo, hi = hi, lo
    return lo + (hi - lo) * _rand_unit()


def _randi(lo, hi):
    if hi < lo:
        lo, hi = hi, lo
    if hasattr(random, "randint"):
        return random.randint(lo, hi)
    span = hi - lo + 1
    if span <= 1:
        return lo
    if hasattr(random, "getrandbits"):
        return lo + (random.getrandbits(16) % span)
    return lo + int(_rand_unit() * span)


def _dip_factor(progress):
    # Smooth trapezoid: 20% down, 60% hold, 20% up.
    if progress < 0.2:
        return progress / 0.2
    if progress < 0.8:
        return 1.0
    return (1.0 - progress) / 0.2


def run():
    if not getattr(config, "ENABLE_OLED", False):
        print("ENABLE_OLED=False in config.py; set ENABLE_OLED=True for visual dip demo.")
        return

    ui = OledUI()
    print("Visual dip demo running (no files). Press Ctrl+C to stop.")

    active_dips = []
    now_ms = _ticks_ms()
    next_dip_ms = _ticks_add(now_ms, _randi(DIP_INTERVAL_MIN_MS, DIP_INTERVAL_MAX_MS))

    try:
        while True:
            now_ms = _ticks_ms()

            # Launch new random dip events on a random schedule.
            if _ticks_diff(now_ms, next_dip_ms) >= 0:
                ch = CHANNELS[_randi(0, len(CHANNELS) - 1)]
                depth_v = _randf(DIP_DEPTH_MIN_V, DIP_DEPTH_MAX_V)
                dur_ms = _randi(DIP_DURATION_MIN_MS, DIP_DURATION_MAX_MS)

                active_dips.append({
                    "channel": ch,
                    "depth_v": depth_v,
                    "start_ms": now_ms,
                    "dur_ms": dur_ms,
                })

                # Feed DIP value into HUD latch to match graph event.
                scale = config.CHANNEL_SCALE.get(ch, 1.0)
                ui.latch_dip_drop_adc(ch, depth_v / scale)

                if PRINT_EVENTS:
                    print(
                        "SIM DIP  ch={}  depth={:.2f}V  dur={}ms".format(
                            ch, depth_v, dur_ms
                        )
                    )

                next_dip_ms = _ticks_add(
                    now_ms, _randi(DIP_INTERVAL_MIN_MS, DIP_INTERVAL_MAX_MS)
                )

            # Sum active dip effect by channel.
            drop_now = {"PLC": 0.0, "MODEM": 0.0, "BATTERY": 0.0}
            still_active = []
            for d in active_dips:
                elapsed = _ticks_diff(now_ms, d["start_ms"])
                dur_ms = d["dur_ms"]
                if dur_ms <= 0:
                    progress = 1.0
                else:
                    progress = elapsed / float(dur_ms)
                if progress < 0.0:
                    progress = 0.0
                if progress > 1.0:
                    progress = 1.0
                factor = _dip_factor(progress)
                drop_now[d["channel"]] += d["depth_v"] * factor

                if progress < 1.0:
                    still_active.append(d)
                else:
                    ch = d["channel"]
                    base_real = BASELINE_REAL.get(ch, 11.8)
                    min_real = base_real - d["depth_v"]
                    drop_real = d["depth_v"]
                    scale = config.CHANNEL_SCALE.get(ch, 1.0)
                    ui.record_dip_event_adc(
                        ch,
                        base_real / scale,
                        min_real / scale,
                        drop_real / scale
                    )
            active_dips = still_active

            # Build per-channel voltages in real domain.
            vals_real = {}
            for ch in CHANNELS:
                base = BASELINE_REAL.get(ch, 11.8)
                noise = _randf(-NOISE_V, NOISE_V)
                v = base + noise - drop_now[ch]

                # Keep values inside display range.
                if v < config.UI_V_MIN:
                    v = config.UI_V_MIN
                if v > config.UI_V_MAX:
                    v = config.UI_V_MAX
                vals_real[ch] = v

            # Convert back to ADC-domain for existing OLED API.
            plc_adc = vals_real["PLC"] / config.CHANNEL_SCALE.get("PLC", 1.0)
            modem_adc = vals_real["MODEM"] / config.CHANNEL_SCALE.get("MODEM", 1.0)
            bat_adc = vals_real["BATTERY"] / config.CHANNEL_SCALE.get("BATTERY", 1.0)

            frame_start_ms = now_ms
            ui.plot_medians_adc(plc_adc, modem_adc, bat_adc)
            if FRAME_MS > 0:
                frame_used_ms = _ticks_diff(_ticks_ms(), frame_start_ms)
                remaining = FRAME_MS - frame_used_ms
                if remaining > 0:
                    _sleep_ms(remaining)

    except KeyboardInterrupt:
        ui.shutdown()
        print("\nVisual dip demo stopped.")


if __name__ == "__main__":
    run()

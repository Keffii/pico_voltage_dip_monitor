# visual_dip_demo.py
#
# OLED-only visual test mode:
# - No CSV writes
# - No ADC hardware sampling
# - Deterministic dip rotation for live demos

import time
import config
from oled_ui import OledUI

try:
    from machine import Pin
except ImportError:
    Pin = None


CHANNELS = ("BLUE", "YELLOW", "GREEN")

BASELINE_REAL = {
    "BLUE": 11.9,
    "YELLOW": 11.8,
    "GREEN": 12.0,
}

FRAME_MS = int(getattr(config, "UI_DEMO_FRAME_MS", 10))
PRINT_EVENTS = bool(getattr(config, "UI_DEMO_PRINT_EVENTS", False))
DIP_INTERVAL_MS = 2000
DIP_DURATION_MS = int(getattr(config, "UI_DEMO_DIP_DURATION_MS", 900))
DIP_DEPTH_REAL = {
    "BLUE": 3.2,
    "YELLOW": 4.0,
    "GREEN": 4.8,
}
CHANNEL_RIPPLE_V = {
    "BLUE": (0.00, 0.01, 0.00, -0.01),
    "YELLOW": (0.01, 0.00, -0.01, 0.00),
    "GREEN": (-0.01, 0.00, 0.01, 0.00),
}

if FRAME_MS < 0:
    FRAME_MS = 0
if DIP_DURATION_MS <= 0 or DIP_DURATION_MS >= DIP_INTERVAL_MS:
    DIP_DURATION_MS = 900


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


def _init_status_led():
    if not getattr(config, "ENABLE_STATUS_LED", False):
        return None
    if Pin is None:
        print("Warning: Status LED disabled (machine.Pin unavailable).")
        return None

    pin_cfg = getattr(config, "STATUS_LED_PIN", "LED")
    try:
        return Pin(pin_cfg, Pin.OUT)
    except Exception as primary_err:
        if pin_cfg != "LED":
            try:
                led = Pin("LED", Pin.OUT)
                print("Status LED: fallback to Pin('LED') succeeded.")
                return led
            except Exception:
                pass
        if pin_cfg != 25:
            try:
                led = Pin(25, Pin.OUT)
                print("Status LED: fallback to Pin(25) succeeded.")
                return led
            except Exception:
                pass
        print(f"Warning: Status LED disabled (init failed on {pin_cfg}): {primary_err}")
        return None


def _set_status_led(led_pin, on):
    if led_pin is None:
        return
    active_low = bool(getattr(config, "STATUS_LED_ACTIVE_LOW", False))
    try:
        if active_low:
            led_pin.value(0 if on else 1)
        else:
            led_pin.value(1 if on else 0)
    except Exception:
        pass


def _dip_factor(progress):
    if progress < 0.2:
        return progress / 0.2
    if progress < 0.8:
        return 1.0
    return (1.0 - progress) / 0.2


def _clamp_real(v_real):
    if v_real < config.UI_V_MIN:
        return config.UI_V_MIN
    if v_real > config.UI_V_MAX:
        return config.UI_V_MAX
    return v_real


def _channel_ripple(channel, frame_index):
    pattern = CHANNEL_RIPPLE_V.get(channel)
    if not pattern:
        return 0.0
    return pattern[frame_index % len(pattern)]


def _channel_scale(channel):
    scale = config.CHANNEL_SCALE.get(channel, 1.0)
    if scale <= 0:
        return 1.0
    return scale


def _emit_dip_event(ui, channel, baseline_real, min_real, event_id, active, sample_index):
    scale = _channel_scale(channel)
    drop_real = baseline_real - min_real
    if drop_real < 0:
        drop_real = 0.0
    ui.record_dip_event_adc(
        channel,
        baseline_real / scale,
        min_real / scale,
        drop_real / scale,
        event_id=event_id,
        active=active,
        sample_index=sample_index,
    )


def create_demo_state(start_ms=0):
    return {
        "next_event_id": 1,
        "next_dip_ms": int(start_ms),
        "rotation_index": 0,
        "active_dips": {},
        "last_vals_real": dict(BASELINE_REAL),
    }


def _start_due_dips(state, ui, now_ms, frame_index):
    while _ticks_diff(now_ms, state["next_dip_ms"]) >= 0:
        channel = CHANNELS[state["rotation_index"] % len(CHANNELS)]
        state["rotation_index"] += 1

        baseline_real = state["last_vals_real"].get(channel, BASELINE_REAL.get(channel, 11.8))
        baseline_real = _clamp_real(baseline_real)
        event_id = state["next_event_id"]
        state["next_event_id"] += 1

        state["active_dips"][channel] = {
            "channel": channel,
            "event_id": event_id,
            "baseline_real": baseline_real,
            "min_real": baseline_real,
            "start_ms": state["next_dip_ms"],
            "dur_ms": DIP_DURATION_MS,
            "depth_v": DIP_DEPTH_REAL.get(channel, 4.0),
            "sample_index": frame_index,
            "progress": 0.0,
        }


        if PRINT_EVENTS:
            print(
                "SIM DIP START  ch={}  base={:.2f}V  depth={:.2f}V  dur={}ms".format(
                    channel,
                    baseline_real,
                    DIP_DEPTH_REAL.get(channel, 4.0),
                    DIP_DURATION_MS,
                )
            )

        state["next_dip_ms"] = _ticks_add(state["next_dip_ms"], DIP_INTERVAL_MS)


def _build_channel_values(state, now_ms, frame_index):
    drop_now = {"BLUE": 0.0, "YELLOW": 0.0, "GREEN": 0.0}
    for dip in state["active_dips"].values():
        elapsed = _ticks_diff(now_ms, dip["start_ms"])
        dur_ms = dip["dur_ms"]
        if dur_ms <= 0:
            progress = 1.0
        else:
            progress = elapsed / float(dur_ms)
        if progress < 0.0:
            progress = 0.0
        if progress > 1.0:
            progress = 1.0
        dip["progress"] = progress
        drop_now[dip["channel"]] += dip["depth_v"] * _dip_factor(progress)

    vals_real = {}
    for channel in CHANNELS:
        baseline_real = BASELINE_REAL.get(channel, 11.8)
        ripple_v = _channel_ripple(channel, frame_index)
        vals_real[channel] = _clamp_real(baseline_real + ripple_v - drop_now[channel])
    return vals_real


def _update_active_dips(state, ui, vals_real):
    finished = []
    for channel, dip in state["active_dips"].items():
        v_now = vals_real.get(channel)
        if v_now is not None and v_now < dip["min_real"]:
            dip["min_real"] = v_now

        if dip["progress"] < 1.0:
            _emit_dip_event(
                ui,
                channel,
                dip["baseline_real"],
                dip["min_real"],
                dip["event_id"],
                True,
                dip["sample_index"],
            )
            continue

        _emit_dip_event(
            ui,
            channel,
            dip["baseline_real"],
            dip["min_real"],
            dip["event_id"],
            False,
            dip["sample_index"],
        )
        ui.latch_dip_drop_adc(channel, (dip["baseline_real"] - dip["min_real"]) / _channel_scale(channel))
        if PRINT_EVENTS:
            print(
                "SIM DIP END    ch={}  base={:.2f}V  min={:.2f}V  drop={:.2f}V".format(
                    channel,
                    dip["baseline_real"],
                    dip["min_real"],
                    dip["baseline_real"] - dip["min_real"],
                )
            )
        finished.append(channel)

    for channel in finished:
        state["active_dips"].pop(channel, None)


def advance_demo_state(state, ui, now_ms, frame_index):
    _start_due_dips(state, ui, now_ms, frame_index)
    vals_real = _build_channel_values(state, now_ms, frame_index)
    _update_active_dips(state, ui, vals_real)
    state["last_vals_real"] = dict(vals_real)
    return (
        vals_real["BLUE"] / _channel_scale("BLUE"),
        vals_real["YELLOW"] / _channel_scale("YELLOW"),
        vals_real["GREEN"] / _channel_scale("GREEN"),
    )


def run():
    if not getattr(config, "ENABLE_OLED", False):
        print("ENABLE_OLED=False in config.py; set ENABLE_OLED=True for visual dip demo.")
        return

    ui = OledUI()
    status_led = _init_status_led()
    _set_status_led(status_led, True)
    print("Visual dip demo running (no files). Press Ctrl+C to stop.")

    state = create_demo_state(start_ms=_ticks_ms())
    frame_index = 0

    try:
        while True:
            frame_start_ms = _ticks_ms()
            blue_adc, yellow_adc, green_adc = advance_demo_state(state, ui, frame_start_ms, frame_index)
            ui.plot_medians_adc(blue_adc, yellow_adc, green_adc)

            if FRAME_MS > 0:
                frame_used_ms = _ticks_diff(_ticks_ms(), frame_start_ms)
                remaining = FRAME_MS - frame_used_ms
                if remaining > 0:
                    _sleep_ms(remaining)
            frame_index += 1

    except KeyboardInterrupt:
        if bool(getattr(config, "STATUS_LED_OFF_ON_EXIT", True)):
            _set_status_led(status_led, False)
        ui.shutdown()
        print("\nVisual dip demo stopped.")
    except Exception:
        if bool(getattr(config, "STATUS_LED_OFF_ON_EXIT", True)):
            _set_status_led(status_led, False)
        raise


if __name__ == "__main__":
    run()


import sys
import types


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


if "machine" not in sys.modules:
    machine = types.ModuleType("machine")

    class _Pin:
        OUT = 1
        IN = 0
        PULL_UP = 1
        PULL_DOWN = 0

        def __init__(self, *_args, **_kwargs):
            pass

        def value(self, *_args, **_kwargs):
            return 0

    class _SPI:
        def __init__(self, *_args, **_kwargs):
            pass

        def write(self, *_args, **_kwargs):
            return 0

    machine.Pin = _Pin
    machine.SPI = _SPI
    sys.modules["machine"] = machine

if "framebuf" not in sys.modules:
    framebuf = types.ModuleType("framebuf")
    framebuf.FrameBuffer = object
    sys.modules["framebuf"] = framebuf

if "lib" not in sys.modules:
    sys.modules["lib"] = types.ModuleType("lib")
if "lib.drivers" not in sys.modules:
    sys.modules["lib.drivers"] = types.ModuleType("lib.drivers")
if "lib.drivers.ssd1351" not in sys.modules:
    sys.modules["lib.drivers.ssd1351"] = types.ModuleType("lib.drivers.ssd1351")
if "lib.drivers.ssd1351.ssd1351" not in sys.modules:
    ssd1351 = types.ModuleType("lib.drivers.ssd1351.ssd1351")

    class _SSD1351:
        def __init__(self, *_args, **_kwargs):
            pass

        @staticmethod
        def rgb(r, g, b):
            return (r, g, b)

    ssd1351.SSD1351 = _SSD1351
    sys.modules["lib.drivers.ssd1351.ssd1351"] = ssd1351

if "oled_ui" in sys.modules:
    del sys.modules["oled_ui"]

import oled_ui

OledUI = oled_ui.OledUI


def _new_zoom_ui(channel_filter="ALL"):
    ui = OledUI.__new__(OledUI)
    ui.auto_zoom = True
    ui.auto_window = 128
    ui.auto_min_span_v = 6.0
    ui.auto_pad_frac = 0.20
    ui.auto_bottom_pad_frac = 0.35
    ui.auto_range_alpha = 1.0
    ui.auto_range_max_step_v = 60.0
    ui.auto_range_epsilon_v = 0.03
    ui.V_MIN = 0.0
    ui.V_MAX = 60.0
    ui.graph_channel_filter = channel_filter
    ui.v_hist = {
        "BLUE": [13.9, 10.7],
        "YELLOW": [14.0, 10.0],
        "GREEN": [13.9, 9.1],
    }
    ui.range_v_min = 4.8
    ui.range_v_max = 16.0
    ui.sample_counter = 5
    ui.auto_zoomout_hold_samples = 100
    ui.auto_zoomout_hold_until_sample = 20
    ui.auto_zoomin_cooldown_samples = 100
    ui.auto_zoomin_cooldown_until_sample = 20
    return ui


def test_calc_target_range_biases_headroom_below_dip():
    ui = _new_zoom_ui()
    lo, hi = ui._calc_target_range()
    visible_min = 9.1
    visible_max = 14.0
    floor_gap = visible_min - lo
    ceiling_gap = hi - visible_max

    _assert(floor_gap > (ceiling_gap + 0.5), "Expected more headroom below the dip than above the baseline")


def test_hold_keeps_bottom_expanded_but_allows_top_to_shrink():
    ui = _new_zoom_ui()

    ui._update_range()

    _assert(ui.range_v_min <= 4.8, "Expected bottom range hold to avoid raising the expanded dip floor")
    _assert(ui.range_v_max < 16.0, "Expected top range to shrink toward the visible trace while hold is active")


def test_single_channel_range_matches_all_mode_framing():
    ui_all = _new_zoom_ui("ALL")
    all_lo, all_hi = ui_all._calc_target_range()

    ui_blue = _new_zoom_ui("BLUE")
    blue_lo, blue_hi = ui_blue._calc_target_range()

    ui_yellow = _new_zoom_ui("YELLOW")
    yellow_lo, yellow_hi = ui_yellow._calc_target_range()

    _assert(abs(blue_lo - all_lo) < 0.000001 and abs(blue_hi - all_hi) < 0.000001, "Expected BLUE single-channel framing to match ALL mode")
    _assert(abs(yellow_lo - all_lo) < 0.000001 and abs(yellow_hi - all_hi) < 0.000001, "Expected YELLOW single-channel framing to match ALL mode")


def run_all():
    tests = (
        test_calc_target_range_biases_headroom_below_dip,
        test_hold_keeps_bottom_expanded_but_allows_top_to_shrink,
        test_single_channel_range_matches_all_mode_framing,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("OLED zoom floor guard tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

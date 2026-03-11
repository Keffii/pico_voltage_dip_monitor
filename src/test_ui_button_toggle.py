# test_ui_button_toggle.py

import sys
import types


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def _install_host_stubs():
    if "machine" not in sys.modules:
        machine = types.ModuleType("machine")

        class _Pin:
            IN = 0
            OUT = 1
            PULL_UP = 2
            PULL_DOWN = 3

            def __init__(self, *_args, **_kwargs):
                self._v = 1

            def value(self, *args):
                if args:
                    self._v = args[0]
                return self._v

        class _SPI:
            def __init__(self, *_args, **_kwargs):
                pass

            def write(self, *_args, **_kwargs):
                return 0

        class _ADC:
            def __init__(self, *_args, **_kwargs):
                pass

            def read_u16(self):
                return 0

        machine.ADC = _ADC
        machine.Pin = _Pin
        machine.SPI = _SPI
        sys.modules["machine"] = machine

    if "lib.drivers.ssd1351.ssd1351" not in sys.modules:
        lib_mod = sys.modules.get("lib")
        if lib_mod is None:
            lib_mod = types.ModuleType("lib")
            sys.modules["lib"] = lib_mod
        if not hasattr(lib_mod, "__path__"):
            lib_mod.__path__ = []

        drivers_mod = sys.modules.get("lib.drivers")
        if drivers_mod is None:
            drivers_mod = types.ModuleType("lib.drivers")
            sys.modules["lib.drivers"] = drivers_mod
        if not hasattr(drivers_mod, "__path__"):
            drivers_mod.__path__ = []

        ssd_pkg_mod = sys.modules.get("lib.drivers.ssd1351")
        if ssd_pkg_mod is None:
            ssd_pkg_mod = types.ModuleType("lib.drivers.ssd1351")
            sys.modules["lib.drivers.ssd1351"] = ssd_pkg_mod
        if not hasattr(ssd_pkg_mod, "__path__"):
            ssd_pkg_mod.__path__ = []

        ssd_mod = types.ModuleType("lib.drivers.ssd1351.ssd1351")

        class _SSD1351:
            @staticmethod
            def rgb(r, g, b):
                return ((r & 0xE0) << 8) | ((g & 0xFC) << 3) | (b >> 3)

            def __init__(self, *_args, **_kwargs):
                pass

            def fill(self, *_args, **_kwargs):
                return None

            def show(self, *_args, **_kwargs):
                return None

        ssd_mod.SSD1351 = _SSD1351
        sys.modules["lib.drivers.ssd1351.ssd1351"] = ssd_mod
        lib_mod.drivers = drivers_mod
        drivers_mod.ssd1351 = ssd_pkg_mod
        ssd_pkg_mod.ssd1351 = ssd_mod


def _load_oled_ui():
    try:
        import oled_ui as module
        return module
    except Exception:
        _install_host_stubs()
        if "oled_ui" in sys.modules:
            del sys.modules["oled_ui"]
        import oled_ui as module
        return module


oled_ui = _load_oled_ui()
OledUI = oled_ui.OledUI


class _FakePin:
    def __init__(self, value=1):
        self._value = value

    def value(self):
        return self._value

    def set(self, value):
        self._value = value


class _FakeClock:
    def __init__(self):
        self.now_ms = 0

    def ticks_ms(self):
        return self.now_ms

    def ticks_diff(self, a, b):
        return a - b

    def advance(self, delta_ms):
        self.now_ms += int(delta_ms)


class _FakeOled:
    def fill(self, *_args, **_kwargs):
        return None


def _with_fake_time(fn):
    clock = _FakeClock()
    original_time = oled_ui.time
    oled_ui.time = clock
    try:
        fn(clock)
    finally:
        oled_ui.time = original_time


def _new_ui(clock, start_mode="GRAPH", initial_val=1):
    ui = OledUI.__new__(OledUI)
    ui._btn_pin = _FakePin(initial_val)
    ui._btn_active_low = True
    ui._btn_debounce_ms = 80
    ui._btn_raw_val = initial_val
    ui._btn_debounced_val = initial_val
    ui._btn_last_change_ms = clock.now_ms
    ui._btn_pressed = False
    ui.view_mode = start_mode
    ui._stats_dirty = False
    ui._force_graph_redraw = False
    return ui


def _debounced_transition(ui, clock, raw_val):
    ui._btn_pin.set(raw_val)
    ui._poll_toggle_button()
    clock.advance(ui._btn_debounce_ms)
    ui._poll_toggle_button()


def test_toggle_on_first_press_edge():
    def _run(clock):
        ui = _new_ui(clock, start_mode="GRAPH")
        _debounced_transition(ui, clock, 0)
        _assert(ui.view_mode == "STATS", "Toggle should switch to STATS on first debounced press edge")

    _with_fake_time(_run)


def test_hold_does_not_retoggle():
    def _run(clock):
        ui = _new_ui(clock, start_mode="GRAPH")
        _debounced_transition(ui, clock, 0)
        _assert(ui.view_mode == "STATS", "Initial press should switch to STATS")

        for _ in range(3):
            clock.advance(ui._btn_debounce_ms)
            ui._poll_toggle_button()

        _assert(ui.view_mode == "STATS", "Holding button should not retrigger toggles")

    _with_fake_time(_run)


def test_release_rearms_next_press():
    def _run(clock):
        ui = _new_ui(clock, start_mode="GRAPH")
        _debounced_transition(ui, clock, 0)
        _assert(ui.view_mode == "STATS", "First press should switch to STATS")

        _debounced_transition(ui, clock, 1)
        _assert(ui.view_mode == "STATS", "Release should not change current mode")

        _debounced_transition(ui, clock, 0)
        _assert(ui.view_mode == "GRAPH", "Second press after release should switch back to GRAPH")

    _with_fake_time(_run)


def test_toggle_sets_correct_redraw_flags():
    def _run(clock):
        ui = _new_ui(clock, start_mode="GRAPH")

        _debounced_transition(ui, clock, 0)
        _assert(ui.view_mode == "STATS", "Press should switch to STATS")
        _assert(ui._stats_dirty is True, "Entering STATS should mark stats dirty")
        _assert(ui._force_graph_redraw is False, "Entering STATS should not force graph redraw")

        ui._stats_dirty = False
        ui._force_graph_redraw = False

        _debounced_transition(ui, clock, 1)
        _debounced_transition(ui, clock, 0)
        _assert(ui.view_mode == "GRAPH", "Next press should switch back to GRAPH")
        _assert(ui._force_graph_redraw is True, "Entering GRAPH should force graph redraw")
        _assert(ui._stats_dirty is False, "Entering GRAPH should not mark stats dirty")

    _with_fake_time(_run)


def test_stats_view_filters_events_to_selected_channel():
    ui = OledUI.__new__(OledUI)
    ui.oled = _FakeOled()
    ui.stats_max_events = 1
    ui.stats_double_height = False
    ui.stats_bold = False
    ui.graph_channel_filter = "BLUE"
    ui.colors = {"BLUE": 1, "YELLOW": 2, "GREEN": 3}
    ui.dip_events = [{
        "channel": "YELLOW",
        "baseline": 12.0,
        "drop": -1.5,
        "pct": 12.5,
        "active": False,
    }]

    draws = []
    ui._draw_stats_text = lambda x, y, text, color: draws.append((x, y, text, color))
    ui._draw_stats()

    _assert(len(draws) >= 1, "Expected stats renderer to draw at least one row")
    _assert(draws[0][2] == "--.-V --.-V ---%", "Filtered stats view should hide hidden-channel events")


def test_stats_view_keeps_all_channel_events_in_all_mode():
    ui = OledUI.__new__(OledUI)
    ui.oled = _FakeOled()
    ui.stats_max_events = 1
    ui.stats_double_height = False
    ui.stats_bold = False
    ui.graph_channel_filter = "ALL"
    ui.colors = {"BLUE": 1, "YELLOW": 2, "GREEN": 3}
    ui.dip_events = [{
        "channel": "YELLOW",
        "baseline": 12.0,
        "drop": -1.5,
        "pct": 12.5,
        "active": False,
    }]

    draws = []
    ui._draw_stats_text = lambda x, y, text, color: draws.append((x, y, text, color))
    ui._draw_stats()

    _assert(len(draws) >= 3, "Expected stats renderer to draw an event row in ALL mode")
    _assert(draws[0][2] == "12.0V", "ALL mode should still render cross-channel event baseline text")


def test_stats_blink_considers_only_visible_active_events():
    def _run(clock):
        ui = OledUI.__new__(OledUI)
        ui.graph_channel_filter = "BLUE"
        ui.stats_active_blink_enabled = True
        ui.stats_active_blink_ms = 500
        ui._stats_blink_visible = True
        ui._stats_dirty = False
        ui.dip_events = [{"channel": "YELLOW", "active": True}]

        clock.now_ms = 600  # 600//500 = 1 => hidden phase
        ui._update_stats_blink_state()

        _assert(ui._stats_blink_visible is True, "Blink state should ignore hidden-channel active events")
        _assert(ui._stats_dirty is False, "Hidden-channel activity should not dirty the visible stats view")

    _with_fake_time(_run)

def run_all():
    tests = (
        test_toggle_on_first_press_edge,
        test_hold_does_not_retoggle,
        test_release_rearms_next_press,
        test_toggle_sets_correct_redraw_flags,
        test_stats_view_filters_events_to_selected_channel,
        test_stats_view_keeps_all_channel_events_in_all_mode,
        test_stats_blink_considers_only_visible_active_events,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("UI toggle button tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

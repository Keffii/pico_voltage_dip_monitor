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
BLACK = oled_ui.BLACK


class _FakeOled:
    def __init__(self):
        self.text_calls = []
        self.fill_rect_calls = []
        self.scroll_calls = []
        self.vline_calls = []
        self.pixel_calls = []
        self.line_calls = []

    def fill_rect(self, x, y, w, h, color):
        self.fill_rect_calls.append((x, y, w, h, color))

    def text(self, txt, x, y, color):
        self.text_calls.append((txt, x, y, color))

    def scroll(self, dx, dy):
        self.scroll_calls.append((dx, dy))

    def vline(self, x, y, h, color):
        self.vline_calls.append((x, y, h, color))

    def pixel(self, x, y, color):
        self.pixel_calls.append((x, y, color))

    def line(self, x0, y0, x1, y1, color):
        self.line_calls.append((x0, y0, x1, y1, color))


def _new_graph_readout_ui():
    ui = OledUI.__new__(OledUI)
    ui.oled = _FakeOled()
    ui.graph_readouts_enabled = True
    ui.graph_readout_decimals = 1
    ui.graph_readout_show_units = False
    ui.graph_readout_top_mode = "RANGE_MAX"
    ui.graph_channel_filter = "GREEN"
    ui.colors = {"BLUE": 1, "YELLOW": 2, "GREEN": 3}
    ui.range_v_max = 12.0
    ui.range_v_min = 5.4
    ui.PLOT_H = 96
    ui.PLOT_W = 128
    return ui


def _new_single_channel_scroll_ui():
    ui = OledUI.__new__(OledUI)
    ui.oled = _FakeOled()
    ui.graph_channel_filter = "BLUE"
    ui.colors = {"BLUE": 1, "YELLOW": 2, "GREEN": 3}
    ui.prev_y = {"BLUE": 10, "YELLOW": 20, "GREEN": 30}
    ui.PLOT_H = 96
    ui.PLOT_W = 128
    ui._v_to_y = lambda value: int(value)
    return ui


def test_single_channel_top_readout_uses_range_max_when_configured():
    ui = _new_graph_readout_ui()

    ui._draw_graph_readouts({"GREEN": 7.2})

    _assert(ui.oled.text_calls[0][0] == "12.0", "Expected top-left readout to stay at graph range max instead of live dipped value")
    _assert(ui.oled.fill_rect_calls[0][4] == BLACK, "Expected readout background to be cleared before redraw")



def test_scroll_draw_only_renders_selected_channel_in_single_channel_mode():
    ui = _new_single_channel_scroll_ui()

    ui._scroll_left_and_draw_right({"BLUE": 11, "YELLOW": 21, "GREEN": 31})

    _assert(len(ui.oled.line_calls) == 1, "Expected only one trace segment when a single channel view is selected")
    _assert(ui.oled.line_calls[0][4] == ui.colors["BLUE"], "Expected only the selected BLUE channel to be drawn")
    _assert(ui.prev_y["BLUE"] == 11, "Expected BLUE previous y to update from the new sample")
    _assert(ui.prev_y["YELLOW"] == 20, "Expected YELLOW previous y to remain unchanged in BLUE-only view")
    _assert(ui.prev_y["GREEN"] == 30, "Expected GREEN previous y to remain unchanged in BLUE-only view")



def run_all():
    tests = (
        test_single_channel_top_readout_uses_range_max_when_configured,
        test_scroll_draw_only_renders_selected_channel_in_single_channel_mode,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("OLED graph readout tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

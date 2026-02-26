# test_display_only_contract.py

import config
import sys

if "machine" not in sys.modules:
    try:
        import types
        machine = types.ModuleType("machine")

        class _ADC:
            def __init__(self, *_args, **_kwargs):
                pass

            def read_u16(self):
                return 0

        class _Pin:
            OUT = 1

            def __init__(self, *_args, **_kwargs):
                pass

            def value(self, *_args, **_kwargs):
                return 0

        class _SPI:
            def __init__(self, *_args, **_kwargs):
                pass

            def write(self, *_args, **_kwargs):
                return 0

        machine.ADC = _ADC
        machine.Pin = _Pin
        machine.SPI = _SPI
        sys.modules["machine"] = machine
    except Exception:
        pass


def _load_main_for_contract_tests():
    original_enable_oled = getattr(config, "ENABLE_OLED", False)
    try:
        config.ENABLE_OLED = False
        if "main" in sys.modules:
            del sys.modules["main"]
        import main as main_module
        return main_module
    finally:
        config.ENABLE_OLED = original_enable_oled


main = _load_main_for_contract_tests()


class _DummyStats:
    def __init__(self):
        self.dips = 0
        self.flash_writes = 0

    def record_dip(self, _channel_name):
        self.dips += 1

    def record_flash_write(self, lines_written=1):
        self.flash_writes += lines_written


class _DummyUI:
    def __init__(self):
        self.latched = []
        self.events = []
        self.sample_counter = 0
        self.source_off_states = []
        self.canceled_events = []

    def latch_dip_drop_adc(self, channel, drop_v):
        self.latched.append((channel, drop_v))

    def record_dip_event_adc(self, channel, baseline_v, min_v, drop_v, event_id=None, active=False, sample_index=None):
        self.events.append((channel, baseline_v, min_v, drop_v, event_id, active, sample_index))

    def set_source_off_state(self, active):
        self.source_off_states.append(bool(active))

    def cancel_dip_event(self, event_id):
        self.canceled_events.append(event_id)


class _DummyMedLog:
    def __init__(self):
        self.buffer = []

    def add(self, t_s, channel_name, median_v):
        self.buffer.append((t_s, channel_name, median_v))

    def flush_to_file(self, _append_lines_fn):
        count = len(self.buffer)
        self.buffer = []
        return count


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def test_display_only_mode_is_valid():
    original_mode = config.LOGGING_MODE
    try:
        config.LOGGING_MODE = "DISPLAY_ONLY"
        config.validate_config()
    finally:
        config.LOGGING_MODE = original_mode


def test_display_only_disables_usb_and_file_writes():
    calls = {"usb": 0, "flash": 0}
    original_usb = main.usb_stream_dip
    original_append = main.append_line
    try:
        def _fake_usb(*_args, **_kwargs):
            calls["usb"] += 1

        def _fake_append(*_args, **_kwargs):
            calls["flash"] += 1
            return True

        main.usb_stream_dip = _fake_usb
        main.append_line = _fake_append

        stats = _DummyStats()
        ui = _DummyUI()
        handlers = main._LoopHandlers(stats, None, "DISPLAY_ONLY", ui, {})
        handlers.current_channel = "BLUE"

        dip_line = "BLUE,1.000,1.040,40,1.230,0.980,0.250\n"
        handlers.dip_append("/pico_dips.csv", dip_line)
        handlers.dip_callback("DIP END BLUE")

        _assert(calls["usb"] == 0, "DISPLAY_ONLY must not emit USB dip lines")
        _assert(calls["flash"] == 0, "DISPLAY_ONLY must not append dip lines to flash")
        _assert(handlers.allow_runtime_prints is False, "DISPLAY_ONLY must disable runtime periodic prints")
        _assert(len(ui.events) == 1, "DISPLAY_ONLY should still update UI dip events")
        _assert(stats.dips == 1, "DISPLAY_ONLY should still track dip statistics")
    finally:
        main.usb_stream_dip = original_usb
        main.append_line = original_append


def test_mode_matrix_validation_and_policy_flags():
    original_mode = config.LOGGING_MODE
    try:
        modes = ("USB_STREAM", "EVENT_ONLY", "FULL_LOCAL", "DISPLAY_ONLY")
        for mode in modes:
            config.LOGGING_MODE = mode
            config.validate_config()

            handlers = main._LoopHandlers(_DummyStats(), None, mode, None, {})
            expected_usb = (mode == "USB_STREAM")
            expected_file = (mode != "DISPLAY_ONLY")
            expected_prints = (mode != "DISPLAY_ONLY")

            _assert(handlers.allow_usb_stream == expected_usb, "Unexpected USB policy for mode {}".format(mode))
            _assert(handlers.allow_file_io == expected_file, "Unexpected file policy for mode {}".format(mode))
            _assert(handlers.allow_runtime_prints == expected_prints, "Unexpected print policy for mode {}".format(mode))
    finally:
        config.LOGGING_MODE = original_mode


def test_core1_event_queue_ring_behavior():
    queue = main._Core1EventQueue(32)
    for idx in range(32):
        _assert(queue.push(idx + 1, idx), "Queue push failed at {}".format(idx))
    _assert(queue.push(999, 0) is False, "Queue should reject push when full")

    first = queue.pop()
    _assert(first is not None, "Queue pop should return an event")
    _assert(first[0] == 1 and first[1] == 0, "Queue pop order mismatch")

    _count, _hwm, dropped = queue.stats()
    _assert(dropped == 1, "Queue dropped counter mismatch")


def test_core1_bridge_display_only_filters_io():
    stats = _DummyStats()
    bridge = main._Core1Bridge(
        stats=stats,
        logging_mode="DISPLAY_ONLY",
        ui_ref=None,
        medlog=_DummyMedLog(),
        perf_rt=None,
        perf_io=None,
    )
    _assert(bridge.queue_usb_median(1.0, "BLUE", 1.2) is True, "DISPLAY_ONLY usb median queue should no-op")
    _assert(
        bridge.queue_usb_dip("BLUE", 1.0, 1.1, 100, 1.2, 1.0, 0.2) is True,
        "DISPLAY_ONLY usb dip queue should no-op"
    )
    _assert(bridge.queue_usb_baseline(1.0, "BLUE", 1.2) is True, "DISPLAY_ONLY usb baseline queue should no-op")
    _assert(bridge.queue_file_append("/tmp.csv", "x\n") is True, "DISPLAY_ONLY file queue should no-op")
    _assert(bridge.queue_median_add(1.0, "BLUE", 1.2) is True, "DISPLAY_ONLY median add queue should no-op")

    depth, _hwm, dropped = bridge.queue_stats()
    _assert(depth == 0, "DISPLAY_ONLY should not enqueue runtime USB/file events")
    _assert(dropped == 0, "DISPLAY_ONLY no-op operations should not drop events")


def test_strict_core1_no_core0_ui_fallback():
    class _RejectUiBridge:
        def queue_ui_dip_latch(self, *_args, **_kwargs):
            return False

        def queue_ui_dip_event(self, *_args, **_kwargs):
            return False

        def queue_ui_source_off_state(self, *_args, **_kwargs):
            return False

        def queue_ui_cancel_event(self, *_args, **_kwargs):
            return False

    original_strict = getattr(config, "UI_CORE1_STRICT", True)
    try:
        config.UI_CORE1_STRICT = True
        stats = _DummyStats()
        ui = _DummyUI()
        handlers = main._LoopHandlers(
            stats=stats,
            perf=None,
            logging_mode="DISPLAY_ONLY",
            ui_ref=ui,
            ui_event_map={},
            core1_bridge=_RejectUiBridge(),
        )
        handlers.current_channel = "BLUE"
        handlers.dip_append("/pico_dips.csv", "BLUE,1.000,1.040,40,1.230,0.980,0.250\n")
        _assert(len(ui.latched) == 0, "Strict Core1 mode must not fallback to Core0 UI latch writes")
        _assert(len(ui.events) == 0, "Strict Core1 mode must not fallback to Core0 UI event writes")
    finally:
        config.UI_CORE1_STRICT = original_strict


def test_strict_core1_headless_behavior_when_no_bridge():
    original_strict = getattr(config, "UI_CORE1_STRICT", True)
    try:
        config.UI_CORE1_STRICT = True
        ui = _DummyUI()
        handlers = main._LoopHandlers(
            stats=_DummyStats(),
            perf=None,
            logging_mode="DISPLAY_ONLY",
            ui_ref=ui,
            ui_event_map={},
            core1_bridge=None,
        )
        _assert(handlers.ui is None, "Strict Core1 mode should run headless when no Core1 bridge is available")
        handlers.dip_append("/pico_dips.csv", "BLUE,1.000,1.040,40,1.230,0.980,0.250\n")
        _assert(len(ui.latched) == 0 and len(ui.events) == 0, "Headless strict mode should not write UI events")
    finally:
        config.UI_CORE1_STRICT = original_strict


def test_ui_source_off_and_cancel_event_direct_paths():
    ui = _DummyUI()
    handlers = main._LoopHandlers(
        stats=_DummyStats(),
        perf=None,
        logging_mode="EVENT_ONLY",
        ui_ref=ui,
        ui_event_map={},
        core1_bridge=None,
    )

    _assert(handlers.set_ui_source_off_state(True) is True, "Expected source-off direct path to succeed")
    _assert(handlers.set_ui_source_off_state(False) is True, "Expected source-on direct path to succeed")
    _assert(ui.source_off_states == [True, False], "Source-off state updates should reach UI in direct mode")

    _assert(handlers.cancel_ui_dip_event(42) is True, "Expected direct UI cancel path to succeed")
    _assert(ui.canceled_events == [42], "Canceled event id should be forwarded to UI")


def test_ui_cancel_event_strict_core1_does_not_fallback():
    class _RejectUiBridge:
        def queue_ui_cancel_event(self, *_args, **_kwargs):
            return False

    original_strict = getattr(config, "UI_CORE1_STRICT", True)
    try:
        config.UI_CORE1_STRICT = True
        ui = _DummyUI()
        handlers = main._LoopHandlers(
            stats=_DummyStats(),
            perf=None,
            logging_mode="EVENT_ONLY",
            ui_ref=ui,
            ui_event_map={},
            core1_bridge=_RejectUiBridge(),
        )
        ok = handlers.cancel_ui_dip_event(7)
        _assert(ok is False, "Strict Core1 mode should report failure when cancel event enqueue fails")
        _assert(len(ui.canceled_events) == 0, "Strict Core1 mode must not fallback cancel writes to Core0 UI")
    finally:
        config.UI_CORE1_STRICT = original_strict


def run_all():
    tests = (
        test_display_only_mode_is_valid,
        test_display_only_disables_usb_and_file_writes,
        test_mode_matrix_validation_and_policy_flags,
        test_core1_event_queue_ring_behavior,
        test_core1_bridge_display_only_filters_io,
        test_strict_core1_no_core0_ui_fallback,
        test_strict_core1_headless_behavior_when_no_bridge,
        test_ui_source_off_and_cancel_event_direct_paths,
        test_ui_cancel_event_strict_core1_does_not_fallback,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("Display-only contract tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

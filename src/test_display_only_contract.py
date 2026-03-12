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
            IN = 0
            OUT = 1
            PULL_UP = 2
            PULL_DOWN = 3

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


def _load_oled_ui_for_contract_tests():
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

            def fill_rect(self, *_args, **_kwargs):
                return None

            def show(self, *_args, **_kwargs):
                return None

            def show_rect(self, *_args, **_kwargs):
                return None

            def pixel(self, *_args, **_kwargs):
                return None

            def line(self, *_args, **_kwargs):
                return None

            def hline(self, *_args, **_kwargs):
                return None

            def vline(self, *_args, **_kwargs):
                return None

            def text(self, *_args, **_kwargs):
                return None

            def scroll(self, *_args, **_kwargs):
                return None

            def set_runtime_diagnostics(self, *_args, **_kwargs):
                return None

        ssd_mod.SSD1351 = _SSD1351
        sys.modules["lib.drivers.ssd1351.ssd1351"] = ssd_mod
        lib_mod.drivers = drivers_mod
        drivers_mod.ssd1351 = ssd_pkg_mod
        ssd_pkg_mod.ssd1351 = ssd_mod

    if "oled_ui" in sys.modules:
        del sys.modules["oled_ui"]
    import oled_ui as oled_ui_module
    if not hasattr(oled_ui_module.time, "ticks_ms"):
        import time as _host_time
        oled_ui_module.time.ticks_ms = lambda: int(_host_time.time() * 1000)
        oled_ui_module.time.ticks_diff = lambda a, b: a - b
        oled_ui_module.time.ticks_add = lambda a, b: a + b
        oled_ui_module.time.sleep_ms = lambda _ms: None
    return oled_ui_module


def _configure_oled_bootstrap_test_mode(ui, bootstrap_frames=2):
    if bootstrap_frames < 2:
        bootstrap_frames = 2
    ui._btn_pin = None
    ui._ch_btn_pin = None
    ui.view_mode = "GRAPH"
    ui.graph_channel_filter = "ALL"
    ui._force_graph_redraw = False
    ui.auto_zoom = True
    ui.bootstrap_enable = True
    ui.bootstrap_frames = int(bootstrap_frames)
    ui.bootstrap_view = "CALIBRATE"
    ui.bootstrap_pctl_low = 5.0
    ui.bootstrap_pctl_high = 95.0
    ui.bootstrap_skip_startup_lock = True
    ui.graph_startup_hold_ms = 0
    ui.graph_startup_anchor_v = None
    ui._range_calibration_start_ms = ui.start_ms
    ui.auto_range_update_every = 1
    ui.auto_range_alpha = 1.0
    ui.auto_range_max_step_v = ui.V_MAX - ui.V_MIN
    ui.auto_zoomout_hold_samples = 0
    ui.auto_zoomout_hold_until_sample = -1
    ui.auto_zoomin_cooldown_samples = 0
    ui.auto_zoomin_cooldown_until_sample = -1
    ui.sample_counter = -1
    ui.frame_count = 0
    ui.graph_full = False
    ui.x = 0
    ui.prev_y = {"BLUE": None, "YELLOW": None, "GREEN": None}
    ui.v_hist = {"BLUE": [], "YELLOW": [], "GREEN": []}
    ui._bootstrap_active = True
    ui._bootstrap_count = 0
    ui._bootstrap_done_range = None
    ui._bootstrap_samples = {
        "BLUE": [0.0] * ui.bootstrap_frames,
        "YELLOW": [0.0] * ui.bootstrap_frames,
        "GREEN": [0.0] * ui.bootstrap_frames,
    }


def _attach_oled_draw_counters(ui):
    counters = {"redraw": 0, "incremental": 0}
    original_redraw = ui._redraw_plot_from_hist
    original_incremental = ui._draw_incremental

    def _counted_redraw():
        counters["redraw"] += 1
        return original_redraw()

    def _counted_incremental(vals_real):
        counters["incremental"] += 1
        return original_incremental(vals_real)

    ui._redraw_plot_from_hist = _counted_redraw
    ui._draw_incremental = _counted_incremental
    return counters


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



def test_ui_frame_scheduler_emits_frames_between_median_blocks():
    scheduler = main._UiFrameScheduler(require_all_channels=False, default_adc_v=0.0, frame_interval_ms=10)
    scheduler.update_latest("BLUE", 1.0)
    scheduler.update_latest("YELLOW", 1.1)
    scheduler.update_latest("GREEN", 0.9)

    _assert(scheduler.maybe_get_plot_values(0) == (1.0, 1.1, 0.9), "Expected initial frame to render immediately")
    _assert(scheduler.maybe_get_plot_values(5) is None, "Frame interval should suppress mid-interval redraw")
    _assert(scheduler.maybe_get_plot_values(10) == (1.0, 1.1, 0.9), "Expected cached values to render on next frame boundary")


def test_ui_frame_scheduler_uses_cached_or_default_values():
    scheduler = main._UiFrameScheduler(require_all_channels=False, default_adc_v=0.25, frame_interval_ms=10)
    scheduler.update_latest("BLUE", 1.0)

    _assert(
        scheduler.maybe_get_plot_values(0) == (1.0, 0.25, 0.25),
        "Missing channels should use default ADC values until cached"
    )

    scheduler.update_latest("YELLOW", 1.1)
    _assert(scheduler.maybe_get_plot_values(9) is None, "Frame interval should still apply after cache updates")
    _assert(
        scheduler.maybe_get_plot_values(10) == (1.0, 1.1, 0.25),
        "Cached channels should override defaults on later frames"
    )


def test_ui_frame_scheduler_require_all_channels_waits_for_full_set():
    scheduler = main._UiFrameScheduler(require_all_channels=True, default_adc_v=0.0, frame_interval_ms=10)
    scheduler.update_latest("BLUE", 1.0)
    scheduler.update_latest("YELLOW", 1.1)

    _assert(scheduler.maybe_get_plot_values(0) is None, "Require-all mode should wait for all channels")

    scheduler.update_latest("GREEN", 0.9)
    _assert(
        scheduler.maybe_get_plot_values(0) == (1.0, 1.1, 0.9),
        "Require-all mode should render once all channels are cached"
    )


def test_ui_fast_refresh_policy_runs_whenever_ui_exists():
    class _BootstrapUi:
        _bootstrap_active = True

    class _IdleUi:
        _bootstrap_active = False

    _assert(main._ui_should_refresh_between_medians(_BootstrapUi()) is True, "Bootstrap UI should opt into between-median refresh")
    _assert(main._ui_should_refresh_between_medians(_IdleUi()) is True, "Live graph UI should keep between-median refresh enabled")
    _assert(main._ui_should_refresh_between_medians(object()) is True, "Any active UI should opt into between-median refresh")
    _assert(main._ui_should_refresh_between_medians(None) is False, "Missing UI should disable between-median refresh")





def test_display_signal_filter_rejects_single_sample_spike():
    filt = main._DisplaySignalFilter(window_size=5, ema_alpha=0.5)
    outputs = [filt.update(v) for v in (1.0, 1.0, 1.0, 4.0, 1.0, 1.0)]
    _assert(outputs[-1] < 1.5, "Display filter should reject a brief spike instead of following it")


def test_display_signal_filter_tracks_sustained_change():
    filt = main._DisplaySignalFilter(window_size=3, ema_alpha=0.5)
    for _ in range(4):
        filt.update(1.0)
    out = None
    for _ in range(6):
        out = filt.update(2.0)
    _assert(out is not None and out > 1.7, "Display filter should follow sustained signal changes")
    _assert(out <= 2.0, "Display filter should stay within input bounds")

def test_ui_runtime_diagnostics_tracks_redraw_flush_and_input_metrics():
    diag = main._UiRuntimeDiagnostics(enabled=True)

    diag.record_input_poll(100)
    diag.record_input_poll(107)
    diag.record_input_poll(119)
    diag.record_full_redraw()
    diag.record_partial_redraw(region_count=3)
    diag.record_full_flush(4200)
    diag.record_partial_flush(700, rect_count=2)

    snapshot = diag.snapshot()
    _assert(snapshot["input_poll_count"] == 3, "Expected input poll count to be tracked")
    _assert(snapshot["input_poll_gap_max_ms"] == 12, "Expected max input poll gap to track widest interval")
    _assert(snapshot["full_redraw_count"] == 1, "Expected full redraw count to increment")
    _assert(snapshot["partial_redraw_count"] == 1, "Expected partial redraw count to increment")
    _assert(snapshot["partial_redraw_regions"] == 3, "Expected partial redraw region count to accumulate")
    _assert(snapshot["full_flush_count"] == 1, "Expected full flush count to increment")
    _assert(snapshot["partial_flush_count"] == 1, "Expected partial flush count to increment")
    _assert(snapshot["full_flush_max_us"] == 4200, "Expected full flush max time to be tracked")
    _assert(snapshot["partial_flush_max_us"] == 700, "Expected partial flush max time to be tracked")
    _assert(snapshot["partial_flush_rects"] == 2, "Expected partial flush rectangle count to accumulate")


def test_ui_runtime_diagnostics_is_quiet_when_disabled():
    diag = main._UiRuntimeDiagnostics(enabled=False)

    diag.record_input_poll(100)
    diag.record_input_poll(150)
    diag.record_full_redraw()
    diag.record_partial_redraw(region_count=5)
    diag.record_full_flush(9999)
    diag.record_partial_flush(8888, rect_count=4)

    snapshot = diag.snapshot()
    _assert(snapshot["input_poll_count"] == 0, "Disabled diagnostics should ignore input polls")
    _assert(snapshot["input_poll_gap_max_ms"] == 0, "Disabled diagnostics should not track poll gaps")
    _assert(snapshot["full_redraw_count"] == 0, "Disabled diagnostics should not count redraws")
    _assert(snapshot["partial_redraw_regions"] == 0, "Disabled diagnostics should not accumulate redraw regions")
    _assert(snapshot["full_flush_max_us"] == 0, "Disabled diagnostics should not track flush timings")
    _assert(snapshot["partial_flush_rects"] == 0, "Disabled diagnostics should not accumulate flush rectangles")






def test_ui_runtime_diagnostics_tracks_queue_depth_and_frame_metrics():
    diag = main._UiRuntimeDiagnostics(enabled=True)

    diag.record_queue_depth(1)
    diag.record_queue_depth(4)
    diag.record_ui_frame(1800)
    diag.record_ui_frame(900, fallback=True)
    diag.record_ui_skip()

    snapshot = diag.snapshot()
    _assert(snapshot["queue_depth_max"] == 4, "Expected queue depth high-water mark to be tracked")
    _assert(snapshot["ui_frame_count"] == 2, "Expected rendered UI frame count to be tracked")
    _assert(snapshot["ui_frame_total_us"] == 2700, "Expected rendered UI frame total time to accumulate")
    _assert(snapshot["ui_frame_max_us"] == 1800, "Expected rendered UI frame max time to be tracked")
    _assert(snapshot["ui_fallback_count"] == 1, "Expected fallback UI frame count to be tracked")
    _assert(snapshot["ui_skipped_count"] == 1, "Expected skipped UI frame count to be tracked")



def test_format_ui_runtime_summary_includes_key_metrics():
    diag = main._UiRuntimeDiagnostics(enabled=True)
    diag.record_input_poll(100)
    diag.record_input_poll(109)
    diag.record_queue_depth(3)
    diag.record_ui_frame(1400, fallback=True)
    diag.record_ui_skip()

    summary = main._format_ui_runtime_summary(12.5, diag.snapshot())
    _assert(summary.startswith('  12.5s  UIRT  '), "Expected summary line to use stable prefix")
    _assert('qmax=3' in summary, "Expected queue depth max in summary line")
    _assert('frame=1' in summary, "Expected UI frame count in summary line")
    _assert('skip=1' in summary, "Expected skipped frame count in summary line")
    _assert('fallback=1' in summary, "Expected fallback frame count in summary line")
    _assert('poll_gap_max_ms=9' in summary, "Expected input poll gap in summary line")



def test_ui_runtime_reporting_config_validation_and_disabled_summary():
    original_enabled = getattr(config, 'UI_RUNTIME_REPORT_ENABLED', False)
    original_interval = getattr(config, 'UI_RUNTIME_REPORT_INTERVAL_MS', 1000)
    original_baudrate = getattr(config, 'OLED_SPI_BAUDRATE', 10_000_000)
    try:
        config.UI_RUNTIME_REPORT_ENABLED = 'bad'
        config.UI_RUNTIME_REPORT_INTERVAL_MS = 10
        config.OLED_SPI_BAUDRATE = 500_000
        try:
            config.validate_config()
            raise AssertionError('Expected invalid UI runtime reporting config to fail validation')
        except ValueError as exc:
            msg = str(exc)
            _assert('UI_RUNTIME_REPORT_ENABLED must be boolean-like' in msg, 'Expected runtime report enable validation error')
            _assert('UI_RUNTIME_REPORT_INTERVAL_MS must be >= 100' in msg, 'Expected runtime report interval validation error')
            _assert('OLED_SPI_BAUDRATE must be in [1000000, 40000000]' in msg, 'Expected OLED SPI baud validation error')
    finally:
        config.UI_RUNTIME_REPORT_ENABLED = original_enabled
        config.UI_RUNTIME_REPORT_INTERVAL_MS = original_interval
        config.OLED_SPI_BAUDRATE = original_baudrate
        config.validate_config()


def test_emit_ui_runtime_report_bypasses_display_only_print_suppression():
    printed = []

    class _DisplayOnlyCore1:
        allow_runtime_prints = False
        def queue_print(self, _line):
            raise AssertionError('queue_print should not be used when runtime prints are suppressed')

    import builtins
    original_print = builtins.print
    try:
        builtins.print = lambda line: printed.append(line)
        main._emit_ui_runtime_report(_DisplayOnlyCore1(), 'UIRT line')
    finally:
        builtins.print = original_print

    _assert(printed == ['UIRT line'], 'Expected UI runtime report to print directly in DISPLAY_ONLY mode')



def test_emit_ui_runtime_report_prefers_core1_queue_when_available():
    printed = []
    queued = []

    class _QueuedCore1:
        allow_runtime_prints = True
        def queue_print(self, line):
            queued.append(line)
            return True

    import builtins
    original_print = builtins.print
    try:
        builtins.print = lambda line: printed.append(line)
        main._emit_ui_runtime_report(_QueuedCore1(), 'UIRT line')
    finally:
        builtins.print = original_print

    _assert(queued == ['UIRT line'], 'Expected UI runtime report to use Core1 queue when normal runtime prints are allowed')
    _assert(printed == [], 'Expected no direct print when Core1 queue accepts the report')
def test_oled_plot_medians_adc_draws_immediately():
    oled_ui = _load_oled_ui_for_contract_tests()
    ui = oled_ui.OledUI()
    try:
        _configure_oled_bootstrap_test_mode(ui, bootstrap_frames=2)
        for _ in range(ui.bootstrap_frames):
            ui.plot_medians_adc(1.0, 1.1, 0.9)

        counters = _attach_oled_draw_counters(ui)
        calls = {"show": 0}
        original_show = ui.oled.show

        def _counted_show(*_args, **_kwargs):
            calls["show"] += 1
            return original_show(*_args, **_kwargs)

        ui.oled.show = _counted_show
        ui.auto_range_update_every = 1000
        ui.plot_medians_adc(1.0, 1.1, 0.9)

        _assert((counters["redraw"] + counters["incremental"]) == 1, "Expected one draw path for one OLED frame")
        _assert(calls["show"] == 1, "Expected plot_medians_adc to flush immediately")
    finally:
        ui.shutdown()



def test_oled_ui_does_not_expose_deferred_render_api():
    oled_ui = _load_oled_ui_for_contract_tests()
    ui = oled_ui.OledUI()
    try:
        _assert(not hasattr(ui, "ingest_display_sample_adc"), "Stable OLED UI should not expose deferred ingest API")
        _assert(not hasattr(ui, "render_pending_frame"), "Stable OLED UI should not expose deferred render API")
    finally:
        ui.shutdown()


def test_ui_plot_mailbox_keeps_only_latest_frame():
    mailbox = main._UiPlotMailbox()
    _assert(mailbox.offer(1.0, 1.1, 0.9) is True, "First mailbox offer should succeed")
    _assert(mailbox.offer(2.0, 2.1, 1.9) is True, "Second mailbox offer should replace prior frame")
    _assert(mailbox.depth() == 1, "Mailbox should hold at most one pending frame")
    _assert(mailbox.take() == (2.0, 2.1, 1.9), "Mailbox should return the newest pending frame")
    _assert(mailbox.take() is None, "Mailbox should be empty after take")


def test_core1_bridge_queue_depth_counts_pending_ui_plot_mailbox():
    bridge = main._Core1Bridge(
        stats=_DummyStats(),
        logging_mode="DISPLAY_ONLY",
        ui_ref=_DummyUI(),
        medlog=_DummyMedLog(),
        perf_rt=None,
        perf_io=None,
    )
    _assert(bridge.queue_depth() == 0, "Initial bridge queue depth should be zero")
    _assert(bridge.queue_ui_plot(1.0, 1.1, 0.9) is True, "UI plot queue should accept frame")
    _assert(bridge.queue_depth() == 1, "Pending UI plot mailbox should contribute to queue depth")

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
        test_ui_frame_scheduler_emits_frames_between_median_blocks,
        test_ui_frame_scheduler_uses_cached_or_default_values,
        test_ui_frame_scheduler_require_all_channels_waits_for_full_set,
        test_ui_fast_refresh_policy_runs_whenever_ui_exists,
        test_display_signal_filter_rejects_single_sample_spike,
        test_display_signal_filter_tracks_sustained_change,
        test_ui_runtime_diagnostics_tracks_redraw_flush_and_input_metrics,
        test_ui_runtime_diagnostics_is_quiet_when_disabled,
        test_ui_runtime_diagnostics_tracks_queue_depth_and_frame_metrics,
        test_format_ui_runtime_summary_includes_key_metrics,
        test_ui_runtime_reporting_config_validation_and_disabled_summary,
        test_emit_ui_runtime_report_bypasses_display_only_print_suppression,
        test_emit_ui_runtime_report_prefers_core1_queue_when_available,
        test_oled_plot_medians_adc_draws_immediately,
        test_oled_ui_does_not_expose_deferred_render_api,
        test_ui_plot_mailbox_keeps_only_latest_frame,
        test_core1_bridge_queue_depth_counts_pending_ui_plot_mailbox,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("Display-only contract tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()





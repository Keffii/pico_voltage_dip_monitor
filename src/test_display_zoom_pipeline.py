# test_display_zoom_pipeline.py


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def _build_ui_or_skip():
    try:
        from oled_ui import OledUI
        return OledUI()
    except Exception as exc:
        print("SKIP: OLED zoom pipeline tests (init failed: {})".format(exc))
        return None


def _configure_bootstrap_test_mode(ui, bootstrap_frames=8):
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


def _attach_draw_counters(ui):
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


def test_bootstrap_blocks_trace_draw_until_ready():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=8)
        counters = _attach_draw_counters(ui)

        for _ in range(ui.bootstrap_frames - 1):
            ui.plot_medians_adc(1.0, 1.1, 0.9)

        _assert(ui._bootstrap_active is True, "Bootstrap should still be active before final frame")
        _assert(ui._bootstrap_count == (ui.bootstrap_frames - 1), "Unexpected bootstrap sample count before release")
        _assert(counters["redraw"] == 0, "No full redraw expected while bootstrap active")
        _assert(counters["incremental"] == 0, "No trace incremental draw expected while bootstrap active")
    finally:
        ui.shutdown()


def test_bootstrap_sets_initial_range_once():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=10)
        for i in range(ui.bootstrap_frames):
            base = 1.0 + (i * 0.2)
            ui.plot_medians_adc(base, base + 0.4, base - 0.3)

        _assert(ui._bootstrap_active is False, "Bootstrap should be released at configured frame count")
        _assert(ui._bootstrap_done_range is not None, "Bootstrap should store computed initial range")

        lo, hi = ui._bootstrap_done_range
        _assert(abs(ui.range_v_min - lo) < 0.000001, "Bootstrap low range should be applied once at release")
        _assert(abs(ui.range_v_max - hi) < 0.000001, "Bootstrap high range should be applied once at release")

        before = ui._bootstrap_done_range
        ui.plot_medians_adc(2.0, 2.1, 1.9)
        _assert(ui._bootstrap_done_range == before, "Bootstrap final range record should remain stable")
    finally:
        ui.shutdown()


def test_bootstrap_first_draw_is_single_full_redraw():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=6)
        counters = _attach_draw_counters(ui)

        for _ in range(ui.bootstrap_frames):
            ui.plot_medians_adc(1.0, 1.1, 0.9)

        _assert(ui._bootstrap_active is False, "Bootstrap should be inactive after release frame")
        _assert(counters["redraw"] == 1, "Release frame should perform exactly one full redraw")
        _assert(counters["incremental"] == 0, "Release frame should not perform incremental trace draw")
    finally:
        ui.shutdown()


def test_post_bootstrap_auto_zoom_still_operates():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=6)
        for _ in range(ui.bootstrap_frames):
            ui.plot_medians_adc(1.0, 1.1, 0.9)

        initial_hi = ui.range_v_max
        for _ in range(5):
            ui.plot_medians_adc(8.0, 9.0, 7.0)

        _assert(ui.range_v_max > (initial_hi + 0.1), "Auto-zoom should continue updating range after bootstrap")
    finally:
        ui.shutdown()


def test_channel_switch_restarts_bootstrap_and_keeps_history():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=6)
        for _ in range(ui.bootstrap_frames):
            ui.plot_medians_adc(1.0, 1.1, 0.9)

        _assert(ui._bootstrap_active is False, "Bootstrap should be inactive before switch-triggered restart")
        blue_before = len(ui.v_hist["BLUE"])
        yellow_before = len(ui.v_hist["YELLOW"])
        green_before = len(ui.v_hist["GREEN"])

        ui._cycle_channel_filter()  # ALL -> BLUE

        _assert(ui.graph_channel_filter == "BLUE", "Expected channel filter to advance to BLUE")
        _assert(ui._bootstrap_active is True, "Channel switch should restart bootstrap")
        _assert(ui._bootstrap_count == 0, "Switch restart should reset bootstrap sample counter")
        _assert(ui._bootstrap_done_range is None, "Switch restart should clear bootstrap done range")

        for _ in range(3):
            ui.plot_medians_adc(0.33, 1.30, 1.95)

        _assert(len(ui.v_hist["BLUE"]) > blue_before, "BLUE history should be preserved and continue growing")
        _assert(len(ui.v_hist["YELLOW"]) > yellow_before, "YELLOW history should be preserved and continue growing")
        _assert(len(ui.v_hist["GREEN"]) > green_before, "GREEN history should be preserved and continue growing")
    finally:
        ui.shutdown()


def test_channel_switch_bootstrap_uses_visible_channel_scope():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=6)
        for _ in range(ui.bootstrap_frames):
            ui.plot_medians_adc(1.0, 1.1, 0.9)

        ui._cycle_channel_filter()  # ALL -> BLUE
        _assert(ui.graph_channel_filter == "BLUE", "Expected BLUE filter after first cycle")
        _assert(ui._bootstrap_active is True, "Switch should restart bootstrap")

        for i in range(ui.bootstrap_frames):
            blue_adc = 0.33 + (i * 0.005)   # ~6V real domain
            yellow_adc = 1.30 + (i * 0.01)  # ~24V real domain
            green_adc = 1.95 + (i * 0.01)   # ~36V real domain
            ui.plot_medians_adc(blue_adc, yellow_adc, green_adc)

        _assert(ui._bootstrap_active is False, "Bootstrap should complete after configured frames")
        _assert(ui.range_v_max < 15.0, "BLUE-only bootstrap range should ignore hidden high-voltage channels")
    finally:
        ui.shutdown()


def test_consecutive_channel_switches_restart_bootstrap_each_time():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=8)
        for _ in range(ui.bootstrap_frames):
            ui.plot_medians_adc(1.0, 1.1, 0.9)

        ui._cycle_channel_filter()  # ALL -> BLUE
        _assert(ui.graph_channel_filter == "BLUE", "Expected BLUE after first cycle")
        _assert(ui._bootstrap_active is True, "First switch should restart bootstrap")

        ui.plot_medians_adc(0.33, 1.30, 1.95)
        _assert(ui._bootstrap_count > 0, "Bootstrap should progress after sample collection")

        ui._cycle_channel_filter()  # BLUE -> YELLOW
        _assert(ui.graph_channel_filter == "YELLOW", "Expected YELLOW after second cycle")
        _assert(ui._bootstrap_active is True, "Second switch should keep bootstrap active")
        _assert(ui._bootstrap_count == 0, "Second switch should reset bootstrap count")

        ui.plot_medians_adc(0.33, 1.30, 1.95)
        _assert(ui._bootstrap_count > 0, "Bootstrap should progress again after second switch")

        ui._cycle_channel_filter()  # YELLOW -> GREEN
        _assert(ui.graph_channel_filter == "GREEN", "Expected GREEN after third cycle")
        _assert(ui._bootstrap_active is True, "Third switch should restart bootstrap")
        _assert(ui._bootstrap_count == 0, "Third switch should reset bootstrap count")
    finally:
        ui.shutdown()


def test_channel_switch_reapplies_startup_lock_without_bootstrap():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=6)
        ui.bootstrap_enable = False
        ui._bootstrap_active = False
        ui._bootstrap_count = 0
        ui._bootstrap_done_range = None
        ui._bootstrap_samples = None
        ui.graph_startup_hold_ms = 2000
        ui.graph_startup_span_v = 6.0
        ui.auto_range_update_every = 1000
        ui.range_v_min = ui.V_MIN
        ui.range_v_max = ui.V_MAX

        ui._range_calibration_start_ms = ui.start_ms - (ui.graph_startup_hold_ms + 1000)
        ui._cycle_channel_filter()  # ALL -> BLUE
        _assert(ui.graph_channel_filter == "BLUE", "Expected BLUE after switch")
        _assert(ui._bootstrap_active is False, "Bootstrap must stay disabled when bootstrap_enable=False")

        ui.plot_medians_adc(0.33, 1.30, 1.95)
        _assert(ui.range_v_max < 15.0, "Startup lock should reapply from channel switch epoch and visible channel data")
    finally:
        ui.shutdown()


def test_source_off_freezes_graph_and_restarts_calibration_on_recovery():
    ui = _build_ui_or_skip()
    if ui is None:
        return
    try:
        _configure_bootstrap_test_mode(ui, bootstrap_frames=6)

        ui.plot_medians_adc(1.0, 1.1, 0.9)
        blue_before = len(ui.v_hist["BLUE"])
        yellow_before = len(ui.v_hist["YELLOW"])
        green_before = len(ui.v_hist["GREEN"])
        frame_before = ui.frame_count

        ui.set_source_off_state(True)
        _assert(ui._source_off_active is True, "Source-off state should latch active")
        for _ in range(3):
            ui.plot_medians_adc(0.2, 0.2, 0.2)

        _assert(len(ui.v_hist["BLUE"]) == blue_before, "BLUE history must freeze while source-off is active")
        _assert(len(ui.v_hist["YELLOW"]) == yellow_before, "YELLOW history must freeze while source-off is active")
        _assert(len(ui.v_hist["GREEN"]) == green_before, "GREEN history must freeze while source-off is active")
        _assert(ui.frame_count == frame_before, "Frame count should not advance while source-off overlay is active")

        ui.set_source_off_state(False)
        _assert(ui._source_off_active is False, "Source-off state should clear on recovery")
        _assert(ui.x == 0 and (not ui.graph_full), "Graph cursor/full state should reset on recovery")
        _assert(len(ui.v_hist["BLUE"]) == 0, "BLUE history should clear on recovery")
        _assert(len(ui.v_hist["YELLOW"]) == 0, "YELLOW history should clear on recovery")
        _assert(len(ui.v_hist["GREEN"]) == 0, "GREEN history should clear on recovery")
        _assert(ui._bootstrap_active is True, "Recovery should restart bootstrap calibration")
        _assert(ui._bootstrap_count == 0, "Recovery should reset bootstrap sample counter")
    finally:
        ui.shutdown()


def run_all():
    tests = (
        test_bootstrap_blocks_trace_draw_until_ready,
        test_bootstrap_sets_initial_range_once,
        test_bootstrap_first_draw_is_single_full_redraw,
        test_post_bootstrap_auto_zoom_still_operates,
        test_channel_switch_restarts_bootstrap_and_keeps_history,
        test_channel_switch_bootstrap_uses_visible_channel_scope,
        test_consecutive_channel_switches_restart_bootstrap_each_time,
        test_channel_switch_reapplies_startup_lock_without_bootstrap,
        test_source_off_freezes_graph_and_restarts_calibration_on_recovery,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("Display zoom pipeline tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

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
    ui._help_btn_pin = None
    ui._ch_btn_pin = None
    ui.view_mode = "GRAPH"
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


def run_all():
    tests = (
        test_bootstrap_blocks_trace_draw_until_ready,
        test_bootstrap_sets_initial_range_once,
        test_bootstrap_first_draw_is_single_full_redraw,
        test_post_bootstrap_auto_zoom_still_operates,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("Display zoom pipeline tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

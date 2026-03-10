# OLED Zoom Floor Guard Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Change the shared OLED auto-range behavior so deep dips stay visibly above the graph floor and match the higher, clearer presentation from `correct.jpg` when exercised through `visual_dip_demo.py`.

**Architecture:** Add a focused regression test in the zoom pipeline, then update `src/oled_ui.py` to compute a target range with asymmetric bottom headroom. Keep the existing drawing/event paths unchanged so the fix is portable to `main.py` after demo validation.

**Tech Stack:** Python, MicroPython-compatible OLED UI code, repository-local test scripts in `src/`

---

### Task 1: Add a failing floor-headroom test

**Files:**
- Modify: `src/test_display_zoom_pipeline.py`
- Test: `src/test_display_zoom_pipeline.py`

**Step 1: Write the failing test**

```python
def test_auto_zoom_keeps_dip_above_graph_floor():
    ui = _build_ui_or_skip()
    _configure_bootstrap_test_mode(ui, bootstrap_frames=6)
    for _ in range(ui.bootstrap_frames):
        ui.plot_medians_adc(0.65, 0.65, 0.65)
    for _ in range(4):
        ui.plot_medians_adc(0.40, 0.65, 0.65)
    assert ui.range_v_min < 6.0
```

**Step 2: Run test to verify it fails**

Run: `python src/test_display_zoom_pipeline.py`
Expected: FAIL because the current range logic does not expand the lower bound enough under a deep dip.

**Step 3: Write minimal implementation**

```python
bottom_pad = span * self.auto_bottom_pad_frac
return self._clamp_range(lo - bottom_pad, hi + top_pad)
```

**Step 4: Run test to verify it passes**

Run: `python src/test_display_zoom_pipeline.py`
Expected: PASS for the new floor-headroom test.

**Step 5: Commit**

```bash
git add src/test_display_zoom_pipeline.py src/oled_ui.py docs/plans/2026-03-10-oled-zoom-floor-guard-design.md docs/plans/2026-03-10-oled-zoom-floor-guard.md
git commit -m "feat: keep oled dips above graph floor"
```

### Task 2: Verify demo compatibility

**Files:**
- Modify: `src/oled_ui.py`
- Test: `src/test_visual_dip_demo.py`
- Test: `src/test_ui_button_toggle.py`

**Step 1: Run focused verification**

```bash
python src/test_display_zoom_pipeline.py
python src/test_visual_dip_demo.py
python src/test_ui_button_toggle.py
python -m py_compile src/oled_ui.py src/visual_dip_demo.py src/test_display_zoom_pipeline.py src/test_visual_dip_demo.py
```

**Step 2: Confirm expected results**

Expected:
- the new zoom-floor regression test passes
- the visual demo tests still pass
- the existing UI button/state tests still pass
- compile check passes without tracebacks

**Step 3: Commit**

```bash
git add src/oled_ui.py src/test_display_zoom_pipeline.py
git commit -m "test: verify oled zoom floor guard"
```

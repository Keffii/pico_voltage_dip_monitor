# Single-Channel UI Dip Gating Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the OLED UI ignore dip logging for non-selected channels whenever the user is viewing a single channel in `GRAPH` or `STATS`, while preserving current `ALL` behavior.

**Architecture:** Keep the fix inside `src/oled_ui.py`, where UI-specific dip state already enters through `record_dip_event_adc(...)` and `latch_dip_drop_adc(...)`. Define the regression first in `src/test_ui_button_toggle.py`, then add a minimal channel gate that accepts every channel in `ALL` mode and only the selected channel in single-channel mode.

**Tech Stack:** Python, MicroPython-compatible OLED UI helpers, repository-local test scripts in `src/`

---

### Task 1: Define single-channel dip-intake behavior in tests

**Files:**
- Modify: `src/test_ui_button_toggle.py`
- Test: `src/test_ui_button_toggle.py`

**Step 1: Write the failing event-intake test**

```python
def test_single_channel_view_ignores_hidden_channel_dip_events():
    ui = OledUI.__new__(OledUI)
    ui.graph_channel_filter = "BLUE"
    ui.view_mode = "GRAPH"
    ui.negative_dip = False
    ui.sample_counter = 17
    ui.stats_max_events = 4
    ui.graph_max_events = 4
    ui.dip_events = []
    ui._stats_dirty = False
    ui._graph_gain = lambda _channel: 1.0
    ui._graph_real = lambda _channel, value: value

    ui.record_dip_event_adc("YELLOW", 12.0, 11.4, 0.6, event_id=3, active=True, sample_index=17)

    _assert(ui.dip_events == [], "Hidden-channel dip events should be ignored in single-channel view")
    _assert(ui._stats_dirty is False, "Ignoring a hidden-channel event should not dirty stats")
```

**Step 2: Write the failing latch-intake test**

```python
def test_single_channel_view_ignores_hidden_channel_dip_latches():
    ui = OledUI.__new__(OledUI)
    ui.graph_channel_filter = "BLUE"
    ui.view_mode = "STATS"
    ui.negative_dip = False
    ui.latched_dip = {"BLUE": 0.0, "YELLOW": 0.0, "GREEN": 0.0}
    ui.min_dip_enabled = True
    ui.min_dip_eps_v = 0.001
    ui.min_drop_real_max = None
    ui.min_drop_channel = None
    ui._graph_gain = lambda _channel: 1.0
    ui._rebuild_min_badge_text = lambda: None

    ui.latch_dip_drop_adc("YELLOW", 0.9)

    _assert(ui.latched_dip["YELLOW"] == 0.0, "Hidden-channel dip latches should be ignored in single-channel view")
    _assert(ui.min_drop_channel is None, "Hidden-channel dip latches should not update min-drop state")
```

**Step 3: Add the `ALL` mode acceptance test**

```python
def test_all_channel_view_keeps_cross_channel_dip_intake():
    ui = OledUI.__new__(OledUI)
    ui.graph_channel_filter = "ALL"
    ui.view_mode = "GRAPH"
    ui.negative_dip = False
    ui.sample_counter = 4
    ui.stats_max_events = 4
    ui.graph_max_events = 4
    ui.dip_events = []
    ui._stats_dirty = False
    ui._graph_gain = lambda _channel: 1.0
    ui._graph_real = lambda _channel, value: value

    ui.record_dip_event_adc("YELLOW", 12.0, 11.4, 0.6, event_id=9, active=False, sample_index=4)

    _assert(len(ui.dip_events) == 1, "ALL mode should still accept cross-channel dip events")
    _assert(ui.dip_events[0]["channel"] == "YELLOW", "Stored event should preserve its source channel")
```

**Step 4: Register the new tests in `run_all()`**

```python
tests = (
    ...,
    test_single_channel_view_ignores_hidden_channel_dip_events,
    test_single_channel_view_ignores_hidden_channel_dip_latches,
    test_all_channel_view_keeps_cross_channel_dip_intake,
)
```

**Step 5: Run test to verify it fails**

Run: `python src/test_ui_button_toggle.py`
Expected: FAIL because `record_dip_event_adc(...)` and `latch_dip_drop_adc(...)` still accept the hidden `YELLOW` channel while `BLUE` is selected.

**Step 6: Commit**

```bash
git add src/test_ui_button_toggle.py
git commit -m "test: define single-channel ui dip gating"
```

### Task 2: Gate UI dip intake by selected channel

**Files:**
- Modify: `src/oled_ui.py`
- Test: `src/test_ui_button_toggle.py`

**Step 1: Add a small helper for UI dip-intake policy**

```python
def _ui_dip_logging_allows(self, channel):
    if self.graph_channel_filter == "ALL":
        return True
    if self.view_mode not in ("GRAPH", "STATS"):
        return True
    return channel == self.graph_channel_filter
```

**Step 2: Use the helper at the top of `latch_dip_drop_adc(...)` and `record_dip_event_adc(...)`**

```python
def latch_dip_drop_adc(self, channel, drop_adc_v):
    if not self._ui_dip_logging_allows(channel):
        return
    ...

def record_dip_event_adc(self, channel, baseline_adc_v, min_adc_v, drop_adc_v, event_id=None, active=False, sample_index=None):
    if not self._ui_dip_logging_allows(channel):
        return
    ...
```

**Step 3: Run focused tests to verify they pass**

Run: `python src/test_ui_button_toggle.py`
Expected: PASS with single-channel views rejecting hidden-channel UI dip intake and `ALL` mode still preserving cross-channel behavior.

**Step 4: Commit**

```bash
git add src/oled_ui.py src/test_ui_button_toggle.py
git commit -m "fix: gate ui dip logging by selected channel"
```

### Task 3: Run nearby regressions and clean up

**Files:**
- Verify: `src/test_display_zoom_pipeline.py`
- Verify: `src/test_oled_graph_readouts.py`

**Step 1: Run channel/filter regression coverage**

Run: `python src/test_display_zoom_pipeline.py`
Expected: PASS with channel cycling, startup recalibration, and source-off behavior unchanged.

**Step 2: Run graph readout regression coverage**

Run: `python src/test_oled_graph_readouts.py`
Expected: PASS with single-channel graph rendering and dip callout behavior unchanged.

**Step 3: Inspect the worktree**

Run: `git status --short`
Expected: Only the intended `src/` files plus any pre-existing unrelated worktree changes remain.

**Step 4: Commit**

```bash
git add src/oled_ui.py src/test_ui_button_toggle.py
git commit -m "test: verify single-channel ui dip gating regressions"
```

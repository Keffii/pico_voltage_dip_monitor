# Stats Channel Filter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the OLED statistics page show only dip events for the selected channel, while preserving all-channel behavior in `ALL` mode.

**Architecture:** Keep dip event storage unchanged in `src/oled_ui.py` and scope the behavior change to the stats-view helper that already feeds both rendering and active-event blinking. Update the UI toggle tests first so they define the filtered stats behavior, then implement the minimal helper change needed to satisfy them.

**Tech Stack:** Python, MicroPython-compatible OLED UI helpers, repository-local test scripts in `src/`

---

### Task 1: Define filtered stats behavior in tests

**Files:**
- Modify: `src/test_ui_button_toggle.py`
- Test: `src/test_ui_button_toggle.py`

**Step 1: Write the failing test**

```python
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

    _assert(draws[0][2] == "--.-V --.-V ---%", "Filtered stats view should not render hidden-channel events")
```

**Step 2: Run test to verify it fails**

Run: `python src/test_ui_button_toggle.py`
Expected: FAIL because stats still render the `YELLOW` event while `BLUE` is selected.

**Step 3: Add coverage for `ALL` mode and blink filtering**

```python
def test_stats_view_keeps_all_channel_events_in_all_mode():
    ...

def test_stats_blink_considers_only_visible_active_events():
    ...
```

**Step 4: Run test to verify the new expectations fail for the right reason**

Run: `python src/test_ui_button_toggle.py`
Expected: FAIL on filtered stats behavior, not on test setup.

**Step 5: Commit**

```bash
git add src/test_ui_button_toggle.py
git commit -m "test: define stats channel filter behavior"
```

### Task 2: Implement filtered stats event selection

**Files:**
- Modify: `src/oled_ui.py`
- Test: `src/test_ui_button_toggle.py`

**Step 1: Write the minimal implementation**

```python
def _stats_events_for_view(self):
    if self.graph_channel_filter == "ALL":
        return self.dip_events
    return [ev for ev in self.dip_events if ev.get("channel") == self.graph_channel_filter]
```

**Step 2: Run focused tests to verify they pass**

Run: `python src/test_ui_button_toggle.py`
Expected: PASS with the new channel-filtered stats behavior.

**Step 3: Run nearby regression coverage**

Run: `python src/test_display_zoom_pipeline.py`
Expected: PASS with the existing channel-switch and zoom behavior still intact.

**Step 4: Commit**

```bash
git add src/oled_ui.py src/test_ui_button_toggle.py
git commit -m "feat: filter stats by selected channel"
```

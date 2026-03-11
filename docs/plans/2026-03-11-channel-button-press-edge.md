# Channel Button Press-Edge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the dedicated OLED channel button cycle the visible channel on press instead of release, while keeping the Graph/Stats toggle unchanged.

**Architecture:** Limit the behavior change to `_poll_channel_button()` in `src/oled_ui.py` and mirror the existing press-edge latch pattern already used by `_poll_toggle_button()`. Define the new behavior first in `src/test_ui_button_toggle.py`, verify the red failure, then implement the smallest input-state change that satisfies the new tests.

**Tech Stack:** Python, MicroPython-compatible UI input handling, repository-local test scripts in `src/`

---

### Task 1: Define channel-button press-edge behavior in tests

**Files:**
- Modify: `src/test_ui_button_toggle.py`
- Test: `src/test_ui_button_toggle.py`

**Step 1: Write the failing test**

```python
def test_channel_button_cycles_on_press_edge():
    def _run(clock):
        ui = _new_channel_ui(clock, start_filter="ALL")
        _debounced_channel_transition(ui, clock, 0)
        _assert(ui.graph_channel_filter == "BLUE", "Channel button should switch on first debounced press edge")

    _with_fake_time(_run)
```

**Step 2: Run test to verify it fails**

Run: `python src/test_ui_button_toggle.py`
Expected: FAIL because `_poll_channel_button()` currently waits for release before calling `_cycle_channel_filter()`.

**Step 3: Add hold and re-arm coverage**

```python
def test_channel_button_hold_does_not_retrigger():
    ...

def test_channel_button_release_rearms_next_press():
    ...
```

**Step 4: Run test to verify the new expectations fail for the right reason**

Run: `python src/test_ui_button_toggle.py`
Expected: FAIL on channel-button timing behavior, not on test setup.

**Step 5: Commit**

```bash
git add src/test_ui_button_toggle.py
git commit -m "test: define channel button press-edge behavior"
```

### Task 2: Implement press-edge channel cycling

**Files:**
- Modify: `src/oled_ui.py`
- Test: `src/test_ui_button_toggle.py`

**Step 1: Write the minimal implementation**

```python
if pressed:
    if not self._ch_btn_pressed:
        self._cycle_channel_filter()
        self._ch_btn_pressed = True
else:
    self._ch_btn_pressed = False
```

**Step 2: Run focused tests to verify they pass**

Run: `python src/test_ui_button_toggle.py`
Expected: PASS with the dedicated channel button switching on press.

**Step 3: Run nearby regression coverage**

Run: `python src/test_display_zoom_pipeline.py`
Expected: PASS with existing graph/channel bootstrap behavior still intact.

**Step 4: Commit**

```bash
git add src/oled_ui.py src/test_ui_button_toggle.py
git commit -m "feat: cycle channel on button press"
```

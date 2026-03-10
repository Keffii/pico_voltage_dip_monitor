# Visual Dip Demo Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `src/visual_dip_demo.py` produce deterministic dips every two seconds while keeping graph and statistics fully synchronized through the same OLED event lifecycle used by `src/main.py`.

**Architecture:** Keep the demo self-contained, but replace the random scheduler with deterministic simulation helpers that own persistent event state. Drive the OLED exclusively through `plot_medians_adc`, `record_dip_event_adc`, and `latch_dip_drop_adc` so view toggles and channel filters render the same stored data instead of recomputing it.

**Tech Stack:** Python, MicroPython-compatible helpers, existing `OledUI` event/state model, repository-local test scripts in `src/`

---

### Task 1: Add a failing scheduler test

**Files:**
- Create: `src/test_visual_dip_demo.py`
- Test: `src/test_visual_dip_demo.py`

**Step 1: Write the failing test**

```python
def test_dips_rotate_every_two_seconds():
    state = demo.create_demo_state()
    ui = _FakeUI()

    demo.advance_demo_state(state, ui, now_ms=0, frame_index=0)
    demo.advance_demo_state(state, ui, now_ms=2000, frame_index=200)
    demo.advance_demo_state(state, ui, now_ms=4000, frame_index=400)

    starts = [event for event in ui.events if event["active"]]
    assert [event["channel"] for event in starts[:3]] == ["BLUE", "YELLOW", "GREEN"]
```

**Step 2: Run test to verify it fails**

Run: `python src/test_visual_dip_demo.py`
Expected: FAIL because `create_demo_state` or `advance_demo_state` does not exist yet.

**Step 3: Write minimal implementation**

```python
def create_demo_state():
    return {
        "next_event_id": 1,
        "next_dip_ms": 0,
        "rotation_index": 0,
        "active_dips": {},
    }
```

**Step 4: Run test to verify it passes**

Run: `python src/test_visual_dip_demo.py`
Expected: PASS for the deterministic rotation test.

**Step 5: Commit**

```bash
git add src/test_visual_dip_demo.py src/visual_dip_demo.py
git commit -m "test: cover deterministic visual dip scheduling"
```

### Task 2: Add a failing lifecycle test for shared event identity

**Files:**
- Modify: `src/test_visual_dip_demo.py`
- Test: `src/test_visual_dip_demo.py`

**Step 1: Write the failing test**

```python
def test_completed_dip_reuses_event_id_and_anchor():
    state = demo.create_demo_state()
    ui = _FakeUI()

    demo.advance_demo_state(state, ui, now_ms=0, frame_index=10)
    demo.advance_demo_state(state, ui, now_ms=demo.DIP_DURATION_MS // 2, frame_index=20)
    demo.advance_demo_state(state, ui, now_ms=demo.DIP_DURATION_MS + 1, frame_index=30)

    assert ui.events[0]["event_id"] == ui.events[-1]["event_id"]
    assert ui.events[-1]["sample_index"] == 10
    assert ui.latched[0]["channel"] == "BLUE"
```

**Step 2: Run test to verify it fails**

Run: `python src/test_visual_dip_demo.py`
Expected: FAIL because the demo does not yet preserve the original event anchor or latch the finished drop.

**Step 3: Write minimal implementation**

```python
dip = {
    "event_id": event_id,
    "sample_index": frame_index,
    "baseline_real": baseline_real,
    "min_real": baseline_real,
}
```

**Step 4: Run test to verify it passes**

Run: `python src/test_visual_dip_demo.py`
Expected: PASS for both the rotation test and the lifecycle test.

**Step 5: Commit**

```bash
git add src/test_visual_dip_demo.py src/visual_dip_demo.py
git commit -m "feat: sync visual demo dip lifecycle with oled event model"
```

### Task 3: Wire the runtime loop to the deterministic helpers

**Files:**
- Modify: `src/visual_dip_demo.py`
- Test: `src/test_visual_dip_demo.py`

**Step 1: Write the failing test**

```python
def test_run_step_updates_plot_values_for_all_channels():
    state = demo.create_demo_state()
    ui = _FakeUI()

    blue_adc, yellow_adc, green_adc = demo.advance_demo_state(
        state, ui, now_ms=0, frame_index=0
    )

    assert blue_adc is not None
    assert yellow_adc is not None
    assert green_adc is not None
```

**Step 2: Run test to verify it fails**

Run: `python src/test_visual_dip_demo.py`
Expected: FAIL because the helper does not yet return plot-ready channel values.

**Step 3: Write minimal implementation**

```python
vals_real = _build_channel_values(state, now_ms)
return (
    vals_real["BLUE"] / config.CHANNEL_SCALE.get("BLUE", 1.0),
    vals_real["YELLOW"] / config.CHANNEL_SCALE.get("YELLOW", 1.0),
    vals_real["GREEN"] / config.CHANNEL_SCALE.get("GREEN", 1.0),
)
```

**Step 4: Run test to verify it passes**

Run: `python src/test_visual_dip_demo.py`
Expected: PASS for the new helper return-value test and the existing lifecycle tests.

**Step 5: Commit**

```bash
git add src/test_visual_dip_demo.py src/visual_dip_demo.py
git commit -m "feat: drive visual dip demo from deterministic step helpers"
```

### Task 4: Verify the feature end to end

**Files:**
- Modify: `src/visual_dip_demo.py`
- Test: `src/test_visual_dip_demo.py`
- Test: `src/test_ui_button_toggle.py`

**Step 1: Run focused verification**

```bash
python src/test_visual_dip_demo.py
python src/test_ui_button_toggle.py
```

**Step 2: Confirm expected results**

Expected:
- the new demo scheduler tests pass
- the existing UI toggle/stats tests still pass
- no new warnings or tracebacks appear

**Step 3: Commit**

```bash
git add src/test_visual_dip_demo.py src/visual_dip_demo.py
git commit -m "feat: add deterministic realtime visual dip demo"
```

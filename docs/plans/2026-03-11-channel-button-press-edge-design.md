# Channel Button Press-Edge Design

**Goal:** Make the dedicated channel-select button cycle the visible channel on the debounced press edge instead of waiting for button release, while leaving the Graph/Stats toggle behavior unchanged.

**Context**

`src/oled_ui.py` has two separate button polling paths. `_poll_toggle_button()` already flips `view_mode` on the first debounced press edge and uses `_btn_pressed` only to suppress repeats while held. `_poll_channel_button()` currently records the press but waits for the matching release edge before calling `_cycle_channel_filter()`, which makes channel changes feel delayed relative to the view toggle.

**Approach**

Change only `_poll_channel_button()` in `src/oled_ui.py` so it mirrors the press-edge latch pattern already used by `_poll_toggle_button()`:

- when the debounced state becomes pressed, call `_cycle_channel_filter()` immediately if `_ch_btn_pressed` is not already latched
- set `_ch_btn_pressed = True` after the first qualifying press edge
- when the debounced state becomes released, only clear `_ch_btn_pressed` so the next press can trigger another channel change

**Why This Approach**

- It keeps behavior consistent between the two physical buttons without changing unrelated input logic.
- It preserves debounce and single-fire-on-hold behavior by reusing the existing `_ch_btn_pressed` latch.
- It avoids touching `src/main.py` or `src/visual_dip_demo.py`, because both already rely on the shared `OledUI.poll_inputs()` path.

**Behavior Details**

- A debounced press of the dedicated channel button advances the filter immediately.
- Holding the button does not keep cycling channels.
- Releasing the button does not change the channel; it only re-arms the next press.
- The Graph/Stats toggle remains press-edge driven exactly as it is today.

**Testing**

Update `src/test_ui_button_toggle.py` to add dedicated channel-button tests that verify:

- the channel filter changes on press
- holding the button does not retrigger cycling
- release only re-arms the next press
- the existing Graph/Stats toggle tests remain unchanged

# Single-Channel UI Dip Gating Design

**Goal:** Make the OLED graph and statistics views ignore dip logging for non-selected channels whenever the user is viewing a single channel, while preserving current cross-channel behavior in `ALL` mode.

**Context**

The OLED UI stores recent dip events in a shared `self.dip_events` list and also keeps per-channel latched drop state for graph readouts and badges. The current UI already filters some rendering paths by `graph_channel_filter`, but dip events from other channels can still enter the UI state while the user is viewing `BLUE`, `YELLOW`, or `GREEN`. That leaves graph and stats behavior inconsistent with the selected single-channel view.

The intended behavior is stricter than simple filtering: while the UI is in `GRAPH` or `STATS` and a single channel is selected, dip logging for the other two channels should be completely ignored by the UI path.

**Approach**

Gate dip-event intake at the UI boundary in `src/oled_ui.py`:

- `record_dip_event_adc(...)` accepts all channels in `ALL` mode.
- `record_dip_event_adc(...)` accepts only the selected channel when `graph_channel_filter` is `BLUE`, `YELLOW`, or `GREEN`.
- `latch_dip_drop_adc(...)` follows the same gate so hidden-channel dips cannot update graph-side latched state.

Keep the detector and non-UI dip handling unchanged in `src/main.py`. The bug is in UI event/logging semantics, not dip detection itself.

**Why This Approach**

- It matches the requirement exactly: hidden channels are ignored, not merely hidden at render time.
- It centralizes the rule in the OLED UI methods that already define UI dip state, avoiding duplicated branching across the direct and queued update paths in `src/main.py`.
- It reduces regression risk because the detector, CSV logging, and USB paths remain untouched.
- It still allows `ALL` mode to behave exactly as it does today.

**Behavior Details**

- In `ALL`, the UI continues to log and render dip activity for every channel.
- In single-channel `GRAPH` or `STATS`, only the selected channel can create or update UI dip events.
- Hidden-channel dips must not be inserted into `self.dip_events`.
- Hidden-channel dips must not update `self.latched_dip`, min-drop badge inputs, or any graph-visible dip markers.
- Existing render-time channel filters remain in place as a safety net, but they are no longer the primary protection.

**Testing**

Update regression coverage so it proves:

- single-channel mode ignores non-matching `record_dip_event_adc(...)` calls
- single-channel mode ignores non-matching `latch_dip_drop_adc(...)` calls
- `ALL` mode still accepts and stores cross-channel dip activity
- nearby graph/stats channel-filter behavior continues to pass unchanged

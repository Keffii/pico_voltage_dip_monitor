# Stats Channel Filter Design

**Goal:** Make the statistics page honor the active channel filter so single-channel views only show dip statistics for the selected channel, while `ALL` mode still shows events from every channel.

**Context**

The OLED UI already stores recent dip events for every channel in one shared `self.dip_events` list. The current stats path does not filter that list, so the stats screen keeps showing cross-channel events even after the user switches the graph to `BLUE`, `YELLOW`, or `GREEN`.

**Approach**

Change the stats view helper in `src/oled_ui.py` so it returns the visible subset of `self.dip_events` based on `self.graph_channel_filter`:

- `ALL` returns all stored events.
- `BLUE`, `YELLOW`, and `GREEN` return only events whose `channel` matches the selected filter.

This keeps event storage unchanged and limits the behavior change to presentation logic.

**Why This Approach**

- It reuses the existing `_stats_events_for_view()` seam instead of adding new UI state.
- `_draw_stats()` and `_update_stats_blink_state()` already consume that helper, so both rendering and active-event blinking stay consistent.
- Graph history and dip event recording remain untouched, which reduces regression risk.

**Behavior Details**

- Entering stats in `ALL` mode still shows the most recent events across all channels.
- Entering stats in a single-channel mode shows only that channel's events.
- Active blink only reacts to visible active events in the current filtered view.
- Placeholder rows still render when the filtered event count is lower than `stats_max_events`.

**Testing**

Update `src/test_ui_button_toggle.py` so it verifies:

- single-channel stats hide non-matching events
- `ALL` mode still shows cross-channel events
- active blink only reacts to active events that are visible under the current filter

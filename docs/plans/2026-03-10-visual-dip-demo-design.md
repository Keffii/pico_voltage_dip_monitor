# Visual Dip Demo Design

## Goal

Make `src/visual_dip_demo.py` behave like the OLED path in `src/main.py` while remaining a standalone demo entrypoint. The demo must show deterministic dips in real time, keep graph and statistics synchronized, and preserve the same data while the user toggles between views or cycles channel filters.

## Selected Approach

Use the existing standalone demo file and replace its random simulator with a deterministic event scheduler. This keeps the change local to the demo while reusing the same OLED API surface that `main.py` uses:

- `plot_medians_adc(...)`
- `record_dip_event_adc(...)`
- `latch_dip_drop_adc(...)`

This is the smallest change that still matches the production event lifecycle.

## Runtime Model

The demo owns one persistent simulation state for the full session:

- frame counter
- next dip start time
- next event id
- deterministic channel rotation index
- last plotted real-voltage values per channel
- active dip records keyed by channel

Every 2000 ms the scheduler starts the next dip in the fixed order `BLUE -> YELLOW -> GREEN -> ...`. Dip timing and depth are deterministic so the demo is predictable during live explanation or recording.

## Sync Model

The graph and stats views stay synchronized by updating the same OLED event record from start to finish:

1. On dip start, allocate an `event_id`, capture the channel baseline, and call `record_dip_event_adc(..., active=True, sample_index=<start frame>)`.
2. While the dip is active, keep updating that same `event_id` with the latest minimum and the original sample anchor.
3. On completion, call `record_dip_event_adc(..., active=False, sample_index=<original start frame>)`.
4. Immediately latch the finished drop with `latch_dip_drop_adc(...)`.

This mirrors the way `main.py` and `oled_ui.py` already keep the graph callouts and stats rows aligned through `event_id` and `sample_index`.

## Data Domain

The simulator continues to generate values in real-voltage space. Conversion back to ADC-domain happens only at the OLED API boundary, which matches the current demo and avoids changing OLED scaling behavior.

## Verification

Add a focused test module for the demo scheduler and event lifecycle before changing the implementation. The tests should verify:

- dips start every 2000 ms
- channels rotate deterministically
- active and finished UI updates reuse the same `event_id`
- the final event keeps the original `sample_index`
- the finished drop is latched after completion

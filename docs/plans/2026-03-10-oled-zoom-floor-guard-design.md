# OLED Zoom Floor Guard Design

## Goal

Adjust the shared OLED auto-range behavior so dips stay visibly above the graph floor instead of visually clipping into the `MIN` readout. The desired result is the higher, clearer presentation shown in `correct.jpg`, while preserving the smoother demo refresh behavior already proven in `visual_dip_demo.py`.

## Selected Approach

Change the shared range calculation in `src/oled_ui.py` rather than faking the effect in the demo. The new logic will reserve stronger bottom headroom under the visible minimum than the current symmetric auto-padding does, so the rendered dip sits higher on the OLED and never hugs the bottom edge during deep events.

## Key Change

After the normal visible-window low/high range is computed, the auto-range target will apply an asymmetric padding policy:

- keep some normal top headroom above the visible maximum
- keep extra bottom headroom below the visible minimum
- preserve the existing minimum-span and smoothing behavior

This keeps the graph readable without changing the event pipeline, stats synchronization, or the improved demo cadence.

## Verification

Add a failing test in `src/test_display_zoom_pipeline.py` that feeds a stable baseline with a deep visible dip and asserts the resulting lower range expands enough that the graph floor stays below the visible minimum by a meaningful margin. Re-run the display zoom tests, the visual demo tests, and a compile check after the implementation.

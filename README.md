# Pico Voltage Dip Monitor (Pico 2)

Measure voltages on GP26, GP27, GP28 with 10 ms sampling, log 100 ms medians, and detect voltage dips with dip start and dip end events.

## What it does
- Samples GP26, GP27, GP28 every 10 ms (100 Hz)
- Computes a 100 ms median per channel (median of 10 samples)
- Uses stability gating to avoid logging floating or noisy readings
- Detects dips on raw 10 ms samples with fixed threshold
- Logs dip start and dip end events

## Hardware
- Raspberry Pi Pico 2
- Prototype: one AAA cell per ADC channel
- Common ground shared between all cells and Pico

ADC pins:
- GP26 = ADC0
- GP27 = ADC1
- GP28 = ADC2

## Safety
- Never exceed 3.3 V on any ADC pin.
- For series packs or higher voltages, use voltage dividers and proper measurement architecture.

## Output files on the Pico
This project writes two files to the Pico filesystem:

- `/pico_medians.csv`
  - Columns: `time_s,channel,median_V`
  - Logged only when stable
- `/pico_dips.csv`
  - Columns: `channel,dip_start_s,dip_end_s,duration_ms,baseline_V,min_V,drop_V`
  - One row per completed dip event

See `docs/data-formats.md` for details.

## Run (Thonny)
1. Install MicroPython onto Pico 2 (RP2350) using Thonny:
   Tools -> Options -> Interpreter -> Install or update MicroPython
2. Copy `src/main.py` to the Pico and run it
3. View files:
   Thonny -> View -> Files -> Raspberry Pi Pico

## Configuration
Tuning is done at the top of `src/main.py`:
- sampling rate (`TICK_MS`)
- stability settings (`STABLE_SPAN_V`, `MIN_V`, `MAX_V`)
- baseline length (`BASELINE_SECONDS`)
- dip detection (`DIP_THRESHOLD_V`, hold times, cooldown)

## Docs
- `docs/wiring.md`
- `docs/data-formats.md`
- `docs/troubleshooting.md`
- `docs/architecture.md`

## License
MIT

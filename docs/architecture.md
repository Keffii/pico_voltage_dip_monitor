# Architecture

## Sampling
- 10 ms scheduler tick
- Reads GP26, GP27, GP28 each tick

## Stability gating
- Tracks a short raw window per channel
- Only considers a channel stable when noise span is low and values are in expected range

## Medians
- Computes 100 ms median per channel (10 samples)
- Buffers median lines and flushes to flash in batches

## Dip detection
- Runs on raw 10 ms samples (low latency)
- Logs dip start and dip end
- Includes duration, min voltage, and drop from baseline

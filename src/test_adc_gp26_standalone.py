# test_adc_gp26_standalone.py
"""
Standalone GP26 ADC validation + calibration helper for Pico.

Purpose:
- Read GP26 continuously with no dependency on project config/runtime.
- Print raw ADC volts, calibrated ADC volts, and VIN estimate.
- Provide one-point gain suggestion from a DMM reading at the ADC node.

Usage on Pico REPL:
    >>> import test_adc_gp26_standalone as t
    >>> t.run()
    >>> t.print_suggested_gain(dmm_adc_node_v=0.1100, sample_count=200)
"""

import time
from machine import ADC


# ADC conversion
VREF = 3.3

# Fixed channel under test
LABEL = "BLUE"
GP = 26

# Divider constants (VIN -> ADC node)
DIVIDER_RTOP_OHM = 820_000
DIVIDER_RBOT_OHM = 47_000

# Initial one-point calibration
ADC_GAIN = 0.751
ADC_OFFSET_V = 0.0

# ADC filter settings
ADC_SETTLE_DISCARDS = 1
ADC_OVERSAMPLE_COUNT = 9
ADC_TRIM_COUNT = 2
ADC_SETTLE_US = 2


def _clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v


def _filter_settings():
    settle_discards = int(ADC_SETTLE_DISCARDS)
    if settle_discards < 0:
        settle_discards = 0

    oversample_count = int(ADC_OVERSAMPLE_COUNT)
    if oversample_count < 1:
        oversample_count = 1

    trim_count = int(ADC_TRIM_COUNT)
    if trim_count < 0:
        trim_count = 0
    max_trim = (oversample_count - 1) // 2
    if trim_count > max_trim:
        trim_count = max_trim

    settle_us = int(ADC_SETTLE_US)
    if settle_us < 0:
        settle_us = 0

    return settle_discards, oversample_count, trim_count, settle_us


def _divider_scale():
    if DIVIDER_RBOT_OHM <= 0:
        return 1.0
    return (DIVIDER_RTOP_OHM + DIVIDER_RBOT_OHM) / DIVIDER_RBOT_OHM


def _read_filtered_raw(adc, sample_buf, settle_discards, settle_us, oversample_count, trim_count):
    for _ in range(settle_discards):
        adc.read_u16()
        if settle_us > 0:
            time.sleep_us(settle_us)

    if oversample_count == 1:
        return adc.read_u16()

    for i in range(oversample_count):
        sample_buf[i] = adc.read_u16()
    sample_buf.sort()

    lo = trim_count
    hi = oversample_count - trim_count
    if hi <= lo:
        return sample_buf[oversample_count // 2]

    total = 0
    count = 0
    for i in range(lo, hi):
        total += sample_buf[i]
        count += 1
    return total / count


def run(interval_ms=150):
    adc = ADC(GP)
    v_per_count = VREF / 65535.0
    divider_scale = _divider_scale()

    settle_discards, oversample_count, trim_count, settle_us = _filter_settings()
    sample_buf = [0] * oversample_count

    interval_ms = int(interval_ms)
    if interval_ms < 0:
        interval_ms = 0

    print("\n" + "=" * 70)
    print("STANDALONE ADC TEST (GP26 ONLY)")
    print("=" * 70)
    print("Mapping: GP26={}".format(LABEL))
    print("Isolation: no config.py imports, no project module dependencies")
    print(
        "Divider: RTOP={} ohm, RBOT={} ohm, scale={:.6f}x".format(
            DIVIDER_RTOP_OHM, DIVIDER_RBOT_OHM, divider_scale
        )
    )
    print("Calibration: gain={:.6f}, offset_v={:.6f}".format(ADC_GAIN, ADC_OFFSET_V))
    print(
        "Filter: discards={}, oversample={}, trim={}, settle_us={}".format(
            settle_discards, oversample_count, trim_count, settle_us
        )
    )
    print("Fields: ADC_V_RAW, ADC_V_CAL, VIN_EST")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            raw = _read_filtered_raw(
                adc=adc,
                sample_buf=sample_buf,
                settle_discards=settle_discards,
                settle_us=settle_us,
                oversample_count=oversample_count,
                trim_count=trim_count,
            )
            adc_v_raw = raw * v_per_count
            adc_v_cal = _clamp((adc_v_raw * ADC_GAIN) + ADC_OFFSET_V, 0.0, VREF)
            vin_est = adc_v_cal * divider_scale
            print(
                "{}(GP{}): ADC_V_RAW={:.4f} | ADC_V_CAL={:.4f} | VIN_EST={:.2f}".format(
                    LABEL, GP, adc_v_raw, adc_v_cal, vin_est
                )
            )
            time.sleep_ms(interval_ms)
    except KeyboardInterrupt:
        print("\nStandalone ADC test stopped.")


def print_suggested_gain(dmm_adc_node_v, sample_count=200):
    dmm_adc_node_v = float(dmm_adc_node_v)
    if dmm_adc_node_v <= 0.0:
        raise ValueError("dmm_adc_node_v must be > 0")

    sample_count = int(sample_count)
    if sample_count < 1:
        sample_count = 1

    adc = ADC(GP)
    v_per_count = VREF / 65535.0
    settle_discards, oversample_count, trim_count, settle_us = _filter_settings()
    sample_buf = [0] * oversample_count

    total_raw_v = 0.0
    for _ in range(sample_count):
        raw = _read_filtered_raw(
            adc=adc,
            sample_buf=sample_buf,
            settle_discards=settle_discards,
            settle_us=settle_us,
            oversample_count=oversample_count,
            trim_count=trim_count,
        )
        total_raw_v += raw * v_per_count

    avg_raw_v = total_raw_v / sample_count
    if avg_raw_v <= 0.0:
        raise ValueError("Average raw ADC voltage is <= 0; cannot compute suggested gain")

    suggested_gain = dmm_adc_node_v / avg_raw_v

    print("\n" + "=" * 70)
    print("ONE-POINT GAIN SUGGESTION (GP26)")
    print("=" * 70)
    print("Samples:               {}".format(sample_count))
    print("Average ADC_V_RAW:     {:.6f} V".format(avg_raw_v))
    print("DMM ADC node voltage:  {:.6f} V".format(dmm_adc_node_v))
    print("Current ADC_GAIN:      {:.6f}".format(ADC_GAIN))
    print("Suggested ADC_GAIN:    {:.6f}".format(suggested_gain))
    print(
        "Use this in file: ADC_GAIN = {:.6f}".format(suggested_gain)
    )
    print("=" * 70)

    return suggested_gain


if __name__ == "__main__":
    run()

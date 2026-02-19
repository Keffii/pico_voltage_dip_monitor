# test_adc_pins.py
"""
Standalone ADC pin test for Pico.

Purpose:
- Read GP26 continuously.
- Print raw/calibrated ADC volts for BLUE(GP26) only.
- Print VIN_EST (estimated input voltage before divider).
- Use ADC accuracy settings from config.py when available.
- Use BLUE gain/offset calibration from config.py when available.
- Use divider constants (820k/47k defaults) to compute VIN_EST.
- Intentionally ignore GP27/GP28 so floating inputs cannot disturb this test.

Usage on Pico REPL:
    >>> import test_adc_pins
    >>> test_adc_pins.run()
"""

import time
from machine import ADC

try:
    import config
except ImportError:
    config = None


def _cfg(name, default):
    if config is None:
        return default
    return getattr(config, name, default)


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
    vref = float(_cfg("VREF", 3.3))
    label = "BLUE"
    gp = 26
    adc = ADC(gp)

    divider_rtop = float(_cfg("DIVIDER_RTOP_OHM", 820_000))
    divider_rbot = float(_cfg("DIVIDER_RBOT_OHM", 47_000))
    if divider_rtop < 0:
        divider_rtop = 0.0
    if divider_rbot <= 0:
        divider_rbot = 47_000.0
    divider_scale = (divider_rtop + divider_rbot) / divider_rbot

    gain_map = _cfg("ADC_CHANNEL_GAIN", {})
    offset_map = _cfg("ADC_CHANNEL_OFFSET_V", {})
    if not isinstance(gain_map, dict):
        gain_map = {}
    if not isinstance(offset_map, dict):
        offset_map = {}
    gain = float(gain_map.get(label, 0.751))
    if gain <= 0:
        gain = 0.751
    offset_v = float(offset_map.get(label, 0.0))

    settle_discards = int(_cfg("ADC_SETTLE_DISCARDS", 1))
    if settle_discards < 0:
        settle_discards = 0

    oversample_count = int(_cfg("ADC_OVERSAMPLE_COUNT", 9))
    if oversample_count < 1:
        oversample_count = 1

    trim_count = int(_cfg("ADC_TRIM_COUNT", 2))
    if trim_count < 0:
        trim_count = 0
    max_trim = (oversample_count - 1) // 2
    if trim_count > max_trim:
        trim_count = max_trim

    settle_us = int(_cfg("ADC_SETTLE_US", 2))
    if settle_us < 0:
        settle_us = 0

    sample_buf = [0] * oversample_count
    v_per_count = vref / 65535.0

    print("\n" + "=" * 70)
    print("ADC PIN TEST (GP26 ONLY)")
    print("=" * 70)
    print("Mapping: GP26=BLUE")
    print("Channels: {}(GP{})".format(label, gp))
    print("Note: GP27/GP28 are intentionally ignored in this test.")
    print(
        "Divider: RTOP={} ohm, RBOT={} ohm, scale={:.6f}x".format(
            int(divider_rtop), int(divider_rbot), divider_scale
        )
    )
    print("Calibration: gain={:.6f}, offset_v={:.6f}".format(gain, offset_v))
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
                trim_count=trim_count
            )
            adc_v_raw = raw * v_per_count
            adc_v_cal = (adc_v_raw * gain) + offset_v
            if adc_v_cal < 0.0:
                adc_v_cal = 0.0
            elif adc_v_cal > vref:
                adc_v_cal = vref
            vin_est = adc_v_cal * divider_scale
            print(
                "{}(GP{}): ADC_V_RAW={:.4f} | ADC_V_CAL={:.4f} | VIN_EST={:.2f}".format(
                    label, gp, adc_v_raw, adc_v_cal, vin_est
                )
            )
            time.sleep_ms(interval_ms)
    except KeyboardInterrupt:
        print("\nADC pin test stopped.")


if __name__ == "__main__":
    run()

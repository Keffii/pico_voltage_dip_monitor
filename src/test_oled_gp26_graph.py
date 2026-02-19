# test_oled_gp26_graph.py
"""
Standalone OLED graph test for GP26 only.

Purpose:
- Sample GP26 (BLUE) ADC only.
- Plot only BLUE on the OLED graph.
- Keep YELLOW/GREEN out of the graph path for this test.

Usage on Pico REPL:
    >>> import test_oled_gp26_graph
    >>> test_oled_gp26_graph.run()
"""

import time
from machine import ADC
from oled_ui import OledUI

VREF = 3.3
LABEL = "BLUE"
GP = 26

ADC_SETTLE_DISCARDS = 1
ADC_OVERSAMPLE_COUNT = 9
ADC_TRIM_COUNT = 2
ADC_SETTLE_US = 2


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


def run(interval_ms=100):
    settle_discards = ADC_SETTLE_DISCARDS if ADC_SETTLE_DISCARDS >= 0 else 0
    oversample_count = ADC_OVERSAMPLE_COUNT if ADC_OVERSAMPLE_COUNT >= 1 else 1
    trim_count = ADC_TRIM_COUNT if ADC_TRIM_COUNT >= 0 else 0
    max_trim = (oversample_count - 1) // 2
    if trim_count > max_trim:
        trim_count = max_trim
    settle_us = ADC_SETTLE_US if ADC_SETTLE_US >= 0 else 0

    adc = ADC(GP)
    ui = OledUI()
    ui.view_mode = "GRAPH"
    ui.graph_channel_filter = "BLUE"
    ui.help_overlay_enabled = False
    ui._force_graph_redraw = True

    sample_buf = [0] * oversample_count
    v_per_count = VREF / 65535.0

    print("\n" + "=" * 70)
    print("OLED GP26 GRAPH TEST (BLUE ONLY)")
    print("=" * 70)
    print("Channel: {}(GP{})".format(LABEL, GP))
    print(
        "Filter: discards={}, oversample={}, trim={}, settle_us={}".format(
            settle_discards, oversample_count, trim_count, settle_us
        )
    )
    print("Graph: BLUE only (YELLOW/GREEN hidden)")
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
            adc_v = raw * v_per_count

            # BLUE is real signal; YELLOW/GREEN are fixed for this isolated graph test.
            ui.plot_medians_adc(adc_v, 0.0, 0.0)
            print("{}(GP{}): ADC_V={:.4f}".format(LABEL, GP, adc_v))
            time.sleep_ms(interval_ms)
    except KeyboardInterrupt:
        ui.shutdown()
        print("\nOLED GP26 graph test stopped.")


if __name__ == "__main__":
    run()

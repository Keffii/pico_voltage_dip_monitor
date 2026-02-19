# adc_sampler.py

import time
from machine import ADC


class AdcSampler:
    def __init__(
        self,
        channel_pins,
        vref,
        settle_discard_count=1,
        oversample_count=9,
        trim_count=2,
        settle_us=2,
        channel_gain=None,
        channel_offset_v=None
    ):
        self.vref = float(vref)
        self._v_per_count = self.vref / 65535.0

        self.settle_discard_count = int(settle_discard_count)
        if self.settle_discard_count < 0:
            self.settle_discard_count = 0

        self.oversample_count = int(oversample_count)
        if self.oversample_count < 1:
            self.oversample_count = 1

        self.trim_count = int(trim_count)
        if self.trim_count < 0:
            self.trim_count = 0
        max_trim = (self.oversample_count - 1) // 2
        if self.trim_count > max_trim:
            self.trim_count = max_trim

        self.settle_us = int(settle_us)
        if self.settle_us < 0:
            self.settle_us = 0

        if channel_gain is None:
            channel_gain = {}
        if channel_offset_v is None:
            channel_offset_v = {}

        self.channels = []
        for name, gp in channel_pins:
            gain = float(channel_gain.get(name, 1.0))
            offset_v = float(channel_offset_v.get(name, 0.0))
            self.channels.append((name, ADC(gp), gain, offset_v))

        # Reuse a single buffer to keep allocations low during the hot loop.
        self._sample_buf = [0] * self.oversample_count

    def _read_filtered_raw(self, adc):
        # Throw away initial conversions after mux switch to reduce crosstalk.
        for _ in range(self.settle_discard_count):
            adc.read_u16()
            if self.settle_us > 0:
                time.sleep_us(self.settle_us)

        if self.oversample_count == 1:
            return adc.read_u16()

        buf = self._sample_buf
        for i in range(self.oversample_count):
            buf[i] = adc.read_u16()
        buf.sort()

        lo = self.trim_count
        hi = self.oversample_count - self.trim_count
        if hi <= lo:
            return buf[self.oversample_count // 2]

        total = 0
        count = 0
        for i in range(lo, hi):
            total += buf[i]
            count += 1
        return total / count

    def read_all_volts(self):
        readings = []
        for name, adc, gain, offset_v in self.channels:
            raw = self._read_filtered_raw(adc)
            v = (raw * self._v_per_count)
            v = (v * gain) + offset_v
            if v < 0.0:
                v = 0.0
            elif v > self.vref:
                v = self.vref
            readings.append((name, v))
        return readings

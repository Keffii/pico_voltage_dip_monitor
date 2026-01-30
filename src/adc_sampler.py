# adc_sampler.py

from machine import ADC

class AdcSampler:
    def __init__(self, channel_pins, vref):
        self.vref = vref
        self.channels = []
        for name, gp in channel_pins:
            self.channels.append((name, ADC(gp)))

    def read_all_volts(self):
        readings = []
        for name, adc in self.channels:
            raw = adc.read_u16()
            v = (raw / 65535.0) * self.vref
            readings.append((name, v))
        return readings
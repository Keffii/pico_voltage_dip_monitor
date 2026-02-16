# oled_ui.py

import time
import config
from machine import Pin, SPI
from lib.drivers.ssd1351.ssd1351_16bit import SSD1351

def rgb565(r, g, b):
    # Panel has green/blue swapped
    return ((r & 0xF8) << 8) | ((b & 0xFC) << 3) | (g >> 3)

BLACK  = rgb565(0, 0, 0)
RED    = rgb565(255, 0, 0)
BLUE   = rgb565(0, 0, 255)
YELLOW = rgb565(255, 255, 0)
GREEN  = rgb565(0, 255, 0)
DIMTXT = rgb565(140, 140, 140)

class OledUI:
    def __init__(self):
        self.W = 128
        self.H = 96

        self.HUD_H = 24
        self.PLOT_H = self.H - self.HUD_H
        self.PLOT_W = self.W

        self.V_MIN = float(config.UI_V_MIN)
        self.V_MAX = float(config.UI_V_MAX)

        self.no_dip_ms = int(getattr(config, "UI_NO_DIP_MS", 1500))
        self.negative_dip = bool(getattr(config, "UI_DIP_NEGATIVE", True))
        self.start_ms = time.ticks_ms()

        spi = SPI(config.OLED_SPI_ID, baudrate=10_000_000, polarity=0, phase=0,
                  sck=Pin(config.OLED_SCK), mosi=Pin(config.OLED_MOSI), miso=None)
        cs  = Pin(config.OLED_CS, Pin.OUT, value=1)
        dc  = Pin(config.OLED_DC, Pin.OUT, value=0)
        rst = Pin(config.OLED_RST, Pin.OUT, value=1)

        rst.value(0); time.sleep_ms(50)
        rst.value(1); time.sleep_ms(50)

        self.oled = SSD1351(spi, cs, dc, rst, width=self.W, height=self.H)
        self.oled.fill(BLACK)
        self.oled.show()

        self.colors = {"PLC": BLUE, "MODEM": YELLOW, "BATTERY": GREEN}
        self.labels = {"PLC": "B:", "MODEM": "Y:", "BATTERY": "G:"}

        self.x = 0
        self.prev_y = {"PLC": None, "MODEM": None, "BATTERY": None}
        self.graph_full = False
        self.y_hist = {"PLC": [], "MODEM": [], "BATTERY": []}

        # Latched dips in REAL volts (negative if enabled)
        self.latched_dip = {"PLC": None, "MODEM": None, "BATTERY": None}

    def _scale(self, channel, v_adc):
        return v_adc * config.CHANNEL_SCALE.get(channel, 1.0)

    def _clamp(self, v, lo, hi):
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v

    def _v_to_y(self, v_real):
        v = self._clamp(v_real, self.V_MIN, self.V_MAX)
        v01 = (v - self.V_MIN) / (self.V_MAX - self.V_MIN)
        return (self.PLOT_H - 1) - int(v01 * (self.PLOT_H - 1))

    def _allow_dips(self):
        return time.ticks_diff(time.ticks_ms(), self.start_ms) >= self.no_dip_ms

    def _clear_hud(self):
        self.oled.fill_rect(0, self.H - self.HUD_H, self.W, self.HUD_H, BLACK)

    def _fmt_v(self, v_real):
        # No trailing "V"
        return "{:>4.1f}".format(v_real)

    def _fmt_dip(self, d_real):
        if d_real is None:
            return "-----"
        return "{:>5.2f}".format(d_real)

    def latch_dip_drop_adc(self, channel, drop_adc_v):
        drop_real = drop_adc_v * config.CHANNEL_SCALE.get(channel, 1.0)
        self.latched_dip[channel] = (-drop_real) if self.negative_dip else drop_real

    def _draw_row(self, y, channel, v_real):
        col = self.colors[channel]
        lbl = self.labels[channel]
        dip = self.latched_dip[channel] if self._allow_dips() else None

        self.oled.text(lbl, 0, y, col)
        self.oled.text(self._fmt_v(v_real), 16, y, col)
        self.oled.text("DIP:", 56, y, col)
        self.oled.text(self._fmt_dip(dip), 88, y, RED if dip is not None else DIMTXT)

    def draw_hud(self, plc_real, modem_real, bat_real):
        self._clear_hud()
        y0 = self.H - self.HUD_H
        self._draw_row(y0 + 0,  "PLC", plc_real)
        self._draw_row(y0 + 8,  "MODEM", modem_real)
        self._draw_row(y0 + 16, "BATTERY", bat_real)

    def _append_hist(self, vals_y):
        for ch, y in vals_y.items():
            h = self.y_hist[ch]
            h.append(y)
            if len(h) > self.PLOT_W:
                h.pop(0)

    def _redraw_plot_from_hist(self):
        self.oled.fill_rect(0, 0, self.W, self.PLOT_H, BLACK)
        for ch in ("PLC", "MODEM", "BATTERY"):
            hist = self.y_hist[ch]
            col = self.colors[ch]
            n = len(hist)
            if n == 0:
                continue
            self.oled.pixel(0, hist[0], col)
            for x in range(1, n):
                self.oled.line(x - 1, hist[x - 1], x, hist[x], col)

    def _scroll_left_and_draw_right(self, vals_y):
        # Prefer framebuffer scroll for smooth strip-chart motion.
        if hasattr(self.oled, "scroll"):
            self.oled.scroll(-1, 0)
            xr = self.PLOT_W - 1
            self.oled.vline(xr, 0, self.PLOT_H, BLACK)
            for ch, y in vals_y.items():
                col = self.colors[ch]
                hist = self.y_hist[ch]
                py = hist[-2] if len(hist) >= 2 else None
                if py is None:
                    self.oled.pixel(xr, y, col)
                else:
                    self.oled.line(xr - 1, py, xr, y, col)
                self.prev_y[ch] = y
            return

        # Fallback path if scroll() is unavailable on this driver.
        self._redraw_plot_from_hist()
        for ch, y in vals_y.items():
            self.prev_y[ch] = y

    def plot_medians_adc(self, plc_adc, modem_adc, bat_adc):
        plc_real = self._scale("PLC", plc_adc)
        modem_real = self._scale("MODEM", modem_adc)
        bat_real = self._scale("BATTERY", bat_adc)

        vals = {"PLC": plc_real, "MODEM": modem_real, "BATTERY": bat_real}
        vals_y = {ch: self._v_to_y(v) for ch, v in vals.items()}
        self._append_hist(vals_y)

        if not self.graph_full:
            self.oled.vline(self.x, 0, self.PLOT_H, BLACK)
            for ch, y in vals_y.items():
                py = self.prev_y[ch]
                col = self.colors[ch]
                if py is None or self.x == 0:
                    self.oled.pixel(self.x, y, col)
                else:
                    self.oled.line(self.x - 1, py, self.x, y, col)
                self.prev_y[ch] = y
            self.x += 1
            if self.x >= self.PLOT_W:
                self.graph_full = True
                self.x = self.PLOT_W - 1
        else:
            self._scroll_left_and_draw_right(vals_y)

        self.draw_hud(plc_real, modem_real, bat_real)
        self.oled.show()

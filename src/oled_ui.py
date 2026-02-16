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
        self.auto_zoom = bool(getattr(config, "UI_AUTO_ZOOM", True))
        self.auto_window = int(getattr(config, "UI_AUTO_WINDOW", self.PLOT_W))
        self.auto_min_span_v = float(getattr(config, "UI_AUTO_MIN_SPAN_V", 1.0))
        self.auto_pad_frac = float(getattr(config, "UI_AUTO_PAD_FRAC", 0.20))
        self.auto_range_alpha = float(getattr(config, "UI_AUTO_RANGE_ALPHA", 0.35))
        self.auto_range_update_every = int(getattr(config, "UI_AUTO_RANGE_UPDATE_EVERY", 4))
        self.auto_range_epsilon_v = float(getattr(config, "UI_AUTO_RANGE_EPSILON_V", 0.03))
        self.plot_top_pad_px = int(getattr(config, "UI_PLOT_TOP_PAD_PX", 1))
        self.plot_bottom_pad_px = int(getattr(config, "UI_PLOT_BOTTOM_PAD_PX", 2))

        if self.auto_window < 4:
            self.auto_window = 4
        if self.auto_window > self.PLOT_W:
            self.auto_window = self.PLOT_W
        if self.auto_min_span_v <= 0:
            self.auto_min_span_v = 1.0
        if self.auto_pad_frac < 0:
            self.auto_pad_frac = 0.0
        if self.auto_range_alpha <= 0 or self.auto_range_alpha > 1.0:
            self.auto_range_alpha = 0.35
        if self.auto_range_update_every < 1:
            self.auto_range_update_every = 1
        if self.auto_range_epsilon_v < 0:
            self.auto_range_epsilon_v = 0.0
        if self.plot_top_pad_px < 0:
            self.plot_top_pad_px = 0
        if self.plot_bottom_pad_px < 0:
            self.plot_bottom_pad_px = 0
        if (self.plot_top_pad_px + self.plot_bottom_pad_px) >= (self.PLOT_H - 1):
            self.plot_top_pad_px = 0
            self.plot_bottom_pad_px = 0

        self.range_v_min = self.V_MIN
        self.range_v_max = self.V_MAX

        self.no_dip_ms = int(getattr(config, "UI_NO_DIP_MS", 1500))
        self.negative_dip = bool(getattr(config, "UI_DIP_NEGATIVE", True))
        self.start_ms = time.ticks_ms()
        self.frame_count = 0
        self.view_mode = str(getattr(config, "UI_STATS_DEFAULT_VIEW", "GRAPH")).upper()
        if self.view_mode not in ("GRAPH", "STATS"):
            self.view_mode = "GRAPH"
        self._force_graph_redraw = False

        spi = SPI(config.OLED_SPI_ID, baudrate=10_000_000, polarity=0, phase=0,
                  sck=Pin(config.OLED_SCK), mosi=Pin(config.OLED_MOSI), miso=None)
        cs  = Pin(config.OLED_CS, Pin.OUT, value=1)
        dc  = Pin(config.OLED_DC, Pin.OUT, value=0)
        rst = Pin(config.OLED_RST, Pin.OUT, value=1)
        self._rst_pin = rst

        rst.value(0); time.sleep_ms(50)
        rst.value(1); time.sleep_ms(50)

        self.oled = SSD1351(spi, cs, dc, rst, width=self.W, height=self.H)
        self.oled.fill(BLACK)
        self.oled.show()

        self.colors = {"PLC": BLUE, "MODEM": YELLOW, "BATTERY": GREEN}
        self.labels = {"PLC": "B:", "MODEM": "Y:", "BATTERY": "G:"}
        self.badge_tokens = {"PLC": "B", "MODEM": "Y", "BATTERY": "G"}

        self.x = 0
        self.graph_full = False
        self.prev_y = {"PLC": None, "MODEM": None, "BATTERY": None}
        self.v_hist = {"PLC": [], "MODEM": [], "BATTERY": []}

        # Latched dips in REAL volts (negative if enabled)
        self.latched_dip = {"PLC": None, "MODEM": None, "BATTERY": None}

        # Global MIN DIP badge (event-driven update, lightweight draw)
        self.min_dip_enabled = bool(getattr(config, "UI_MIN_DIP_ENABLED", True))
        self.min_dip_x = int(getattr(config, "UI_MIN_DIP_X", 0))
        self.min_dip_y = int(getattr(config, "UI_MIN_DIP_Y", self.PLOT_H - 8))
        self.min_dip_w = int(getattr(config, "UI_MIN_DIP_W", 60))
        self.min_dip_h = int(getattr(config, "UI_MIN_DIP_H", 8))
        self.min_dip_show_channel = bool(getattr(config, "UI_MIN_DIP_SHOW_CHANNEL", True))
        self.min_dip_reset_on_start = bool(getattr(config, "UI_MIN_DIP_RESET_ON_START", True))
        self.min_dip_eps_v = float(getattr(config, "UI_MIN_DIP_EPS_V", 0.01))
        if self.min_dip_x < 0:
            self.min_dip_x = 0
        if self.min_dip_y < 0:
            self.min_dip_y = 0
        if self.min_dip_w <= 0:
            self.min_dip_w = 1
        if self.min_dip_h <= 0:
            self.min_dip_h = 1
        if self.min_dip_eps_v < 0:
            self.min_dip_eps_v = 0.0
        if (self.min_dip_x + self.min_dip_w) > self.PLOT_W:
            self.min_dip_w = self.PLOT_W - self.min_dip_x
        if (self.min_dip_y + self.min_dip_h) > self.PLOT_H:
            self.min_dip_y = self.PLOT_H - self.min_dip_h
        if self.min_dip_w <= 0 or self.min_dip_h <= 0:
            self.min_dip_enabled = False

        self.min_drop_real_max = None
        self.min_drop_channel = None
        self.min_badge_text = "MIN ---"
        self.min_badge_draw_w = self.min_dip_w
        self.min_badge_prev_draw_w = self.min_dip_w
        if self.min_dip_reset_on_start:
            self.min_drop_real_max = None
            self.min_drop_channel = None
        self._rebuild_min_badge_text()

        # Stats view (latest dip events)
        self.stats_max_events = int(getattr(config, "UI_STATS_MAX_EVENTS", 6))
        if self.stats_max_events < 1:
            self.stats_max_events = 1
        if self.stats_max_events > 6:
            self.stats_max_events = 6
        self.dip_events = []
        self._stats_dirty = True

        # Toggle button
        self._btn_pin = None
        self._btn_active_low = bool(getattr(config, "UI_TOGGLE_ACTIVE_LOW", True))
        self._btn_debounce_ms = int(getattr(config, "UI_TOGGLE_DEBOUNCE_MS", 80))
        self._btn_raw_val = None
        self._btn_debounced_val = None
        self._btn_last_change_ms = 0

        btn_pin = getattr(config, "UI_TOGGLE_BTN_PIN", None)
        pull_cfg = getattr(config, "UI_TOGGLE_PULL", "UP")
        if btn_pin is not None:
            pull = Pin.PULL_UP if pull_cfg == "UP" else Pin.PULL_DOWN
            try:
                self._btn_pin = Pin(btn_pin, Pin.IN, pull)
                v = self._btn_pin.value()
                self._btn_raw_val = v
                self._btn_debounced_val = v
            except Exception:
                self._btn_pin = None

    def _scale(self, channel, v_adc):
        return v_adc * config.CHANNEL_SCALE.get(channel, 1.0)

    def _clamp(self, v, lo, hi):
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v

    def _v_to_y(self, v_real):
        v = self._clamp(v_real, self.range_v_min, self.range_v_max)
        span = self.range_v_max - self.range_v_min
        if span <= 0:
            span = 1.0

        top = self.plot_top_pad_px
        bottom = self.PLOT_H - 1 - self.plot_bottom_pad_px
        if bottom <= top:
            top = 0
            bottom = self.PLOT_H - 1

        v01 = (v - self.range_v_min) / span
        return bottom - int(v01 * (bottom - top))

    def _allow_dips(self):
        return time.ticks_diff(time.ticks_ms(), self.start_ms) >= self.no_dip_ms

    def _poll_toggle_button(self):
        if self._btn_pin is None:
            return

        try:
            val = self._btn_pin.value()
        except Exception:
            return

        now_ms = time.ticks_ms()
        if self._btn_raw_val is None:
            self._btn_raw_val = val
            self._btn_debounced_val = val
            self._btn_last_change_ms = now_ms
            return

        if val != self._btn_raw_val:
            self._btn_raw_val = val
            self._btn_last_change_ms = now_ms
            return

        if time.ticks_diff(now_ms, self._btn_last_change_ms) < self._btn_debounce_ms:
            return

        if self._btn_debounced_val == val:
            return

        self._btn_debounced_val = val
        pressed = (val == 0) if self._btn_active_low else (val == 1)
        if pressed:
            if self.view_mode == "GRAPH":
                self.view_mode = "STATS"
                self._stats_dirty = True
            else:
                self.view_mode = "GRAPH"
                self._force_graph_redraw = True

    def _clear_hud(self):
        self.oled.fill_rect(0, self.H - self.HUD_H, self.W, self.HUD_H, BLACK)

    def _fmt_v(self, v_real):
        # No trailing "V"
        return "{:>4.1f}".format(v_real)

    def _fmt_dip(self, d_real):
        if d_real is None:
            return "-----"
        return "{:>5.2f}".format(d_real)

    def _text_w(self, txt):
        # Built-in MicroPython bitmap font is 8px wide per char.
        return len(txt) * 8

    def _rebuild_min_badge_text(self):
        if self.min_drop_real_max is None:
            self.min_badge_text = "MIN ---"
        else:
            val = -self.min_drop_real_max if self.negative_dip else self.min_drop_real_max
            if self.min_dip_show_channel:
                token = self.badge_tokens.get(self.min_drop_channel, "?")
                self.min_badge_text = "MIN {}:{:.2f}".format(token, val)
            else:
                self.min_badge_text = "MIN:{:.2f}".format(val)

        text_w = self._text_w(self.min_badge_text)
        draw_w = self.min_dip_w
        if text_w > draw_w and (self.min_dip_x + text_w) <= self.PLOT_W:
            draw_w = text_w
        if (self.min_dip_x + draw_w) > self.PLOT_W:
            draw_w = self.PLOT_W - self.min_dip_x
        if draw_w <= 0:
            draw_w = 1
        self.min_badge_draw_w = draw_w

    def _draw_min_badge(self):
        if not self.min_dip_enabled:
            return

        clear_w = self.min_badge_draw_w
        if self.min_badge_prev_draw_w > clear_w:
            clear_w = self.min_badge_prev_draw_w
        if (self.min_dip_x + clear_w) > self.PLOT_W:
            clear_w = self.PLOT_W - self.min_dip_x
        if clear_w <= 0:
            return

        self.oled.fill_rect(self.min_dip_x, self.min_dip_y, clear_w, self.min_dip_h, BLACK)
        col = RED if self.min_drop_real_max is not None else DIMTXT
        self.oled.text(self.min_badge_text, self.min_dip_x, self.min_dip_y, col)
        self.min_badge_prev_draw_w = self.min_badge_draw_w

    def _draw_stats(self):
        self.oled.fill(BLACK)
        placeholder = "-- ---- ---V --%"
        n = self.stats_max_events
        for i in range(n):
            y = i * 8
            if i < len(self.dip_events):
                ev = self.dip_events[i]
                token = self.badge_tokens.get(ev["channel"], "?")
                base_txt = "{:>4.1f}".format(ev["baseline"])
                if len(base_txt) > 4:
                    base_txt = "{:>4.0f}".format(ev["baseline"])
                drop_txt = "{:>4.1f}".format(ev["drop"])
                if len(drop_txt) > 4:
                    drop_txt = "{:>4.0f}".format(ev["drop"])
                pct = ev["pct"]
                if pct < 0:
                    pct = -pct
                if pct > 99:
                    pct = 99
                pct_txt = "{:>2.0f}".format(pct)
                line = "{} {} {}V {}%".format(token, base_txt, drop_txt, pct_txt)
                col = self.colors.get(ev["channel"], DIMTXT)
            else:
                line = placeholder
                col = DIMTXT
            self.oled.text(line, 0, y, col)

    def shutdown(self):
        try:
            self.oled.fill(BLACK)
            self.oled.show()
        except Exception:
            pass

        if (
            self._call_if_present("poweroff")
            or self._call_if_present("power_off")
            or self._call_if_present("display_off")
            or self._call_if_present("displayoff")
            or self._call_if_present("sleep", True)
            or self._call_if_present("sleep_mode", True)
        ):
            return

        if self._rst_pin is not None:
            try:
                self._rst_pin.value(0)
            except Exception:
                pass

    def _call_if_present(self, name, *args):
        fn = getattr(self.oled, name, None)
        if fn is None:
            return False
        try:
            fn(*args)
        except TypeError:
            try:
                fn()
            except Exception:
                return False
        except Exception:
            return False
        return True

    def latch_dip_drop_adc(self, channel, drop_adc_v):
        drop_real = drop_adc_v * config.CHANNEL_SCALE.get(channel, 1.0)
        self.latched_dip[channel] = (-drop_real) if self.negative_dip else drop_real

        if not self.min_dip_enabled:
            return

        if drop_real < 0:
            drop_real = -drop_real

        if self.min_drop_real_max is None or drop_real > (self.min_drop_real_max + self.min_dip_eps_v):
            self.min_drop_real_max = drop_real
            self.min_drop_channel = channel
            self._rebuild_min_badge_text()

    def record_dip_event_adc(self, channel, baseline_adc_v, min_adc_v, drop_adc_v):
        if baseline_adc_v is None or drop_adc_v is None:
            return
        scale = config.CHANNEL_SCALE.get(channel, 1.0)
        baseline_real = baseline_adc_v * scale
        drop_real = drop_adc_v * scale
        if drop_real < 0:
            drop_real = -drop_real
        drop_pct = (drop_real / baseline_real * 100.0) if baseline_real > 0 else 0.0
        drop_display = (-drop_real) if self.negative_dip else drop_real

        self.dip_events.insert(0, {
            "channel": channel,
            "baseline": baseline_real,
            "drop": drop_display,
            "pct": drop_pct,
        })
        if len(self.dip_events) > self.stats_max_events:
            self.dip_events = self.dip_events[:self.stats_max_events]
        self._stats_dirty = True

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

    def _append_hist(self, vals_real):
        for ch, v in vals_real.items():
            h = self.v_hist[ch]
            h.append(v)
            if len(h) > self.PLOT_W:
                h.pop(0)

    def _clamp_range(self, lo, hi):
        lo = self._clamp(lo, self.V_MIN, self.V_MAX)
        hi = self._clamp(hi, self.V_MIN, self.V_MAX)

        full_span = self.V_MAX - self.V_MIN
        min_span = self.auto_min_span_v if self.auto_min_span_v < full_span else full_span
        if min_span <= 0:
            min_span = full_span

        if (hi - lo) < min_span:
            mid = (lo + hi) * 0.5
            half = min_span * 0.5
            lo = mid - half
            hi = mid + half
            if lo < self.V_MIN:
                lo = self.V_MIN
                hi = lo + min_span
            if hi > self.V_MAX:
                hi = self.V_MAX
                lo = hi - min_span

        if hi <= lo:
            lo = self.V_MIN
            hi = self.V_MAX

        return lo, hi

    def _calc_target_range(self):
        if not self.auto_zoom:
            return self.V_MIN, self.V_MAX

        lo = None
        hi = None
        for ch in ("PLC", "MODEM", "BATTERY"):
            h = self.v_hist[ch]
            if not h:
                continue
            if len(h) > self.auto_window:
                w = h[-self.auto_window:]
            else:
                w = h
            ch_lo = min(w)
            ch_hi = max(w)
            if lo is None or ch_lo < lo:
                lo = ch_lo
            if hi is None or ch_hi > hi:
                hi = ch_hi

        if lo is None or hi is None:
            return self.V_MIN, self.V_MAX

        span = hi - lo
        if span < self.auto_min_span_v:
            mid = (lo + hi) * 0.5
            half = self.auto_min_span_v * 0.5
            lo = mid - half
            hi = mid + half
            span = hi - lo

        pad = span * self.auto_pad_frac
        return self._clamp_range(lo - pad, hi + pad)

    def _update_range(self):
        target_lo, target_hi = self._calc_target_range()
        if not self.auto_zoom:
            self.range_v_min = target_lo
            self.range_v_max = target_hi
            return

        a = self.auto_range_alpha
        lo = self.range_v_min + (target_lo - self.range_v_min) * a
        hi = self.range_v_max + (target_hi - self.range_v_max) * a
        self.range_v_min, self.range_v_max = self._clamp_range(lo, hi)

    def _redraw_plot_from_hist(self):
        self.oled.fill_rect(0, 0, self.W, self.PLOT_H, BLACK)
        for ch in ("PLC", "MODEM", "BATTERY"):
            hist = self.v_hist[ch]
            col = self.colors[ch]
            n = len(hist)
            if n == 0:
                continue
            y0 = self._v_to_y(hist[0])
            self.oled.pixel(0, y0, col)
            for x in range(1, n):
                y1 = self._v_to_y(hist[x])
                y2 = self._v_to_y(hist[x - 1])
                self.oled.line(x - 1, y2, x, y1, col)

        # Sync incremental state after a full redraw.
        n = len(self.v_hist["PLC"])
        self.graph_full = n >= self.PLOT_W
        self.x = (self.PLOT_W - 1) if self.graph_full else max(0, n - 1)
        for ch in ("PLC", "MODEM", "BATTERY"):
            hist = self.v_hist[ch]
            self.prev_y[ch] = self._v_to_y(hist[-1]) if hist else None

    def _scroll_left_and_draw_right(self, vals_real):
        if hasattr(self.oled, "scroll"):
            self.oled.scroll(-1, 0)
            xr = self.PLOT_W - 1
            self.oled.vline(xr, 0, self.PLOT_H, BLACK)
            for ch, v in vals_real.items():
                y = self._v_to_y(v)
                py = self.prev_y[ch]
                col = self.colors[ch]
                if py is None:
                    self.oled.pixel(xr, y, col)
                else:
                    self.oled.line(xr - 1, py, xr, y, col)
                self.prev_y[ch] = y
            return

        # Driver without scroll support: full redraw fallback.
        self._redraw_plot_from_hist()

    def _draw_incremental(self, vals_real):
        n = len(self.v_hist["PLC"])
        if n <= 0:
            return

        # Initial fill from left to right.
        if not self.graph_full:
            self.x = n - 1
            self.oled.vline(self.x, 0, self.PLOT_H, BLACK)
            for ch, v in vals_real.items():
                y = self._v_to_y(v)
                py = self.prev_y[ch]
                col = self.colors[ch]
                if py is None or self.x == 0:
                    self.oled.pixel(self.x, y, col)
                else:
                    self.oled.line(self.x - 1, py, self.x, y, col)
                self.prev_y[ch] = y

            if n >= self.PLOT_W:
                self.graph_full = True
                self.x = self.PLOT_W - 1
            return

        # Full width reached: strip-chart scrolling.
        self._scroll_left_and_draw_right(vals_real)

    def plot_medians_adc(self, plc_adc, modem_adc, bat_adc):
        self._poll_toggle_button()

        plc_real = self._scale("PLC", plc_adc)
        modem_real = self._scale("MODEM", modem_adc)
        bat_real = self._scale("BATTERY", bat_adc)

        vals = {"PLC": plc_real, "MODEM": modem_real, "BATTERY": bat_real}
        self._append_hist(vals)
        self.frame_count += 1

        range_changed = False
        if not self.auto_zoom:
            range_changed = (self.range_v_min != self.V_MIN) or (self.range_v_max != self.V_MAX)
            self.range_v_min = self.V_MIN
            self.range_v_max = self.V_MAX
        elif (self.frame_count % self.auto_range_update_every) == 0:
            old_lo = self.range_v_min
            old_hi = self.range_v_max
            self._update_range()
            range_changed = (
                abs(self.range_v_min - old_lo) >= self.auto_range_epsilon_v
                or abs(self.range_v_max - old_hi) >= self.auto_range_epsilon_v
            )
            if not range_changed:
                # Keep prior mapping so existing pixels remain consistent.
                self.range_v_min = old_lo
                self.range_v_max = old_hi

        if self.view_mode == "STATS":
            if self._stats_dirty:
                self._draw_stats()
                self.oled.show()
                self._stats_dirty = False
            return

        if self._force_graph_redraw:
            range_changed = True
            self._force_graph_redraw = False

        if range_changed:
            self._redraw_plot_from_hist()
        else:
            self._draw_incremental(vals)

        self.draw_hud(plc_real, modem_real, bat_real)
        self._draw_min_badge()
        self.oled.show()

# oled_ui.py

import time
import config
from machine import Pin, SPI
from lib.drivers.ssd1351.ssd1351 import SSD1351

try:
    import framebuf
except ImportError:
    framebuf = None

def rgb8(r, g, b):
    # Calibrated with test_oled_color_picker (RGB mapping).
    return SSD1351.rgb(r, g, b)

BLACK  = rgb8(0, 0, 0)
RED    = rgb8(255, 0, 0)
BLUE   = rgb8(0, 0, 255)
YELLOW = rgb8(255, 255, 0)
GREEN  = rgb8(0, 255, 0)
DIMTXT = rgb8(140, 140, 140)
WHITETXT = rgb8(235, 235, 235)

class OledUI:
    def __init__(self):
        self.W = 128
        self.H = 96

        self.HUD_H = int(getattr(config, "UI_HUD_H", 0))
        if self.HUD_H < 0:
            self.HUD_H = 0
        if self.HUD_H >= self.H:
            self.HUD_H = self.H - 1
        self.PLOT_H = self.H - self.HUD_H
        self.PLOT_W = self.W

        self.V_MIN = float(config.UI_V_MIN)
        self.V_MAX = float(config.UI_V_MAX)
        self.auto_zoom = bool(getattr(config, "UI_AUTO_ZOOM", True))
        self.auto_window = int(getattr(config, "UI_AUTO_WINDOW", self.PLOT_W))
        self.auto_min_span_v = float(getattr(config, "UI_AUTO_MIN_SPAN_V", 6.0))
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
        if self.auto_min_span_v < 6.0:
            self.auto_min_span_v = 6.0
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
        self.sample_counter = -1
        self.view_mode = str(getattr(config, "UI_STATS_DEFAULT_VIEW", "GRAPH")).upper()
        if self.view_mode not in ("GRAPH", "STATS"):
            self.view_mode = "GRAPH"
        self._force_graph_redraw = False

        spi = SPI(config.OLED_SPI_ID, baudrate=10_000_000, polarity=0, phase=0,
                  sck=Pin(config.OLED_SCK), mosi=Pin(config.OLED_MOSI), miso=None)
        cs  = Pin(config.OLED_CS, Pin.OUT, value=1)
        dc  = Pin(config.OLED_DC, Pin.OUT, value=0)
        rst = Pin(config.OLED_RST, Pin.OUT, value=1)
        self._spi = spi
        self._cs_pin = cs
        self._dc_pin = dc
        self._rst_pin = rst

        rst.value(0); time.sleep_ms(50)
        rst.value(1); time.sleep_ms(50)

        self.oled = SSD1351(spi, cs, dc, rst, width=self.W, height=self.H)
        self.oled.fill(BLACK)
        self.oled.show()

        self.colors = {"BLUE": BLUE, "YELLOW": YELLOW, "GREEN": GREEN}
        self.badge_tokens = {"BLUE": "B", "YELLOW": "Y", "GREEN": "G"}

        self.x = 0
        self.graph_full = False
        self.prev_y = {"BLUE": None, "YELLOW": None, "GREEN": None}
        self.v_hist = {"BLUE": [], "YELLOW": [], "GREEN": []}

        # Latched dips in REAL volts (negative if enabled)
        self.latched_dip = {"BLUE": None, "YELLOW": None, "GREEN": None}

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
        self.stats_double_height = bool(getattr(config, "UI_STATS_DOUBLE_HEIGHT", True))
        self.stats_bold = bool(getattr(config, "UI_STATS_BOLD", True))
        self.stats_active_blink_enabled = bool(getattr(config, "UI_STATS_ACTIVE_BLINK_ENABLED", True))
        self.stats_active_blink_ms = int(getattr(config, "UI_STATS_ACTIVE_BLINK_MS", 500))
        if self.stats_active_blink_ms < 100:
            self.stats_active_blink_ms = 100
        self._stats_blink_visible = True
        self.y_axis_enabled = bool(getattr(config, "UI_Y_AXIS_ENABLED", True))
        self.y_axis_strip_w = int(getattr(config, "UI_Y_AXIS_STRIP_W", 36))
        self.y_axis_decimals = int(getattr(config, "UI_Y_AXIS_DECIMALS", 1))
        self.y_axis_show_mid = bool(getattr(config, "UI_Y_AXIS_SHOW_MID", False))
        self.graph_legend_enabled = bool(getattr(config, "UI_GRAPH_LEGEND_ENABLED", True))
        self.graph_readouts_enabled = bool(getattr(config, "UI_GRAPH_READOUTS_ENABLED", True))
        self.graph_readout_decimals = int(getattr(config, "UI_GRAPH_READOUT_DECIMALS", 1))
        self.graph_readout_show_units = bool(getattr(config, "UI_GRAPH_READOUT_SHOW_UNITS", False))
        self.graph_readout_top_mode = str(getattr(config, "UI_GRAPH_READOUT_TOP_MODE", "LIVE_VISIBLE_MAX")).upper()
        self.graph_startup_span_v = float(getattr(config, "UI_GRAPH_STARTUP_SPAN_V", 6.0))
        self.graph_startup_hold_ms = int(getattr(config, "UI_GRAPH_STARTUP_HOLD_MS", 2000))
        self.graph_max_events = int(getattr(config, "UI_GRAPH_MAX_EVENTS", 24))
        self.graph_baseline_enabled = bool(getattr(config, "UI_GRAPH_BASELINE_ENABLED", True))
        self.graph_baseline_alpha_up = float(getattr(config, "UI_GRAPH_BASELINE_ALPHA_UP", 0.25))
        self.graph_baseline_alpha_down = float(getattr(config, "UI_GRAPH_BASELINE_ALPHA_DOWN", 0.03))
        self.graph_channel_filter = str(getattr(config, "UI_GRAPH_CHANNEL_FILTER", "ALL")).upper()
        if self.graph_startup_span_v <= 0:
            self.graph_startup_span_v = 6.0
        if self.graph_startup_hold_ms < 0:
            self.graph_startup_hold_ms = 0
        if self.graph_max_events < 1:
            self.graph_max_events = 1
        if self.graph_baseline_alpha_up <= 0 or self.graph_baseline_alpha_up > 1.0:
            self.graph_baseline_alpha_up = 0.25
        if self.graph_baseline_alpha_down <= 0 or self.graph_baseline_alpha_down > 1.0:
            self.graph_baseline_alpha_down = 0.03
        if self.graph_channel_filter not in ("ALL", "BLUE", "YELLOW", "GREEN"):
            self.graph_channel_filter = "ALL"
        self.graph_startup_anchor_v = None
        self.graph_baseline_v = None
        self.auto_zoomout_hold_screens = int(getattr(config, "UI_AUTO_ZOOMOUT_HOLD_SCREENS", 3))
        if self.auto_zoomout_hold_screens < 0:
            self.auto_zoomout_hold_screens = 0
        self.auto_zoomout_hold_samples = self.auto_zoomout_hold_screens * self.PLOT_W
        self.auto_zoomout_hold_until_sample = -1
        self.auto_zoomin_cooldown_screens = int(getattr(config, "UI_AUTO_ZOOMIN_COOLDOWN_SCREENS", 1))
        if self.auto_zoomin_cooldown_screens < 0:
            self.auto_zoomin_cooldown_screens = 0
        self.auto_zoomin_cooldown_samples = self.auto_zoomin_cooldown_screens * self.PLOT_W
        self.auto_zoomin_cooldown_until_sample = -1
        self.auto_range_max_step_v = float(getattr(config, "UI_AUTO_RANGE_MAX_STEP_V", 0.20))
        if self.auto_range_max_step_v <= 0:
            self.auto_range_max_step_v = 0.20
        self.dip_callouts_enabled = bool(getattr(config, "UI_DIP_CALLOUTS_ENABLED", True))
        self.dip_callout_include_active = bool(getattr(config, "UI_DIP_CALLOUT_INCLUDE_ACTIVE", False))
        self.dip_callout_scope = str(getattr(config, "UI_DIP_CALLOUT_SCOPE", "LATEST_PER_CHANNEL")).upper()
        self.dip_label_overlap_mode = str(getattr(config, "UI_DIP_LABEL_OVERLAP_MODE", "PRIORITY_SKIP")).upper()
        self.dip_label_priority = str(getattr(config, "UI_DIP_LABEL_PRIORITY", "LARGEST_DROP")).upper()
        if self.dip_callout_scope not in ("LATEST_PER_CHANNEL", "ALL_FINISHED_IN_WINDOW"):
            self.dip_callout_scope = "LATEST_PER_CHANNEL"
        if self.dip_label_overlap_mode not in ("DRAW_ALL", "PRIORITY_SKIP"):
            self.dip_label_overlap_mode = "PRIORITY_SKIP"
        if self.dip_label_priority not in ("LARGEST_DROP", "NEWEST"):
            self.dip_label_priority = "LARGEST_DROP"
        if self.y_axis_strip_w < 1:
            self.y_axis_strip_w = 1
        if self.y_axis_strip_w >= self.PLOT_W:
            self.y_axis_strip_w = self.PLOT_W - 1
        if self.y_axis_decimals < 0:
            self.y_axis_decimals = 0
        if self.y_axis_decimals > 1:
            self.y_axis_decimals = 1
        if self.graph_readout_decimals < 0:
            self.graph_readout_decimals = 0
        if self.graph_readout_decimals > 1:
            self.graph_readout_decimals = 1
        if self.graph_readout_top_mode not in ("LIVE_VISIBLE_MAX", "RANGE_MAX"):
            self.graph_readout_top_mode = "LIVE_VISIBLE_MAX"
        self.graph_event_markers_enabled = bool(getattr(config, "UI_GRAPH_EVENT_MARKERS_ENABLED", True))
        self.graph_event_marker_active_hollow = bool(getattr(config, "UI_GRAPH_EVENT_MARKER_ACTIVE_HOLLOW", True))
        self.graph_event_marker_active_force_min_size = bool(getattr(config, "UI_GRAPH_EVENT_MARKER_ACTIVE_FORCE_MIN_SIZE", True))
        self.graph_event_marker_y = int(getattr(config, "UI_GRAPH_EVENT_MARKER_Y", 0))
        self.graph_event_marker_h = int(getattr(config, "UI_GRAPH_EVENT_MARKER_H", 3))
        self.graph_event_marker_w = int(getattr(config, "UI_GRAPH_EVENT_MARKER_W", 3))
        if self.graph_event_marker_y < 0:
            self.graph_event_marker_y = 0
        if self.graph_event_marker_h < 1:
            self.graph_event_marker_h = 1
        if self.graph_event_marker_w < 1:
            self.graph_event_marker_w = 1
        if self.graph_event_marker_y >= self.PLOT_H:
            self.graph_event_marker_y = self.PLOT_H - 1
        if (self.graph_event_marker_y + self.graph_event_marker_h) > self.PLOT_H:
            self.graph_event_marker_h = self.PLOT_H - self.graph_event_marker_y
            if self.graph_event_marker_h < 1:
                self.graph_event_marker_h = 1
        self.dip_events = []
        self._stats_dirty = True

        self.help_overlay_enabled = bool(getattr(config, "UI_HELP_OVERLAY_ENABLED", True))
        self.help_longpress_ms = int(getattr(config, "UI_HELP_LONGPRESS_MS", 2000))
        self.help_show_in_stats = bool(getattr(config, "UI_HELP_SHOW_IN_STATS", True))
        if self.help_longpress_ms < 300:
            self.help_longpress_ms = 300
        self._help_overlay_was_visible = False
        self._channel_badge_ms = int(getattr(config, "UI_CHANNEL_BADGE_MS", 1000))
        if self._channel_badge_ms < 0:
            self._channel_badge_ms = 0
        self._channel_badge_until_ms = -1
        self._channel_badge_was_visible = False

        # Toggle button (tap to switch Graph/Stats)
        self._btn_pin = None
        self._btn_active_low = bool(getattr(config, "UI_TOGGLE_ACTIVE_LOW", True))
        self._btn_debounce_ms = int(getattr(config, "UI_TOGGLE_DEBOUNCE_MS", 80))
        self._btn_raw_val = None
        self._btn_debounced_val = None
        self._btn_last_change_ms = 0
        self._btn_pressed = False

        btn_pin = getattr(config, "UI_TOGGLE_BTN_PIN", None)
        pull_cfg = getattr(config, "UI_TOGGLE_PULL", "UP")
        if btn_pin is not None:
            pull = Pin.PULL_UP if pull_cfg == "UP" else Pin.PULL_DOWN
            try:
                self._btn_pin = Pin(btn_pin, Pin.IN, pull)
                v = self._btn_pin.value()
                self._btn_raw_val = v
                self._btn_debounced_val = v
                # Ignore startup level and wait for a fresh press/release tap.
                self._btn_pressed = False
            except Exception:
                self._btn_pin = None

        # Dedicated HELP button (show help while held)
        self._help_btn_pin = None
        self._help_btn_active_low = bool(getattr(config, "UI_HELP_BTN_ACTIVE_LOW", True))
        self._help_btn_debounce_ms = int(getattr(config, "UI_HELP_BTN_DEBOUNCE_MS", 30))
        if self._help_btn_debounce_ms < 0:
            self._help_btn_debounce_ms = 0
        self._help_btn_raw_val = None
        self._help_btn_debounced_val = None
        self._help_btn_last_change_ms = 0
        self._help_btn_pressed = False

        help_btn_pin = getattr(config, "UI_HELP_BTN_PIN", None)
        help_pull_cfg = getattr(config, "UI_HELP_BTN_PULL", "UP")
        if help_btn_pin is not None:
            help_pull = Pin.PULL_UP if help_pull_cfg == "UP" else Pin.PULL_DOWN
            try:
                self._help_btn_pin = Pin(help_btn_pin, Pin.IN, help_pull)
                v = self._help_btn_pin.value()
                self._help_btn_raw_val = v
                self._help_btn_debounced_val = v
                self._help_btn_pressed = (v == 0) if self._help_btn_active_low else (v == 1)
            except Exception:
                self._help_btn_pin = None

        # Dedicated channel-select button (tap to cycle visible channels)
        self._ch_btn_pin = None
        self._ch_btn_active_low = bool(getattr(config, "UI_CHANNEL_BTN_ACTIVE_LOW", True))
        self._ch_btn_debounce_ms = int(getattr(config, "UI_CHANNEL_BTN_DEBOUNCE_MS", 30))
        if self._ch_btn_debounce_ms < 0:
            self._ch_btn_debounce_ms = 0
        self._ch_btn_raw_val = None
        self._ch_btn_debounced_val = None
        self._ch_btn_last_change_ms = 0
        self._ch_btn_pressed = False
        self._channel_filter_order = ("ALL", "BLUE", "YELLOW", "GREEN")

        ch_btn_pin = getattr(config, "UI_CHANNEL_BTN_PIN", None)
        ch_pull_cfg = getattr(config, "UI_CHANNEL_BTN_PULL", "UP")
        if ch_btn_pin is not None:
            ch_pull = Pin.PULL_UP if ch_pull_cfg == "UP" else Pin.PULL_DOWN
            try:
                self._ch_btn_pin = Pin(ch_btn_pin, Pin.IN, ch_pull)
                v = self._ch_btn_pin.value()
                self._ch_btn_raw_val = v
                self._ch_btn_debounced_val = v
                # Ignore startup level and wait for a fresh press/release tap.
                self._ch_btn_pressed = False
            except Exception:
                self._ch_btn_pin = None

    def _scale(self, channel, v_adc):
        return self._graph_real(channel, v_adc)

    def _graph_gain(self, channel):
        gain = config.CHANNEL_SCALE.get(channel, 1.0)
        gain_map = getattr(config, "UI_GRAPH_REAL_GAIN", None)
        if isinstance(gain_map, dict) and (channel in gain_map):
            gain = gain_map[channel]
        try:
            gain = float(gain)
        except Exception:
            gain = float(config.CHANNEL_SCALE.get(channel, 1.0))
        if gain <= 0:
            gain = float(config.CHANNEL_SCALE.get(channel, 1.0))
        if gain <= 0:
            gain = 1.0
        return gain

    def _graph_offset(self, channel):
        offset = 0.0
        offset_map = getattr(config, "UI_GRAPH_REAL_OFFSET_V", None)
        if isinstance(offset_map, dict) and (channel in offset_map):
            offset = offset_map[channel]
        try:
            return float(offset)
        except Exception:
            return 0.0

    def _graph_real(self, channel, v_adc):
        gain = self._graph_gain(channel)
        offset = self._graph_offset(channel)
        v_real = (v_adc * gain) + offset
        clamp_min = float(getattr(config, "UI_GRAPH_REAL_CLAMP_MIN_V", self.V_MIN))
        clamp_max = float(getattr(config, "UI_GRAPH_REAL_CLAMP_MAX_V", self.V_MAX))
        if clamp_max <= clamp_min:
            clamp_min = self.V_MIN
            clamp_max = self.V_MAX
        return self._clamp(v_real, clamp_min, clamp_max)

    def _clamp(self, v, lo, hi):
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v

    def _iter_plot_channels(self):
        if self.graph_channel_filter in ("BLUE", "YELLOW", "GREEN"):
            return (self.graph_channel_filter,)
        return ("BLUE", "YELLOW", "GREEN")

    def _channel_filter_allows(self, channel):
        if self.graph_channel_filter == "ALL":
            return True
        return channel == self.graph_channel_filter

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
            self._btn_pressed = False
            return

        if val != self._btn_raw_val:
            self._btn_raw_val = val
            self._btn_last_change_ms = now_ms
        elif time.ticks_diff(now_ms, self._btn_last_change_ms) >= self._btn_debounce_ms:
            if self._btn_debounced_val != val:
                self._btn_debounced_val = val
                pressed = (val == 0) if self._btn_active_low else (val == 1)
                if pressed:
                    self._btn_pressed = True
                else:
                    if self._btn_pressed:
                        if self.view_mode == "GRAPH":
                            self.view_mode = "STATS"
                            self._stats_dirty = True
                        else:
                            self.view_mode = "GRAPH"
                            self._force_graph_redraw = True
                    self._btn_pressed = False

    def _poll_help_button(self):
        if self._help_btn_pin is None:
            self._help_btn_pressed = False
            return

        try:
            val = self._help_btn_pin.value()
        except Exception:
            return

        now_ms = time.ticks_ms()
        if self._help_btn_raw_val is None:
            self._help_btn_raw_val = val
            self._help_btn_debounced_val = val
            self._help_btn_last_change_ms = now_ms
            self._help_btn_pressed = (val == 0) if self._help_btn_active_low else (val == 1)
            return

        if val != self._help_btn_raw_val:
            self._help_btn_raw_val = val
            self._help_btn_last_change_ms = now_ms
        elif time.ticks_diff(now_ms, self._help_btn_last_change_ms) >= self._help_btn_debounce_ms:
            if self._help_btn_debounced_val != val:
                self._help_btn_debounced_val = val
                self._help_btn_pressed = (val == 0) if self._help_btn_active_low else (val == 1)

    def _poll_channel_button(self):
        if self._ch_btn_pin is None:
            return

        try:
            val = self._ch_btn_pin.value()
        except Exception:
            return

        now_ms = time.ticks_ms()
        if self._ch_btn_raw_val is None:
            self._ch_btn_raw_val = val
            self._ch_btn_debounced_val = val
            self._ch_btn_last_change_ms = now_ms
            self._ch_btn_pressed = False
            return

        if val != self._ch_btn_raw_val:
            self._ch_btn_raw_val = val
            self._ch_btn_last_change_ms = now_ms
        elif time.ticks_diff(now_ms, self._ch_btn_last_change_ms) >= self._ch_btn_debounce_ms:
            if self._ch_btn_debounced_val != val:
                self._ch_btn_debounced_val = val
                pressed = (val == 0) if self._ch_btn_active_low else (val == 1)
                if pressed:
                    self._ch_btn_pressed = True
                else:
                    if self._ch_btn_pressed:
                        self._cycle_channel_filter()
                    self._ch_btn_pressed = False

    def _cycle_channel_filter(self):
        order = self._channel_filter_order
        current = self.graph_channel_filter
        try:
            idx = order.index(current)
        except ValueError:
            idx = 0
        self.graph_channel_filter = order[(idx + 1) % len(order)]
        self._force_graph_redraw = True
        self._stats_dirty = True
        if self._channel_badge_ms > 0:
            self._channel_badge_until_ms = time.ticks_add(time.ticks_ms(), self._channel_badge_ms)
        else:
            self._channel_badge_until_ms = -1

    def _channel_badge_is_visible(self):
        if self._channel_badge_until_ms < 0:
            return False
        return time.ticks_diff(self._channel_badge_until_ms, time.ticks_ms()) > 0

    def _draw_channel_mode_badge(self):
        if not self._channel_badge_is_visible():
            return

        token = "ALL"
        if self.graph_channel_filter == "BLUE":
            token = "B"
        elif self.graph_channel_filter == "YELLOW":
            token = "Y"
        elif self.graph_channel_filter == "GREEN":
            token = "G"
        txt = "CH:{}".format(token)

        text_w = len(txt) * 8
        if text_w < 8:
            text_w = 8
        x = self.PLOT_W - text_w
        if x < 0:
            x = 0
        y = self.PLOT_H - 8
        if y < 0:
            y = 0

        color = WHITETXT
        if self.graph_channel_filter in self.colors:
            color = self.colors[self.graph_channel_filter]
        self.oled.fill_rect(x, y, text_w, 8, BLACK)
        self.oled.text(txt, x, y, color)

    def _help_overlay_should_draw(self):
        if not self.help_overlay_enabled:
            return False
        if not self._help_btn_pressed:
            return False
        if self.view_mode == "STATS" and not self.help_show_in_stats:
            return False
        return True

    def _draw_help_overlay(self):
        self.oled.fill(BLACK)

        lines = (
            ("HELP", 8),
            ("Tap: Graph/Stats", 24),
            ("Hold HELP: Show", 36),
            ("Release HELP: Back", 48),
        )
        for txt, y in lines:
            x = (self.W - self._text_w(txt)) // 2
            if x < 0:
                x = 0
            self.oled.text(txt, x, y, WHITETXT)

        self.oled.text("B", 0, 64, self.colors["BLUE"])
        self.oled.text("=BLUE", 8, 64, WHITETXT)
        self.oled.text("Y", 48, 64, self.colors["YELLOW"])
        self.oled.text("=YELLOW", 56, 64, WHITETXT)
        self.oled.text("G", 0, 76, self.colors["GREEN"])
        self.oled.text("=GREEN", 8, 76, WHITETXT)

    def _text_w(self, txt):
        # Built-in MicroPython bitmap font is 8px wide per char.
        return len(txt) * 8

    def _fmt_stats_stable(self, v_real):
        txt = "{:.1f}V".format(v_real)
        if len(txt) > 6:
            txt = "{:.0f}V".format(v_real)
        return txt

    def _fmt_stats_drop(self, drop_real):
        d = drop_real if drop_real >= 0 else -drop_real
        txt = "-{:.1f}V".format(d)
        if len(txt) > 7:
            txt = "-{:.0f}V".format(d)
        return txt

    def _fmt_stats_pct(self, pct):
        p = pct if pct >= 0 else -pct
        p_i = int(p + 0.5)
        if p_i > 99:
            p_i = 99
        return "-{}%".format(p_i)

    def _update_stats_blink_state(self):
        visible = True
        if self.stats_active_blink_enabled:
            any_active = False
            for ev in self.dip_events:
                if not self._channel_filter_allows(ev.get("channel")):
                    continue
                if ev.get("active", False):
                    any_active = True
                    break
            if any_active:
                now_ms = time.ticks_ms()
                visible = ((now_ms // self.stats_active_blink_ms) & 1) == 0

        if visible != self._stats_blink_visible:
            self._stats_blink_visible = visible
            self._stats_dirty = True

    def _fmt_graph_readout(self, v_real):
        if self.graph_readout_decimals <= 0:
            txt = "{:.0f}".format(v_real)
        else:
            txt = "{:.1f}".format(v_real)
        if self.graph_readout_show_units:
            txt = txt + "V"
        return txt

    def _fmt_graph_drop(self, d_real):
        d = d_real if d_real >= 0 else -d_real
        if self.graph_readout_decimals <= 0:
            return "-{:.0f}".format(d)
        txt = "-{:.1f}".format(d)
        if len(txt) > 5:
            txt = "-{:.0f}".format(d)
        return txt

    def _apply_startup_range_lock(self, current_hi):
        if not self.auto_zoom:
            return False
        if self.graph_startup_hold_ms <= 0:
            return False

        elapsed_ms = time.ticks_diff(time.ticks_ms(), self.start_ms)
        if elapsed_ms < 0 or elapsed_ms >= self.graph_startup_hold_ms:
            return False

        if self.graph_startup_anchor_v is None or current_hi > self.graph_startup_anchor_v:
            self.graph_startup_anchor_v = current_hi

        span = self.graph_startup_span_v
        if span <= 0:
            span = 6.0
        lo = self.graph_startup_anchor_v - span
        hi = self.graph_startup_anchor_v
        self.range_v_min, self.range_v_max = self._clamp_range(lo, hi)
        return True

    def _draw_graph_readouts(self, vals_real=None):
        if not self.graph_readouts_enabled:
            return

        top_v = self.range_v_max
        if self.graph_readout_top_mode == "LIVE_VISIBLE_MAX":
            top_v = None
            if isinstance(vals_real, dict):
                for ch in self._iter_plot_channels():
                    v = vals_real.get(ch)
                    if v is None:
                        continue
                    if top_v is None or v > top_v:
                        top_v = v
            if top_v is None:
                top_v = self.range_v_max

        rows = (
            (0, self._fmt_graph_readout(top_v)),
            (self.PLOT_H - 8, self._fmt_graph_readout(self.range_v_min)),
        )

        max_y = self.PLOT_H - 8
        if max_y < 0:
            max_y = 0

        for y, txt in rows:
            yy = y
            if yy < 0:
                yy = 0
            if yy > max_y:
                yy = max_y
            w = len(txt) * 8
            if w < 8:
                w = 8
            if w > self.PLOT_W:
                w = self.PLOT_W
            self.oled.fill_rect(0, yy, w, 8, BLACK)
            self.oled.text(txt, 0, yy, WHITETXT)

    def _update_graph_baseline(self, vals_real):
        if not self.graph_baseline_enabled:
            return

        anchor = None
        for ch in self._iter_plot_channels():
            v = vals_real.get(ch)
            if v is None:
                continue
            if anchor is None or v > anchor:
                anchor = v
        if anchor is None:
            return

        anchor = self._clamp(anchor, self.V_MIN, self.V_MAX)
        if self.graph_baseline_v is None:
            self.graph_baseline_v = anchor
            return

        a = self.graph_baseline_alpha_up if anchor > self.graph_baseline_v else self.graph_baseline_alpha_down
        self.graph_baseline_v = self.graph_baseline_v + (anchor - self.graph_baseline_v) * a
        self.graph_baseline_v = self._clamp(self.graph_baseline_v, self.V_MIN, self.V_MAX)

    def _draw_graph_baseline_line(self):
        if not self.graph_baseline_enabled:
            return
        if self.graph_baseline_v is None:
            return
        if self.PLOT_W <= 0 or self.PLOT_H <= 0:
            return

        y = self._v_to_y(self.graph_baseline_v)
        if y < 0:
            y = 0
        if y >= self.PLOT_H:
            y = self.PLOT_H - 1
        self.oled.hline(0, y, self.PLOT_W, DIMTXT)

    def _fmt_axis_v(self, v_real):
        max_chars = ((self.y_axis_strip_w - 3) // 8)
        if max_chars < 1:
            max_chars = 1
        if self.y_axis_decimals <= 0:
            txt = "{:.0f}".format(v_real)
        else:
            txt = "{:.1f}".format(v_real)
            if txt.endswith(".0"):
                txt = txt[:-2]
        if len(txt) > max_chars:
            txt = "{:.0f}".format(v_real)
        if len(txt) > max_chars:
            txt = txt[:max_chars]
        return txt

    def _fmt_callout_v(self, v_real):
        max_chars = ((self.y_axis_strip_w - 3) // 8)
        if max_chars < 1:
            max_chars = 1
        txt = "{:.1f}".format(v_real)
        if len(txt) > max_chars:
            txt = "{:.0f}".format(v_real)
        if len(txt) > max_chars:
            txt = txt[:max_chars]
        return txt

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
        placeholder = "--.-V --.-V ---%"
        n = self.stats_max_events
        line_h = 16 if self.stats_double_height else 8
        events = []
        for ev in self.dip_events:
            if self._channel_filter_allows(ev.get("channel")):
                events.append(ev)
        for i in range(n):
            y = i * line_h
            if i < len(events):
                ev = events[i]
                base_txt = self._fmt_stats_stable(ev["baseline"])
                drop_txt = self._fmt_stats_drop(ev["drop"])
                pct_txt = self._fmt_stats_pct(ev["pct"])
                channel_col = self.colors.get(ev["channel"], DIMTXT)
                is_active = bool(ev.get("active", False))
                show_stable = (not is_active) or (not self.stats_active_blink_enabled) or self._stats_blink_visible
                if show_stable:
                    self._draw_stats_text(0, y, base_txt, channel_col)
                self._draw_stats_text(48, y, drop_txt, RED)
                self._draw_stats_text(96, y, pct_txt, RED)
            else:
                self._draw_stats_text(0, y, placeholder, DIMTXT)

    def _draw_stats_text(self, x, y, text, color):
        if not self.stats_double_height:
            self.oled.text(text, x, y, color)
            can_bold = self.stats_bold and ((x + (len(text) * 8)) < self.W)
            if can_bold:
                self.oled.text(text, x + 1, y, color)
            return

        if framebuf is None:
            self.oled.text(text, x, y, color)
            can_bold = self.stats_bold and ((x + (len(text) * 8)) < self.W)
            if can_bold:
                self.oled.text(text, x + 1, y, color)
            return

        width = len(text) * 8
        if width <= 0:
            return

        mode = getattr(framebuf, "MONO_VLSB", None)
        if mode is None:
            mode = getattr(framebuf, "MONO_HLSB", None)
        if mode is None:
            self.oled.text(text, x, y, color)
            return

        try:
            buf = bytearray(width)
            fb = framebuf.FrameBuffer(buf, width, 8, mode)
            fb.fill(0)
            fb.text(text, 0, 0, 1)
        except Exception:
            self.oled.text(text, x, y, color)
            return

        x_limit = self.W - 1
        y_limit = self.H - 1
        x_max = x + width
        if x_max > self.W:
            x_max = self.W

        can_bold = self.stats_bold and x_max < self.W
        for sx in range(width):
            ox = x + sx
            if ox > x_limit:
                break
            on = False
            for sy in range(8):
                if fb.pixel(sx, sy):
                    on = True
                    dy = y + (sy * 2)
                    if dy <= y_limit:
                        h = 2
                        if (dy + 1) > y_limit:
                            h = 1
                        self.oled.vline(ox, dy, h, color)
                        if can_bold and (ox + 1) <= x_limit:
                            self.oled.vline(ox + 1, dy, h, color)
            if not on:
                continue

    def _draw_text_clipped(self, x, y, text, color):
        if text is None or len(text) <= 0:
            return

        width = len(text) * 8
        if width <= 0:
            return

        if y >= self.PLOT_H or (y + 8) <= 0:
            return
        if x >= self.PLOT_W or (x + width) <= 0:
            return

        clear_x0 = x if x > 0 else 0
        clear_x1 = x + width
        if clear_x1 > self.PLOT_W:
            clear_x1 = self.PLOT_W
        clear_w = clear_x1 - clear_x0

        clear_y0 = y if y > 0 else 0
        clear_y1 = y + 8
        if clear_y1 > self.PLOT_H:
            clear_y1 = self.PLOT_H
        clear_h = clear_y1 - clear_y0

        if clear_w <= 0 or clear_h <= 0:
            return

        self.oled.fill_rect(clear_x0, clear_y0, clear_w, clear_h, BLACK)

        # Fallback if framebuf is not available: only draw fully in-bounds text.
        if framebuf is None:
            if x >= 0 and (x + width) <= self.PLOT_W and y >= 0 and (y + 8) <= self.PLOT_H:
                self.oled.text(text, x, y, color)
            return

        mode = getattr(framebuf, "MONO_VLSB", None)
        if mode is None:
            mode = getattr(framebuf, "MONO_HLSB", None)
        if mode is None:
            if x >= 0 and (x + width) <= self.PLOT_W and y >= 0 and (y + 8) <= self.PLOT_H:
                self.oled.text(text, x, y, color)
            return

        try:
            buf = bytearray(width)
            fb = framebuf.FrameBuffer(buf, width, 8, mode)
            fb.fill(0)
            fb.text(text, 0, 0, 1)
        except Exception:
            if x >= 0 and (x + width) <= self.PLOT_W and y >= 0 and (y + 8) <= self.PLOT_H:
                self.oled.text(text, x, y, color)
            return

        sx0 = 0 if x >= 0 else -x
        sx1 = width if (x + width) <= self.PLOT_W else (self.PLOT_W - x)
        sy0 = 0 if y >= 0 else -y
        sy1 = 8 if (y + 8) <= self.PLOT_H else (self.PLOT_H - y)
        if sx1 <= sx0 or sy1 <= sy0:
            return

        for sx in range(sx0, sx1):
            ox = x + sx
            for sy in range(sy0, sy1):
                if fb.pixel(sx, sy):
                    self.oled.pixel(ox, y + sy, color)

    def _draw_solid_marker(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        if x >= self.PLOT_W or y >= self.PLOT_H:
            return
        if (x + w) > self.PLOT_W:
            w = self.PLOT_W - x
        if (y + h) > self.PLOT_H:
            h = self.PLOT_H - y
        if w <= 0 or h <= 0:
            return
        self.oled.fill_rect(x, y, w, h, color)

    def _draw_hollow_marker(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        if x < 0:
            w += x
            x = 0
        if y < 0:
            h += y
            y = 0
        if x >= self.PLOT_W or y >= self.PLOT_H:
            return
        if (x + w) > self.PLOT_W:
            w = self.PLOT_W - x
        if (y + h) > self.PLOT_H:
            h = self.PLOT_H - y
        if w <= 0 or h <= 0:
            return

        self.oled.hline(x, y, w, color)
        if h > 1:
            self.oled.hline(x, y + h - 1, w, color)
        self.oled.vline(x, y, h, color)
        if w > 1:
            self.oled.vline(x + w - 1, y, h, color)

        if w >= 3 and h >= 3:
            self.oled.fill_rect(x + 1, y + 1, w - 2, h - 2, BLACK)

    def _get_render_window_start(self):
        if self.sample_counter < 0:
            return 0
        if not self.graph_full:
            return 0
        start = self.sample_counter - (self.PLOT_W - 1)
        if start < 0:
            return 0
        return start

    def _draw_graph_event_markers(self):
        if not self.graph_event_markers_enabled:
            return
        if self.sample_counter < 0:
            return

        window_start = self._get_render_window_start()
        y = self.graph_event_marker_y
        h = self.graph_event_marker_h
        w = self.graph_event_marker_w

        for ev in self.dip_events:
            is_active = bool(ev.get("active", False))
            sample_index = ev.get("sample_index")
            if sample_index is None:
                continue
            x = sample_index - window_start
            if x < 0 or x >= self.PLOT_W:
                continue
            draw_w = w
            draw_h = h
            if is_active and self.graph_event_marker_active_force_min_size:
                if draw_w < 3:
                    draw_w = 3
                if draw_h < 3:
                    draw_h = 3

            if (x + draw_w) > self.PLOT_W:
                draw_w = self.PLOT_W - x
            if (y + draw_h) > self.PLOT_H:
                draw_h = self.PLOT_H - y
            if draw_w <= 0 or draw_h <= 0:
                continue
            col = self.colors.get(ev.get("channel"), WHITETXT)
            if is_active and self.graph_event_marker_active_hollow:
                self._draw_hollow_marker(x, y, draw_w, draw_h, col)
            else:
                self._draw_solid_marker(x, y, draw_w, draw_h, col)

    def _collect_graph_callouts(self, window_start):
        if not self.dip_callouts_enabled:
            return []

        plot_channels = self._iter_plot_channels()
        allowed_channels = {}
        for ch in plot_channels:
            allowed_channels[ch] = True

        callouts = []
        seen_channels = {}
        for ev in self.dip_events:
            channel = ev.get("channel")
            if channel is None:
                continue
            if channel not in allowed_channels:
                continue

            is_active = bool(ev.get("active", False))
            if self.dip_callout_scope == "LATEST_PER_CHANNEL":
                if channel in seen_channels:
                    continue
                if (not self.dip_callout_include_active) and is_active:
                    continue
            else:
                if is_active:
                    continue

            sample_index = ev.get("sample_index")
            if sample_index is None:
                continue
            x = sample_index - window_start
            if x < 0 or x >= self.PLOT_W:
                continue

            baseline = ev.get("baseline")
            drop = ev.get("drop")
            min_real = ev.get("min")
            if min_real is None:
                if baseline is None or drop is None:
                    continue
                drop_abs = drop if drop >= 0 else -drop
                min_real = baseline - drop_abs
            else:
                min_real = float(min_real)
            if baseline is not None and min_real > baseline:
                min_real = baseline
            min_real = self._clamp(min_real, self.V_MIN, self.V_MAX)
            y = self._v_to_y(min_real)
            if drop is None:
                drop_real = (baseline - min_real) if baseline is not None else 0.0
            else:
                drop_real = drop if drop >= 0 else -drop

            callouts.append({
                "channel": channel,
                "x": x,
                "y": y,
                "min_real": min_real,
                "drop_real": drop_real,
                "color": self.colors.get(channel, WHITETXT),
            })
            if self.dip_callout_scope == "LATEST_PER_CHANNEL":
                seen_channels[channel] = True
                if len(seen_channels) >= len(plot_channels):
                    break

        return callouts

    def _draw_dip_callouts(self, callouts):
        if not callouts:
            return

        max_text_y = self.PLOT_H - 8
        if max_text_y < 0:
            max_text_y = 0

        label_candidates = []
        for c in callouts:
            col = c["color"]
            x_dip = c["x"]
            y_dip = c["y"]
            txt = self._fmt_graph_drop(c.get("drop_real", 0.0))
            txt_w = len(txt) * 8
            if txt_w < 8:
                txt_w = 8
            if x_dip >= self.PLOT_W:
                x_dip = self.PLOT_W - 1
            if x_dip < 0:
                x_dip = 0
            if y_dip < 0:
                y_dip = 0
            if y_dip >= self.PLOT_H:
                y_dip = self.PLOT_H - 1

            marker_top = y_dip - 1
            if marker_top < 0:
                marker_top = 0
            marker_h = 3
            if (marker_top + marker_h) > self.PLOT_H:
                marker_h = self.PLOT_H - marker_top
            if marker_h > 0:
                self.oled.vline(x_dip, marker_top, marker_h, col)

            x_label = x_dip - txt_w - 1
            if (x_label + txt_w) <= 0 or x_label >= self.PLOT_W:
                continue

            y_label = y_dip + 2
            if y_label < 0:
                y_label = 0
            if y_label > max_text_y:
                y_label = max_text_y

            label_candidates.append({
                "x": x_label,
                "y": y_label,
                "w": txt_w,
                "h": 8,
                "text": txt,
                "color": col,
                "drop_real": c.get("drop_real", 0.0),
                "x_dip": x_dip,
            })

        if not label_candidates:
            return

        if self.dip_label_overlap_mode == "DRAW_ALL":
            draw_list = label_candidates
        else:
            if self.dip_label_priority == "NEWEST":
                sorted_labels = sorted(label_candidates, key=lambda item: item["x_dip"], reverse=True)
            else:
                sorted_labels = sorted(
                    label_candidates,
                    key=lambda item: (item["drop_real"], item["x_dip"]),
                    reverse=True
                )

            draw_list = []
            drawn_boxes = []
            for item in sorted_labels:
                overlap = False
                x0 = item["x"]
                y0 = item["y"]
                x1 = x0 + item["w"]
                y1 = y0 + item["h"]
                for box in drawn_boxes:
                    bx0 = box[0]
                    by0 = box[1]
                    bx1 = box[2]
                    by1 = box[3]
                    if not (x1 <= bx0 or bx1 <= x0 or y1 <= by0 or by1 <= y0):
                        overlap = True
                        break
                if overlap:
                    continue
                draw_list.append(item)
                drawn_boxes.append((x0, y0, x1, y1))

        for item in draw_list:
            self._draw_text_clipped(item["x"], item["y"], item["text"], item["color"])

    def _draw_y_axis_overlay(self, bottom_v_real=None):
        if not self.y_axis_enabled:
            return

        strip_w = self.y_axis_strip_w
        if strip_w < 1:
            return
        if strip_w >= self.PLOT_W:
            strip_w = self.PLOT_W - 1
        if strip_w < 1:
            return

        self.oled.fill_rect(0, 0, strip_w, self.PLOT_H, BLACK)
        axis_x = strip_w - 1
        self.oled.vline(axis_x, 0, self.PLOT_H, DIMTXT)

        top = self.plot_top_pad_px
        bottom = self.PLOT_H - 1 - self.plot_bottom_pad_px
        if bottom <= top:
            top = 0
            bottom = self.PLOT_H - 1
        bottom_v = self.range_v_min if bottom_v_real is None else bottom_v_real
        bottom_v = self._clamp(bottom_v, self.V_MIN, self.V_MAX)

        ticks = [(top, self.range_v_max)]
        if self.y_axis_show_mid:
            mid = top + ((bottom - top) // 2)
            ticks.append((mid, (self.range_v_min + self.range_v_max) * 0.5))
        ticks.append((bottom, bottom_v))

        label_max_y = self.PLOT_H - 8
        if label_max_y < 0:
            label_max_y = 0

        for y, v in ticks:
            tick_x = axis_x - 3
            tick_w = 4
            if tick_x < 0:
                tick_w += tick_x
                tick_x = 0
            if tick_w > 0:
                self.oled.hline(tick_x, y, tick_w, DIMTXT)

            label = self._fmt_axis_v(v).strip()
            ly = y - 4
            if ly < 0:
                ly = 0
            if ly > label_max_y:
                ly = label_max_y
            lx = axis_x - 2 - (len(label) * 8)
            if lx < 0:
                lx = 0
            self.oled.text(label, lx, ly, WHITETXT)

    def _draw_graph_legend(self):
        if not self.graph_legend_enabled:
            return

        x0 = 2
        if self.y_axis_enabled:
            x0 = self.y_axis_strip_w + 2
        if x0 >= self.PLOT_W:
            return

        legend_w = 26
        if (x0 + legend_w) > self.PLOT_W:
            legend_w = self.PLOT_W - x0
        if legend_w > 0:
            self.oled.fill_rect(x0, 0, legend_w, 8, BLACK)
        self.oled.text("B", x0, 0, self.colors["BLUE"])
        if (x0 + 10) < self.PLOT_W:
            self.oled.text("Y", x0 + 10, 0, self.colors["YELLOW"])
        if (x0 + 20) < self.PLOT_W:
            self.oled.text("G", x0 + 20, 0, self.colors["GREEN"])

    def shutdown(self):
        try:
            self.oled.fill(BLACK)
            self.oled.show()
        except Exception:
            pass

        turned_off = (
            self._call_if_present("poweroff")
            or self._call_if_present("power_off")
            or self._call_if_present("display_off")
            or self._call_if_present("displayoff")
            or self._call_if_present("sleep", True)
            or self._call_if_present("sleep_mode", True)
            or self._call_if_present("write_cmd", 0xAE)
            or self._call_if_present("cmd", 0xAE)
            or self._call_if_present("_write_cmd", 0xAE)
            or self._call_if_present("_command", 0xAE)
            or self._send_display_off_cmd()
        )

        # Hold controller in reset after shutdown so the panel stays off.
        if self._rst_pin is not None:
            try:
                self._rst_pin.value(0)
            except Exception:
                pass

        if not turned_off:
            try:
                if self._dc_pin is not None:
                    self._dc_pin.value(0)
                if self._cs_pin is not None:
                    self._cs_pin.value(1)
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

    def _send_display_off_cmd(self):
        if self._spi is None or self._cs_pin is None or self._dc_pin is None:
            return False
        try:
            self._cs_pin.value(0)
            self._dc_pin.value(0)
            self._spi.write(b"\xAE")  # SSD1351 DISPLAYOFF
            self._cs_pin.value(1)
            return True
        except Exception:
            try:
                self._cs_pin.value(1)
            except Exception:
                pass
            return False

    def latch_dip_drop_adc(self, channel, drop_adc_v):
        drop_real = drop_adc_v * self._graph_gain(channel)
        self.latched_dip[channel] = (-drop_real) if self.negative_dip else drop_real

        if not self.min_dip_enabled:
            return

        if drop_real < 0:
            drop_real = -drop_real

        if self.min_drop_real_max is None or drop_real > (self.min_drop_real_max + self.min_dip_eps_v):
            self.min_drop_real_max = drop_real
            self.min_drop_channel = channel
            self._rebuild_min_badge_text()

    def record_dip_event_adc(self, channel, baseline_adc_v, min_adc_v, drop_adc_v, event_id=None, active=False, sample_index=None):
        if baseline_adc_v is None or drop_adc_v is None:
            return
        baseline_real = self._graph_real(channel, baseline_adc_v)
        if min_adc_v is None:
            min_adc_v = baseline_adc_v - abs(drop_adc_v)
        min_real = self._graph_real(channel, min_adc_v)
        if min_real > baseline_real:
            min_real = baseline_real
        drop_real = baseline_real - min_real
        drop_pct = (drop_real / baseline_real * 100.0) if baseline_real > 0 else 0.0
        drop_display = (-drop_real) if self.negative_dip else drop_real

        sample_index_supplied = sample_index is not None
        if not sample_index_supplied:
            sample_index = self.sample_counter

        event = {
            "id": event_id,
            "channel": channel,
            "baseline": baseline_real,
            "min": min_real,
            "drop": drop_display,
            "pct": drop_pct,
            "active": bool(active),
            "sample_index": sample_index,
        }

        if event_id is not None:
            hit_index = None
            for i, ev in enumerate(self.dip_events):
                if ev.get("id") == event_id:
                    hit_index = i
                    break
            if hit_index is None:
                self.dip_events.insert(0, event)
            else:
                prior = self.dip_events[hit_index]
                if (not sample_index_supplied) and ("sample_index" in prior):
                    event["sample_index"] = prior.get("sample_index")
                self.dip_events[hit_index] = event
        else:
            self.dip_events.insert(0, event)

        keep_n = self.stats_max_events
        if self.graph_max_events > keep_n:
            keep_n = self.graph_max_events
        if len(self.dip_events) > keep_n:
            self.dip_events = self.dip_events[:keep_n]
        self._stats_dirty = True

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
        for ch in self._iter_plot_channels():
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

    def _limit_range_step(self, current_lo, current_hi, target_lo, target_hi):
        max_step = self.auto_range_max_step_v
        if max_step <= 0:
            return target_lo, target_hi

        lo = target_lo
        hi = target_hi
        d_lo = lo - current_lo
        d_hi = hi - current_hi

        if d_lo > max_step:
            lo = current_lo + max_step
        elif d_lo < -max_step:
            lo = current_lo - max_step

        if d_hi > max_step:
            hi = current_hi + max_step
        elif d_hi < -max_step:
            hi = current_hi - max_step

        return self._clamp_range(lo, hi)

    def _update_range(self):
        target_lo, target_hi = self._calc_target_range()
        if not self.auto_zoom:
            self.range_v_min = target_lo
            self.range_v_max = target_hi
            return

        current_lo = self.range_v_min
        current_hi = self.range_v_max
        a = self.auto_range_alpha
        next_lo = current_lo + (target_lo - current_lo) * a
        next_hi = current_hi + (target_hi - current_hi) * a
        next_lo, next_hi = self._clamp_range(next_lo, next_hi)
        lo, hi = self._limit_range_step(current_lo, current_hi, next_lo, next_hi)

        eps = self.auto_range_epsilon_v
        if eps <= 0:
            eps = 0.000001

        expanded = (lo < (current_lo - eps)) or (hi > (current_hi + eps))
        if expanded:
            if self.auto_zoomout_hold_samples > 0:
                self.auto_zoomout_hold_until_sample = self.sample_counter + self.auto_zoomout_hold_samples
            else:
                self.auto_zoomout_hold_until_sample = -1
            if self.auto_zoomin_cooldown_samples > 0:
                cooldown_start = self.sample_counter
                if self.auto_zoomout_hold_until_sample > cooldown_start:
                    cooldown_start = self.auto_zoomout_hold_until_sample
                self.auto_zoomin_cooldown_until_sample = cooldown_start + self.auto_zoomin_cooldown_samples
            else:
                self.auto_zoomin_cooldown_until_sample = -1

        hold_active = (
            self.auto_zoomout_hold_samples > 0
            and self.sample_counter < self.auto_zoomout_hold_until_sample
        )
        cooldown_active = (
            self.auto_zoomin_cooldown_samples > 0
            and self.sample_counter < self.auto_zoomin_cooldown_until_sample
        )
        if hold_active or cooldown_active:
            if lo > current_lo:
                lo = current_lo
            if hi < current_hi:
                hi = current_hi
            lo, hi = self._clamp_range(lo, hi)

        self.range_v_min, self.range_v_max = lo, hi

    def _redraw_plot_from_hist(self):
        self.oled.fill_rect(0, 0, self.W, self.PLOT_H, BLACK)
        plot_channels = self._iter_plot_channels()
        for ch in plot_channels:
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
        n = len(self.v_hist[plot_channels[0]])
        self.graph_full = n >= self.PLOT_W
        self.x = (self.PLOT_W - 1) if self.graph_full else max(0, n - 1)
        for ch in plot_channels:
            hist = self.v_hist[ch]
            self.prev_y[ch] = self._v_to_y(hist[-1]) if hist else None

    def _scroll_left_and_draw_right(self, vals_real):
        if hasattr(self.oled, "scroll"):
            self.oled.scroll(-1, 0)
            xr = self.PLOT_W - 1
            self.oled.vline(xr, 0, self.PLOT_H, BLACK)
            for ch in self._iter_plot_channels():
                v = vals_real.get(ch)
                if v is None:
                    continue
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
        plot_channels = self._iter_plot_channels()
        n = len(self.v_hist[plot_channels[0]])
        if n <= 0:
            return

        # Initial fill from left to right.
        if not self.graph_full:
            self.x = n - 1
            self.oled.vline(self.x, 0, self.PLOT_H, BLACK)
            for ch in plot_channels:
                v = vals_real.get(ch)
                if v is None:
                    continue
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

    def plot_medians_adc(self, blue_adc, yellow_adc, green_adc):
        self._poll_toggle_button()
        self._poll_help_button()
        self._poll_channel_button()
        self.sample_counter += 1

        blue_real = self._scale("BLUE", blue_adc)
        yellow_real = self._scale("YELLOW", yellow_adc)
        green_real = self._scale("GREEN", green_adc)

        vals = {"BLUE": blue_real, "YELLOW": yellow_real, "GREEN": green_real}
        self._append_hist(vals)
        self.frame_count += 1

        range_changed = False
        if not self.auto_zoom:
            range_changed = (self.range_v_min != self.V_MIN) or (self.range_v_max != self.V_MAX)
            self.range_v_min = self.V_MIN
            self.range_v_max = self.V_MAX
            self.auto_zoomout_hold_until_sample = -1
            self.auto_zoomin_cooldown_until_sample = -1
        else:
            old_lo = self.range_v_min
            old_hi = self.range_v_max
            current_hi = blue_real
            if yellow_real > current_hi:
                current_hi = yellow_real
            if green_real > current_hi:
                current_hi = green_real

            if self._apply_startup_range_lock(current_hi):
                range_changed = (
                    abs(self.range_v_min - old_lo) >= self.auto_range_epsilon_v
                    or abs(self.range_v_max - old_hi) >= self.auto_range_epsilon_v
                )
            elif (self.frame_count % self.auto_range_update_every) == 0:
                self._update_range()
                range_changed = (
                    abs(self.range_v_min - old_lo) >= self.auto_range_epsilon_v
                    or abs(self.range_v_max - old_hi) >= self.auto_range_epsilon_v
                )
                if not range_changed:
                    # Keep prior mapping so existing pixels remain consistent.
                    self.range_v_min = old_lo
                    self.range_v_max = old_hi

        badge_visible = self._channel_badge_is_visible()
        if badge_visible != self._channel_badge_was_visible:
            self._channel_badge_was_visible = badge_visible
            if self.view_mode == "GRAPH":
                self._force_graph_redraw = True
            else:
                self._stats_dirty = True
        elif badge_visible and self.view_mode == "STATS":
            # Stats view is mostly static; redraw while badge is active so it stays current.
            self._stats_dirty = True

        help_visible = self._help_overlay_should_draw()
        if help_visible:
            self._help_overlay_was_visible = True
            self._draw_help_overlay()
            self.oled.show()
            return

        if self._help_overlay_was_visible:
            self._help_overlay_was_visible = False
            if self.view_mode == "GRAPH":
                self._force_graph_redraw = True
            else:
                self._stats_dirty = True

        if self.view_mode == "STATS":
            self._update_stats_blink_state()
            if self._stats_dirty:
                self._draw_stats()
                if badge_visible:
                    self._draw_channel_mode_badge()
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

        self._update_graph_baseline(vals)
        self._draw_graph_baseline_line()
        self._draw_min_badge()

        window_start = self._get_render_window_start()
        callouts = self._collect_graph_callouts(window_start)
        self._draw_dip_callouts(callouts)
        self._draw_graph_readouts(vals)
        if badge_visible:
            self._draw_channel_mode_badge()
        self.oled.show()

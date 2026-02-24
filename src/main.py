# main.py

import time
import gc

import config
from adc_sampler import AdcSampler
from channel_state import ChannelState
from dip_detector import DipDetector
from median_logger import MedianLogger
from perf_metrics import PerfMetrics
from storage import ensure_file, append_lines, append_line, check_file_size_limit, get_free_space
from stats_tracker import StatsTracker

try:
    from machine import Pin
except ImportError:
    Pin = None

try:
    import _thread
except ImportError:
    _thread = None

# OLED UI
ui = None
if getattr(config, "ENABLE_OLED", False):
    try:
        from oled_ui import OledUI
        ui = OledUI()
        print("OLED UI enabled.")
    except Exception as e:
        ui = None
        print(f"Warning: OLED UI disabled (init failed): {e}")


def _ticks_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def _ticks_us():
    if hasattr(time, "ticks_us"):
        return time.ticks_us()
    return int(time.time() * 1000000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _ticks_add(a, b):
    if hasattr(time, "ticks_add"):
        return time.ticks_add(a, b)
    return a + b


def _sleep_ms(delay_ms):
    if delay_ms <= 0:
        return
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(delay_ms)
    else:
        time.sleep(delay_ms / 1000.0)


def _init_status_led():
    if not getattr(config, "ENABLE_STATUS_LED", False):
        return None
    if Pin is None:
        print("Warning: Status LED disabled (machine.Pin unavailable).")
        return None

    pin_cfg = getattr(config, "STATUS_LED_PIN", "LED")
    try:
        return Pin(pin_cfg, Pin.OUT)
    except Exception as primary_err:
        # Compatibility fallback: if explicit GPIO fails, try board LED alias;
        # if alias fails, try GP25.
        if pin_cfg != "LED":
            try:
                led = Pin("LED", Pin.OUT)
                print("Status LED: fallback to Pin('LED') succeeded.")
                return led
            except Exception:
                pass
        if pin_cfg != 25:
            try:
                led = Pin(25, Pin.OUT)
                print("Status LED: fallback to Pin(25) succeeded.")
                return led
            except Exception:
                pass
        print(f"Warning: Status LED disabled (init failed on {pin_cfg}): {primary_err}")
        return None


def _set_status_led(led_pin, on):
    if led_pin is None:
        return
    active_low = bool(getattr(config, "STATUS_LED_ACTIVE_LOW", False))
    try:
        if active_low:
            led_pin.value(0 if on else 1)
        else:
            led_pin.value(1 if on else 0)
    except Exception:
        pass

def usb_stream_median(t_s, channel_name, median_v):
    # median_v is ADC-pin volts. Convert to REAL for streaming.
    real_v = median_v * config.CHANNEL_SCALE.get(channel_name, 1.0)
    msg = f"MEDIAN,{t_s:.3f},{channel_name},{real_v:.3f}\n"
    print(msg, end='')

def usb_stream_dip(channel, dip_start_s, dip_end_s, duration_ms, baseline_v, min_v, drop_v):
    # All dip values are in ADC-pin volts. Convert to REAL for streaming.
    scale = config.CHANNEL_SCALE.get(channel, 1.0)
    baseline_real = baseline_v * scale
    min_real = min_v * scale
    drop_real = drop_v * scale

    msg = f"DIP,{channel},{dip_start_s:.3f},{dip_end_s:.3f},{duration_ms},{baseline_real:.3f},{min_real:.3f},{drop_real:.3f}\n"
    print(msg, end='')

def usb_stream_baseline(t_s, channel_name, baseline_v):
    # baseline_v is ADC-pin volts. Convert to REAL for streaming.
    real_v = baseline_v * config.CHANNEL_SCALE.get(channel_name, 1.0)
    msg = f"BASELINE,{t_s:.3f},{channel_name},{real_v:.3f}\n"
    print(msg, end='')


class _Core1EventQueue:
    def __init__(self, size):
        queue_size = int(size)
        if queue_size < 32:
            queue_size = 32
        self.size = queue_size
        self.kind = [0] * queue_size
        self.p0 = [None] * queue_size
        self.p1 = [None] * queue_size
        self.p2 = [None] * queue_size
        self.p3 = [None] * queue_size
        self.p4 = [None] * queue_size
        self.p5 = [None] * queue_size
        self.p6 = [None] * queue_size
        self.p7 = [None] * queue_size
        self.head = 0
        self.tail = 0
        self.count = 0
        self.depth_hwm = 0
        self.dropped = 0
        self.lock = _thread.allocate_lock() if _thread is not None else None

    def _lock_enter(self):
        if self.lock is not None:
            self.lock.acquire()

    def _lock_exit(self):
        if self.lock is not None:
            self.lock.release()

    def push(self, kind, p0=None, p1=None, p2=None, p3=None, p4=None, p5=None, p6=None, p7=None):
        self._lock_enter()
        try:
            if self.count >= self.size:
                self.dropped += 1
                return False

            idx = self.head
            self.kind[idx] = kind
            self.p0[idx] = p0
            self.p1[idx] = p1
            self.p2[idx] = p2
            self.p3[idx] = p3
            self.p4[idx] = p4
            self.p5[idx] = p5
            self.p6[idx] = p6
            self.p7[idx] = p7

            idx += 1
            if idx >= self.size:
                idx = 0
            self.head = idx
            self.count += 1
            if self.count > self.depth_hwm:
                self.depth_hwm = self.count
            return True
        finally:
            self._lock_exit()

    def pop(self):
        self._lock_enter()
        try:
            if self.count <= 0:
                return None

            idx = self.tail
            item = (
                self.kind[idx],
                self.p0[idx],
                self.p1[idx],
                self.p2[idx],
                self.p3[idx],
                self.p4[idx],
                self.p5[idx],
                self.p6[idx],
                self.p7[idx],
            )
            self.kind[idx] = 0
            self.p0[idx] = None
            self.p1[idx] = None
            self.p2[idx] = None
            self.p3[idx] = None
            self.p4[idx] = None
            self.p5[idx] = None
            self.p6[idx] = None
            self.p7[idx] = None

            idx += 1
            if idx >= self.size:
                idx = 0
            self.tail = idx
            self.count -= 1
            return item
        finally:
            self._lock_exit()

    def depth(self):
        self._lock_enter()
        try:
            return self.count
        finally:
            self._lock_exit()

    def stats(self):
        self._lock_enter()
        try:
            return self.count, self.depth_hwm, self.dropped
        finally:
            self._lock_exit()


class _Core1Bridge:
    EVT_PRINT = 1
    EVT_USB_MEDIAN = 2
    EVT_USB_DIP = 3
    EVT_USB_BASELINE = 4
    EVT_FILE_APPEND = 5
    EVT_MEDLOG_ADD = 6
    EVT_MEDLOG_FLUSH_AND_TRIM = 7
    EVT_UI_PLOT = 8
    EVT_UI_DIP_LATCH = 9
    EVT_UI_DIP_EVENT = 10
    EVT_STATS_PRINT = 11
    EVT_PERF_REPORT = 12
    EVT_UI_SHUTDOWN = 13
    EVT_STOP = 255

    def __init__(self, stats, logging_mode, ui_ref, medlog, perf_rt=None, perf_io=None):
        self.stats = stats
        self.logging_mode = logging_mode
        self.ui = ui_ref
        self.medlog = medlog
        self.perf_rt = perf_rt
        self.perf_io = perf_io
        self.allow_file_io = (logging_mode != "DISPLAY_ONLY")
        self.allow_runtime_prints = (logging_mode != "DISPLAY_ONLY")
        self.allow_usb_stream = (logging_mode == "USB_STREAM")
        self.idle_sleep_ms = int(getattr(config, "CORE1_IDLE_SLEEP_MS", 1))
        if self.idle_sleep_ms < 0:
            self.idle_sleep_ms = 0
        queue_size = int(getattr(config, "CORE1_QUEUE_SIZE", 256))
        self.queue = _Core1EventQueue(queue_size)
        self._started = False
        self._running = 0
        self._alive = 0
        self._ui_failed = False

    def start(self):
        if _thread is None:
            return False
        if self._started:
            return True
        self._running = 1
        try:
            _thread.start_new_thread(self._worker_loop, ())
        except Exception as e:
            self._running = 0
            if self.allow_runtime_prints:
                print(f"Warning: Core1 worker unavailable: {e}")
            return False
        self._started = True
        return True

    def stop(self, timeout_ms=2000):
        if not self._started:
            return
        self._running = 0
        self.queue.push(self.EVT_STOP)
        end_ms = _ticks_add(_ticks_ms(), int(timeout_ms))
        while self._alive and _ticks_diff(end_ms, _ticks_ms()) > 0:
            _sleep_ms(5)

    def queue_depth(self):
        return self.queue.depth()

    def queue_stats(self):
        return self.queue.stats()

    def queue_print(self, msg):
        if not self.allow_runtime_prints:
            return True
        return self.queue.push(self.EVT_PRINT, msg)

    def queue_usb_median(self, t_s, channel_name, median_v):
        if not self.allow_usb_stream:
            return True
        return self.queue.push(self.EVT_USB_MEDIAN, t_s, channel_name, median_v)

    def queue_usb_dip(self, channel, dip_start_s, dip_end_s, duration_ms, baseline_v, min_v, drop_v):
        if not self.allow_usb_stream:
            return True
        return self.queue.push(
            self.EVT_USB_DIP,
            channel,
            dip_start_s,
            dip_end_s,
            duration_ms,
            baseline_v,
            min_v,
            drop_v
        )

    def queue_usb_baseline(self, t_s, channel_name, baseline_v):
        if not self.allow_usb_stream:
            return True
        return self.queue.push(self.EVT_USB_BASELINE, t_s, channel_name, baseline_v)

    def queue_file_append(self, path, line):
        if not self.allow_file_io:
            return True
        return self.queue.push(self.EVT_FILE_APPEND, path, line)

    def queue_median_add(self, t_s, channel_name, median_v):
        if not self.allow_file_io:
            return True
        if self.logging_mode != "FULL_LOCAL":
            return True
        return self.queue.push(self.EVT_MEDLOG_ADD, t_s, channel_name, median_v)

    def queue_median_flush_and_trim(self):
        if not self.allow_file_io:
            return True
        if self.logging_mode != "FULL_LOCAL":
            return True
        return self.queue.push(self.EVT_MEDLOG_FLUSH_AND_TRIM)

    def queue_ui_plot(self, blue_v, yellow_v, green_v):
        if self.ui is None:
            return True
        return self.queue.push(self.EVT_UI_PLOT, blue_v, yellow_v, green_v)

    def queue_ui_dip_latch(self, channel_name, drop_v):
        if self.ui is None:
            return True
        return self.queue.push(self.EVT_UI_DIP_LATCH, channel_name, drop_v)

    def queue_ui_dip_event(self, channel_name, baseline_v, min_v, drop_v, event_id=None, active=False, sample_index=None):
        if self.ui is None:
            return True
        return self.queue.push(
            self.EVT_UI_DIP_EVENT,
            channel_name,
            baseline_v,
            min_v,
            drop_v,
            event_id,
            active,
            sample_index
        )

    def queue_stats_print(self):
        if not self.allow_runtime_prints:
            return True
        return self.queue.push(self.EVT_STATS_PRINT)

    def queue_perf_report(self):
        return self.queue.push(self.EVT_PERF_REPORT)

    def queue_ui_shutdown(self):
        if self.ui is None:
            return True
        return self.queue.push(self.EVT_UI_SHUTDOWN)

    def _record_io_timing(self, name, start_us):
        if self.perf_io is None or start_us is None:
            return
        self.perf_io.add_timing(name, _ticks_diff(_ticks_us(), start_us))

    def _print_perf_summary(self):
        if not self.allow_runtime_prints:
            return
        if self.perf_rt is not None:
            print("PERF[core0]")
            try:
                lines = self.perf_rt.summary_lines()
            except MemoryError:
                lines = self.perf_rt.compact_summary_lines()
                lines.insert(1, "  (compact summary: full percentile report skipped due low memory)")
            for line in lines:
                print(line)
        if self.perf_io is not None:
            print("PERF[core1]")
            try:
                lines = self.perf_io.summary_lines()
            except MemoryError:
                lines = self.perf_io.compact_summary_lines()
                lines.insert(1, "  (compact summary: full percentile report skipped due low memory)")
            for line in lines:
                print(line)
        q_depth, q_hwm, q_dropped = self.queue.stats()
        print(
            "CORE1 queue depth={} hwm={} dropped={}".format(
                q_depth,
                q_hwm,
                q_dropped
            )
        )

    def _worker_loop(self):
        self._alive = 1
        try:
            while self._running or (self.queue.depth() > 0):
                item = self.queue.pop()
                if item is None:
                    _sleep_ms(self.idle_sleep_ms)
                    continue
                kind, p0, p1, p2, p3, p4, p5, p6, p7 = item
                if kind == self.EVT_STOP:
                    self._running = 0
                    continue

                try:
                    if kind == self.EVT_PRINT:
                        print(p0)

                    elif kind == self.EVT_USB_MEDIAN:
                        start_us = _ticks_us() if self.perf_io is not None else None
                        usb_stream_median(p0, p1, p2)
                        self._record_io_timing("usb_write_us", start_us)

                    elif kind == self.EVT_USB_DIP:
                        start_us = _ticks_us() if self.perf_io is not None else None
                        usb_stream_dip(p0, p1, p2, p3, p4, p5, p6)
                        self._record_io_timing("usb_write_us", start_us)

                    elif kind == self.EVT_USB_BASELINE:
                        start_us = _ticks_us() if self.perf_io is not None else None
                        usb_stream_baseline(p0, p1, p2)
                        self._record_io_timing("usb_write_us", start_us)

                    elif kind == self.EVT_FILE_APPEND:
                        start_us = _ticks_us() if self.perf_io is not None else None
                        if append_line(p0, p1):
                            self.stats.record_flash_write()
                        self._record_io_timing("flash_write_us", start_us)

                    elif kind == self.EVT_MEDLOG_ADD:
                        self.medlog.add(p0, p1, p2)

                    elif kind == self.EVT_MEDLOG_FLUSH_AND_TRIM:
                        start_us = _ticks_us() if self.perf_io is not None else None
                        lines_written = self.medlog.flush_to_file(append_lines)
                        if lines_written > 0:
                            self.stats.record_flash_write(lines_written)
                        check_file_size_limit(
                            config.MEDIANS_FILE,
                            config.MAX_MEDIANS_SIZE_BYTES,
                            "time_s,channel,median_V",
                            config.MAX_MEDIANS_LINES
                        )
                        self._record_io_timing("flash_write_us", start_us)

                    elif kind == self.EVT_UI_PLOT:
                        if self.ui is not None and (not self._ui_failed):
                            start_us = _ticks_us() if self.perf_io is not None else None
                            self.ui.plot_medians_adc(p0, p1, p2)
                            self._record_io_timing("ui_frame_us", start_us)

                    elif kind == self.EVT_UI_DIP_LATCH:
                        if self.ui is not None and (not self._ui_failed):
                            self.ui.latch_dip_drop_adc(p0, p1)

                    elif kind == self.EVT_UI_DIP_EVENT:
                        if self.ui is not None and (not self._ui_failed):
                            self.ui.record_dip_event_adc(
                                p0,
                                p1,
                                p2,
                                p3,
                                event_id=p4,
                                active=p5,
                                sample_index=p6
                            )

                    elif kind == self.EVT_STATS_PRINT:
                        self.stats.print_summary(config.MEDIANS_FILE, config.DIPS_FILE)

                    elif kind == self.EVT_PERF_REPORT:
                        if self.perf_io is not None:
                            gc_start_us = _ticks_us()
                            gc.collect()
                            self.perf_io.record_gc(_ticks_diff(_ticks_us(), gc_start_us))
                        self._print_perf_summary()

                    elif kind == self.EVT_UI_SHUTDOWN:
                        if self.ui is not None and (not self._ui_failed):
                            self.ui.shutdown()

                except Exception as event_err:
                    if kind in (
                        self.EVT_UI_PLOT,
                        self.EVT_UI_DIP_LATCH,
                        self.EVT_UI_DIP_EVENT,
                        self.EVT_UI_SHUTDOWN,
                    ):
                        self._ui_failed = True
                    if self.allow_runtime_prints:
                        print(f"Warning: Core1 event failed ({kind}): {event_err}")
        finally:
            self._alive = 0


class _LoopHandlers:
    def __init__(self, stats, perf, logging_mode, ui_ref, ui_event_map, core1_bridge=None):
        self.stats = stats
        self.perf = perf
        self.logging_mode = logging_mode
        self.ui = ui_ref
        self.ui_active_event_id_by_channel = ui_event_map
        self.core1 = core1_bridge
        self.current_channel = None
        self.allow_file_io = (logging_mode != "DISPLAY_ONLY")
        self.allow_runtime_prints = (logging_mode != "DISPLAY_ONLY")
        self.allow_usb_stream = (logging_mode == "USB_STREAM")

    def _record_timing(self, name, start_us):
        if self.perf is None or start_us is None:
            return
        self.perf.add_timing(name, _ticks_diff(_ticks_us(), start_us))

    def dip_callback(self, msg):
        if self.allow_runtime_prints:
            if self.core1 is not None:
                if not self.core1.queue_print(msg):
                    print(msg)
            else:
                print(msg)
        if "DIP END" in msg and self.current_channel is not None:
            self.stats.record_dip(self.current_channel)

    def dip_append(self, path, line):
        parts = line.strip().split(',')
        if len(parts) == 7:
            channel = parts[0]
            dip_start_s = float(parts[1])
            dip_end_s = float(parts[2])
            duration_ms = int(parts[3])
            baseline_v = float(parts[4])
            min_v = float(parts[5])
            drop_v = float(parts[6])

            if self.allow_usb_stream:
                if self.core1 is not None:
                    queued = self.core1.queue_usb_dip(
                        channel,
                        dip_start_s,
                        dip_end_s,
                        duration_ms,
                        baseline_v,
                        min_v,
                        drop_v
                    )
                    if not queued:
                        usb_start_us = _ticks_us() if self.perf is not None else None
                        usb_stream_dip(channel, dip_start_s, dip_end_s, duration_ms, baseline_v, min_v, drop_v)
                        self._record_timing("usb_write_us", usb_start_us)
                else:
                    usb_start_us = _ticks_us() if self.perf is not None else None
                    usb_stream_dip(channel, dip_start_s, dip_end_s, duration_ms, baseline_v, min_v, drop_v)
                    self._record_timing("usb_write_us", usb_start_us)

            if self.ui is not None:
                event_id = self.ui_active_event_id_by_channel.pop(channel, None)
                if self.core1 is not None:
                    queued_latch = self.core1.queue_ui_dip_latch(channel, drop_v)
                    queued_event = self.core1.queue_ui_dip_event(
                        channel,
                        baseline_v,
                        min_v,
                        drop_v,
                        event_id=event_id,
                        active=False,
                        sample_index=None
                    )
                    if (not queued_latch) or (not queued_event):
                        self.ui.latch_dip_drop_adc(channel, drop_v)
                        self.ui.record_dip_event_adc(
                            channel,
                            baseline_v,
                            min_v,
                            drop_v,
                            event_id=event_id,
                            active=False,
                            sample_index=getattr(self.ui, "sample_counter", None)
                        )
                else:
                    self.ui.latch_dip_drop_adc(channel, drop_v)
                    self.ui.record_dip_event_adc(
                        channel,
                        baseline_v,
                        min_v,
                        drop_v,
                        event_id=event_id,
                        active=False,
                        sample_index=getattr(self.ui, "sample_counter", None)
                    )

        if self.allow_file_io:
            if self.core1 is not None:
                queued = self.core1.queue_file_append(path, line)
                if not queued:
                    flash_start_us = _ticks_us() if self.perf is not None else None
                    if append_line(path, line):
                        self.stats.record_flash_write()
                    self._record_timing("flash_write_us", flash_start_us)
            else:
                flash_start_us = _ticks_us() if self.perf is not None else None
                if append_line(path, line):
                    self.stats.record_flash_write()
                self._record_timing("flash_write_us", flash_start_us)

def run():
    status_led = None

    # Validate configuration
    try:
        config.validate_config()
        print("Configuration validated successfully.")
    except ValueError as e:
        print(f"FATAL: {e}")
        return

    logging_mode = config.LOGGING_MODE
    display_only_mode = (logging_mode == "DISPLAY_ONLY")
    allow_file_io = (not display_only_mode)
    allow_runtime_prints = (not display_only_mode)
    dual_core_requested = bool(getattr(config, "DUAL_CORE_ENABLED", True))
    perf = None
    perf_io = None
    if bool(getattr(config, "PERF_METRICS_ENABLED", False)):
        perf = PerfMetrics(getattr(config, "PERF_RING_SIZE", 1024))
        if dual_core_requested:
            perf_io = PerfMetrics(getattr(config, "PERF_RING_SIZE", 1024))

    status_led = _init_status_led()
    _set_status_led(status_led, True)

    # Print configuration summary
    print(f"\n{'='*60}")
    print("PICO VOLTAGE DIP MONITOR")
    print(f"{'='*60}")
    print(f"Logging mode:    {logging_mode}")
    print(f"Sampling:        {config.TICK_MS} ms ({1000/config.TICK_MS:.0f} Hz)")
    print(f"Channels:        {', '.join(ch for ch, _ in config.CHANNEL_PINS)}")
    print(f"Dip threshold:   {config.DIP_THRESHOLD_V:.3f} V (ADC domain)")
    print(f"Divider scale:   {config.DIVIDER_SCALE:.3f}x (display/logging only)")
    print(f"Dual core:       {'Requested' if dual_core_requested else 'Disabled'}")
    print(f"Free flash:      {get_free_space():,} bytes")
    print(f"{'='*60}\n")

    # Initialize files based on logging mode
    if allow_file_io:
        try:
            ensure_file(config.DIPS_FILE, "channel,dip_start_s,dip_end_s,duration_ms,baseline_V,min_V,drop_V")

            if logging_mode in ["FULL_LOCAL", "EVENT_ONLY"]:
                ensure_file(config.BASELINE_SNAPSHOTS_FILE, "time_s,channel,baseline_V")

            if logging_mode == "FULL_LOCAL":
                ensure_file(config.MEDIANS_FILE, "time_s,channel,median_V")
        except Exception as e:
            print(f"FATAL: Failed to initialize files: {e}")
            if bool(getattr(config, "STATUS_LED_OFF_ON_EXIT", True)):
                _set_status_led(status_led, False)
            return

    settle_discards_cfg = getattr(config, "ADC_SETTLE_DISCARDS", 0)
    oversample_cfg = getattr(config, "ADC_OVERSAMPLE_COUNT", 1)
    trim_cfg = getattr(config, "ADC_TRIM_COUNT", 0)
    settle_us_cfg = getattr(config, "ADC_SETTLE_US", 0)
    channel_gain_cfg = getattr(config, "ADC_CHANNEL_GAIN", None)
    channel_offset_cfg = getattr(config, "ADC_CHANNEL_OFFSET_V", None)

    sampler = None
    sampler_attempts = (
        (
            "modern",
            {
                "settle_discard_count": settle_discards_cfg,
                "oversample_count": oversample_cfg,
                "trim_count": trim_cfg,
                "settle_us": settle_us_cfg,
                "channel_gain": channel_gain_cfg,
                "channel_offset_v": channel_offset_cfg,
            },
        ),
        (
            "legacy_settle_name",
            {
                "settle_discards": settle_discards_cfg,
                "oversample_count": oversample_cfg,
                "trim_count": trim_cfg,
                "settle_us": settle_us_cfg,
                "channel_gain": channel_gain_cfg,
                "channel_offset_v": channel_offset_cfg,
            },
        ),
        (
            "modern_no_cal",
            {
                "settle_discard_count": settle_discards_cfg,
                "oversample_count": oversample_cfg,
                "trim_count": trim_cfg,
                "settle_us": settle_us_cfg,
            },
        ),
        (
            "legacy_no_cal",
            {
                "settle_discards": settle_discards_cfg,
                "oversample_count": oversample_cfg,
                "trim_count": trim_cfg,
                "settle_us": settle_us_cfg,
            },
        ),
    )
    sampler_errors = []
    for mode, kwargs in sampler_attempts:
        try:
            sampler = AdcSampler(config.CHANNEL_PINS, config.VREF, **kwargs)
            if mode != "modern":
                print(f"Warning: Using ADC sampler compatibility mode '{mode}'.")
            break
        except TypeError as e:
            sampler_errors.append(f"{mode}: {e}")

    if sampler is None:
        if sampler_errors:
            print(f"FATAL: Failed to initialize ADC sampler: {sampler_errors[-1]}")
        else:
            print("FATAL: Failed to initialize ADC sampler: unknown constructor mismatch")
        if bool(getattr(config, "STATUS_LED_OFF_ON_EXIT", True)):
            _set_status_led(status_led, False)
        return
    stats = StatsTracker()

    states = {}
    for name, _gp in config.CHANNEL_PINS:
        states[name] = ChannelState(
            stable_window=config.STABLE_WINDOW,
            median_block=config.MEDIAN_BLOCK,
            baseline_init_samples=config.BASELINE_INIT_SAMPLES,
            baseline_alpha=config.BASELINE_ALPHA
        )

    dip = DipDetector(
        threshold_v=config.DIP_THRESHOLD_V,
        recovery_margin_v=config.RECOVERY_MARGIN_V,
        start_hold=config.DIP_START_HOLD,
        end_hold=config.DIP_END_HOLD,
        cooldown_ms=config.DIP_COOLDOWN_MS
    )

    medlog = MedianLogger(config.MEDIANS_FILE)
    core1 = None
    if dual_core_requested:
        if _thread is None:
            if allow_runtime_prints:
                print("Warning: _thread unavailable; using single-core loop.")
            perf_io = None
        else:
            core1 = _Core1Bridge(
                stats=stats,
                logging_mode=logging_mode,
                ui_ref=ui,
                medlog=medlog,
                perf_rt=perf,
                perf_io=perf_io
            )
            if not core1.start():
                core1 = None
                perf_io = None
            elif allow_runtime_prints:
                print("Core1 worker started: OLED/USB/file/reporting offloaded.")

    next_tick_ms = _ticks_add(_ticks_ms(), config.TICK_MS)
    last_flush_ms = _ticks_ms()
    last_status_ms = _ticks_ms()
    last_stats_ms = _ticks_ms()
    last_baseline_snapshot_ms = _ticks_ms()
    last_perf_ms = _ticks_ms()
    tick_count = 0
    ui_next_event_id = 1
    ui_active_event_id_by_channel = {}
    handlers = _LoopHandlers(stats, perf, logging_mode, ui, ui_active_event_id_by_channel, core1_bridge=core1)
    ui_plot_require_all_channels = bool(getattr(config, "UI_MAIN_PLOT_REQUIRE_ALL_CHANNELS", False))
    ui_plot_default_adc_v = float(getattr(config, "UI_MAIN_PLOT_DEFAULT_ADC_V", 0.0))
    if ui_plot_default_adc_v < 0:
        ui_plot_default_adc_v = 0.0
    last_plot_adc = {"BLUE": None, "YELLOW": None, "GREEN": None}
    ui_plot_rendered = 0
    ui_plot_skipped = 0
    ui_plot_fallback_frames = 0

    if allow_runtime_prints:
        print("Starting sampling loop...")
        print("Press Ctrl+C to stop.\n")

    try:
        while True:
            loop_start_us = _ticks_us()
            now_ms = _ticks_ms()

            wait = _ticks_diff(next_tick_ms, now_ms)
            if perf is not None and wait < 0:
                backlog_ticks = int((-wait) // config.TICK_MS)
                perf.observe_backlog(backlog_ticks)
                perf.add_missed_ticks(backlog_ticks)
            if wait > 0:
                _sleep_ms(wait)

            now_ms = _ticks_ms()
            t_s = now_ms / 1000.0
            next_tick_ms = _ticks_add(next_tick_ms, config.TICK_MS)
            tick_count += 1
            processing_start_us = _ticks_us() if perf is not None else None

            adc_start_us = _ticks_us() if perf is not None else None
            readings = sampler.read_all_volts()  # ADC volts
            if perf is not None:
                perf.add_timing("adc_us", _ticks_diff(_ticks_us(), adc_start_us))

            state_elapsed_us = 0
            dip_elapsed_us = 0

            # Per-tick processing (detection stays in ADC volts)
            for name, v in readings:
                state_start_us = _ticks_us() if perf is not None else None
                stats.record_sample()
                st = states[name]

                st.update_raw_window(v)
                st.update_median_block(v)

                stable = False
                if st.raw_window_ready():
                    vmin, vmax = st.raw_window_bounds()
                    span = vmax - vmin
                    stable = (vmin >= config.MIN_V) and (vmax <= config.MAX_V) and (span <= config.STABLE_SPAN_V)

                st.stable = stable

                if st.stable:
                    st.last_stable_ms = now_ms
                    if not st.dip_active:
                        st.update_baseline_with_raw(v)
                        if st.baseline is not None:
                            stats.record_baseline_valid(name)
                elif st.baseline is None:
                    st.reset_baseline_seed()

                if perf is not None and state_start_us is not None:
                    state_elapsed_us += _ticks_diff(_ticks_us(), state_start_us)

                was_dip_active = st.dip_active
                handlers.current_channel = name
                dip_start_us = _ticks_us() if perf is not None else None
                dip.process_sample(
                    now_ms=now_ms,
                    t_s=t_s,
                    channel_name=name,
                    v=v,
                    st=st,
                    print_fn=handlers.dip_callback,
                    append_line_fn=handlers.dip_append,
                    dips_file=config.DIPS_FILE
                )
                if perf is not None and dip_start_us is not None:
                    dip_elapsed_us += _ticks_diff(_ticks_us(), dip_start_us)
                if ui is not None:
                    if (not was_dip_active) and st.dip_active:
                        ui_active_event_id_by_channel[name] = ui_next_event_id
                        ui_next_event_id += 1
                    if st.dip_active:
                        baseline_v = st.dip_baseline_v
                        min_v = st.dip_min_v
                        if baseline_v is not None and min_v is not None:
                            drop_v = baseline_v - min_v
                            if drop_v < 0:
                                drop_v = 0.0
                            if core1 is not None:
                                queued = core1.queue_ui_dip_event(
                                    name,
                                    baseline_v,
                                    min_v,
                                    drop_v,
                                    event_id=ui_active_event_id_by_channel.get(name),
                                    active=True,
                                    sample_index=None
                                )
                                if not queued:
                                    ui.record_dip_event_adc(
                                        name,
                                        baseline_v,
                                        min_v,
                                        drop_v,
                                        event_id=ui_active_event_id_by_channel.get(name),
                                        active=True,
                                        sample_index=getattr(ui, "sample_counter", None)
                                    )
                            else:
                                ui.record_dip_event_adc(
                                    name,
                                    baseline_v,
                                    min_v,
                                    drop_v,
                                    event_id=ui_active_event_id_by_channel.get(name),
                                    active=True,
                                    sample_index=getattr(ui, "sample_counter", None)
                                )

            if perf is not None:
                perf.add_timing("state_us", state_elapsed_us)
                perf.add_timing("dip_us", dip_elapsed_us)

            # Every 100 ms: compute medians + logging + OLED
            median_stage_start_us = _ticks_us() if perf is not None else None
            if (tick_count % config.MEDIAN_BLOCK) == 0:
                meds = {}
                for name, _gp in config.CHANNEL_PINS:
                    st = states[name]
                    med_v = st.compute_block_median_and_clear()
                    if med_v is None:
                        continue

                    meds[name] = med_v
                    stats.record_median_computed()

                    if st.stable:
                        if logging_mode == "USB_STREAM":
                            if core1 is not None:
                                queued = core1.queue_usb_median(t_s, name, med_v)
                                if not queued:
                                    usb_start_us = _ticks_us() if perf is not None else None
                                    usb_stream_median(t_s, name, med_v)
                                    if perf is not None:
                                        perf.add_timing("usb_write_us", _ticks_diff(_ticks_us(), usb_start_us))
                            else:
                                usb_start_us = _ticks_us() if perf is not None else None
                                usb_stream_median(t_s, name, med_v)
                                if perf is not None:
                                    perf.add_timing("usb_write_us", _ticks_diff(_ticks_us(), usb_start_us))
                            stats.record_median_logged()
                        elif logging_mode == "FULL_LOCAL":
                            # FULL_LOCAL stores ADC volts (unchanged)
                            if core1 is not None:
                                queued = core1.queue_median_add(t_s, name, med_v)
                                if not queued:
                                    medlog.add(t_s, name, med_v)
                            else:
                                medlog.add(t_s, name, med_v)
                            stats.record_median_logged()

                if ui is not None:
                    for ch in ("BLUE", "YELLOW", "GREEN"):
                        if ch in meds:
                            last_plot_adc[ch] = meds[ch]

                    if ui_plot_require_all_channels:
                        if all(ch in meds for ch in ("BLUE", "YELLOW", "GREEN")):
                            if core1 is not None:
                                queued = core1.queue_ui_plot(
                                    meds["BLUE"],
                                    meds["YELLOW"],
                                    meds["GREEN"]
                                )
                                if (not queued):
                                    ui_start_us = _ticks_us() if perf is not None else None
                                    ui.plot_medians_adc(
                                        meds["BLUE"],
                                        meds["YELLOW"],
                                        meds["GREEN"]
                                    )
                                    if perf is not None:
                                        perf.add_timing("ui_frame_us", _ticks_diff(_ticks_us(), ui_start_us))
                            else:
                                ui_start_us = _ticks_us() if perf is not None else None
                                ui.plot_medians_adc(
                                    meds["BLUE"],
                                    meds["YELLOW"],
                                    meds["GREEN"]
                                )
                                if perf is not None:
                                    perf.add_timing("ui_frame_us", _ticks_diff(_ticks_us(), ui_start_us))
                            ui_plot_rendered += 1
                        else:
                            ui_plot_skipped += 1
                    else:
                        fallback_used = False
                        plot_vals = {}
                        for ch in ("BLUE", "YELLOW", "GREEN"):
                            if ch in meds:
                                plot_vals[ch] = meds[ch]
                                continue

                            cached_v = last_plot_adc[ch]
                            if cached_v is None:
                                plot_vals[ch] = ui_plot_default_adc_v
                            else:
                                plot_vals[ch] = cached_v
                            fallback_used = True

                        if core1 is not None:
                            queued = core1.queue_ui_plot(
                                plot_vals["BLUE"],
                                plot_vals["YELLOW"],
                                plot_vals["GREEN"]
                            )
                            if not queued:
                                ui_start_us = _ticks_us() if perf is not None else None
                                ui.plot_medians_adc(
                                    plot_vals["BLUE"],
                                    plot_vals["YELLOW"],
                                    plot_vals["GREEN"]
                                )
                                if perf is not None:
                                    perf.add_timing("ui_frame_us", _ticks_diff(_ticks_us(), ui_start_us))
                        else:
                            ui_start_us = _ticks_us() if perf is not None else None
                            ui.plot_medians_adc(
                                plot_vals["BLUE"],
                                plot_vals["YELLOW"],
                                plot_vals["GREEN"]
                            )
                            if perf is not None:
                                perf.add_timing("ui_frame_us", _ticks_diff(_ticks_us(), ui_start_us))
                        ui_plot_rendered += 1
                        if fallback_used:
                            ui_plot_fallback_frames += 1
            if perf is not None and median_stage_start_us is not None:
                perf.add_timing("median_us", _ticks_diff(_ticks_us(), median_stage_start_us))

            # Flush medians in batches (FULL_LOCAL mode only)
            if logging_mode == "FULL_LOCAL":
                if _ticks_diff(now_ms, last_flush_ms) >= int(config.MEDIAN_FLUSH_EVERY_S * 1000):
                    if core1 is not None:
                        queued = core1.queue_median_flush_and_trim()
                        if not queued:
                            flash_start_us = _ticks_us() if perf is not None else None
                            lines_written = medlog.flush_to_file(append_lines)
                            stats.record_flash_write(lines_written)
                            if perf is not None:
                                perf.add_timing("flash_write_us", _ticks_diff(_ticks_us(), flash_start_us))
                            check_file_size_limit(
                                config.MEDIANS_FILE,
                                config.MAX_MEDIANS_SIZE_BYTES,
                                "time_s,channel,median_V",
                                config.MAX_MEDIANS_LINES
                            )
                    else:
                        flash_start_us = _ticks_us() if perf is not None else None
                        lines_written = medlog.flush_to_file(append_lines)
                        stats.record_flash_write(lines_written)
                        if perf is not None:
                            perf.add_timing("flash_write_us", _ticks_diff(_ticks_us(), flash_start_us))

                        check_file_size_limit(
                            config.MEDIANS_FILE,
                            config.MAX_MEDIANS_SIZE_BYTES,
                            "time_s,channel,median_V",
                            config.MAX_MEDIANS_LINES
                        )
                    last_flush_ms = now_ms

            # Baseline snapshots (EVENT_ONLY and FULL_LOCAL modes)
            if logging_mode in ["EVENT_ONLY", "FULL_LOCAL"]:
                if _ticks_diff(now_ms, last_baseline_snapshot_ms) >= int(config.BASELINE_SNAPSHOT_EVERY_S * 1000):
                    for name, _gp in config.CHANNEL_PINS:
                        st = states[name]
                        if st.baseline is not None:
                            line = f"{t_s:.3f},{name},{st.baseline:.3f}\n"  # ADC volts
                            if core1 is not None:
                                queued = core1.queue_file_append(config.BASELINE_SNAPSHOTS_FILE, line)
                                if not queued:
                                    flash_start_us = _ticks_us() if perf is not None else None
                                    if append_line(config.BASELINE_SNAPSHOTS_FILE, line):
                                        stats.record_flash_write()
                                    if perf is not None:
                                        perf.add_timing("flash_write_us", _ticks_diff(_ticks_us(), flash_start_us))
                            else:
                                flash_start_us = _ticks_us() if perf is not None else None
                                if append_line(config.BASELINE_SNAPSHOTS_FILE, line):
                                    stats.record_flash_write()
                                if perf is not None:
                                    perf.add_timing("flash_write_us", _ticks_diff(_ticks_us(), flash_start_us))
                    last_baseline_snapshot_ms = now_ms

            # USB baseline snapshots (scaled to REAL volts for streaming)
            if logging_mode == "USB_STREAM":
                if _ticks_diff(now_ms, last_baseline_snapshot_ms) >= int(config.BASELINE_SNAPSHOT_EVERY_S * 1000):
                    for name, _gp in config.CHANNEL_PINS:
                        st = states[name]
                        if st.baseline is not None:
                            if core1 is not None:
                                queued = core1.queue_usb_baseline(t_s, name, st.baseline)
                                if not queued:
                                    usb_start_us = _ticks_us() if perf is not None else None
                                    usb_stream_baseline(t_s, name, st.baseline)
                                    if perf is not None:
                                        perf.add_timing("usb_write_us", _ticks_diff(_ticks_us(), usb_start_us))
                            else:
                                usb_start_us = _ticks_us() if perf is not None else None
                                usb_stream_baseline(t_s, name, st.baseline)
                                if perf is not None:
                                    perf.add_timing("usb_write_us", _ticks_diff(_ticks_us(), usb_start_us))
                    last_baseline_snapshot_ms = now_ms

            # Status line
            if allow_runtime_prints and _ticks_diff(now_ms, last_status_ms) >= int(config.SHELL_STATUS_EVERY_S * 1000):
                parts = []
                for name, _gp in config.CHANNEL_PINS:
                    st = states[name]
                    b = st.baseline
                    btxt = "None" if b is None else f"{b:.3f}"
                    parts.append(f"{name}: stable={1 if st.stable else 0} base={btxt} dip={1 if st.dip_active else 0}")
                status_line = f"{t_s:8.1f}s  " + "  ".join(parts)
                if core1 is not None:
                    if not core1.queue_print(status_line):
                        print(status_line)
                else:
                    print(status_line)
                if ui is not None:
                    oled_line = "          OLED: rendered={} skipped={} fallback={}".format(
                        ui_plot_rendered, ui_plot_skipped, ui_plot_fallback_frames
                    )
                    if core1 is not None:
                        if not core1.queue_print(oled_line):
                            print(oled_line)
                    else:
                        print(oled_line)
                last_status_ms = now_ms

            # Stats report
            if allow_runtime_prints and _ticks_diff(now_ms, last_stats_ms) >= int(config.STATS_REPORT_EVERY_S * 1000):
                if core1 is not None:
                    if not core1.queue_stats_print():
                        stats.print_summary(config.MEDIANS_FILE, config.DIPS_FILE)
                else:
                    stats.print_summary(config.MEDIANS_FILE, config.DIPS_FILE)
                last_stats_ms = now_ms

            if perf is not None and _ticks_diff(now_ms, last_perf_ms) >= int(config.PERF_REPORT_EVERY_S * 1000):
                if core1 is not None:
                    if not core1.queue_perf_report():
                        gc_start_us = _ticks_us()
                        gc.collect()
                        perf.record_gc(_ticks_diff(_ticks_us(), gc_start_us))
                        if allow_runtime_prints:
                            for line in perf.summary_lines():
                                print(line)
                else:
                    gc_start_us = _ticks_us()
                    gc.collect()
                    perf.record_gc(_ticks_diff(_ticks_us(), gc_start_us))
                    if allow_runtime_prints:
                        for line in perf.summary_lines():
                            print(line)
                last_perf_ms = now_ms

            if perf is not None:
                if core1 is not None:
                    perf.observe_backlog(core1.queue_depth())
                if processing_start_us is not None:
                    perf.add_timing("processing_us", _ticks_diff(_ticks_us(), processing_start_us))
                perf.add_timing("loop_us", _ticks_diff(_ticks_us(), loop_start_us))

    except KeyboardInterrupt:
        if allow_runtime_prints:
            print("\n\nShutdown requested. Flushing buffers...")

        if core1 is not None:
            if logging_mode == "FULL_LOCAL":
                core1.queue_median_flush_and_trim()
            core1.queue_ui_shutdown()
            if allow_runtime_prints:
                core1.queue_print("\nFinal statistics:")
                core1.queue_stats_print()
                core1.queue_perf_report()
            core1.stop(timeout_ms=3000)
        else:
            if logging_mode == "FULL_LOCAL" and medlog.buffer:
                lines_written = medlog.flush_to_file(append_lines)
                if allow_runtime_prints:
                    print(f"Flushed {lines_written} median lines to flash")

            if ui is not None:
                ui.shutdown()
        if bool(getattr(config, "STATUS_LED_OFF_ON_EXIT", True)):
            _set_status_led(status_led, False)

        if allow_runtime_prints and core1 is None:
            print("\nFinal statistics:")
            stats.print_summary(config.MEDIANS_FILE, config.DIPS_FILE)
            if perf is not None:
                for line in perf.summary_lines():
                    print(line)
            print("\nShutdown complete.")
        elif allow_runtime_prints:
            print("\nShutdown complete.")

    except Exception as e:
        if core1 is not None:
            core1.stop(timeout_ms=1000)
        if bool(getattr(config, "STATUS_LED_OFF_ON_EXIT", True)):
            _set_status_led(status_led, False)
        print(f"\nFATAL ERROR: {e}")
        import sys
        sys.print_exception(e)

if __name__ == "__main__":
    run()

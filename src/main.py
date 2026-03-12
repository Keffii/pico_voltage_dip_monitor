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


class _UiPlotMailbox:
    def __init__(self):
        self.blue_v = None
        self.yellow_v = None
        self.green_v = None
        self.pending = False
        self.lock = _thread.allocate_lock() if _thread is not None else None

    def _lock_enter(self):
        if self.lock is not None:
            self.lock.acquire()

    def _lock_exit(self):
        if self.lock is not None:
            self.lock.release()

    def offer(self, blue_v, yellow_v, green_v):
        self._lock_enter()
        try:
            self.blue_v = blue_v
            self.yellow_v = yellow_v
            self.green_v = green_v
            self.pending = True
            return True
        finally:
            self._lock_exit()

    def take(self):
        self._lock_enter()
        try:
            if not self.pending:
                return None
            item = (self.blue_v, self.yellow_v, self.green_v)
            self.pending = False
            return item
        finally:
            self._lock_exit()

    def depth(self):
        self._lock_enter()
        try:
            return 1 if self.pending else 0
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
    EVT_UI_SOURCE_OFF = 14
    EVT_UI_CANCEL_EVENT = 15
    EVT_STOP = 255

    def __init__(self, stats, logging_mode, ui_ref, medlog, perf_rt=None, perf_io=None, ui_diag=None):
        self.stats = stats
        self.logging_mode = logging_mode
        self.ui = ui_ref
        self.medlog = medlog
        self.perf_rt = perf_rt
        self.perf_io = perf_io
        self.ui_diag = ui_diag
        self.allow_file_io = (logging_mode != "DISPLAY_ONLY")
        self.allow_runtime_prints = (logging_mode != "DISPLAY_ONLY")
        self.allow_usb_stream = (logging_mode == "USB_STREAM")
        self.idle_sleep_ms = int(getattr(config, "CORE1_IDLE_SLEEP_MS", 1))
        if self.idle_sleep_ms < 0:
            self.idle_sleep_ms = 0
        queue_size = int(getattr(config, "CORE1_QUEUE_SIZE", 256))
        self.queue = _Core1EventQueue(queue_size)
        self.ui_plot_mailbox = _UiPlotMailbox() if self.ui is not None else None
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
        depth = self.queue.depth()
        if self.ui_plot_mailbox is not None:
            depth += self.ui_plot_mailbox.depth()
        return depth

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
        if self.ui_plot_mailbox is not None:
            return self.ui_plot_mailbox.offer(blue_v, yellow_v, green_v)
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

    def queue_ui_source_off_state(self, active):
        if self.ui is None:
            return True
        return self.queue.push(self.EVT_UI_SOURCE_OFF, bool(active))

    def queue_ui_cancel_event(self, event_id):
        if self.ui is None:
            return True
        return self.queue.push(self.EVT_UI_CANCEL_EVENT, event_id)

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
                if self.ui is not None and (not self._ui_failed) and hasattr(self.ui, "poll_inputs"):
                    try:
                        if self.ui_diag is not None:
                            self.ui_diag.record_input_poll(_ticks_ms())
                        self.ui.poll_inputs()
                    except Exception as poll_err:
                        self._ui_failed = True
                        if self.allow_runtime_prints:
                            print(f"Warning: Core1 UI input poll failed: {poll_err}")
                item = self.queue.pop()
                if item is None and self.ui_plot_mailbox is not None:
                    plot_item = self.ui_plot_mailbox.take()
                    if plot_item is not None:
                        item = (
                            self.EVT_UI_PLOT,
                            plot_item[0],
                            plot_item[1],
                            plot_item[2],
                            None,
                            None,
                            None,
                            None,
                            None,
                        )
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
                            start_us = _ticks_us()
                            self.ui.plot_medians_adc(p0, p1, p2)
                            duration_us = _ticks_diff(_ticks_us(), start_us)
                            if self.perf_io is not None:
                                self.perf_io.add_timing("ui_frame_us", duration_us)
                            if self.ui_diag is not None:
                                self.ui_diag.record_ui_frame(duration_us, fallback=False)

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

                    elif kind == self.EVT_UI_SOURCE_OFF:
                        if self.ui is not None and (not self._ui_failed):
                            self.ui.set_source_off_state(bool(p0))

                    elif kind == self.EVT_UI_CANCEL_EVENT:
                        if self.ui is not None and (not self._ui_failed):
                            self.ui.cancel_dip_event(p0)

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
                        self.EVT_UI_SOURCE_OFF,
                        self.EVT_UI_CANCEL_EVENT,
                        self.EVT_UI_SHUTDOWN,
                    ):
                        self._ui_failed = True
                    if self.allow_runtime_prints:
                        print(f"Warning: Core1 event failed ({kind}): {event_err}")
        finally:
            self._alive = 0


def _ui_should_refresh_between_medians(ui_ref):
    return ui_ref is not None


def _render_ui_plot_frame(ui_runtime, core1, ui_core1_strict, perf, plot_vals, ui_diag=None):
    rendered_frame = False
    if core1 is not None:
        queued = core1.queue_ui_plot(
            plot_vals[0],
            plot_vals[1],
            plot_vals[2]
        )
        if not queued:
            if not ui_core1_strict:
                ui_start_us = _ticks_us() if perf is not None else None
                ui_runtime.plot_medians_adc(
                    plot_vals[0],
                    plot_vals[1],
                    plot_vals[2]
                )
                duration_us = _ticks_diff(_ticks_us(), ui_start_us)
                if perf is not None:
                    perf.add_timing("ui_frame_us", duration_us)
                if ui_diag is not None:
                    ui_diag.record_ui_frame(duration_us, fallback=True)
                rendered_frame = True
        else:
            rendered_frame = True
    else:
        ui_start_us = _ticks_us() if perf is not None else None
        ui_runtime.plot_medians_adc(
            plot_vals[0],
            plot_vals[1],
            plot_vals[2]
        )
        duration_us = _ticks_diff(_ticks_us(), ui_start_us)
        if perf is not None:
            perf.add_timing("ui_frame_us", duration_us)
        if ui_diag is not None:
            ui_diag.record_ui_frame(duration_us, fallback=False)
        rendered_frame = True
    return rendered_frame


class _UiRuntimeDiagnostics:
    def __init__(self, enabled=False):
        self.enabled = bool(enabled)
        self.input_poll_count = 0
        self.input_poll_gap_max_ms = 0
        self._last_input_poll_ms = None
        self.full_redraw_count = 0
        self.partial_redraw_count = 0
        self.partial_redraw_regions = 0
        self.full_flush_count = 0
        self.partial_flush_count = 0
        self.full_flush_max_us = 0
        self.partial_flush_max_us = 0
        self.partial_flush_rects = 0
        self.queue_depth_max = 0
        self.ui_frame_count = 0
        self.ui_frame_total_us = 0
        self.ui_frame_max_us = 0
        self.ui_fallback_count = 0
        self.ui_skipped_count = 0

    def record_input_poll(self, now_ms):
        if not self.enabled:
            return
        self.input_poll_count += 1
        if self._last_input_poll_ms is not None:
            gap_ms = _ticks_diff(now_ms, self._last_input_poll_ms)
            if gap_ms > self.input_poll_gap_max_ms:
                self.input_poll_gap_max_ms = gap_ms
        self._last_input_poll_ms = now_ms

    def record_full_redraw(self):
        if not self.enabled:
            return
        self.full_redraw_count += 1

    def record_partial_redraw(self, region_count=1):
        if not self.enabled:
            return
        self.partial_redraw_count += 1
        if region_count > 0:
            self.partial_redraw_regions += int(region_count)

    def record_full_flush(self, duration_us):
        if not self.enabled:
            return
        self.full_flush_count += 1
        if duration_us > self.full_flush_max_us:
            self.full_flush_max_us = int(duration_us)

    def record_partial_flush(self, duration_us, rect_count=1):
        if not self.enabled:
            return
        self.partial_flush_count += 1
        if duration_us > self.partial_flush_max_us:
            self.partial_flush_max_us = int(duration_us)
        if rect_count > 0:
            self.partial_flush_rects += int(rect_count)

    def record_queue_depth(self, depth):
        if not self.enabled:
            return
        depth = int(depth)
        if depth > self.queue_depth_max:
            self.queue_depth_max = depth

    def record_ui_frame(self, duration_us, fallback=False):
        if not self.enabled:
            return
        duration_us = int(duration_us)
        self.ui_frame_count += 1
        self.ui_frame_total_us += duration_us
        if duration_us > self.ui_frame_max_us:
            self.ui_frame_max_us = duration_us
        if fallback:
            self.ui_fallback_count += 1

    def record_ui_skip(self):
        if not self.enabled:
            return
        self.ui_skipped_count += 1

    def snapshot(self):
        return {
            "enabled": self.enabled,
            "input_poll_count": self.input_poll_count,
            "input_poll_gap_max_ms": self.input_poll_gap_max_ms,
            "full_redraw_count": self.full_redraw_count,
            "partial_redraw_count": self.partial_redraw_count,
            "partial_redraw_regions": self.partial_redraw_regions,
            "full_flush_count": self.full_flush_count,
            "partial_flush_count": self.partial_flush_count,
            "full_flush_max_us": self.full_flush_max_us,
            "partial_flush_max_us": self.partial_flush_max_us,
            "partial_flush_rects": self.partial_flush_rects,
            "queue_depth_max": self.queue_depth_max,
            "ui_frame_count": self.ui_frame_count,
            "ui_frame_total_us": self.ui_frame_total_us,
            "ui_frame_max_us": self.ui_frame_max_us,
            "ui_fallback_count": self.ui_fallback_count,
            "ui_skipped_count": self.ui_skipped_count,
        }


def _emit_ui_runtime_report(core1, line):
    if core1 is not None and getattr(core1, "allow_runtime_prints", False):
        if core1.queue_print(line):
            return
    print(line)


def _format_ui_runtime_summary(uptime_s, snapshot):
    return (
        "{:6.1f}s  UIRT  qmax={} frame={} frame_max_us={} frame_total_us={} skip={} fallback={} poll_gap_max_ms={}".format(
            uptime_s,
            snapshot.get("queue_depth_max", 0),
            snapshot.get("ui_frame_count", 0),
            snapshot.get("ui_frame_max_us", 0),
            snapshot.get("ui_frame_total_us", 0),
            snapshot.get("ui_skipped_count", 0),
            snapshot.get("ui_fallback_count", 0),
            snapshot.get("input_poll_gap_max_ms", 0),
        )
    )


class _DisplaySignalFilter:
    def __init__(self, window_size=5, ema_alpha=0.5):
        self.window_size = int(window_size)
        if self.window_size < 1:
            self.window_size = 1
        self.ema_alpha = float(ema_alpha)
        if self.ema_alpha <= 0 or self.ema_alpha > 1.0:
            self.ema_alpha = 0.5
        self.samples = [0.0] * self.window_size
        self.sorted_buf = [0.0] * self.window_size
        self.count = 0
        self.index = 0
        self.filtered_v = None

    def _median(self):
        count = self.count
        if count <= 0:
            return 0.0
        for i in range(count):
            self.sorted_buf[i] = self.samples[i]
        i = 1
        while i < count:
            key = self.sorted_buf[i]
            j = i - 1
            while j >= 0 and self.sorted_buf[j] > key:
                self.sorted_buf[j + 1] = self.sorted_buf[j]
                j -= 1
            self.sorted_buf[j + 1] = key
            i += 1
        mid = count // 2
        if (count % 2) == 1:
            return self.sorted_buf[mid]
        return (self.sorted_buf[mid - 1] + self.sorted_buf[mid]) * 0.5

    def update(self, value_v):
        self.samples[self.index] = value_v
        self.index += 1
        if self.index >= self.window_size:
            self.index = 0
        if self.count < self.window_size:
            self.count += 1

        median_v = self._median()
        if self.filtered_v is None:
            self.filtered_v = median_v
        else:
            self.filtered_v += (median_v - self.filtered_v) * self.ema_alpha
        return self.filtered_v


class _UiFrameScheduler:
    def __init__(self, require_all_channels=False, default_adc_v=0.0, frame_interval_ms=0):
        self.require_all_channels = bool(require_all_channels)
        self.default_adc_v = float(default_adc_v)
        if self.default_adc_v < 0:
            self.default_adc_v = 0.0
        self.frame_interval_ms = int(frame_interval_ms)
        if self.frame_interval_ms < 0:
            self.frame_interval_ms = 0
        self.latest_adc = {"BLUE": None, "YELLOW": None, "GREEN": None}
        self.next_frame_ms = None
        self.used_fallback = False

    def update_latest(self, channel_name, adc_v):
        if channel_name in self.latest_adc:
            self.latest_adc[channel_name] = adc_v

    def maybe_get_plot_values(self, now_ms):
        if self.require_all_channels:
            for channel_name in ("BLUE", "YELLOW", "GREEN"):
                if self.latest_adc[channel_name] is None:
                    self.used_fallback = False
                    return None

        if self.next_frame_ms is not None and self.frame_interval_ms > 0:
            if _ticks_diff(now_ms, self.next_frame_ms) < 0:
                self.used_fallback = False
                return None

        plot_vals = []
        fallback_used = False
        for channel_name in ("BLUE", "YELLOW", "GREEN"):
            adc_v = self.latest_adc[channel_name]
            if adc_v is None:
                adc_v = self.default_adc_v
                fallback_used = True
            plot_vals.append(adc_v)

        self.used_fallback = fallback_used
        if self.frame_interval_ms > 0:
            self.next_frame_ms = _ticks_add(now_ms, self.frame_interval_ms)
        else:
            self.next_frame_ms = now_ms
        return tuple(plot_vals)


class _LoopHandlers:
    def __init__(self, stats, perf, logging_mode, ui_ref, ui_event_map, core1_bridge=None):
        self.stats = stats
        self.perf = perf
        self.logging_mode = logging_mode
        self.core1 = core1_bridge
        self.ui_core1_strict = bool(getattr(config, "UI_CORE1_STRICT", False))
        self.ui = ui_ref
        if self.ui_core1_strict and self.core1 is None:
            self.ui = None
        self.ui_active_event_id_by_channel = ui_event_map
        self.current_channel = None
        self.allow_file_io = (logging_mode != "DISPLAY_ONLY")
        self.allow_runtime_prints = (logging_mode != "DISPLAY_ONLY")
        self.allow_usb_stream = (logging_mode == "USB_STREAM")
        self.adc_debug_terminal_enabled = bool(getattr(config, "ADC_DEBUG_TERMINAL_ENABLED", False))
        self.adc_debug_terminal_show_ui_events = bool(getattr(config, "ADC_DEBUG_TERMINAL_SHOW_UI_EVENTS", True))
        self.adc_debug_terminal_channel_filter = str(getattr(config, "ADC_DEBUG_TERMINAL_CHANNEL_FILTER", "ALL")).upper()
        if self.adc_debug_terminal_channel_filter not in ("ALL", "BLUE", "YELLOW", "GREEN"):
            self.adc_debug_terminal_channel_filter = "ALL"

    def _record_timing(self, name, start_us):
        if self.perf is None or start_us is None:
            return
        self.perf.add_timing(name, _ticks_diff(_ticks_us(), start_us))

    def _emit_runtime_debug(self, msg):
        if not self.allow_runtime_prints:
            return
        if self.core1 is not None:
            if not self.core1.queue_print(msg):
                print(msg)
        else:
            print(msg)

    def set_ui_source_off_state(self, active):
        if self.ui is None:
            return True
        if self.core1 is not None:
            queued = self.core1.queue_ui_source_off_state(active)
            if not queued:
                if self.ui_core1_strict:
                    return False
                self.ui.set_source_off_state(active)
                return True
            return True
        self.ui.set_source_off_state(active)
        return True

    def cancel_ui_dip_event(self, event_id):
        if event_id is None or self.ui is None:
            return True
        if self.core1 is not None:
            queued = self.core1.queue_ui_cancel_event(event_id)
            if not queued:
                if self.ui_core1_strict:
                    return False
                self.ui.cancel_dip_event(event_id)
                return True
            return True
        self.ui.cancel_dip_event(event_id)
        return True

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
                ui_path = None
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
                        if not self.ui_core1_strict:
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
                            ui_path = "core1_fallback(q_latch={},q_event={})".format(
                                1 if queued_latch else 0,
                                1 if queued_event else 0
                            )
                        else:
                            ui_path = "core1_drop_strict(q_latch={},q_event={})".format(
                                1 if queued_latch else 0,
                                1 if queued_event else 0
                            )
                    else:
                        ui_path = "core1_queue"
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
                    ui_path = "core0_direct"

                if (
                    self.adc_debug_terminal_enabled
                    and self.adc_debug_terminal_show_ui_events
                    and (
                        self.adc_debug_terminal_channel_filter == "ALL"
                        or channel == self.adc_debug_terminal_channel_filter
                    )
                ):
                    event_id_txt = "None" if event_id is None else str(event_id)
                    marker = "ADCDBG_UI,ch={},drop={:.3f},id={},active=0,path={}".format(
                        channel,
                        drop_v,
                        event_id_txt,
                        ui_path
                    )
                    self._emit_runtime_debug(marker)

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
    ui_core1_strict = bool(getattr(config, "UI_CORE1_STRICT", False))
    ui_runtime = ui
    perf = None
    perf_io = None
    if bool(getattr(config, "PERF_METRICS_ENABLED", False)):
        perf = PerfMetrics(getattr(config, "PERF_RING_SIZE", 1024))
        if dual_core_requested:
            perf_io = PerfMetrics(getattr(config, "PERF_RING_SIZE", 1024))

    ui_runtime_diagnostics = _UiRuntimeDiagnostics(enabled=bool(getattr(config, "UI_PERF_DIAGNOSTICS_ENABLED", False)))
    ui_runtime_report_enabled = bool(getattr(config, "UI_RUNTIME_REPORT_ENABLED", False))
    ui_runtime_report_interval_ms = int(getattr(config, "UI_RUNTIME_REPORT_INTERVAL_MS", 1000))
    if ui_runtime_report_interval_ms < 100:
        ui_runtime_report_interval_ms = 100

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
                ui_ref=ui_runtime,
                medlog=medlog,
                perf_rt=perf,
                perf_io=perf_io,
                ui_diag=ui_runtime_diagnostics
            )
            if not core1.start():
                core1 = None
                perf_io = None
            elif allow_runtime_prints:
                print("Core1 worker started: OLED/USB/file/reporting offloaded.")

    if ui_core1_strict and ui_runtime is not None and core1 is None:
        if allow_runtime_prints:
            print("Warning: UI_CORE1_STRICT enabled and Core1 unavailable; running headless (OLED disabled).")
        ui_runtime = None

    next_tick_ms = _ticks_add(_ticks_ms(), config.TICK_MS)
    last_flush_ms = _ticks_ms()
    last_status_ms = _ticks_ms()
    last_stats_ms = _ticks_ms()
    last_baseline_snapshot_ms = _ticks_ms()
    last_perf_ms = _ticks_ms()
    tick_count = 0
    ui_next_event_id = 1
    ui_active_event_id_by_channel = {}
    handlers = _LoopHandlers(stats, perf, logging_mode, ui_runtime, ui_active_event_id_by_channel, core1_bridge=core1)
    ui_plot_require_all_channels = bool(getattr(config, "UI_MAIN_PLOT_REQUIRE_ALL_CHANNELS", False))
    ui_plot_default_adc_v = float(getattr(config, "UI_MAIN_PLOT_DEFAULT_ADC_V", 0.0))
    display_filter_window = int(getattr(config, "UI_DISPLAY_FILTER_WINDOW", 5))
    display_filter_alpha = float(getattr(config, "UI_DISPLAY_FILTER_ALPHA", 0.5))
    ui_frame_scheduler = _UiFrameScheduler(
        require_all_channels=ui_plot_require_all_channels,
        default_adc_v=ui_plot_default_adc_v,
        frame_interval_ms=0,
    )
    display_filters = {}
    for name, _gp in config.CHANNEL_PINS:
        display_filters[name] = _DisplaySignalFilter(
            window_size=display_filter_window,
            ema_alpha=display_filter_alpha,
        )
    ui_plot_rendered = 0
    ui_plot_skipped = 0
    ui_plot_fallback_frames = 0
    adc_debug_terminal_enabled = bool(getattr(config, "ADC_DEBUG_TERMINAL_ENABLED", False))
    adc_debug_terminal_interval_ms = int(getattr(config, "ADC_DEBUG_TERMINAL_INTERVAL_MS", 100))
    adc_debug_terminal_channel_filter = str(getattr(config, "ADC_DEBUG_TERMINAL_CHANNEL_FILTER", "ALL")).upper()
    if adc_debug_terminal_channel_filter not in ("ALL", "BLUE", "YELLOW", "GREEN"):
        adc_debug_terminal_channel_filter = "ALL"
    if adc_debug_terminal_interval_ms < 50:
        adc_debug_terminal_interval_ms = 50
    if not allow_runtime_prints:
        adc_debug_terminal_enabled = False
    last_adc_debug_ms = _ticks_ms()
    last_ui_runtime_report_ms = _ticks_ms()

    source_off_enabled = bool(getattr(config, "SOURCE_OFF_ENABLED", True))
    source_off_adc_v = float(getattr(config, "SOURCE_OFF_ADC_V", 0.08))
    source_off_hold_ms = int(getattr(config, "SOURCE_OFF_HOLD_MS", 250))
    source_off_release_adc_v = float(getattr(config, "SOURCE_OFF_RELEASE_ADC_V", 0.12))
    source_off_release_ms = int(getattr(config, "SOURCE_OFF_RELEASE_MS", 400))
    source_off_dip_cancel_window_ms = int(getattr(config, "SOURCE_OFF_DIP_CANCEL_WINDOW_MS", 2500))
    if source_off_adc_v < 0:
        source_off_adc_v = 0.0
    if source_off_release_adc_v < source_off_adc_v:
        source_off_release_adc_v = source_off_adc_v
    if source_off_hold_ms < 0:
        source_off_hold_ms = 0
    if source_off_release_ms < 0:
        source_off_release_ms = 0
    if source_off_dip_cancel_window_ms < 0:
        source_off_dip_cancel_window_ms = 0
    source_off_active = False
    source_off_candidate_since_ms = None
    source_off_recover_since_ms = None

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

            if ui_runtime is not None and core1 is None and hasattr(ui_runtime, "poll_inputs"):
                ui_runtime_diagnostics.record_input_poll(now_ms)
                ui_runtime.poll_inputs()

            fast_ui_refresh = _ui_should_refresh_between_medians(ui_runtime)

            adc_start_us = _ticks_us() if perf is not None else None
            readings = sampler.read_all_volts()  # ADC volts
            if perf is not None:
                perf.add_timing("adc_us", _ticks_diff(_ticks_us(), adc_start_us))
            adc_debug_snapshot = {} if adc_debug_terminal_enabled else None

            if source_off_enabled:
                all_at_or_below_off = True
                all_at_or_above_release = True
                for _ch_name, ch_v in readings:
                    if ch_v > source_off_adc_v:
                        all_at_or_below_off = False
                    if ch_v < source_off_release_adc_v:
                        all_at_or_above_release = False

                if not source_off_active:
                    source_off_recover_since_ms = None
                    if all_at_or_below_off:
                        if source_off_candidate_since_ms is None:
                            source_off_candidate_since_ms = now_ms
                        if _ticks_diff(now_ms, source_off_candidate_since_ms) >= source_off_hold_ms:
                            source_off_active = True
                            source_off_candidate_since_ms = None
                            source_off_recover_since_ms = None
                            handlers.set_ui_source_off_state(True)

                            # OFF transitions can produce false dip starts.
                            # Cancel only near-transition active dips and clear their detector state.
                            for ch_name, _gp in config.CHANNEL_PINS:
                                st = states[ch_name]
                                if not st.dip_active:
                                    continue

                                dip_age_ms = source_off_dip_cancel_window_ms + 1
                                if st.dip_start_s is not None:
                                    dip_age_ms = int(round((t_s - st.dip_start_s) * 1000.0))
                                    if dip_age_ms < 0:
                                        dip_age_ms = 0

                                if dip_age_ms <= source_off_dip_cancel_window_ms:
                                    event_id = ui_active_event_id_by_channel.pop(ch_name, None)
                                    handlers.cancel_ui_dip_event(event_id)

                                    st.dip_active = False
                                    st.dip_start_s = None
                                    st.dip_min_v = None
                                    st.dip_baseline_v = None
                                    st.below_count = 0
                                    st.first_below_ms = None
                                    st.above_count = 0
                                    st.cooldown_until_ms = _ticks_add(now_ms, dip.cooldown_ms)
                    else:
                        source_off_candidate_since_ms = None
                else:
                    source_off_candidate_since_ms = None
                    if all_at_or_above_release:
                        if source_off_recover_since_ms is None:
                            source_off_recover_since_ms = now_ms
                        if _ticks_diff(now_ms, source_off_recover_since_ms) >= source_off_release_ms:
                            source_off_active = False
                            source_off_recover_since_ms = None
                            handlers.set_ui_source_off_state(False)
                    else:
                        source_off_recover_since_ms = None

            state_elapsed_us = 0
            dip_elapsed_us = 0

            # Per-tick processing (detection stays in ADC volts)
            for name, v in readings:
                state_start_us = _ticks_us() if perf is not None else None
                stats.record_sample()
                st = states[name]

                st.update_raw_window(v)
                st.update_median_block(v)
                if ui_runtime is not None and fast_ui_refresh:
                    ui_display_v = display_filters[name].update(v)
                    ui_frame_scheduler.update_latest(name, ui_display_v)

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
                    dips_file=config.DIPS_FILE,
                    allow_start=(not source_off_active)
                )
                if perf is not None and dip_start_us is not None:
                    dip_elapsed_us += _ticks_diff(_ticks_us(), dip_start_us)
                if ui_runtime is not None:
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
                                    if not ui_core1_strict:
                                        ui_runtime.record_dip_event_adc(
                                            name,
                                            baseline_v,
                                            min_v,
                                            drop_v,
                                            event_id=ui_active_event_id_by_channel.get(name),
                                            active=True,
                                            sample_index=getattr(ui_runtime, "sample_counter", None)
                                        )
                            else:
                                ui_runtime.record_dip_event_adc(
                                    name,
                                    baseline_v,
                                    min_v,
                                    drop_v,
                                    event_id=ui_active_event_id_by_channel.get(name),
                                    active=True,
                                    sample_index=getattr(ui_runtime, "sample_counter", None)
                                )

                if adc_debug_terminal_enabled:
                    baseline_dbg = st.baseline
                    threshold_dbg = None
                    drop_dbg = None
                    if baseline_dbg is not None:
                        threshold_dbg = baseline_dbg - config.DIP_THRESHOLD_V
                        drop_dbg = baseline_dbg - v

                    cooldown_remaining_ms = _ticks_diff(st.cooldown_until_ms, now_ms)
                    in_cooldown = cooldown_remaining_ms > 0
                    if cooldown_remaining_ms < 0:
                        cooldown_remaining_ms = 0

                    recently_stable = (
                        st.stable or
                        (st.last_stable_ms is not None and _ticks_diff(now_ms, st.last_stable_ms) <= config.STABLE_GRACE_MS)
                    )
                    eligible = (
                        (baseline_dbg is not None)
                        and (not st.dip_active)
                        and recently_stable
                        and (not in_cooldown)
                        and (not source_off_active)
                    )
                    if adc_debug_terminal_channel_filter == "ALL" or name == adc_debug_terminal_channel_filter:
                        adc_debug_snapshot[name] = (
                            v,
                            baseline_dbg,
                            threshold_dbg,
                            drop_dbg,
                            st.stable,
                            st.dip_active,
                            cooldown_remaining_ms,
                            eligible
                        )

            if adc_debug_terminal_enabled and _ticks_diff(now_ms, last_adc_debug_ms) >= adc_debug_terminal_interval_ms:
                def _fmt_dbg(v):
                    if v is None:
                        return "None"
                    return "{:.3f}".format(v)

                dbg_parts = []
                for name, _gp in config.CHANNEL_PINS:
                    if adc_debug_terminal_channel_filter != "ALL" and name != adc_debug_terminal_channel_filter:
                        continue
                    snap = adc_debug_snapshot.get(name)
                    if snap is None:
                        dbg_parts.append("{}:v=None base=None thr=None drop=None stable=0 dip=0 cooldown_ms=0 eligible=0".format(name))
                        continue
                    v_dbg, base_dbg, thr_dbg, drop_dbg, stable_dbg, dip_dbg, cooldown_dbg, eligible_dbg = snap
                    dbg_parts.append(
                        "{}:v={} base={} thr={} drop={} stable={} dip={} cooldown_ms={} eligible={}".format(
                            name,
                            _fmt_dbg(v_dbg),
                            _fmt_dbg(base_dbg),
                            _fmt_dbg(thr_dbg),
                            _fmt_dbg(drop_dbg),
                            1 if stable_dbg else 0,
                            1 if dip_dbg else 0,
                            cooldown_dbg,
                            1 if eligible_dbg else 0,
                        )
                    )
                adc_line = "{:8.3f}s  ADCDBG  {}".format(t_s, " | ".join(dbg_parts))
                if core1 is not None:
                    if not core1.queue_print(adc_line):
                        print(adc_line)
                else:
                    print(adc_line)
                last_adc_debug_ms = now_ms

            if perf is not None:
                perf.add_timing("state_us", state_elapsed_us)
                perf.add_timing("dip_us", dip_elapsed_us)

            if ui_runtime is not None and fast_ui_refresh:
                plot_vals = ui_frame_scheduler.maybe_get_plot_values(now_ms)
                if plot_vals is not None:
                    rendered_frame = _render_ui_plot_frame(ui_runtime, core1, ui_core1_strict, perf, plot_vals, ui_diag=ui_runtime_diagnostics)
                    if rendered_frame:
                        ui_plot_rendered += 1
                        if ui_frame_scheduler.used_fallback:
                            ui_plot_fallback_frames += 1
                    else:
                        ui_plot_skipped += 1
                        ui_runtime_diagnostics.record_ui_skip()
                else:
                    ui_plot_skipped += 1
                    ui_runtime_diagnostics.record_ui_skip()

            # Every 100 ms: compute medians + logging
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

                if ui_runtime is not None and (not fast_ui_refresh):
                    plot_vals = ui_frame_scheduler.maybe_get_plot_values(now_ms)
                    if plot_vals is not None:
                        rendered_frame = _render_ui_plot_frame(ui_runtime, core1, ui_core1_strict, perf, plot_vals, ui_diag=ui_runtime_diagnostics)
                        if rendered_frame:
                            ui_plot_rendered += 1
                            if ui_frame_scheduler.used_fallback:
                                ui_plot_fallback_frames += 1
                        else:
                            ui_plot_skipped += 1
                    else:
                        ui_plot_skipped += 1
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
                if ui_runtime is not None:
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

            if core1 is not None:
                ui_runtime_diagnostics.record_queue_depth(core1.queue_depth())

            if ui_runtime_report_enabled and _ticks_diff(now_ms, last_ui_runtime_report_ms) >= ui_runtime_report_interval_ms:
                line = _format_ui_runtime_summary(t_s, ui_runtime_diagnostics.snapshot())
                _emit_ui_runtime_report(core1, line)
                last_ui_runtime_report_ms = now_ms

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

            if ui_runtime is not None:
                ui_runtime.shutdown()
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

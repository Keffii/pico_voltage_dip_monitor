# perf_metrics.py

import time


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


class _TimingSeries:
    def __init__(self, ring_size):
        self._size = int(ring_size)
        if self._size < 32:
            self._size = 32
        self._buf = [0] * self._size
        self._next_idx = 0
        self._count = 0
        self._total = 0
        self._min = 0
        self._max = 0

    def add(self, value_us):
        value = int(value_us)
        if value < 0:
            value = 0

        overwritten = None
        if self._count < self._size:
            self._buf[self._next_idx] = value
            self._count += 1
        else:
            overwritten = self._buf[self._next_idx]
            self._total -= overwritten
            self._buf[self._next_idx] = value

        self._next_idx += 1
        if self._next_idx >= self._size:
            self._next_idx = 0

        self._total += value

        if self._count == 1:
            self._min = value
            self._max = value
        else:
            if (overwritten is not None) and ((overwritten == self._min) or (overwritten == self._max)):
                local_min = self._buf[0]
                local_max = self._buf[0]
                n = self._count
                for i in range(1, n):
                    sample = self._buf[i]
                    if sample < local_min:
                        local_min = sample
                    if sample > local_max:
                        local_max = sample
                self._min = local_min
                self._max = local_max
            else:
                if value < self._min:
                    self._min = value
                if value > self._max:
                    self._max = value

    def _percentile(self, pct):
        if self._count <= 0:
            return 0

        n = self._count
        values = [0] * n
        if self._count < self._size:
            for i in range(n):
                values[i] = self._buf[i]
        else:
            for i in range(n):
                src = self._next_idx + i
                if src >= self._size:
                    src -= self._size
                values[i] = self._buf[src]

        values.sort()

        if pct <= 0:
            return values[0]
        if pct >= 100:
            return values[n - 1]

        rank = (pct * (n - 1)) // 100
        return values[rank]

    def snapshot(self):
        if self._count <= 0:
            return {
                "count": 0,
                "min": 0,
                "avg": 0,
                "p95": 0,
                "p99": 0,
                "max": 0,
            }

        return {
            "count": self._count,
            "min": self._min,
            "avg": int(self._total // self._count),
            "p95": self._percentile(95),
            "p99": self._percentile(99),
            "max": self._max,
        }

    def snapshot_compact(self):
        if self._count <= 0:
            return {
                "count": 0,
                "min": 0,
                "avg": 0,
                "max": 0,
            }
        return {
            "count": self._count,
            "min": self._min,
            "avg": int(self._total // self._count),
            "max": self._max,
        }


class PerfMetrics:
    def __init__(self, ring_size=1024):
        self._series = {
            "loop_us": _TimingSeries(ring_size),
            "processing_us": _TimingSeries(ring_size),
            "adc_us": _TimingSeries(ring_size),
            "state_us": _TimingSeries(ring_size),
            "dip_us": _TimingSeries(ring_size),
            "median_us": _TimingSeries(ring_size),
            "ui_frame_us": _TimingSeries(ring_size),
            "usb_write_us": _TimingSeries(ring_size),
            "flash_write_us": _TimingSeries(ring_size),
        }
        self.missed_ticks = 0
        self.backlog_hwm = 0
        self.gc_count = 0
        self.gc_us_total = 0
        self.start_ms = time.ticks_ms() if hasattr(time, "ticks_ms") else 0

    def add_timing(self, name, duration_us):
        series = self._series.get(name)
        if series is not None:
            series.add(duration_us)

    def add_missed_ticks(self, missed):
        value = int(missed)
        if value > 0:
            self.missed_ticks += value

    def observe_backlog(self, backlog_depth):
        value = int(backlog_depth)
        if value > self.backlog_hwm:
            self.backlog_hwm = value

    def record_gc(self, gc_duration_us):
        value = int(gc_duration_us)
        if value < 0:
            value = 0
        self.gc_count += 1
        self.gc_us_total += value

    def snapshot(self):
        snap = {
            "uptime_s": 0.0,
            "missed_ticks": self.missed_ticks,
            "backlog_hwm": self.backlog_hwm,
            "gc_count": self.gc_count,
            "gc_us_total": self.gc_us_total,
        }
        now_ms = time.ticks_ms() if hasattr(time, "ticks_ms") else 0
        if now_ms:
            snap["uptime_s"] = _ticks_diff(now_ms, self.start_ms) / 1000.0
        for key, series in self._series.items():
            snap[key] = series.snapshot()
        return snap

    def summary_lines(self):
        snap = self.snapshot()
        lines = []
        lines.append(
            "PERF uptime={:.1f}s missed={} backlog_hwm={} gc_count={} gc_total_us={}".format(
                snap["uptime_s"],
                snap["missed_ticks"],
                snap["backlog_hwm"],
                snap["gc_count"],
                snap["gc_us_total"],
            )
        )
        for key in (
            "loop_us",
            "processing_us",
            "adc_us",
            "state_us",
            "dip_us",
            "median_us",
            "ui_frame_us",
            "usb_write_us",
            "flash_write_us",
        ):
            entry = snap[key]
            lines.append(
                "  {} count={} min={} avg={} p95={} p99={} max={}".format(
                    key,
                    entry["count"],
                    entry["min"],
                    entry["avg"],
                    entry["p95"],
                    entry["p99"],
                    entry["max"],
                )
            )
        return lines

    def compact_summary_lines(self):
        lines = []
        uptime_s = 0.0
        now_ms = time.ticks_ms() if hasattr(time, "ticks_ms") else 0
        if now_ms:
            uptime_s = _ticks_diff(now_ms, self.start_ms) / 1000.0
        lines.append(
            "PERF uptime={:.1f}s missed={} backlog_hwm={} gc_count={} gc_total_us={}".format(
                uptime_s,
                self.missed_ticks,
                self.backlog_hwm,
                self.gc_count,
                self.gc_us_total,
            )
        )
        for key in (
            "loop_us",
            "processing_us",
            "adc_us",
            "state_us",
            "dip_us",
            "median_us",
            "ui_frame_us",
            "usb_write_us",
            "flash_write_us",
        ):
            entry = self._series[key].snapshot_compact()
            lines.append(
                "  {} count={} min={} avg={} max={}".format(
                    key,
                    entry["count"],
                    entry["min"],
                    entry["avg"],
                    entry["max"],
                )
            )
        return lines

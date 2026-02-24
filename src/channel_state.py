# channel_state.py

from utils import median

class ChannelState:
    def __init__(self, stable_window, median_block, baseline_init_samples, baseline_alpha):
        self.raw_buf = [0.0] * int(stable_window)
        self.raw_count = 0
        self.raw_next = 0

        self.block_buf = [0.0] * int(median_block)
        self.block_count = 0
        self.block_next = 0
        self._median_work = [0.0] * int(median_block)

        self.baseline_seed_buf = []
        self.baseline = None

        self.stable = False

        # Dip state
        self.dip_active = False
        self.dip_start_s = None
        self.dip_min_v = None
        self.dip_baseline_v = None
        self.below_count = 0
        self.first_below_ms = None
        self.above_count = 0
        self.cooldown_until_ms = 0
        self.last_stable_ms = None

        self._stable_window = stable_window
        self._median_block = median_block
        self._baseline_init_samples = baseline_init_samples
        self._baseline_alpha = baseline_alpha

    def update_raw_window(self, v):
        if self._stable_window <= 0:
            return
        if self.raw_count < self._stable_window:
            self.raw_buf[self.raw_count] = v
            self.raw_count += 1
            if self.raw_count == self._stable_window:
                self.raw_next = 0
            return
        self.raw_buf[self.raw_next] = v
        self.raw_next += 1
        if self.raw_next >= self._stable_window:
            self.raw_next = 0

    def raw_window_ready(self):
        return self.raw_count == self._stable_window

    def raw_window_bounds(self):
        if self.raw_count <= 0:
            return None, None
        vmin = self.raw_buf[0]
        vmax = self.raw_buf[0]
        for i in range(1, self.raw_count):
            v = self.raw_buf[i]
            if v < vmin:
                vmin = v
            if v > vmax:
                vmax = v
        return vmin, vmax

    def update_median_block(self, v):
        if self._median_block <= 0:
            return
        if self.block_count < self._median_block:
            self.block_buf[self.block_count] = v
            self.block_count += 1
            if self.block_count == self._median_block:
                self.block_next = 0
            return
        # Keep a rolling block if consumer runs late.
        self.block_buf[self.block_next] = v
        self.block_next += 1
        if self.block_next >= self._median_block:
            self.block_next = 0

    def _median_from_block(self):
        n = self._median_block
        work = self._median_work
        for i in range(n):
            work[i] = self.block_buf[i]
        for i in range(1, n):
            key = work[i]
            j = i - 1
            while j >= 0 and work[j] > key:
                work[j + 1] = work[j]
                j -= 1
            work[j + 1] = key
        mid = n // 2
        if (n % 2) == 0:
            return (work[mid - 1] + work[mid]) / 2.0
        return work[mid]

    def compute_block_median_and_clear(self):
        if self.block_count != self._median_block:
            return None
        med_v = self._median_from_block()
        self.block_count = 0
        self.block_next = 0
        return med_v

    def reset_baseline_seed(self):
        self.baseline_seed_buf.clear()

    def update_baseline_with_raw(self, v):
        if self.baseline is None:
            self.baseline_seed_buf.append(v)
            if len(self.baseline_seed_buf) >= self._baseline_init_samples:
                self.baseline = median(self.baseline_seed_buf)
                self.baseline_seed_buf.clear()
            return

        self.baseline += self._baseline_alpha * (v - self.baseline)

    def update_baseline_with_median(self, med_v):
        # Backward-compatible alias for older callers.
        self.update_baseline_with_raw(med_v)

    @property
    def raw_win(self):
        # Backward-compatibility view for host tools that still read raw_win.
        if self.raw_count <= 0:
            return []
        if self.raw_count < self._stable_window:
            return self.raw_buf[:self.raw_count]
        out = [0.0] * self._stable_window
        for i in range(self._stable_window):
            src = self.raw_next + i
            if src >= self._stable_window:
                src -= self._stable_window
            out[i] = self.raw_buf[src]
        return out

    @property
    def block(self):
        # Backward-compatibility view for host tools that still read block.
        if self.block_count <= 0:
            return []
        return self.block_buf[:self.block_count]
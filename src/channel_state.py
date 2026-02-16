# channel_state.py

from utils import median

class ChannelState:
    def __init__(self, stable_window, median_block, baseline_init_samples, baseline_alpha):
        self.raw_win = []
        self.block = []
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
        self.raw_win.append(v)
        if len(self.raw_win) > self._stable_window:
            self.raw_win.pop(0)

    def update_median_block(self, v):
        self.block.append(v)
        if len(self.block) > self._median_block:
            self.block.pop(0)

    def compute_block_median_and_clear(self):
        if len(self.block) != self._median_block:
            return None
        med_v = median(self.block)
        self.block.clear()
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
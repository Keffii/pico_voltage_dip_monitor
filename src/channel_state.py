# channel_state.py

from utils import median

class ChannelState:
    def __init__(self, stable_window, median_block, baseline_len):
        self.raw_win = []
        self.block = []
        self.baseline_buf = []
        self.baseline = None

        self.stable = False

        # Dip state
        self.dip_active = False
        self.dip_start_s = None
        self.dip_min_v = None
        self.dip_baseline_v = None
        self.below_count = 0
        self.above_count = 0
        self.cooldown_until_ms = 0
        self.last_stable_ms = None

        self._stable_window = stable_window
        self._median_block = median_block
        self._baseline_len = baseline_len

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

    def update_baseline_with_median(self, med_v):
        self.baseline_buf.append(med_v)
        if len(self.baseline_buf) > self._baseline_len:
            self.baseline_buf.pop(0)
        if len(self.baseline_buf) >= 3:
            self.baseline = median(self.baseline_buf)

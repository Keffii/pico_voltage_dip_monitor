# median_logger.py

class MedianLogger:
    def __init__(self, medians_file):
        self.medians_file = medians_file
        self.buffer = []  # lines to flush

    def add(self, t_s, channel_name, median_v):
        self.buffer.append(f"{t_s:.3f},{channel_name},{median_v:.3f}\n")

    def flush_to_file(self, append_lines_fn):
        if not self.buffer:
            return 0
        lines_written = append_lines_fn(self.medians_file, self.buffer)
        self.buffer.clear()
        return lines_written
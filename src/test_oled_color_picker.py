# test_oled_color_picker.py
#
# OLED color calibration helper for SSD1351 (8-bit driver).
# Cycles channel-order mappings and shows spectrum + swatch pages so you can
# pick final BLUE/YELLOW/GREEN values by eye.

import time
import config
from machine import Pin, SPI
from lib.drivers.ssd1351.ssd1351 import SSD1351


PERMUTATIONS = (
    ("RGB", (0, 1, 2)),
    ("RBG", (0, 2, 1)),
    ("GRB", (1, 0, 2)),
    ("GBR", (1, 2, 0)),
    ("BRG", (2, 0, 1)),
    ("BGR", (2, 1, 0)),
)

BLUE_CANDIDATES = (
    (0, 0, 255),
    (0, 60, 255),
    (0, 120, 255),
    (20, 90, 220),
    (30, 150, 255),
    (70, 170, 255),
    (90, 140, 220),
    (130, 190, 255),
)

YELLOW_CANDIDATES = (
    (255, 255, 0),
    (255, 230, 0),
    (255, 210, 0),
    (240, 190, 0),
    (255, 255, 70),
    (255, 240, 90),
    (220, 200, 40),
    (255, 180, 20),
)

GREEN_CANDIDATES = (
    (0, 255, 0),
    (0, 230, 0),
    (20, 210, 20),
    (30, 240, 80),
    (0, 220, 120),
    (0, 180, 90),
    (80, 255, 120),
    (120, 255, 160),
)


def _sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000.0)


def _ticks_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def _ticks_diff(a, b):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(a, b)
    return a - b


def _encode(mapping_idx, r, g, b):
    _name, order = PERMUTATIONS[mapping_idx]
    vals = (r, g, b)
    return SSD1351.rgb(vals[order[0]], vals[order[1]], vals[order[2]])


def _init_oled():
    spi = SPI(
        config.OLED_SPI_ID,
        baudrate=10_000_000,
        polarity=0,
        phase=0,
        sck=Pin(config.OLED_SCK),
        mosi=Pin(config.OLED_MOSI),
        miso=None
    )
    cs = Pin(config.OLED_CS, Pin.OUT, value=1)
    dc = Pin(config.OLED_DC, Pin.OUT, value=0)
    rst = Pin(config.OLED_RST, Pin.OUT, value=1)
    rst.value(0)
    _sleep_ms(50)
    rst.value(1)
    _sleep_ms(50)
    return SSD1351(spi, cs, dc, rst, width=128, height=96)


def _draw_header(oled, mapping_idx, title):
    white = _encode(mapping_idx, 235, 235, 235)
    dim = _encode(mapping_idx, 130, 130, 130)
    oled.fill(_encode(mapping_idx, 0, 0, 0))
    oled.text("Map: {}".format(PERMUTATIONS[mapping_idx][0]), 0, 0, white)
    oled.text(title, 0, 8, white)
    oled.hline(0, 16, 128, dim)


def _draw_spectrum_page(oled, mapping_idx):
    _draw_header(oled, mapping_idx, "Spectrum R/G/B")
    white = _encode(mapping_idx, 235, 235, 235)

    # Three horizontal gradients
    for x in range(128):
        v = (x * 255) // 127
        c_r = _encode(mapping_idx, v, 0, 0)
        c_g = _encode(mapping_idx, 0, v, 0)
        c_b = _encode(mapping_idx, 0, 0, v)
        for y in range(20, 40):
            oled.pixel(x, y, c_r)
        for y in range(44, 64):
            oled.pixel(x, y, c_g)
        for y in range(68, 88):
            oled.pixel(x, y, c_b)

    oled.text("R", 0, 26, white)
    oled.text("G", 0, 50, white)
    oled.text("B", 0, 74, white)
    oled.show()


def _text_color_for(rgb, mapping_idx):
    r, g, b = rgb
    lum = (r * 30 + g * 59 + b * 11) // 100
    if lum < 120:
        return _encode(mapping_idx, 255, 255, 255)
    return _encode(mapping_idx, 0, 0, 0)


def _draw_swatch_page(oled, mapping_idx, title, candidates):
    _draw_header(oled, mapping_idx, title)
    border = _encode(mapping_idx, 200, 200, 200)
    dim = _encode(mapping_idx, 120, 120, 120)
    tile_w = 30
    tile_h = 30
    pad_x = 2
    pad_y = 2
    grid_x = 0
    grid_y = 20

    for idx in range(8):
        col = idx % 4
        row = idx // 4
        x = grid_x + (tile_w + pad_x) * col
        y = grid_y + (tile_h + pad_y) * row
        rgb = candidates[idx]
        oled.fill_rect(x, y, tile_w, tile_h, _encode(mapping_idx, rgb[0], rgb[1], rgb[2]))
        oled.rect(x, y, tile_w, tile_h, border)
        oled.text(str(idx), x + 2, y + 20, _text_color_for(rgb, mapping_idx))

    oled.hline(0, 86, 128, dim)
    oled.text("idx shown on tile", 0, 88, dim)
    oled.show()


def _print_candidates(title, candidates):
    print(title)
    for idx, rgb in enumerate(candidates):
        print("  {}: ({:3d}, {:3d}, {:3d})".format(idx, rgb[0], rgb[1], rgb[2]))


def run(page_ms=2500):
    oled = _init_oled()
    print("\nOLED color picker started.")
    print("Press Ctrl+C to stop.\n")
    print("RGB mapping only. Cycling 4 screens: Spectrum, BLUE, YELLOW, GREEN.")

    try:
        mapping_idx = 0  # Fixed to RGB only.
        while True:
            print("\n=== Mapping RGB ===")

            _draw_spectrum_page(oled, mapping_idx)
            _sleep_ms(page_ms)

            _draw_swatch_page(oled, mapping_idx, "BLUE candidates", BLUE_CANDIDATES)
            _print_candidates("BLUE candidates", BLUE_CANDIDATES)
            _sleep_ms(page_ms)

            _draw_swatch_page(oled, mapping_idx, "YELLOW candidates", YELLOW_CANDIDATES)
            _print_candidates("YELLOW candidates", YELLOW_CANDIDATES)
            _sleep_ms(page_ms)

            _draw_swatch_page(oled, mapping_idx, "GREEN candidates", GREEN_CANDIDATES)
            _print_candidates("GREEN candidates", GREEN_CANDIDATES)
            _sleep_ms(page_ms)

            print("Pick B/Y/G index values from RGB pages.")

    except KeyboardInterrupt:
        oled.fill(_encode(mapping_idx, 0, 0, 0))
        oled.show()
        print("\nColor picker stopped.")


if __name__ == "__main__":
    run()

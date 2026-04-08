# Pico Voltage Dip Monitor

Used to monitor voltage stability and fluctuations, and log dip events on Raspberry Pi Pico 2, with an onboard OLED UI and optional live streaming to InfluxDB and Grafana.

<table>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/923e38a2-64cb-4a6f-9f9a-cd6aab6a3905" alt="OLED graph screen showing recent voltage dips across channels" height="420" /></td>
    <td><img src="https://github.com/user-attachments/assets/f8bc838c-e033-4923-a4bf-5a62aaaa6eec" alt="OLED stats screen showing live channel baselines, drops, and stability percentages" height="420" /></td>
  </tr>
</table>

## Why This Project

- Samples three channels at 100 Hz on a Pico 2.
- Monitors voltage fluctuations and logs dip events using baseline-aware detection.
- With the configured voltage-divider scaling, measures and calibrates external inputs from the Pico's 3.3V ADC domain up to about 60V.
- Runs standalone on-device or streams live data over USB.
- Shows live stats and dip graphs on an SSD1351 OLED.
- Includes PC tools for download, validation, plotting, and live monitoring.

## Grafana

The device can stream measured voltage data over USB serial for external monitoring and analysis.  
In this setup, the data is collected and visualized in Grafana, making it easier to observe stable baselines, compare channels, and review detected dip events over time.

<img width="2243" height="1003" alt="dip_monitor" src="https://github.com/user-attachments/assets/b3321b7f-63a6-4d7c-9084-f0e7295a82c1" />

The dashboard shows:
- live median voltage for all channels
- baseline tracking for the monitored inputs
- detected voltage dip events and their drop magnitude
- current voltage per channel
- dip count by channel
- summary statistics such as drop size and duration

This makes the monitor useful not only as a standalone embedded device with an OLED interface, but also as a logging and diagnostic tool for longer testing sessions, trend analysis, and troubleshooting intermittent power issues.

## Hardware

- Enclosure CAD is included at [`cad/pico_enclosure_with_oled.scad`](cad/pico_enclosure_with_oled.scad).
- Input wiring and safety notes are documented in [`docs/wiring.md`](docs/wiring.md).
- The current configuration uses voltage-divider scaling so the Pico's `3.3V` ADC range maps to roughly `60V` external input.

## Quick Start

1. Install MicroPython on a Raspberry Pi Pico 2 and upload the files in [`src/`](src/).
2. Wire your inputs to `GP26`, `GP27`, and `GP28` with a common ground.
3. Pick a logging mode in [`src/config.py`](src/config.py).
4. Run [`src/main.py`](src/main.py).

Recommended modes:

| Mode | Best for |
| --- | --- |
| `EVENT_ONLY` | Standalone logging with minimal flash wear |
| `USB_STREAM` | Live monitoring with InfluxDB and Grafana |
| `FULL_LOCAL` | Short debug runs with full local median history |
| `DISPLAY_ONLY` | OLED-focused demos and UI performance testing |

> [!WARNING]
> Never exceed `3.3V` on Pico ADC pins. This project scales that ADC range to roughly `60V` external input with the configured voltage dividers.

## How It Works

- The Pico samples `PLC`, `MODEM`, and `BATTERY` every `10 ms`.
- It computes `100 ms` medians, updates per-channel baselines, and detects dips from raw samples.
- Depending on mode, it logs events locally, keeps a rolling history, or streams data to a PC.

## Further Reading

- [`docs/THONNY_SETUP.md`](docs/THONNY_SETUP.md) easiest path to get the Pico running
- [`docs/QUICKSTART.md`](docs/QUICKSTART.md) shorter setup walkthrough
- [`docs/wiring.md`](docs/wiring.md) wiring and safety notes
- [`docs/SETUP_INFLUXDB.md`](docs/SETUP_INFLUXDB.md) live dashboard setup
- [`docs/data-formats.md`](docs/data-formats.md) CSV schemas
- [`docs/troubleshooting.md`](docs/troubleshooting.md) common hardware and Thonny issues
- [`docs/architecture.md`](docs/architecture.md) runtime flow and design notes

## License

[MIT](LICENSE)

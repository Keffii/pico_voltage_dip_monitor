# Troubleshooting

## Random values when disconnected
ADC inputs float. This is normal.
Fix:
- battery holder or better contact
- 100 k pulldown to GND
- 100 nF cap to GND

## No files appear on the Pico
You are likely looking at the wrong location or the script did not run.
Check:
- Thonny -> View -> Files -> Raspberry Pi Pico
- Confirm the script is running and has stable readings

## Thonny says device is busy
- Ensure MicroPython is installed on Pico 2
- Unplug and plug in normally (do not hold BOOTSEL)
- Run -> Stop/Restart backend

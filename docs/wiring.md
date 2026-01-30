# Wiring

## Prototype: one AAA cell per ADC channel
- Cell A + -> GP26
- Cell B + -> GP27
- Cell C + -> GP28
- All cell negatives -> Pico GND (common ground)

Recommended:
- Use a battery holder for stable contact.
- Add 100 nF capacitor from each ADC pin to GND for noise reduction.
- Optional: add a 100 k pulldown from each ADC pin to GND to avoid floating readings when disconnected.

## Safety
Never exceed 3.3 V on any ADC pin.

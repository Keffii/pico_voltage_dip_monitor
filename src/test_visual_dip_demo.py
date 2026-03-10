import sys
import types


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


if "oled_ui" not in sys.modules:
    oled_ui = types.ModuleType("oled_ui")

    class _DummyOledUI:
        pass

    oled_ui.OledUI = _DummyOledUI
    sys.modules["oled_ui"] = oled_ui

if "visual_dip_demo" in sys.modules:
    del sys.modules["visual_dip_demo"]

import visual_dip_demo as demo


class _FakeUI:
    def __init__(self):
        self.events = []
        self.latched = []

    def record_dip_event_adc(self, channel, baseline_v, min_v, drop_v, event_id=None, active=False, sample_index=None):
        self.events.append({
            "channel": channel,
            "baseline_v": baseline_v,
            "min_v": min_v,
            "drop_v": drop_v,
            "event_id": event_id,
            "active": bool(active),
            "sample_index": sample_index,
        })

    def latch_dip_drop_adc(self, channel, drop_v):
        self.latched.append({"channel": channel, "drop_v": drop_v})


def test_dips_rotate_every_two_seconds():
    state = demo.create_demo_state(start_ms=0)
    ui = _FakeUI()

    demo.advance_demo_state(state, ui, now_ms=0, frame_index=0)
    demo.advance_demo_state(state, ui, now_ms=2000, frame_index=200)
    demo.advance_demo_state(state, ui, now_ms=4000, frame_index=400)

    starts = [event for event in ui.events if event["active"]]
    _assert(
        [event["channel"] for event in starts[:3]] == ["BLUE", "YELLOW", "GREEN"],
        "Expected deterministic BLUE -> YELLOW -> GREEN rotation every 2 seconds",
    )


def test_completed_dip_reuses_event_id_and_anchor():
    state = demo.create_demo_state(start_ms=0)
    ui = _FakeUI()

    demo.advance_demo_state(state, ui, now_ms=0, frame_index=10)
    demo.advance_demo_state(state, ui, now_ms=demo.DIP_DURATION_MS // 2, frame_index=20)
    demo.advance_demo_state(state, ui, now_ms=demo.DIP_DURATION_MS + 1, frame_index=30)

    first_event_id = ui.events[0]["event_id"]
    final_event = ui.events[-1]

    _assert(final_event["event_id"] == first_event_id, "Expected finished event to reuse the original event id")
    _assert(final_event["sample_index"] == 10, "Expected finished event to keep the original graph anchor")
    _assert(ui.latched and ui.latched[0]["channel"] == "BLUE", "Expected completed dip to latch the BLUE channel drop")


def test_run_step_updates_plot_values_for_all_channels():
    state = demo.create_demo_state(start_ms=0)
    ui = _FakeUI()

    blue_adc, yellow_adc, green_adc = demo.advance_demo_state(state, ui, now_ms=0, frame_index=0)

    _assert(blue_adc is not None, "Expected BLUE plot value")
    _assert(yellow_adc is not None, "Expected YELLOW plot value")
    _assert(green_adc is not None, "Expected GREEN plot value")


def run_all():
    tests = (
        test_dips_rotate_every_two_seconds,
        test_completed_dip_reuses_event_id_and_anchor,
        test_run_step_updates_plot_values_for_all_channels,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("Visual dip demo tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

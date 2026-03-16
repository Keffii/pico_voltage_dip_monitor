import config
import sys


if "machine" not in sys.modules:
    import types

    machine = types.ModuleType("machine")

    class _ADC:
        def __init__(self, *_args, **_kwargs):
            pass

        def read_u16(self):
            return 0

    class _Pin:
        IN = 0
        OUT = 1
        PULL_UP = 2
        PULL_DOWN = 3

        def __init__(self, *_args, **_kwargs):
            pass

        def value(self, *_args, **_kwargs):
            return 0

    class _SPI:
        def __init__(self, *_args, **_kwargs):
            pass

        def write(self, *_args, **_kwargs):
            return 0

    machine.ADC = _ADC
    machine.Pin = _Pin
    machine.SPI = _SPI
    sys.modules["machine"] = machine


def _load_main_for_tests():
    original_enable_oled = getattr(config, "ENABLE_OLED", False)
    try:
        config.ENABLE_OLED = False
        if "main" in sys.modules:
            del sys.modules["main"]
        import main as main_module
        return main_module
    finally:
        config.ENABLE_OLED = original_enable_oled


main = _load_main_for_tests()


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def test_source_off_policy_keeps_divider_scaled_low_signal_visible():
    readings = (
        ("BLUE", 0.041),
        ("YELLOW", 0.042),
        ("GREEN", 0.043),
    )

    _assert(
        main._all_channels_below_source_off_thresholds(readings, 0.08, 0.25) is False,
        "Divider-scaled low ADC readings should not be treated as source-off",
    )
    _assert(
        main._all_channels_above_source_off_release_thresholds(readings, 0.12, 0.40) is True,
        "Divider-scaled low ADC readings should release the source-off overlay",
    )


def test_source_off_policy_still_flags_true_near_zero_signal():
    readings = (
        ("BLUE", 0.000),
        ("YELLOW", 0.002),
        ("GREEN", 0.001),
    )

    _assert(
        main._all_channels_below_source_off_thresholds(readings, 0.08, 0.25) is True,
        "True near-zero readings should still count as source-off",
    )
    _assert(
        main._all_channels_above_source_off_release_thresholds(readings, 0.12, 0.40) is False,
        "True near-zero readings should not satisfy source-off release thresholds",
    )


def test_source_off_real_threshold_validation_rejects_inverted_release():
    original_off = getattr(config, "SOURCE_OFF_REAL_V", 0.25)
    original_release = getattr(config, "SOURCE_OFF_RELEASE_REAL_V", 0.40)
    try:
        config.SOURCE_OFF_REAL_V = 0.40
        config.SOURCE_OFF_RELEASE_REAL_V = 0.25
        try:
            config.validate_config()
        except ValueError as exc:
            _assert(
                "SOURCE_OFF_RELEASE_REAL_V must be >= SOURCE_OFF_REAL_V" in str(exc),
                "Expected real-domain source-off validation error",
            )
        else:
            raise AssertionError("Expected inverted real-domain source-off thresholds to fail validation")
    finally:
        config.SOURCE_OFF_REAL_V = original_off
        config.SOURCE_OFF_RELEASE_REAL_V = original_release
        config.validate_config()


def run_all():
    tests = (
        test_source_off_policy_keeps_divider_scaled_low_signal_visible,
        test_source_off_policy_still_flags_true_near_zero_signal,
        test_source_off_real_threshold_validation_rejects_inverted_release,
    )
    passed = 0
    for test in tests:
        test()
        passed += 1
        print("PASS:", test.__name__)
    print("Source-off policy tests passed: {}/{}".format(passed, len(tests)))


if __name__ == "__main__":
    run_all()

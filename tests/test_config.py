# tests/test_config.py
import pytest
from dashboard.config import util_status, ot_status, COLORS, OT_PREMIUM


def test_util_status_green():
    assert util_status(80) == "green"
    assert util_status(95) == "green"


def test_util_status_amber():
    assert util_status(60) == "amber"
    assert util_status(79) == "amber"


def test_util_status_red():
    assert util_status(59) == "red"
    assert util_status(0) == "red"


def test_ot_status_green():
    assert ot_status(-0.10) == "green"
    assert ot_status(-0.06) == "green"


def test_ot_status_amber():
    assert ot_status(0.0) == "amber"
    assert ot_status(0.14) == "amber"


def test_ot_status_red():
    assert ot_status(0.15) == "red"
    assert ot_status(0.50) == "red"


def test_colors_has_required_keys():
    required = {"bg_base", "bg_card", "bg_elevated", "border",
                "text_primary", "text_secondary", "blue", "green", "amber", "red"}
    assert required.issubset(set(COLORS.keys()))


def test_all_color_values_are_hex():
    for key, val in COLORS.items():
        assert val.startswith("#"), f"{key}: {val!r} is not a hex color"
        assert len(val) == 7, f"{key}: {val!r} is not a 6-digit hex color"


def test_ot_premium_is_float():
    assert isinstance(OT_PREMIUM, float)
    assert OT_PREMIUM > 0

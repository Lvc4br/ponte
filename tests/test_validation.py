import pytest

from app.core.models import NumericRange
from app.core.validation import (
    format_display_value,
    parse_input_number,
    parse_number,
    parse_range,
)


def test_decimal_comma():
    assert parse_number("1,60") == 1.6


def test_decimal_point():
    assert parse_number("1.60") == 1.6


def test_brazilian_thousands_and_decimal_separators():
    assert parse_number("1.234,56") == 1234.56


def test_interval():
    assert parse_range("41,25 - 41,80") == NumericRange(41.25, 41.8)


def test_single_value():
    assert parse_range("20,5") == NumericRange(20.5, 20.5)


def test_blank_input_is_optional():
    assert parse_input_number("   ", "Largura") is None


@pytest.mark.parametrize("value", ["abc", "12m", "nan", "inf", "-inf"])
def test_invalid_user_input_is_rejected(value):
    with pytest.raises(ValueError, match="Largura"):
        parse_input_number(value, "Largura")


def test_valid_user_input_with_decimal_comma():
    assert parse_input_number("12,75", "Largura") == 12.75


def test_valid_user_input_with_decimal_point():
    assert parse_input_number("12.75", "Largura") == 12.75


def test_display_decimal_with_comma():
    assert format_display_value("12.50") == "12,50"
    assert format_display_value("12,50") == "12,50"


def test_display_preserves_intervals_and_formulas():
    assert format_display_value("41,25 - 41,80") == "41,25 - 41,80"
    assert format_display_value("1,60+0,20") == "1,60+0,20"


def test_display_does_not_change_integer_or_empty_values():
    assert format_display_value("20") == "20"
    assert format_display_value(None) == ""

import pytest

from app.core.models import NumericRange
from app.core.validation import parse_input_number, parse_number, parse_range


def test_decimal_comma():
    assert parse_number("1,60") == 1.6


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

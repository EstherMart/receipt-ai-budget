from decimal import Decimal

import pytest

from app.money import format_brl, parse_brl, split_installments


@pytest.mark.parametrize(
    "text, expected",
    [("1.234,56", "1234.56"), ("R$ 42,9", "42.90"), ("42.90", "42.90"), ("1.234", "1234.00")],
)
def test_parse_brl(text, expected):
    assert parse_brl(text) == Decimal(expected)


def test_format_brl():
    assert format_brl(Decimal("1901.6")) == "R$ 1.901,60"


def test_installments_keep_cents_exact():
    assert split_installments(Decimal("100"), 3) == [
        Decimal("33.33"),
        Decimal("33.33"),
        Decimal("33.34"),
    ]
    assert sum(split_installments(Decimal("999.99"), 7)) == Decimal("999.99")

"""Exact money arithmetic and Brazilian number/date formats."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")
DATE_FORMAT = "%d/%m/%Y"

_THOUSANDS_ONLY = re.compile(r"^\d{1,3}(\.\d{3})+$")

Number = Decimal | int | float | str


def to_money(value: Number) -> Decimal:
    """Round any numeric value to cents (half up)."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def parse_brl(text: Number) -> Decimal:
    """Parse '1.234,56', 'R$ 42,9' or '42.90' into a Decimal rounded to cents."""
    if not isinstance(text, str):
        return to_money(text)
    cleaned = text.replace("R$", "").replace(" ", "").strip()
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif _THOUSANDS_ONLY.match(cleaned):
        cleaned = cleaned.replace(".", "")
    try:
        return to_money(cleaned)
    except InvalidOperation as error:
        raise ValueError(f"Invalid amount: {text!r}") from error


def format_brl(amount: Decimal) -> str:
    """Format as 'R$ 1.234,56'."""
    us_style = f"{to_money(amount):,.2f}"
    return "R$ " + us_style.replace(",", "_").replace(".", ",").replace("_", ".")


def parse_br_date(text: str) -> date:
    """Parse 'dd/mm/yyyy'."""
    try:
        return datetime.strptime(text.strip(), DATE_FORMAT).date()
    except ValueError as error:
        raise ValueError(f"Invalid date: {text!r} (expected dd/mm/yyyy)") from error


def format_br_date(value: date) -> str:
    return value.strftime(DATE_FORMAT)


def split_installments(total: Decimal, count: int) -> list[Decimal]:
    """Split a total into installments; the last one absorbs the cents left over.

    100.00 in 3 -> 33.33 + 33.33 + 33.34
    """
    if count < 1:
        raise ValueError("Installment count must be at least 1")
    base = (total / count).quantize(CENT, rounding=ROUND_DOWN)
    installments = [base] * count
    installments[-1] = to_money(total - base * (count - 1))
    return installments

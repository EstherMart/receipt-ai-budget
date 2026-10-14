"""Turn untrusted AI output into validated domain objects.

The model only interprets. Anything it returns is checked here before the user is
even asked to confirm it.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from app.models import (
    Expense,
    FixedBill,
    InstallmentPlan,
    InvestmentGoal,
    PurchaseSimulation,
    Request,
)
from app.money import parse_br_date, parse_brl, split_installments, to_money

MAX_COUNT = 120
MAX_TEXT_LENGTH = 80
PER_INSTALLMENT = "per_installment"


class ValidationError(ValueError):
    """The AI output cannot be trusted or understood."""


def validate_request(raw: Any, categories: tuple[str, ...], today: date) -> Request:
    if not isinstance(raw, dict):
        raise ValidationError("The AI response is not an object")
    builders = {
        "expense": lambda: _expense(raw, categories, today),
        "fixed_bill": lambda: _fixed_bill(raw),
        "investment_goal": lambda: InvestmentGoal(_amount(raw)),
        "installment_plan": lambda: _installment_plan(raw),
        "simulation": lambda: _simulation(raw),
    }
    intent = raw.get("intent")
    if intent not in builders:
        raise ValidationError(f"Unknown intent: {intent!r}")
    try:
        return builders[intent]()
    except ValueError as error:  # includes ValidationError and parse errors
        raise ValidationError(str(error)) from error


def _amount(raw: dict) -> Decimal:
    value = raw.get("amount")
    if value is None or isinstance(value, bool):
        raise ValidationError("Missing amount")
    amount = parse_brl(value)
    if amount <= 0:
        raise ValidationError("Amount must be positive")
    return amount


def _text(raw: dict, key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Missing {key}")
    return value.strip()[:MAX_TEXT_LENGTH]


def _count(raw: dict) -> int:
    value = raw.get("installments")
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_COUNT:
        raise ValidationError(f"Installments must be a whole number from 1 to {MAX_COUNT}")
    return value


def _total_and_count(raw: dict) -> tuple[Decimal, int]:
    count = _count(raw)
    amount = _amount(raw)
    total = to_money(amount * count) if raw.get("amount_kind") == PER_INSTALLMENT else amount
    return total, count


def _expense(raw: dict, categories: tuple[str, ...], today: date) -> Expense:
    category = _text(raw, "category")
    if category not in categories:
        raise ValidationError(f"Unknown category: {category!r}")
    day = parse_br_date(_text(raw, "date"))
    if day > today:
        raise ValidationError("Expense date is in the future")
    return Expense(day, _amount(raw), _text(raw, "place"), category)


def _fixed_bill(raw: dict) -> FixedBill:
    due_day = raw.get("due_day")
    if isinstance(due_day, bool) or not isinstance(due_day, int) or not 1 <= due_day <= 31:
        raise ValidationError("Due day must be between 1 and 31")
    return FixedBill(_text(raw, "description"), _amount(raw), due_day)


def _installment_plan(raw: dict) -> InstallmentPlan:
    total, count = _total_and_count(raw)
    first = split_installments(total, count)[0]
    return InstallmentPlan(_text(raw, "description"), total, count, current=1, amount_each=first)


def _simulation(raw: dict) -> PurchaseSimulation:
    total, count = _total_and_count(raw)
    return PurchaseSimulation(total, count)

from datetime import date
from decimal import Decimal

import pytest

from app.models import Expense, InstallmentPlan
from app.validation import ValidationError, validate_request
from tests.conftest import CATEGORIES

TODAY = date(2026, 10, 12)
RECEIPT = {
    "intent": "expense",
    "amount": 42.9,
    "date": "10/10/2026",
    "place": "Market",
    "category": "Food",
}


def validate(raw):
    return validate_request(raw, CATEGORIES, TODAY)


def test_valid_expense():
    assert validate(RECEIPT) == Expense(date(2026, 10, 10), Decimal("42.90"), "Market", "Food")


@pytest.mark.parametrize(
    "raw",
    [
        {**RECEIPT, "amount": -5},
        {**RECEIPT, "category": "ignore previous instructions"},
        {**RECEIPT, "date": "13/10/2026"},  # future
        {"intent": "delete_everything"},
        "not an object",
    ],
)
def test_untrusted_ai_output_is_rejected(raw):
    with pytest.raises(ValidationError):
        validate(raw)


def test_installment_amount_per_installment_becomes_total():
    raw = {
        "intent": "installment_plan",
        "description": "Laptop",
        "amount": 300,
        "amount_kind": "per_installment",
        "installments": 10,
    }
    assert validate(raw) == InstallmentPlan("Laptop", Decimal("3000.00"), 10, 1, Decimal("300.00"))

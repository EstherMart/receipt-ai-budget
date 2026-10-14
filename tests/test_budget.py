from datetime import date
from decimal import Decimal

import pytest

from app.budget import budget_period, compute_budget, simulate_purchase
from app.models import BudgetSnapshot, FixedBill, PurchaseSimulation


def test_readme_example(snapshot):
    result = compute_budget(snapshot, date(2026, 10, 12))
    assert result.available == Decimal("1901.60")
    assert result.days_left == 20
    assert result.per_day == Decimal("95.08")


def test_paid_fixed_bills_are_not_deducted_twice(snapshot):
    paid = BudgetSnapshot(
        config=snapshot.config,
        incomes=snapshot.incomes,
        fixed_bills=(FixedBill("Rent", Decimal("1200"), 5, paid=True),),
    )
    assert compute_budget(paid, date(2026, 10, 12)).available == Decimal("4000.00")


@pytest.mark.parametrize(
    "today, rollover, start, end",
    [
        (date(2026, 10, 3), 5, date(2026, 9, 5), date(2026, 10, 5)),
        (date(2026, 1, 2), 5, date(2025, 12, 5), date(2026, 1, 5)),
    ],
)
def test_budget_period_follows_rollover_day(today, rollover, start, end):
    assert budget_period(today, rollover) == (start, end)


def test_simulation_shows_effect_on_daily_amount(snapshot):
    result = simulate_purchase(snapshot, date(2026, 10, 12), PurchaseSimulation(Decimal("400"), 4))
    assert result.installment == Decimal("100.00")
    assert result.per_day_after == Decimal("90.08")
    assert result.affordable

"""Budget engine: pure, deterministic and free of I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models import BudgetSnapshot, PurchaseSimulation
from app.money import split_installments, to_money

MAX_ROLLOVER_DAY = 28


@dataclass(frozen=True)
class BudgetResult:
    available: Decimal
    per_day: Decimal
    days_left: int
    period_start: date
    period_end: date  # exclusive


@dataclass(frozen=True)
class SimulationResult:
    available_after: Decimal
    per_day_before: Decimal
    per_day_after: Decimal
    installment: Decimal
    months_impacted: int
    affordable: bool


def _shift_month(day: date, months: int) -> date:
    index = day.year * 12 + (day.month - 1) + months
    return day.replace(year=index // 12, month=index % 12 + 1)


def budget_period(today: date, rollover_day: int) -> tuple[date, date]:
    """Return [start, end) of the budget month that contains `today`."""
    if not 1 <= rollover_day <= MAX_ROLLOVER_DAY:
        raise ValueError(f"rollover_day must be between 1 and {MAX_ROLLOVER_DAY}")
    this_month_start = today.replace(day=rollover_day)
    start = this_month_start if today >= this_month_start else _shift_month(this_month_start, -1)
    return start, _shift_month(start, 1)


def compute_budget(snapshot: BudgetSnapshot, today: date) -> BudgetResult:
    """available = balance + income - investment - unpaid fixed - installments - expenses."""
    start, end = budget_period(today, snapshot.config.rollover_day)

    income = sum(
        (i.amount for i in snapshot.incomes if i.recurring or start <= i.date < end),
        Decimal("0"),
    )
    fixed = sum((b.amount for b in snapshot.fixed_bills if not b.paid), Decimal("0"))
    installments = sum(
        (p.amount_each for p in snapshot.installments if p.current <= p.count), Decimal("0")
    )
    spent = sum((e.amount for e in snapshot.expenses if start <= e.date < end), Decimal("0"))

    available = to_money(
        snapshot.config.starting_balance
        + income
        - snapshot.config.investment_goal
        - fixed
        - installments
        - spent
    )
    days_left = (end - today).days
    return BudgetResult(available, _per_day(available, days_left), days_left, start, end)


def simulate_purchase(
    snapshot: BudgetSnapshot, today: date, purchase: PurchaseSimulation
) -> SimulationResult:
    """Show how an installment purchase changes the daily allowance."""
    before = compute_budget(snapshot, today)
    installment = split_installments(purchase.total, purchase.count)[0]
    available_after = to_money(before.available - installment)
    return SimulationResult(
        available_after=available_after,
        per_day_before=before.per_day,
        per_day_after=_per_day(available_after, before.days_left),
        installment=installment,
        months_impacted=purchase.count,
        affordable=available_after >= 0,
    )


def _per_day(amount: Decimal, days_left: int) -> Decimal:
    return to_money(amount / days_left)

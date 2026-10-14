"""Application flow: interpret -> validate -> confirm -> save. No Telegram code here."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from app.ai import Interpreter, InterpreterInput
from app.budget import compute_budget, simulate_purchase
from app.models import (
    Expense,
    FixedBill,
    InstallmentPlan,
    InvestmentGoal,
    PurchaseSimulation,
    Request,
)
from app.money import format_br_date, format_brl
from app.sheets import SheetsRepository
from app.validation import ValidationError, validate_request


@dataclass(frozen=True)
class Reply:
    """What to tell the user. `pending` is set when a confirmation is required."""

    text: str
    pending: Request | None = None


class BudgetAssistant:
    def __init__(
        self,
        interpreter: Interpreter,
        repository: SheetsRepository,
        categories: tuple[str, ...],
        today: Callable[[], date] = date.today,
    ) -> None:
        self._interpreter = interpreter
        self._repository = repository
        self._categories = categories
        self._today = today

    def balance(self) -> Reply:
        result = compute_budget(self._repository.load_snapshot(), self._today())
        return Reply(
            f"{format_brl(result.available)} left this month, "
            f"{format_brl(result.per_day)} per day ({result.days_left} days left)."
        )

    def understand(self, request: InterpreterInput) -> Reply:
        try:
            parsed = validate_request(
                self._interpreter.interpret_request(request), self._categories, self._today()
            )
        except ValidationError as error:
            return Reply(f"I could not use that: {error}. Please try again.")
        if isinstance(parsed, PurchaseSimulation):
            return Reply(self._simulation_text(parsed))
        return Reply(self._confirmation_text(parsed), pending=parsed)

    def confirm(self, request: Request) -> Reply:
        if isinstance(request, Expense):
            self._repository.add_expense(request)
        elif isinstance(request, FixedBill):
            self._repository.add_fixed_bill(request)
        elif isinstance(request, InstallmentPlan):
            self._repository.add_installment_plan(request)
        elif isinstance(request, InvestmentGoal):
            self._repository.set_investment_goal(request.amount)
        else:
            raise TypeError(f"Cannot save {type(request).__name__}")
        return Reply("Saved.")

    def is_duplicate(self, expense: Expense) -> bool:
        key = (expense.date, expense.amount, expense.place.lower())
        return any(
            (e.date, e.amount, e.place.lower()) == key
            for e in self._repository.load_snapshot().expenses
        )

    def _simulation_text(self, purchase: PurchaseSimulation) -> str:
        result = simulate_purchase(self._repository.load_snapshot(), self._today(), purchase)
        verdict = "You can afford it." if result.affordable else "This would exceed your budget."
        return (
            f"{verdict} {purchase.count}x {format_brl(result.installment)}: "
            f"per day goes from {format_brl(result.per_day_before)} to "
            f"{format_brl(result.per_day_after)}, for {result.months_impacted} months."
        )

    def _confirmation_text(self, request: Request) -> str:
        if isinstance(request, Expense):
            warning = " (looks like a duplicate)" if self.is_duplicate(request) else ""
            summary = (
                f"Expense {format_brl(request.amount)} at {request.place}, "
                f"{request.category}, {format_br_date(request.date)}{warning}"
            )
        elif isinstance(request, FixedBill):
            summary = (
                f"Fixed bill {request.name}: {format_brl(request.amount)} every {request.due_day}th"
            )
        elif isinstance(request, InstallmentPlan):
            summary = (
                f"Installments {request.description}: {request.count}x "
                f"{format_brl(request.amount_each)} (total {format_brl(request.total)})"
            )
        else:
            summary = f"Investment goal: {format_brl(request.amount)} per month"
        return f"{summary}. Save?"

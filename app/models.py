"""Plain data objects shared across the app."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Config:
    starting_balance: Decimal = Decimal("0.00")
    investment_goal: Decimal = Decimal("0.00")
    rollover_day: int = 1


@dataclass(frozen=True)
class Income:
    description: str
    amount: Decimal
    date: date
    recurring: bool = False


@dataclass(frozen=True)
class FixedBill:
    name: str
    amount: Decimal
    due_day: int
    paid: bool = False


@dataclass(frozen=True)
class InstallmentPlan:
    description: str
    total: Decimal
    count: int
    current: int
    amount_each: Decimal


@dataclass(frozen=True)
class Expense:
    date: date
    amount: Decimal
    place: str
    category: str


@dataclass(frozen=True)
class InvestmentGoal:
    amount: Decimal


@dataclass(frozen=True)
class PurchaseSimulation:
    total: Decimal
    count: int


@dataclass(frozen=True)
class BudgetSnapshot:
    config: Config = field(default_factory=Config)
    incomes: tuple[Income, ...] = ()
    fixed_bills: tuple[FixedBill, ...] = ()
    installments: tuple[InstallmentPlan, ...] = ()
    expenses: tuple[Expense, ...] = ()


# Everything the AI can ask the bot to do.
Request = Expense | FixedBill | InvestmentGoal | InstallmentPlan | PurchaseSimulation

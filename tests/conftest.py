from datetime import date
from decimal import Decimal

import pytest

from app.models import BudgetSnapshot, Config, Expense, FixedBill, Income, InstallmentPlan

CATEGORIES = ("Food", "Transport", "Housing", "Health", "Leisure", "Other")


@pytest.fixture
def today() -> date:
    return date(2026, 10, 12)


@pytest.fixture
def snapshot() -> BudgetSnapshot:
    """The README example, with fictional values."""
    return BudgetSnapshot(
        config=Config(Decimal("500"), Decimal("500"), 1),
        incomes=(Income("Salary", Decimal("4000"), date(2026, 10, 5)),),
        fixed_bills=(
            FixedBill("Rent", Decimal("1200"), 5),
            FixedBill("Internet", Decimal("530"), 10),
        ),
        installments=(InstallmentPlan("Laptop", Decimal("3000"), 10, 2, Decimal("300")),),
        expenses=(Expense(date(2026, 10, 3), Decimal("68.40"), "Market", "Food"),),
    )


class FakeWorksheet:
    def __init__(self, records=None):
        self.records = list(records or [])
        self.appended: list[list] = []
        self.updated: list[tuple] = []

    def get_all_records(self):
        return self.records

    def append_row(self, values):
        self.appended.append(values)

    def update_cell(self, row, col, value):
        self.updated.append((row, col, value))


class FakeSpreadsheet:
    def __init__(self, **sheets: FakeWorksheet):
        self.sheets = sheets

    def worksheet(self, title):
        return self.sheets.get(title, FakeWorksheet())

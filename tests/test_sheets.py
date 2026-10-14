from datetime import date
from decimal import Decimal

from app.models import Expense
from app.sheets import SheetsRepository
from tests.conftest import FakeSpreadsheet, FakeWorksheet


def test_expense_round_trips_through_the_sheet():
    sheet = FakeWorksheet()
    repo = SheetsRepository(FakeSpreadsheet(Expenses=sheet))
    expense = Expense(date(2026, 10, 3), Decimal("1234.50"), "Market", "Food")

    repo.add_expense(expense)
    columns = ["date", "amount", "place", "category"]
    sheet.records = [dict(zip(columns, sheet.appended[0], strict=True))]

    assert sheet.appended == [["03/10/2026", "1234.50", "Market", "Food"]]
    assert repo.load_snapshot().expenses == (expense,)

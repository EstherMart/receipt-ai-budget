"""Google Sheets storage. Parsing is separated from gspread so it can be tested offline."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Protocol

from app.models import (
    BudgetSnapshot,
    Config,
    Expense,
    FixedBill,
    Income,
    InstallmentPlan,
)
from app.money import format_br_date, parse_br_date, parse_brl

CONFIG, INCOME, FIXED, INSTALLMENTS, EXPENSES = (
    "Config",
    "Income",
    "Fixed",
    "Installments",
    "Expenses",
)
TRUE_VALUES = {"true", "yes", "sim", "1", "x"}


class Worksheet(Protocol):
    def get_all_records(self) -> list[dict[str, Any]]: ...
    def append_row(self, values: list[Any]) -> Any: ...
    def update_cell(self, row: int, col: int, value: Any) -> Any: ...


class Spreadsheet(Protocol):
    def worksheet(self, title: str) -> Worksheet: ...


def _money(value: Any) -> Decimal:
    return parse_brl(value if isinstance(value, str) else str(value))


def _flag(value: Any) -> bool:
    return str(value).strip().lower() in TRUE_VALUES


def _text_amount(amount: Decimal) -> str:
    return f"{amount:.2f}"  # always dot-decimal, so it reads back the same in any locale


def parse_config(records: list[dict[str, Any]]) -> Config:
    values = {str(r["key"]).strip(): r["value"] for r in records}
    defaults = Config()
    return Config(
        starting_balance=_money(values.get("starting_balance", defaults.starting_balance)),
        investment_goal=_money(values.get("investment_goal", defaults.investment_goal)),
        rollover_day=int(values.get("rollover_day", defaults.rollover_day)),
    )


class SheetsRepository:
    def __init__(self, spreadsheet: Spreadsheet) -> None:
        self._spreadsheet = spreadsheet

    @classmethod
    def connect(cls, service_account_file: str, spreadsheet_id: str) -> SheetsRepository:
        import gspread

        client = gspread.service_account(filename=service_account_file)
        return cls(client.open_by_key(spreadsheet_id))

    def load_snapshot(self) -> BudgetSnapshot:
        return BudgetSnapshot(
            config=parse_config(self._records(CONFIG)),
            incomes=tuple(
                Income(
                    r["description"],
                    _money(r["amount"]),
                    parse_br_date(r["date"]),
                    _flag(r["recurring"]),
                )
                for r in self._records(INCOME)
            ),
            fixed_bills=tuple(
                FixedBill(r["name"], _money(r["amount"]), int(r["due_day"]), _flag(r["paid"]))
                for r in self._records(FIXED)
            ),
            installments=tuple(
                InstallmentPlan(
                    r["description"],
                    _money(r["total"]),
                    int(r["count"]),
                    int(r["current"]),
                    _money(r["amount_each"]),
                )
                for r in self._records(INSTALLMENTS)
            ),
            expenses=tuple(
                Expense(parse_br_date(r["date"]), _money(r["amount"]), r["place"], r["category"])
                for r in self._records(EXPENSES)
            ),
        )

    def add_expense(self, expense: Expense) -> None:
        self._append(
            EXPENSES,
            [
                format_br_date(expense.date),
                _text_amount(expense.amount),
                expense.place,
                expense.category,
            ],
        )

    def add_fixed_bill(self, bill: FixedBill) -> None:
        self._append(FIXED, [bill.name, _text_amount(bill.amount), bill.due_day, "no"])

    def add_installment_plan(self, plan: InstallmentPlan) -> None:
        self._append(
            INSTALLMENTS,
            [
                plan.description,
                _text_amount(plan.total),
                plan.count,
                plan.current,
                _text_amount(plan.amount_each),
            ],
        )

    def set_investment_goal(self, amount: Decimal) -> None:
        sheet = self._spreadsheet.worksheet(CONFIG)
        for index, record in enumerate(sheet.get_all_records()):
            if str(record["key"]).strip() == "investment_goal":
                sheet.update_cell(index + 2, 2, _text_amount(amount))  # row 1 is the header
                return
        sheet.append_row(["investment_goal", _text_amount(amount)])

    def _records(self, title: str) -> list[dict[str, Any]]:
        return self._spreadsheet.worksheet(title).get_all_records()

    def _append(self, title: str, row: list[Any]) -> None:
        self._spreadsheet.worksheet(title).append_row(row)

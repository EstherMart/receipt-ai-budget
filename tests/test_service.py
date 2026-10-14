from datetime import date
from decimal import Decimal

from app.ai import InterpreterInput
from app.models import Expense
from app.service import BudgetAssistant
from app.sheets import SheetsRepository
from tests.conftest import CATEGORIES, FakeSpreadsheet, FakeWorksheet

TODAY = date(2026, 10, 12)


class FakeInterpreter:
    def __init__(self, response):
        self.response = response
        self.received: list[InterpreterInput] = []

    def interpret_request(self, request):
        self.received.append(request)
        return self.response


def make_assistant(response, **sheets):
    sheets.setdefault("Config", FakeWorksheet([{"key": "starting_balance", "value": 1000}]))
    repo = SheetsRepository(FakeSpreadsheet(**sheets))
    return BudgetAssistant(FakeInterpreter(response), repo, CATEGORIES, lambda: TODAY), sheets


RECEIPT = {
    "intent": "expense",
    "amount": 42.9,
    "date": "10/10/2026",
    "place": "Market",
    "category": "Food",
}


def test_receipt_requires_confirmation_before_saving():
    assistant, sheets = make_assistant(RECEIPT, Expenses=FakeWorksheet())

    reply = assistant.understand(InterpreterInput(image=b"img"))

    assert reply.pending == Expense(date(2026, 10, 10), Decimal("42.90"), "Market", "Food")
    assert reply.text == "Expense R$ 42,90 at Market, Food, 10/10/2026. Save?"
    assert sheets["Expenses"].appended == []  # nothing written yet

    assistant.confirm(reply.pending)
    assert sheets["Expenses"].appended == [["10/10/2026", "42.90", "Market", "Food"]]


def test_invalid_ai_output_is_never_proposed():
    assistant, sheets = make_assistant({**RECEIPT, "amount": -1})
    reply = assistant.understand(InterpreterInput(text="x"))
    assert reply.pending is None
    assert "Amount must be positive" in reply.text


def test_simulation_answers_without_confirmation_or_writing():
    assistant, sheets = make_assistant({"intent": "simulation", "amount": 400, "installments": 4})
    reply = assistant.understand(InterpreterInput(text="Can I buy sneakers?"))
    assert reply.pending is None
    assert "You can afford it." in reply.text
    assert "4x R$ 100,00" in reply.text

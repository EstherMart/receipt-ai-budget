import asyncio
from types import SimpleNamespace

import pytest
from telegram import Update

from app import bot
from app.config import Settings

OWNER_ID = 123
SETTINGS = Settings(
    telegram_bot_token="1:fake-token",
    allowed_telegram_user_id=OWNER_ID,
    gemini_api_key="key",
    gemini_model="model",
    google_service_account_file="sa.json",
    spreadsheet_id="sheet",
    categories=("Food",),
)


@pytest.fixture
def application(monkeypatch):
    monkeypatch.setattr(bot, "GeminiInterpreter", lambda *args: object())
    monkeypatch.setattr(bot.SheetsRepository, "connect", lambda *args: object())
    return bot.build_application(SETTINGS)


def command_update(user_id: int) -> Update:
    data = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 0,
            "chat": {"id": user_id, "type": "private"},
            "from": {"id": user_id, "is_bot": False, "first_name": "Someone"},
            "text": "/balance",
            "entities": [{"type": "bot_command", "offset": 0, "length": 8}],
        },
    }
    return Update.de_json(data, SimpleNamespace(username="testbot"))  # commands need a username


def matching_handlers(application, update):
    return [h for h in application.handlers[0] if h.check_update(update)]


def test_owner_commands_are_handled(application):
    assert len(matching_handlers(application, command_update(OWNER_ID))) == 1


def test_other_users_are_silently_ignored(application):
    assert matching_handlers(application, command_update(999)) == []


def test_confirmation_buttons_ignore_other_users(application):
    class Query:
        from_user = SimpleNamespace(id=999)
        data = "yes"
        answered = False

        async def answer(self):
            self.answered = True

    query = Query()
    context = SimpleNamespace(application=application, user_data={bot.PENDING: object()})
    asyncio.run(bot.answer_confirmation(SimpleNamespace(callback_query=query), context))

    assert not query.answered
    assert context.user_data[bot.PENDING] is not None

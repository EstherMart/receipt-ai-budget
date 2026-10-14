"""Telegram entry point. Run with: python -m app.bot"""

from __future__ import annotations

import logging
from dataclasses import asdict

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.ai import GeminiInterpreter, InterpreterInput
from app.config import Settings
from app.service import BudgetAssistant, Reply
from app.sheets import SheetsRepository

PENDING = "pending"
AWAITING_FIX = "awaiting_fix"
CONFIRM_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Yes", callback_data="yes"),
            InlineKeyboardButton("Fix", callback_data="fix"),
        ]
    ]
)


def _assistant(context: ContextTypes.DEFAULT_TYPE) -> BudgetAssistant:
    return context.application.bot_data["assistant"]


async def _send(update: Update, context: ContextTypes.DEFAULT_TYPE, reply: Reply) -> None:
    context.user_data[PENDING] = reply.pending
    context.user_data[AWAITING_FIX] = False
    markup = CONFIRM_KEYBOARD if reply.pending else None
    await update.effective_message.reply_text(reply.text, reply_markup=markup)


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send(update, context, _assistant(context).balance())


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file = await update.effective_message.photo[-1].get_file()
    image = bytes(await file.download_as_bytearray())  # kept in memory, never written to disk
    await _send(update, context, _assistant(context).understand(InterpreterInput(image=image)))


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending = context.user_data.get(PENDING) if context.user_data.get(AWAITING_FIX) else None
    previous = {key: str(value) for key, value in asdict(pending).items()} if pending else None
    request = InterpreterInput(text=update.effective_message.text, previous=previous)
    await _send(update, context, _assistant(context).understand(request))


async def answer_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.from_user.id != context.application.bot_data["owner_id"]:
        return  # callback queries cannot be filtered by user, so check here
    await query.answer()
    pending = context.user_data.get(PENDING)
    if pending is None:
        await query.edit_message_text("Nothing to confirm.")
    elif query.data == "yes":
        context.user_data[PENDING] = None
        await query.edit_message_text(_assistant(context).confirm(pending).text)
    else:
        context.user_data[AWAITING_FIX] = True
        await query.edit_message_text("Send the correction.")


def build_application(settings: Settings) -> Application:
    assistant = BudgetAssistant(
        GeminiInterpreter(settings.gemini_api_key, settings.gemini_model, settings.categories),
        SheetsRepository.connect(settings.google_service_account_file, settings.spreadsheet_id),
        settings.categories,
    )
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["assistant"] = assistant
    app.bot_data["owner_id"] = settings.allowed_telegram_user_id

    # Every handler is restricted to the owner; other users are silently ignored.
    owner = filters.User(user_id=settings.allowed_telegram_user_id)
    app.add_handler(CommandHandler("balance", balance, filters=owner))
    app.add_handler(MessageHandler(owner & filters.PHOTO, photo))
    app.add_handler(MessageHandler(owner & filters.TEXT & ~filters.COMMAND, text))
    app.add_handler(CallbackQueryHandler(answer_confirmation, pattern="^(yes|fix)$"))
    return app


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.WARNING)  # never log receipts or amounts
    build_application(Settings.from_env()).run_polling()


if __name__ == "__main__":
    main()

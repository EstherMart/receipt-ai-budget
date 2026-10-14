"""Settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Raised when a required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    allowed_telegram_user_id: int
    gemini_api_key: str
    gemini_model: str
    google_service_account_file: str
    spreadsheet_id: str
    categories: tuple[str, ...]

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        env = dict(os.environ) if env is None else env

        def required(name: str) -> str:
            value = env.get(name, "").strip()
            if not value:
                raise ConfigError(f"Missing required setting: {name}")
            return value

        try:
            user_id = int(required("ALLOWED_TELEGRAM_USER_ID"))
        except ValueError as error:
            raise ConfigError("ALLOWED_TELEGRAM_USER_ID must be an integer") from error

        categories = tuple(c.strip() for c in required("CATEGORIES").split(",") if c.strip())
        if not categories:
            raise ConfigError("CATEGORIES must contain at least one category")

        return cls(
            telegram_bot_token=required("TELEGRAM_BOT_TOKEN"),
            allowed_telegram_user_id=user_id,
            gemini_api_key=required("GEMINI_API_KEY"),
            gemini_model=required("GEMINI_MODEL"),
            google_service_account_file=required("GOOGLE_SERVICE_ACCOUNT_FILE"),
            spreadsheet_id=required("SPREADSHEET_ID"),
            categories=categories,
        )

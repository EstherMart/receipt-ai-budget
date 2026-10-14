# Security policy

The bot handles personal financial data. Take any flaw that exposes secrets, data or access seriously.

## How to report a vulnerability

Do not open a public issue. Use GitHub's **Security → Report a vulnerability** tab (private report) or write to the maintainer. Describe what happened, how to reproduce it and the impact. We reply within 7 days.

## If a key leaked

1. Revoke the key with the provider (Telegram/BotFather, Google AI Studio, Google Cloud).
2. Generate a new one and update your `.env`.
3. Deleting the commit is not enough: treat the key as compromised.

## Project rules

- Never commit `.env`, service account JSON, spreadsheets or real receipts.
- Use only fictional values in tests, examples and GIFs.
- More details in the [Security and privacy](README.md#security-and-privacy) section of the README.

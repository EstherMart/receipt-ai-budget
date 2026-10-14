# Contributing

Thanks for wanting to help! Code, tests, documentation and ideas are all welcome.

## Before you start

1. Search the [issues](../../issues) for something similar. If there is none, open one so we can talk before a large PR.
2. Fork the repo and create a branch from `main`: `git checkout -b feat/my-idea`.

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest                  # no credentials needed
ruff check . && ruff format --check .
```

## Rules

- **Money math is code.** The AI only interprets. Do not ask the model to add, divide or round.
- Every new calculation in the budget engine needs a test, including cents (R$ 100 in 3 installments = 33.33 + 33.33 + 33.34) and month rollover.
- Validate AI output with a schema and keep the confirmation step before saving.
- Keep the Gemini call behind `interpret_request(input) -> dict`, so the rest of the code does not depend on the SDK.
- **No real data:** tests, screenshots and GIFs use fictional values only. Never submit `.env`, keys, spreadsheets or receipts.

## Pull requests

- One topic per PR, with a description of what changed and why.
- Passing `pytest` and `ruff`, and updated documentation.
- Commit messages in English, in the imperative ("Add installment simulation").

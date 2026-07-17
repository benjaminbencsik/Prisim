# Prism

Prism is a portable Python CLI for inspecting Kalshi markets and managing trades. It is designed for a VPS, uses Kalshi's v2 REST API, and defaults to **demo environment + dry-run orders** so an accidental command cannot place live trades.

## Install

Requires Python 3.10+.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
```

## Configure

Copy `.env.example` to your shell environment (Prism intentionally does not load `.env` automatically):

```bash
export KALSHI_ENV=demo
export KALSHI_API_KEY_ID='your-key-id'
export KALSHI_PRIVATE_KEY_PATH="$HOME/.kalshi/private_key.pem"
export PRISM_DRY_RUN=true
```

The private key must be an unencrypted PEM RSA key downloaded from Kalshi. Keep it outside the repository and restrict it with `chmod 600`.

## Commands

```bash
prism markets --limit 10
prism market TICKER
prism balance
prism positions
prism order TICKER --action buy --side yes --count 1 --price 35
```

Orders print a generated client order ID and are only simulated while `PRISM_DRY_RUN=true`. To place a live order, set `KALSHI_ENV=prod`, set `PRISM_DRY_RUN=false`, and pass `--confirm-live` on the specific order command:

```bash
KALSHI_ENV=prod PRISM_DRY_RUN=false prism order TICKER \
  --action buy --side yes --count 1 --price 35 --confirm-live
```

Review the market, price, count, and account before live use. Prism is an execution client, not financial advice or an automated strategy.

## Development

```bash
python -m unittest discover -s tests
# or, if pytest is installed:
python -m pytest
```

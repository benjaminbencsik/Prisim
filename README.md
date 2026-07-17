# Prism

## Install on a VPS

Requires Python 3.10+. On Ubuntu/Debian, install `git`, `python3`, and `python3-venv` if they are not already installed, then run:

```bash
git clone https://github.com/benjaminbencsik/Prisim.git
cd Prisim
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
python -m unittest discover -s tests -v
prism doctor
```

The default is demo mode with dry-run orders, so this setup does not require credentials or place trades. After reconnecting to the VPS:

```bash
cd ~/Prisim && source .venv/bin/activate
```

To update an existing checkout, run `git pull origin main` from the `Prisim` directory. If you prefer the requirements workflow, use `python -m pip install -r requirements.txt` before `python -m pip install -e .`.

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
prism search "keyword"
prism book TICKER
prism trades TICKER
prism balance
prism positions
prism orders --status resting
prism fills
prism pnl
prism reconcile
prism order-status ORDER_ID
prism cancel ORDER_ID
prism doctor
prism order TICKER --action buy --side yes --count 1 --price 35
```

Orders print a generated client order ID and are only simulated while `PRISM_DRY_RUN=true`. To place a live order, set `KALSHI_ENV=prod`, set `PRISM_DRY_RUN=false`, and pass `--confirm-live` on the specific order command:

```bash
KALSHI_ENV=prod PRISM_DRY_RUN=false prism order TICKER \
  --action buy --side yes --count 1 --price 35 --confirm-live
```

Review the market, price, count, and account before live use. Prism is an execution client, not financial advice or an automated strategy.

## Safety and local audit history

Every simulated or submitted order is recorded in the SQLite database configured by `PRISM_DATABASE` (default: `prism.db`). The database is local-only and ignored by Git. Before an order is sent, Prism enforces:

- Dry-run mode unless explicitly disabled
- A per-order cost ceiling with `PRISM_MAX_ORDER_COST_CENTS`
- A maximum number of open local orders with `PRISM_MAX_OPEN_ORDERS`
- An emergency stop using `PRISM_KILL_SWITCH=true`
- Explicit `--confirm-live` for live orders and cancellations

The API client retries transient HTTP and network failures with short exponential backoff. Use `prism doctor` to inspect environment, credential presence, private-API readiness, database path, and kill-switch state without printing secrets. `orders`, `balance`, `positions`, and order lifecycle commands require credentials; a missing or invalid key will return an API authentication error.

`prism reconcile` refreshes local order statuses and stores fills from Kalshi. `prism pnl` reports fill cash flow only: it is not a mark-to-market P&L calculation. A sample systemd unit is provided at `systemd/prism.service.example`; customize it before enabling a service.

These controls do not constitute a trading strategy or guarantee against losses. Do not enable unattended live trading until you have independently tested reconciliation, account limits, and your intended strategy in the demo environment.

## Development

```bash
python -m unittest discover -s tests
# or, if pytest is installed:
python -m pytest
```

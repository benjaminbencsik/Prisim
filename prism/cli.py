"""Command-line interface for Prism."""

import argparse
import json
import sys
import uuid

from .client import KalshiClient, KalshiError
from .config import Config


def _json(data: dict) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prism", description="Portable Kalshi trading CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    markets = sub.add_parser("markets", help="List markets")
    markets.add_argument("--limit", type=int, default=20)
    markets.add_argument("--status", default=None)
    market = sub.add_parser("market", help="Show one market")
    market.add_argument("ticker")
    sub.add_parser("balance", help="Show account balance")
    positions = sub.add_parser("positions", help="Show positions")
    positions.add_argument("--ticker")
    order = sub.add_parser("order", help="Create an order (dry-run by default)")
    order.add_argument("ticker")
    order.add_argument("--action", choices=["buy", "sell"], required=True)
    order.add_argument("--side", choices=["yes", "no"], required=True)
    order.add_argument("--count", type=int, required=True)
    order.add_argument("--price", type=int, required=True, help="Price in cents, 1-99")
    order.add_argument("--client-order-id", default=None)
    order.add_argument("--confirm-live", action="store_true", help="Allow live order when PRISM_DRY_RUN=false")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = Config.from_env()
        client = KalshiClient.from_config(config)
        if args.command == "markets":
            result = client.markets(args.limit, args.status)
        elif args.command == "market":
            result = client.market(args.ticker)
        elif args.command == "balance":
            result = client.balance()
        elif args.command == "positions":
            result = client.positions(args.ticker)
        else:
            if not 1 <= args.price <= 99 or args.count < 1:
                raise ValueError("price must be 1-99 cents and count must be positive")
            if not config.dry_run and not args.confirm_live:
                raise ValueError("Live order blocked: pass --confirm-live explicitly")
            result = client.create_order({
                "ticker": args.ticker, "client_order_id": args.client_order_id or str(uuid.uuid4()),
                "action": args.action, "side": args.side, "count": args.count,
                "type": "limit", "yes_price": args.price if args.side == "yes" else None,
                "no_price": args.price if args.side == "no" else None,
            })
        _json(result)
        return 0
    except (ValueError, KalshiError, OSError) as exc:
        print(f"prism: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

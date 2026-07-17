"""Hard safety gates for all order submissions."""

from .config import Config
from .storage import Storage


class RiskError(ValueError):
    pass


def validate_order(order: dict, config: Config, storage: Storage, confirm_live: bool = False) -> None:
    price = order.get("yes_price") or order.get("no_price")
    count = order.get("count", 0)
    if not isinstance(price, int) or not 1 <= price <= 99:
        raise RiskError("price must be 1-99 cents")
    if not isinstance(count, int) or count < 1:
        raise RiskError("count must be positive")
    if price * count > config.max_order_cost_cents:
        raise RiskError(f"order cost exceeds PRISM_MAX_ORDER_COST_CENTS ({config.max_order_cost_cents})")
    if storage.open_order_count() >= config.max_open_orders:
        raise RiskError(f"maximum open orders reached ({config.max_open_orders})")
    if config.kill_switch:
        raise RiskError("kill switch is active; set PRISM_KILL_SWITCH=false to submit orders")
    if not config.dry_run and not config.live_trading_enabled:
        raise RiskError("live trading is disabled; set PRISM_LIVE_TRADING=enabled explicitly")
    if not config.dry_run and not confirm_live:
        raise RiskError("live order blocked: pass --confirm-live explicitly")

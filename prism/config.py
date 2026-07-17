"""Runtime configuration loaded from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Config:
    api_key_id: str | None
    private_key_path: Path | None
    environment: str = "demo"
    dry_run: bool = True
    timeout: float = 20.0
    database_path: Path = Path("prism.db")
    max_order_cost_cents: int = 10000
    max_open_orders: int = 20
    kill_switch: bool = False

    @property
    def base_url(self) -> str:
        if self.environment == "prod":
            return "https://api.elections.kalshi.com/trade-api/v2"
        return "https://demo-api.kalshi.co/trade-api/v2"

    @classmethod
    def from_env(cls) -> "Config":
        environment = os.getenv("KALSHI_ENV", "demo").lower()
        if environment not in {"demo", "prod"}:
            raise ValueError("KALSHI_ENV must be 'demo' or 'prod'")
        private_key = os.getenv("KALSHI_PRIVATE_KEY_PATH")
        dry_run = os.getenv("PRISM_DRY_RUN", "true").lower() not in {"0", "false", "no"}
        return cls(
            api_key_id=os.getenv("KALSHI_API_KEY_ID"),
            private_key_path=Path(private_key).expanduser() if private_key else None,
            environment=environment,
            dry_run=dry_run,
            timeout=float(os.getenv("PRISM_TIMEOUT", "20")),
            database_path=Path(os.getenv("PRISM_DATABASE", "prism.db")).expanduser(),
            max_order_cost_cents=int(os.getenv("PRISM_MAX_ORDER_COST_CENTS", "10000")),
            max_open_orders=int(os.getenv("PRISM_MAX_OPEN_ORDERS", "20")),
            kill_switch=os.getenv("PRISM_KILL_SWITCH", "false").lower() in {"1", "true", "yes"},
        )

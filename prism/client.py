"""Small stdlib HTTP client for Kalshi's v2 API."""

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .auth import KalshiSigner
from .config import Config


class KalshiError(RuntimeError):
    """An API or transport error returned by Kalshi."""


@dataclass
class KalshiClient:
    config: Config
    signer: KalshiSigner | None = None

    @classmethod
    def from_config(cls, config: Config) -> "KalshiClient":
        signer = None
        if config.api_key_id or config.private_key_path:
            if not config.api_key_id or not config.private_key_path:
                raise ValueError("KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY_PATH must be set together")
            signer = KalshiSigner(config.api_key_id, config.private_key_path)
        return cls(config, signer)

    def request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        query = f"?{urlencode({k: v for k, v in (params or {}).items() if v is not None})}" if params else ""
        url = f"{self.config.base_url}{path}{query}"
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if self.signer:
            headers.update(self.signer.headers(method, f"/trade-api/v2{path}"))
        request = Request(url, method=method.upper(), headers=headers,
                          data=json.dumps(body).encode() if body is not None else None)
        try:
            with urlopen(request, timeout=self.config.timeout) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise KalshiError(f"Kalshi HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise KalshiError(f"Unable to reach Kalshi: {exc.reason}") from exc

    def markets(self, limit: int = 20, status: str | None = None, cursor: str | None = None) -> dict:
        return self.request("GET", "/markets", {"limit": limit, "status": status, "cursor": cursor})

    def market(self, ticker: str) -> dict:
        return self.request("GET", f"/markets/{ticker}")

    def balance(self) -> dict:
        return self.request("GET", "/portfolio/balance")

    def positions(self, ticker: str | None = None) -> dict:
        return self.request("GET", "/portfolio/positions", {"ticker": ticker})

    def create_order(self, order: dict) -> dict:
        if self.config.dry_run:
            return {"dry_run": True, "order": order}
        if not self.signer:
            raise KalshiError("Live orders require API credentials")
        return self.request("POST", "/portfolio/orders", body=order)

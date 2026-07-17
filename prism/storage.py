"""SQLite audit storage for Prism orders."""

import json
import sqlite3
from pathlib import Path


class Storage:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS orders (
                client_order_id TEXT PRIMARY KEY, order_id TEXT, ticker TEXT NOT NULL,
                status TEXT NOT NULL, request_json TEXT NOT NULL, response_json TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS fills (
                fill_id TEXT PRIMARY KEY, order_id TEXT, ticker TEXT NOT NULL,
                side TEXT, action TEXT, count INTEGER, price INTEGER,
                raw_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    def record_order(self, request: dict, response: dict, status: str) -> None:
        client_id = request["client_order_id"]
        order_id = response.get("order", response).get("order_id") if isinstance(response.get("order", response), dict) else None
        with self._connect() as db:
            db.execute("""INSERT INTO orders (client_order_id, order_id, ticker, status, request_json, response_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(client_order_id) DO UPDATE SET order_id=excluded.order_id,
                status=excluded.status, response_json=excluded.response_json, updated_at=CURRENT_TIMESTAMP""",
                (client_id, order_id, request["ticker"], status, json.dumps(request), json.dumps(response)))

    def update_status(self, order_id: str, status: str, response: dict) -> None:
        with self._connect() as db:
            db.execute("UPDATE orders SET status=?, response_json=?, updated_at=CURRENT_TIMESTAMP WHERE order_id=?",
                       (status, json.dumps(response), order_id))

    def open_order_count(self) -> int:
        with self._connect() as db:
            return db.execute("SELECT COUNT(*) FROM orders WHERE status IN ('resting', 'pending', 'open')").fetchone()[0]

    def orders(self, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM orders"
        args: tuple = ()
        if status:
            query += " WHERE status=?"
            args = (status,)
        query += " ORDER BY created_at DESC"
        with self._connect() as db:
            return [dict(row) for row in db.execute(query, args).fetchall()]

    def record_fills(self, payload: dict) -> int:
        fills = payload.get("fills", [])
        with self._connect() as db:
            for fill in fills:
                fill_id = fill.get("fill_id") or fill.get("id")
                if not fill_id:
                    continue
                db.execute("""INSERT OR REPLACE INTO fills
                    (fill_id, order_id, ticker, side, action, count, price, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
                    fill_id, fill.get("order_id"), fill.get("ticker", "unknown"),
                    fill.get("side"), fill.get("action"), fill.get("count"),
                    fill.get("yes_price") or fill.get("no_price") or fill.get("price"), json.dumps(fill)))
        return len(fills)

    def fills(self) -> list[dict]:
        with self._connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM fills ORDER BY created_at DESC").fetchall()]

    def cashflow(self) -> dict:
        """Return fill cash flow; this is not mark-to-market P&L."""
        rows = self.fills()
        buy = sum((row["price"] or 0) * (row["count"] or 0) for row in rows if row["action"] == "buy")
        sell = sum((row["price"] or 0) * (row["count"] or 0) for row in rows if row["action"] == "sell")
        return {"fills": len(rows), "buy_cents": buy, "sell_cents": sell, "net_cashflow_cents": sell - buy}

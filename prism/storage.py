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

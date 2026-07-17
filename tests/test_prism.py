import io
import json
import os
from pathlib import Path
import unittest
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from prism.cli import main
from prism.config import Config
from prism.risk import RiskError, validate_order
from prism.storage import Storage


class PrismTests(unittest.TestCase):
    def test_demo_config_defaults_to_safe_mode(self):
        with patch.dict(os.environ, {}, clear=True):
            config = Config.from_env()
        self.assertEqual(config.environment, "demo")
        self.assertTrue(config.dry_run)


    def test_order_is_dry_run(self):
        stdout = io.StringIO()
        with patch.dict(os.environ, {"PRISM_DRY_RUN": "true"}), redirect_stdout(stdout):
            result = main(["order", "TEST-MARKET", "--action", "buy", "--side", "yes", "--count", "2", "--price", "40"])
        output = json.loads(stdout.getvalue())
        self.assertEqual(result, 0)
        self.assertTrue(output["dry_run"])
        self.assertEqual(output["order"]["yes_price"], 40)


    def test_invalid_order_price(self):
        stderr = io.StringIO()
        with patch.dict(os.environ, {"PRISM_DRY_RUN": "true"}), redirect_stderr(stderr):
            result = main(["order", "TEST", "--action", "buy", "--side", "yes", "--count", "1", "--price", "100"])
        self.assertEqual(result, 2)
        self.assertIn("price must be", stderr.getvalue())

    def test_risk_limit_blocks_expensive_order(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(None, None, max_order_cost_cents=50, database_path=Path(directory) / "p.db")
            with self.assertRaises(RiskError):
                validate_order({"ticker": "T", "count": 2, "yes_price": 30}, config, Storage(config.database_path))

    def test_storage_records_order(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "p.db")
            request = {"client_order_id": "abc", "ticker": "T"}
            storage.record_order(request, {"dry_run": True}, "dry_run")
            self.assertEqual(storage.orders()[0]["client_order_id"], "abc")

    def test_kill_switch_blocks_order(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(None, None, kill_switch=True, database_path=Path(directory) / "p.db")
            with self.assertRaisesRegex(RiskError, "kill switch"):
                validate_order({"ticker": "T", "count": 1, "yes_price": 30}, config, Storage(config.database_path))


if __name__ == "__main__":
    unittest.main()

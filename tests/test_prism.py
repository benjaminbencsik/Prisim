import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from prism.cli import main
from prism.config import Config


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


if __name__ == "__main__":
    unittest.main()

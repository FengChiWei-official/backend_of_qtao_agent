import unittest

import os, sys
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PATH_TO_ROOT)
import logging
logger = logging.getLogger(__name__)

from config.loadConfig import ConfigLoader

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.config_loader = ConfigLoader(os.path.join(PATH_TO_ROOT, "config", "config.yaml"))
        self.test_default = ConfigLoader(os.path.join(PATH_TO_ROOT, "tests", "config", "test.yaml"))
        self.test_missing_required = ConfigLoader(os.path.join(PATH_TO_ROOT, "tests", "config", "test_missing_required.yaml"))
    def test_get_db_config(self):
        db_config = self.config_loader.get_db_config()
        self.assertIn("db_type", db_config)
        self.assertIn(db_config["db_type"], db_config)
        self.assertIsInstance(db_config[db_config["db_type"]], dict)
        self.assertIn("user", db_config[db_config["db_type"]])
        self.assertIn("password", db_config[db_config["db_type"]])
        self.assertIn("host", db_config[db_config["db_type"]])
        self.assertIn("port", db_config[db_config["db_type"]])
        self.assertIn("database", db_config[db_config["db_type"]])
        logger.info("Database config loaded successfully: %s", db_config)

    def test_default_config(self):
        db_config = self.test_default.get_db_config()
        self.assertIn("db_type", db_config)
        self.assertIn(db_config["db_type"], db_config)
        self.assertIsInstance(db_config[db_config["db_type"]], dict)
        self.assertIn("user", db_config[db_config["db_type"]])
        self.assertIn("password", db_config[db_config["db_type"]])
        self.assertIn("host", db_config[db_config["db_type"]])
        self.assertIn("port", db_config[db_config["db_type"]])
        self.assertIn("database", db_config[db_config["db_type"]])
        self.assertIn("driver", db_config[db_config["db_type"]])
        self.assertIn("echo", db_config[db_config["db_type"]])
        self.assertIn("pool_size", db_config[db_config["db_type"]])
        self.assertIn("max_overflow", db_config[db_config["db_type"]])
        self.assertIn("pool_timeout", db_config[db_config["db_type"]])
        self.assertIn("pool_recycle", db_config[db_config["db_type"]])
        self.assertIn("connection_args", db_config[db_config["db_type"]])
        self.assertIn("charset", db_config[db_config["db_type"]]["connection_args"])
        self.assertIn("connect_timeout", db_config[db_config["db_type"]]["connection_args"])
        logger.info("Default config loaded successfully: %s", db_config)

    def test_missing_required_config(self):
        with self.assertRaises(ValueError) as context:
            self.test_missing_required.get_db_config()
        self.assertIn("configuration", str(context.exception))
        logger.info("Missing required config test passed: %s", str(context.exception))
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    unittest.main()

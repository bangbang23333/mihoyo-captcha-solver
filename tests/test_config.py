import os
import tempfile
import unittest
from unittest import mock

from mihoyo_captcha.config import SolverConfig, load_config

INI = """[setting]
enable = true
api_key = ini-key
base_url = https://example.com/v1
model = ini-model
timeout = 60
headless = false
max_rounds = 3
"""


class LoadConfigTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".ini")
        os.close(fd)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(INI)
        env = mock.patch.dict(os.environ, {
            "DEEPSEEK_API_KEY": "", "DEEPSEEK_API_BASE": "", "DEEPSEEK_MODEL": "",
        })
        env.start()
        self.addCleanup(env.stop)

    def tearDown(self):
        os.remove(self.path)

    def test_read_ini(self):
        config = load_config(self.path)
        self.assertTrue(config.enable)
        self.assertEqual(config.api_key, "ini-key")
        self.assertEqual(config.base_url, "https://example.com/v1")
        self.assertEqual(config.model, "ini-model")
        self.assertEqual(config.timeout, 60)
        self.assertFalse(config.headless)
        self.assertEqual(config.max_rounds, 3)

    def test_missing_file_uses_defaults(self):
        config = load_config("/path/does/not/exist.ini")
        self.assertEqual(config, SolverConfig())
        self.assertEqual(config.api_key, "")

    def test_overrides_win(self):
        config = load_config(self.path, model="override-model", headless=True)
        self.assertEqual(config.model, "override-model")
        self.assertTrue(config.headless)
        self.assertEqual(config.api_key, "ini-key")

    def test_env_wins(self):
        with mock.patch.dict(os.environ, {"DEEPSEEK_API_KEY": "env-key", "DEEPSEEK_MODEL": "env-model"}):
            config = load_config(self.path)
        self.assertEqual(config.api_key, "env-key")
        self.assertEqual(config.model, "env-model")


if __name__ == "__main__":
    unittest.main()

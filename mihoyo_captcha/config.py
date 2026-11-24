import configparser
import os
from dataclasses import dataclass
from typing import List, Optional

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-flash"


@dataclass
class SolverConfig:
    """验证码识别配置。"""

    enable: bool = True
    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    timeout: int = 120
    headless: bool = True
    max_rounds: int = 2


def _candidate_paths(path: Optional[str]) -> List[str]:
    if path:
        return [path]
    env_path = os.getenv("MIHOYO_CAPTCHA_CONFIG")
    if env_path:
        return [env_path]
    package_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    return [
        os.path.join(os.getcwd(), "captcha.ini"),
        os.path.expanduser("~/.config/mihoyo-captcha/captcha.ini"),
        os.path.join(package_root, "captcha.ini"),
    ]


def load_config(path: Optional[str] = None, **overrides) -> SolverConfig:
    """读取配置。

    查找顺序：显式 path > 环境变量 MIHOYO_CAPTCHA_CONFIG > 当前目录 captcha.ini
    > ~/.config/mihoyo-captcha/captcha.ini > 项目根目录 captcha.ini。

    环境变量 DEEPSEEK_API_KEY / DEEPSEEK_API_BASE / DEEPSEEK_MODEL 优先级最高，
    显式传入的关键字参数会覆盖以上所有来源。
    """
    config = SolverConfig()
    for candidate in _candidate_paths(path):
        if candidate and os.path.exists(candidate):
            parser = configparser.ConfigParser()
            parser.read(candidate, encoding="utf-8")
            if parser.has_section("setting"):
                section = parser["setting"]
                config.enable = section.getboolean("enable", fallback=config.enable)
                config.api_key = section.get("api_key", config.api_key)
                config.base_url = section.get("base_url", config.base_url)
                config.model = section.get("model", config.model)
                config.timeout = section.getint("timeout", fallback=config.timeout)
                config.headless = section.getboolean("headless", fallback=config.headless)
                config.max_rounds = section.getint("max_rounds", fallback=config.max_rounds)
            break

    env_api_key = os.getenv("DEEPSEEK_API_KEY")
    if env_api_key:
        config.api_key = env_api_key
    env_base_url = os.getenv("DEEPSEEK_API_BASE")
    if env_base_url:
        config.base_url = env_base_url
    env_model = os.getenv("DEEPSEEK_MODEL")
    if env_model:
        config.model = env_model

    for key, value in overrides.items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config

"""极验九宫格点选验证码识别。

通过浏览器加载极验组件，把验证码截图交给视觉模型判断应选中的格子，
再模拟点击完成验证。识别结果以 ``{"challenge": ..., "validate": ...}`` 返回，
可直接用于米游社的 ``verifyVerification`` 或游戏签到的 ``x-rpc-*`` 请求头。
"""
from .config import SolverConfig, load_config
from .solver import solve

__version__ = "0.1.0"

__all__ = ["SolverConfig", "load_config", "solve", "bbs_captcha", "game_captcha"]


def bbs_captcha(gt: str, challenge: str, **kwargs):
    """兼容米游社社区签到/点赞的调用方式。"""
    return solve(gt, challenge, **kwargs)


def game_captcha(gt: str, challenge: str, **kwargs):
    """兼容米游社游戏签到的调用方式。"""
    return solve(gt, challenge, **kwargs)

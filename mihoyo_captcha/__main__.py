import argparse
import json
import logging
import sys

from .config import load_config
from .solver import solve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mihoyo-captcha",
        description="识别米游社使用的极验九宫格点选验证码，输出 challenge/validate JSON",
    )
    parser.add_argument("--gt", required=True, help="极验 gt")
    parser.add_argument("--challenge", required=True, help="极验 challenge")
    parser.add_argument("--config", default=None, help="captcha.ini 路径")
    parser.add_argument("--api-key", default=None, help="视觉模型 API Key")
    parser.add_argument("--base-url", default=None, help="OpenAI 兼容接口地址")
    parser.add_argument("--model", default=None, help="视觉模型名称")
    parser.add_argument("--timeout", type=int, default=None, help="单次识别请求超时（秒）")
    parser.add_argument("--max-rounds", type=int, default=None, help="最多识别轮数")
    headless = parser.add_mutually_exclusive_group()
    headless.add_argument("--headless", dest="headless", action="store_true", help="无头模式（默认）")
    headless.add_argument("--no-headless", dest="headless", action="store_false", help="显示浏览器窗口，便于调试")
    parser.set_defaults(headless=None)
    parser.add_argument("--quiet", action="store_true", help="只输出错误日志")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    config = load_config(
        args.config,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
        timeout=args.timeout,
        headless=args.headless,
        max_rounds=args.max_rounds,
    )
    result = solve(args.gt, args.challenge, config=config)
    if not result:
        print("验证码识别失败", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

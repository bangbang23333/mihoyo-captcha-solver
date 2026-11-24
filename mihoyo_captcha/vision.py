import base64
import json
import logging
import re
from typing import List

import httpx

from .config import SolverConfig

logger = logging.getLogger("mihoyo_captcha")

_PROMPT = """这是极验的九宫格点选验证码。
顶部文字“请选中下图中所有的：”右侧的小图是目标物体。
下面是 3x3 九宫格，编号规则：从左到右、从上到下依次为 1-9。
如果题目是“请选中下图中所有的：X”，返回所有包含 X 的格子；
如果题目是“请依次点击：X、Y、Z”，按题目要求顺序返回每个目标所在的格子。
只输出一行 JSON，不要输出其它内容：
{"target": "目标物体名称", "cells": [包含目标的格子编号]}"""


def parse_cells(content: str) -> List[int]:
    """从模型输出中解析格子编号，兼容纯 JSON、代码块包裹、字符串形式的编号。"""
    match = re.search(r"\{.*\}", content, re.S)
    if not match:
        logger.warning(f"验证码识别结果无法解析：{content[:200]}")
        return []
    try:
        data = json.loads(match.group(0))
    except ValueError:
        logger.warning(f"验证码识别结果无法解析：{content[:200]}")
        return []

    cells = []
    for item in data.get("cells", []):
        for token in re.findall(r"\d+", str(item)):
            index = int(token)
            if 1 <= index <= 9 and index not in cells:
                cells.append(index)
    if cells:
        logger.info(f"视觉模型识别结果：目标「{data.get('target', '')}」，选择格子 {cells}")
    return cells


def ask_model(config: SolverConfig, widget_png: bytes, tip_png: bytes) -> List[int]:
    """把验证码截图发给视觉模型，返回应选中的格子编号列表。"""
    payload = {
        "model": config.model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": _PROMPT},
            {"type": "image_url", "image_url": {
                "url": "data:image/png;base64," + base64.b64encode(widget_png).decode()}},
            {"type": "text", "text": "这是顶部目标小图的放大图，便于看清目标物体："},
            {"type": "image_url", "image_url": {
                "url": "data:image/png;base64," + base64.b64encode(tip_png).decode()}},
        ]}],
        "max_tokens": 300,
        "temperature": 0,
    }
    url = config.base_url.rstrip("/") + "/chat/completions"
    resp = httpx.post(url, headers={"Authorization": f"Bearer {config.api_key}"},
                      json=payload, timeout=config.timeout)
    if resp.status_code != 200:
        logger.warning(f"验证码识别接口返回 {resp.status_code}：{resp.text[:200]}")
        return []

    content = resp.json()["choices"][0]["message"].get("content") or ""
    return parse_cells(content)

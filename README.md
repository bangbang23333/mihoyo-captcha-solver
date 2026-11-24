# mihoyo-captcha-solver

米游社使用的**极验九宫格点选验证码**识别组件。通过 Playwright 加载极验组件并截图，交给视觉模型（默认 DeepSeek）判断应选中的格子，再模拟点击完成验证。

从 [MihoyoBBSTools](https://github.com/Womsxd/MihoyoBBSTools) 的 `captcha.py` 中剥离出来，可独立安装、独立配置，供任意签到/爬虫项目调用。

## 安装

```bash
pip install -e .
python -m playwright install chromium
```

只安装浏览器依赖而不装 Playwright 的情况会自动跳过验证码（返回 `None`），不影响调用方主流程。

## 配置

复制 `captcha.example.ini` 为 `captcha.ini`，填入 `api_key`：

```ini
[setting]
enable = true
api_key = sk-xxxx
base_url = https://api.deepseek.com/v1
model = deepseek-flash
timeout = 120
headless = true
max_rounds = 2
```

查找顺序：显式 `config_path` > 环境变量 `MIHOYO_CAPTCHA_CONFIG` > 当前目录 `captcha.ini` > `~/.config/mihoyo-captcha/captcha.ini` > 项目根目录 `captcha.ini`。

也可以用环境变量覆盖：`DEEPSEEK_API_KEY`、`DEEPSEEK_API_BASE`、`DEEPSEEK_MODEL`。

## Python 调用

```python
from mihoyo_captcha import solve

result = solve(gt, challenge, config_path="/path/to/captcha.ini")
if result:
    print(result["challenge"], result["validate"])
```

`bbs_captcha(gt, challenge)` / `game_captcha(gt, challenge)` 是与原项目一致的别名。

返回约定：

| 返回值 | 含义 |
| --- | --- |
| `{"challenge": ..., "validate": ...}` | 识别成功，调用方拼接 `validate + "\|jordan"` 作为 `geetest_seccode` |
| `None` | 识别失败、未配置 key、未安装 Playwright 或遇到不支持的验证码类型 |

## 命令行调用

```bash
python -m mihoyo_captcha --gt <gt> --challenge <challenge> --config captcha.ini
# 或安装后
mihoyo-captcha --gt <gt> --challenge <challenge>
```

成功时向 stdout 输出一行 JSON，失败时返回码为 1，便于非 Python 项目通过子进程调用。

## 在 MihoyoBBSTools 中调用

原项目的 `captcha.py` 已改为适配层，按以下顺序加载本包：

1. 已安装的 `mihoyo_captcha`；
2. 环境变量 `MIHOYO_CAPTCHA_SOLVER_PATH` 指向的项目目录；
3. 与原项目同级的 `mihoyo-captcha-solver` 目录。

因此既可以用 `pip install -e` 安装，也可以直接把本目录放在原项目旁边，原项目无需改代码。

## 限制

- 目前仅支持九宫格点选类型；遇到滑动验证码会记录日志并返回 `None`。
- 需要可运行 Chromium 的环境（Windows 上会自动回退到系统 Edge）。
- 识别结果依赖视觉模型，多轮失败时调用方应按原有逻辑跳过或重试签到。

## 目录结构

```
mihoyo-captcha-solver/
├── mihoyo_captcha/
│   ├── __init__.py   # 对外 API
│   ├── __main__.py   # 命令行入口
│   ├── config.py     # 配置加载
│   ├── solver.py     # Playwright + 点击流程
│   └── vision.py     # 视觉模型调用与结果解析
├── captcha.example.ini
├── pyproject.toml
└── README.md
```

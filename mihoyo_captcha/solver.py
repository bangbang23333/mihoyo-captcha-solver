import logging
import time
from typing import Optional

from .config import SolverConfig, load_config
from .vision import ask_model

logger = logging.getLogger("mihoyo_captcha")

_PAGE_URL = "https://webstatic.mihoyo.com/bbs/event/signin/hk4e/index.html"

_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>captcha</title>
<script src="https://static.geetest.com/static/js/gt.0.4.9.js"></script>
</head><body style="margin:0">
<div id="captcha"></div>
<script>
window.__gt_state = "boot";
initGeetest({
  gt: "%s", challenge: "%s", offline: false, new_captcha: true,
  product: "bind", width: "300px", lang: "zh-cn", https: true
}, function (captchaObj) {
  window.captchaObj = captchaObj;
  captchaObj.appendTo("#captcha");
  captchaObj.onReady(function () {
    window.__gt_state = "ready";
    setTimeout(function () { captchaObj.verify(); }, 300);
  });
  captchaObj.onSuccess(function () {
    window.__gt_state = "success";
    window.__gt_validate = captchaObj.getValidate();
  });
  captchaObj.onError(function (e) { window.__gt_state = "error:" + JSON.stringify(e); });
});
</script>
</body></html>"""


def _launch_browser(playwright, headless: bool):
    args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]
    try:
        return playwright.chromium.launch(headless=headless, args=args)
    except Exception as e:
        logger.warning(f"内置 Chromium 启动失败，尝试使用系统 Edge：{e}")
        return playwright.chromium.launch(channel="msedge", headless=headless, args=args)


def _new_page(browser, gt: str, challenge: str):
    html = _HTML % (gt, challenge)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        viewport={"width": 900, "height": 700},
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        device_scale_factor=2,
    )
    context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
    page = context.new_page()

    def handle_route(route):
        if route.request.resource_type == "document":
            route.fulfill(status=200, content_type="text/html; charset=utf-8", body=html)
        else:
            route.continue_()

    page.route("https://webstatic.mihoyo.com/**", handle_route)
    page.goto(_PAGE_URL, wait_until="load")
    return page


def _wait_captcha(page, timeout: int = 30) -> bool:
    """等待验证码出现：成功（智能验证直接通过）或九宫格点选/滑动组件加载完成。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        state = page.evaluate("window.__gt_state")
        if state == "success":
            return True
        if state.startswith("error"):
            logger.warning(f"验证码加载失败：{state}")
            return False
        slider = page.locator(".geetest_slider")
        if slider.count() and slider.first.is_visible():
            logger.warning("遇到滑动验证码，当前仅支持九宫格点选验证码")
            return False
        if page.locator(".geetest_item").count() >= 9:
            return True
        page.wait_for_timeout(300)
    logger.warning("等待验证码加载超时")
    return False


def _read_validate(page) -> Optional[dict]:
    validate = page.evaluate("window.__gt_validate")
    if not validate:
        return None
    challenge = validate.get("geetest_challenge")
    value = validate.get("geetest_validate")
    if not challenge or not value:
        return None
    return {"challenge": challenge, "validate": value}


def _solve_with_browser(gt: str, challenge: str, config: SolverConfig) -> Optional[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("未安装 playwright，无法自动处理验证码（pip install playwright）")
        return None

    with sync_playwright() as playwright:
        browser = _launch_browser(playwright, config.headless)
        try:
            page = _new_page(browser, gt, challenge)
            if not _wait_captcha(page):
                return None
            if page.evaluate("window.__gt_state") == "success":
                return _read_validate(page)

            page.wait_for_timeout(800)  # 等九宫格图片加载完
            for _ in range(max(1, config.max_rounds)):
                widget = page.locator(".geetest_widget").first
                tip = page.locator(".geetest_tip_img").first
                if not widget.count() or not tip.count():
                    logger.warning("验证码结构不是预期的九宫格点选类型")
                    return None
                cells = ask_model(config, widget.screenshot(), tip.screenshot())
                if not cells:
                    return None

                items = page.locator(".geetest_item")
                for index in cells:
                    items.nth(index - 1).click()
                    page.wait_for_timeout(200)

                confirm = page.locator(".geetest_commit").first
                if not confirm.count():
                    logger.warning("未找到验证码确认按钮")
                    return None
                confirm.click()
                try:
                    page.wait_for_function("window.__gt_state === 'success'", timeout=15000)
                    break
                except Exception:
                    logger.warning("验证码校验未通过，重新识别")
                    page.wait_for_timeout(2000)
                    if page.locator(".geetest_item").count() < 9:
                        return None
            return _read_validate(page)
        finally:
            browser.close()


def solve(gt: str, challenge: str, config: Optional[SolverConfig] = None,
          config_path: Optional[str] = None) -> Optional[dict]:
    """识别极验九宫格点选验证码。

    :param gt: 极验 gt
    :param challenge: 极验 challenge
    :param config: 已加载的配置对象，传入后忽略 config_path
    :param config_path: captcha.ini 路径，为空时按默认规则查找
    :return: 成功返回 ``{"challenge": ..., "validate": ...}``，失败返回 None
    """
    if not gt or not challenge:
        return None
    if config is None:
        config = load_config(config_path)
    if not config.enable:
        return None
    if not config.api_key:
        logger.debug("未配置验证码识别 api_key，跳过自动处理")
        return None

    logger.info("触发验证码，正在使用视觉模型自动识别...")
    try:
        result = _solve_with_browser(gt, challenge, config)
    except Exception as e:
        logger.error(f"验证码自动处理异常：{e}")
        return None
    if result:
        logger.info("验证码已通过")
    else:
        logger.warning("验证码自动处理失败")
    return result

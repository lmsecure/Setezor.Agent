import datetime
import asyncio
from playwright.async_api import async_playwright
import os
import base64
import sys



class Screenshoter:
    @classmethod
    async def take_screenshot(cls, url: str, screenshots_folder: str, timeout: float):
        filename = url.replace("://", "_").replace("/", "_")
        tz = datetime.datetime.now(datetime.timezone(
            datetime.timedelta(0))).astimezone().tzinfo
        current_datetime = datetime.datetime.now(tz=tz).isoformat()
        filename = f"{current_datetime}_{filename}.png"
        path = os.path.join(screenshots_folder, filename)
        result = []
        async with async_playwright() as p:
            browser = await p.firefox.launch()
            page = await browser.new_page(ignore_https_errors=True)
            await page.goto(url=url, wait_until='load')
            await asyncio.sleep(timeout)
            await page.screenshot(path=path, full_page=True)
            result.append(path)
            await browser.close()
        return path
    
    
    @classmethod
    async def _ensure_browser_installed(cls):
        try:
            async with async_playwright() as p:
                browser_path = p.chromium.executable_path
                if browser_path and os.path.exists(browser_path):
                    return True
        except Exception:
            pass
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "playwright",
                "install",
                "chromium",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False


    @classmethod
    async def take_screenshot_base64(cls, url: str, timeout: float = 2.0):
        """
        Делает скриншот страницы по url и возвращает его в base64 (без сохранения на диск).
        """
        browser_ready = await cls._ensure_browser_installed()
        if not browser_ready:
            raise Exception("Failed to install Playwright browser (chromium)")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(ignore_https_errors=True)
            await page.goto(url=url, timeout=20000)
            screenshot_bytes = await page.screenshot(full_page=True)
            await browser.close()
        raw_result = base64.b64encode(screenshot_bytes).decode("utf-8")
        return raw_result

import os
from pathlib import Path
from playwright.async_api import async_playwright

# Correct path to where Chromium is installed by Playwright on Render
CHROME_PATH = Path(
    "/opt/render/project/.venv/lib/python3.11/site-packages/playwright/driver/package/.local-browsers/chromium-1105/chrome-linux/chrome"
)

async def fetch_rendered_html(url: str) -> str:
    try:
        print(f"[Playwright] Launching browser for: {url}")
        print(f"[Playwright] Using executable: {CHROME_PATH}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=str(CHROME_PATH),
                args=["--no-sandbox"]
            )
            page = await browser.new_page()
            await page.goto(url, timeout=20000)
            html = await page.content()
            await browser.close()
            return html

    except Exception as e:
        print(f"[Playwright Error] {e}")
        raise

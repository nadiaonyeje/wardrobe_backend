import os
from pathlib import Path
from playwright.async_api import async_playwright

# Construct local path where browser is installed (after build.sh runs `npx playwright install`)
BASE_DIR = Path(__file__).resolve().parent
CHROME_PATH = BASE_DIR / "ms-playwright" / "chromium-1105" / "chrome-linux" / "chrome"

async def fetch_rendered_html(url: str) -> str:
    try:
        print(f"[Playwright] Launching browser for: {url}")
        print(f"[Playwright] Using executable: {CHROME_PATH}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=str(CHROME_PATH),  # Force path so it works in Render
                args=["--no-sandbox"]              # Important for restricted envs
            )
            page = await browser.new_page()
            await page.goto(url, timeout=20000)
            html = await page.content()
            await browser.close()
            return html

    except Exception as e:
        print(f"[Playwright Error] {e}")
        raise

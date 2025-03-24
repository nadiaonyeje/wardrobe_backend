from playwright.async_api import async_playwright
from pathlib import Path

# Playwright puts Chromium here when PLAYWRIGHT_BROWSERS_PATH=0
CHROME_PATH = Path(".") / ".playwright" / "chromium-1105" / "chrome-linux" / "chrome"

async def fetch_rendered_html(url: str) -> str:
    try:
        print(f"[Playwright] Launching browser for: {url}")
        print(f"[Playwright] Using executable: {CHROME_PATH.resolve()}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=str(CHROME_PATH.resolve()),
                args=[
                    "--no-sandbox",
                    "--disable-http2",                      # << Block HTTP/2 fallback
                    "--disable-features=NetworkService",     # << Fix HTTP protocol issues
                    "--disable-extensions",
                ]
            )
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            content = await page.content()
            await browser.close()
            return content

    except Exception as e:
        print(f"[Playwright Error] {e}")
        raise

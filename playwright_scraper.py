from playwright.async_api import async_playwright

CHROME_PATH = "/opt/render/project/src/.venv/lib/python3.11/site-packages/playwright/driver/package/.local-browsers/chromium-1105/chrome-linux/chrome"

async def fetch_rendered_html(url: str) -> str:
    try:
        print(f"[Playwright] Launching browser for: {url}")
        print(f"[Playwright] Using executable: {CHROME_PATH}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=CHROME_PATH,
                args=[
                    "--no-sandbox",
                    "--disable-http2",
                    "--disable-features=NetworkService",
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

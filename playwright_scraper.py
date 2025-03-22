# utils/playwright_scraper.py

from playwright.async_api import async_playwright

async def fetch_rendered_html(url: str) -> str:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page()
            await page.goto(url, timeout=20000)  # 20 sec timeout
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        print(f"[Playwright] Error fetching HTML: {e}")
        raise

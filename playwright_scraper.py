# utils/playwright_scraper.py
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)  # always headless in cloud

async def fetch_rendered_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=15000)
        content = await page.content()
        await browser.close()
        return content

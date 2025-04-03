# utils/scraper_pipeline.py

from utils.scraper import DynamicScraper
from utils.playwright_scraper import fetch_rendered_html
from bs4 import BeautifulSoup
from urllib.parse import urlparse

async def scrape_product_data(url: str) -> dict:
    scraper = DynamicScraper(url)
    
    # First try: BeautifulSoup
    result = scraper.scrape_with_bs()
    
    # Fallback: Playwright only if price is None or missing key fields
    if not result or not result.get("price"):
        print("[Fallback] Switching to Playwright...")
        try:
            html = await fetch_rendered_html(url)
            soup = BeautifulSoup(html, "html.parser")
            result = {
                "title": scraper._extract_title(soup),
                "price": scraper._extract_json_ld_price(soup) or scraper._extract_meta_price(soup),
                "image_url": scraper._extract_image(soup),
                "site_icon_url": scraper._extract_site_icon(soup),
                "site_name": urlparse(url).netloc.replace("www.", ""),
            }
        except Exception as e:
            print("[Fallback Failed]", e)
            result["price"] = None

    return result

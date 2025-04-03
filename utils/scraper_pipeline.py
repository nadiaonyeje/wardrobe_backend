# utils/scraper_pipeline.py

from utils.scraper import DynamicScraper

async def scrape_product_data(url: str) -> dict:
    scraper = DynamicScraper(url)
    
    # Only BeautifulSoup, no Playwright fallback
    result = scraper.scrape_with_bs()

    # Graceful fallback defaults if scraping failed
    return result or {
        "title": "Unknown Product",
        "price": None,
        "image_url": "",
        "site_icon_url": "",
        "site_name": ""
    }

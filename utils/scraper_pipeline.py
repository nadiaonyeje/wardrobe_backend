# utils/scraper_pipeline.py

from utils.scraper import DynamicScraper

async def scrape_data_pipeline(url: str) -> dict:
    """
    Attempt to scrape data from the given URL using BeautifulSoup first.
    If that fails or key data is missing, fallback to Playwright.

    :param url: Product page URL to scrape
    :return: Dictionary with scraped product data (title, price, image_url, site_icon_url, site_name)
    """
    scraper = DynamicScraper(url)

    # Try with BeautifulSoup first
    bs_result = scraper.scrape_with_bs()

    if bs_result:
        # Check if the result has essential data
        has_image = bs_result.get("image_url")
        has_price = bs_result.get("price")

        if has_image and has_price:
            return bs_result

    # Fallback to Playwright if BS4 result is missing key data
    print("[Scraper Pipeline] Falling back to Playwright...")
    playwright_result = await scraper.scrape_with_playwright()

    return playwright_result or {
        "title": "Unknown Product",
        "price": None,
        "image_url": "",
        "site_icon_url": "",
        "site_name": url.split("//")[-1].split("/")[0].replace("www.", "")
    }

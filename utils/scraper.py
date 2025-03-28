# utils/scraper.py
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright
from urllib.parse import urlparse

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

class DynamicScraper:
    def __init__(self, url):
        self.url = url
        self.headers = {"User-Agent": USER_AGENT}
        self.base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    def _format_price(self, raw_price: str) -> str:
        price = raw_price.replace("£", "").replace("$", "").replace("€", "").strip()
        if "£" in raw_price:
            return f"£{price}"
        elif "$" in raw_price:
            return f"${price}"
        elif "€" in raw_price:
            return f"€{price}"
        return price

    def _extract_price(self, soup):
        selectors = [
            {"name": "meta", "attrs": {"property": "product:price:amount"}},
            {"name": "meta", "attrs": {"property": "og:price:amount"}},
            {"name": "span", "class_": "price"},
            {"name": "div", "class_": "price"},
            {"name": "span", "class_": "current-price"},
            {"name": "span", "class_": "product-price"},
        ]
        for selector in selectors:
            tag = None
            if "attrs" in selector:
                tag = soup.find(selector["name"], attrs=selector["attrs"])
            elif "class_" in selector:
                tag = soup.find(selector["name"], class_=selector["class_"])
            if tag:
                raw_price = tag.get("content") or tag.text
                if raw_price and "menu" not in raw_price.lower():
                    return self._format_price(raw_price)
        return None

    def _extract_image(self, soup):
        og_image = soup.find("meta", property="og:image")
        return og_image["content"] if og_image and og_image.get("content") else ""

    def _extract_title(self, soup):
        title = soup.find("title")
        return title.text.strip().split("|")[0].strip() if title and title.text else "Unknown Product"

    def _extract_site_icon(self, soup):
        icon = soup.find("link", rel=lambda val: val and "icon" in val.lower())
        if icon and icon.get("href"):
            href = icon["href"]
            return href if href.startswith("http") else self.base_url + href
        return self._extract_image(soup)

    def scrape_with_bs(self):
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            return self._scrape_data(soup)
        except Exception:
            return None

    async def scrape_with_playwright(self):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
                page = await browser.new_page()
                await page.goto(self.url, timeout=30000)
                html = await page.content()
                await browser.close()
                soup = BeautifulSoup(html, "html.parser")
                return self._scrape_data(soup)
        except Exception as e:
            print("[Playwright Fallback Error]", e)
            return None

    def _scrape_data(self, soup):
        return {
            "title": self._extract_title(soup),
            "price": self._extract_price(soup),
            "image_url": self._extract_image(soup),
            "site_icon_url": self._extract_site_icon(soup)
        }

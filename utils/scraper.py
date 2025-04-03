# utils/scraper.py
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
from playwright.async_api import async_playwright

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

class DynamicScraper:
    def __init__(self, url):
        self.url = url
        self.headers = {"User-Agent": USER_AGENT}
        self.base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    def resolve_url(self, href: str) -> str:
        if not href:
            return ""
        if href.startswith("http"):
            return href
        if href.startswith("//"):
            return "https:" + href
        if href.startswith("/"):
            return self.base_url + href
        return f"{self.base_url}/{href}"

    def format_price(self, raw_price: str, currency: str = "") -> str:
        if not raw_price:
            return None

        price = raw_price.replace(",", "").strip()

        try:
            numeric_price = float(price)
            formatted_price = f"{numeric_price:.2f}"
            if formatted_price.endswith(".00"):
                formatted_price = str(int(numeric_price))
        except ValueError:
            return raw_price

        currency_symbols = {
            "GBP": "£", "USD": "$", "EUR": "€"
        }
        symbol = currency_symbols.get(currency.upper(), "")
        return f"{symbol}{formatted_price}"

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
                    currency_tag = soup.find("meta", attrs={"property": "product:price:currency"})
                    currency = currency_tag.get("content") if currency_tag else ""
                    return self.format_price(raw_price, currency)
        return None

    def _extract_image(self, soup):
        og_image = soup.find("meta", property="og:image")
        return self.resolve_url(og_image["content"]) if og_image and og_image.get("content") else ""

    def _extract_title(self, soup):
        title = soup.find("title")
        return title.text.strip().split("|")[0].strip() if title and title.text else "Unknown Product"

    def _extract_site_icon(self, soup):
        icon = soup.find("link", rel=lambda val: val and "icon" in val.lower())
        if icon and icon.get("href"):
            return self.resolve_url(icon["href"])
        return self._extract_image(soup)

    def _scrape_data(self, soup):
        return {
            "title": self._extract_title(soup),
            "price": self._extract_price(soup),
            "image_url": self._extract_image(soup),
            "site_icon_url": self._extract_site_icon(soup),
            "site_name": urlparse(self.url).netloc.replace("www.", "")
        }

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

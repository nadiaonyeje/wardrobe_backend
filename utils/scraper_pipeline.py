import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
CURRENCY_SYMBOLS = {
    "GBP": "£", "USD": "$", "EUR": "€", "CAD": "C$", "AUD": "A$", "JPY": "¥"
}

def resolve_url(href, base):
    if not href:
        return ""
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return "https:" + href
    return urljoin(base, href)

def clean_price(raw_price: str, currency: str = "") -> str:
    if not raw_price:
        return None

    price = raw_price.replace(",", "").replace("£", "").replace("$", "").replace("€", "").strip()
    try:
        value = float(price)
        formatted = f"{value:.2f}"
        if formatted.endswith(".00"):
            formatted = str(int(value))
    except ValueError:
        return raw_price

    symbol = CURRENCY_SYMBOLS.get(currency.upper(), "")
    return f"{symbol}{formatted}" if symbol else formatted

def extract_price(soup):
    selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
        {"name": "span", "class_": "current-price"},
        {"name": "span", "class_": "product-price"},
    ]
    for sel in selectors:
        tag = soup.find(sel["name"], attrs=sel.get("attrs")) if "attrs" in sel else \
              soup.find(sel["name"], class_=sel.get("class_"))
        if tag:
            raw = tag.get("content") or tag.text
            if raw and "menu" not in raw.lower():
                currency_tag = soup.find("meta", attrs={"property": "product:price:currency"})
                currency = currency_tag.get("content") if currency_tag else ""
                return clean_price(raw, currency)
    return None

def extract_title(soup):
    title = soup.find("title")
    return title.text.strip().split("|")[0].strip() if title else "Unknown Product"

def extract_site_icon(soup, base_url):
    icon = soup.find("link", rel=lambda val: val and "icon" in val.lower())
    if icon and icon.get("href"):
        return resolve_url(icon["href"], base_url)
    og = soup.find("meta", property="og:image")
    return resolve_url(og.get("content"), base_url) if og else ""

def extract_main_image(soup, base_url):
    og = soup.find("meta", property="og:image")
    return resolve_url(og.get("content"), base_url) if og else ""

def extract_all_images(soup, base_url):
    og_multiple = soup.find_all("meta", property="og:image")
    unique = {resolve_url(meta["content"], base_url) for meta in og_multiple if meta.get("content")}
    return list(unique) if unique else [extract_main_image(soup, base_url)]

def extract_site_name(parsed_url):
    return parsed_url.netloc.replace("www.", "")

async def scrape_product_data(url: str) -> dict:
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"[Scraper] Error fetching page: {e}")
        return {
            "title": "Unknown Product",
            "price": None,
            "image_url": "",
            "site_icon_url": "",
            "site_name": extract_site_name(parsed),
            "images": []
        }

    return {
        "title": extract_title(soup),
        "price": extract_price(soup),
        "image_url": extract_main_image(soup, base_url),
        "site_icon_url": extract_site_icon(soup, base_url),
        "site_name": extract_site_name(parsed),
        "images": extract_all_images(soup, base_url)
    }

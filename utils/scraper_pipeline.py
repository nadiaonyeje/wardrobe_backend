import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json

from utils.playwright_scraper import fetch_rendered_html  # Enable fallback

ENABLE_PLAYWRIGHT = True  # Toggle Playwright fallback here

def format_price(raw_price: str) -> str:
    if not raw_price:
        return None
    price = raw_price.replace(",", "").strip()
    for symbol in ["£", "$", "€"]:
        if symbol in raw_price:
            return f"{symbol}{price.replace(symbol, '').strip()}"
    return price

def extract_from_html(soup):
    title_tag = soup.find("title")
    title = title_tag.text.strip().split("|")[0] if title_tag else "Unknown Product"

    image_tag = soup.find("meta", property="og:image")
    image = image_tag.get("content") if image_tag else ""

    selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
        {"name": "span", "class_": "current-price"},
        {"name": "span", "class_": "product-price"},
    ]
    price = None
    for sel in selectors:
        tag = soup.find(sel["name"], attrs=sel.get("attrs")) if "attrs" in sel else \
              soup.find(sel["name"], class_=sel.get("class_"))
        if tag:
            raw = tag.get("content") or tag.text
            if raw and "menu" not in raw.lower():
                price = format_price(raw)
                break

    return {"title": title, "image": image, "price": price}

def extract_from_json_ld(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for entry in data:
                    if entry.get("@type") == "Product":
                        offer = entry.get("offers", {})
                        return {
                            "title": entry.get("name", ""),
                            "image": entry.get("image", ""),
                            "price": format_price(str(offer.get("price", "")))
                        }
            elif data.get("@type") == "Product":
                offer = data.get("offers", {})
                return {
                    "title": data.get("name", ""),
                    "image": data.get("image", ""),
                    "price": format_price(str(offer.get("price", "")))
                }
        except Exception:
            continue
    return {}

def extract_site_icon(soup, base_url):
    icon = soup.find("link", rel=lambda val: val and "icon" in val.lower())
    if icon and icon.get("href"):
        href = icon["href"]
        return href if href.startswith("http") else base_url + href if href.startswith("/") else f"{base_url}/{href}"
    return None

async def scrape_product_data(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    try:
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        soup = None

    result = extract_from_html(soup) if soup else {}

    if not result.get("price") or not result.get("image"):
        json_result = extract_from_json_ld(soup) if soup else {}
        result.update({k: v for k, v in json_result.items() if v})

    if (not result.get("price") or not result.get("image")) and ENABLE_PLAYWRIGHT:
        print("[Scraper] Falling back to Playwright...")
        rendered_html = await fetch_rendered_html(url)
        soup = BeautifulSoup(rendered_html, "html.parser")
        result = extract_from_html(soup)

    result["site_icon_url"] = extract_site_icon(soup, base_url) or ""
    result["site_name"] = parsed.netloc.replace("www.", "")
    return result

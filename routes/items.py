from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from database import items_collection
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
import requests

from playwright_scraper import fetch_rendered_html  # fallback method

router = APIRouter()

class ItemRequest(BaseModel):
    url: str
    users_id: str

def format_price(raw_price: str) -> str:
    price = raw_price.replace("£", "").replace("$", "").replace("€", "").strip()
    if "£" in raw_price:
        return f"£{price}"
    elif "$" in raw_price:
        return f"${price}"
    elif "€" in raw_price:
        return f"€{price}"
    return price

def extract_price(soup):
    selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
        {"name": "span", "class_": "current-price"},
        {"name": "span", "class_": "product-price"},
    ]
    for selector in selectors:
        tag = soup.find(selector["name"], attrs=selector.get("attrs")) if "attrs" in selector else \
              soup.find(selector["name"], class_=selector.get("class_"))
        if tag:
            raw_price = tag.get("content") or tag.text
            if raw_price and "menu" not in raw_price.lower():
                return format_price(raw_price)
    return None

def extract_site_icon(soup, base_url):
    icon = soup.find("link", rel=lambda val: val and "icon" in val.lower())
    if icon and icon.get("href"):
        href = icon["href"]
        return href if href.startswith("http") else base_url + href if href.startswith("/") else f"{base_url}/{href}"
    og_image = soup.find("meta", property="og:image")
    return og_image.get("content") if og_image else None

def extract_clean_title(soup):
    title_tag = soup.find("title")
    return title_tag.text.strip().split("|")[0].strip() if title_tag and title_tag.text else "Unknown Product"

async def parse_with_fallback(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception:
        soup = None

    # Fallback to Playwright if soup is None or missing key data
    def is_valid(s): return s and s.strip() and s != "Unknown Product"
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    if not soup or not soup.find("meta", property="og:image"):
        html = await fetch_rendered_html(url)
        soup = BeautifulSoup(html, "html.parser")

    title = extract_clean_title(soup)
    price = extract_price(soup)
    image_tag = soup.find("meta", property="og:image")
    image_url = image_tag.get("content") if image_tag else ""
    site_icon = extract_site_icon(soup, base_url)

    return {
        "title": title,
        "price": price or None,
        "image_url": image_url,
        "site_icon_url": site_icon or "",
        "site_name": parsed.netloc.replace("www.", ""),
    }

@router.post("/save-item/")
async def save_item(item: ItemRequest):
    if not item.users_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    url = item.url.strip()
    existing = await items_collection.find_one({"users_id": item.users_id, "source": url})
    if existing:
        raise HTTPException(status_code=409, detail="Item already saved.")

    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        scraped = await parse_with_fallback(url)

        item_data = {
            "users_id": item.users_id,
            "source": url,
            "created_at": datetime.utcnow(),
            **scraped
        }

        saved_item = await items_collection.insert_one(item_data)
        item_data["id"] = str(saved_item.inserted_id)
        return item_data

    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Item already saved.")

    except Exception as e:
        print(f"Error during item save: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scraping item: {str(e)}")

@router.get("/items/{users_id}")
async def get_items(users_id: str):
    cursor = items_collection.find({"users_id": users_id}).sort("created_at", -1)
    items = await cursor.to_list(100)
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    result = await items_collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 1:
        return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")

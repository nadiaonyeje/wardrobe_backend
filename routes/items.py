from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from database import items_collection
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from playwright_scraper import fetch_rendered_html

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
        {"name": "span", "class_": "product-price"},
        {"name": "div", "class_": "product-price"},
        {"name": "span", "class_": "product__price"},  # possible Boohoo fallback
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
                return format_price(raw_price.strip())

    return None

def extract_site_icon(soup, base_url):
    icon = soup.find("link", rel=lambda value: value and "icon" in value.lower())
    if icon and icon.get("href"):
        href = icon["href"]
        if href.startswith("http"):
            return href
        return base_url + href if href.startswith("/") else f"{base_url}/{href}"

    og_image = soup.find("meta", property="og:image")
    return og_image.get("content") if og_image and og_image.get("content") else None

def extract_clean_title(soup):
    title_tag = soup.find("title")
    if not title_tag or not title_tag.text.strip():
        return "Unknown Product"
    raw_title = title_tag.text.strip()
    return raw_title.split("|")[0].strip()

def extract_product_image(soup):
    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return og_image["content"]

    # Boohoo fallback or generic
    fallback_img = soup.find("img", class_="product-image")
    if fallback_img and fallback_img.get("src"):
        return fallback_img["src"]

    return ""

@router.post("/save-item/")
async def save_item(item: ItemRequest):
    if not item.users_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    url = item.url.strip()

    # Check for existing item
    existing = await items_collection.find_one({"users_id": item.users_id, "source": url})
    if existing:
        raise HTTPException(status_code=409, detail="Item already saved.")

    try:
        html = await fetch_rendered_html(url)
        soup = BeautifulSoup(html, "html.parser")

        title = extract_clean_title(soup)
        price = extract_price(soup)
        image_tag = soup.find("meta", property="og:image")
        image = image_tag.get("content") if image_tag else ""

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        site_icon = extract_site_icon(soup, base_url)

        item_data = {
            "users_id": item.users_id,
            "title": title,
            "price": price or None,
            "image_url": image,
            "source": url,
            "site_name": parsed.netloc.replace("www.", ""),
            "site_icon_url": site_icon or "",
            "created_at": datetime.utcnow(),
        }

        saved_item = await items_collection.insert_one(item_data)
        item_data["id"] = str(saved_item.inserted_id)
        return item_data

    except Exception as e:
        print(f"Error during item save: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

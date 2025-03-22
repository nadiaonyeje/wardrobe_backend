from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from database import items_collection
from datetime import datetime

router = APIRouter()

class ItemRequest(BaseModel):
    url: str
    users_id: str

# ✅ Try to clean up and format price
def format_price(raw_price: str) -> str:
    price = raw_price.replace("£", "").replace("$", "").replace("€", "").strip()

    # Auto-detect currency symbol if included in original string
    if "£" in raw_price:
        return f"£{price}"
    elif "$" in raw_price:
        return f"${price}"
    elif "€" in raw_price:
        return f"€{price}"
    else:
        return price

# ✅ Extract a valid price
def extract_price(soup):
    possible_price_selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
    ]

    for selector in possible_price_selectors:
        tag = None
        if "attrs" in selector:
            tag = soup.find(selector["name"], attrs=selector["attrs"])
        elif "class_" in selector:
            tag = soup.find(selector["name"], class_=selector["class_"])

        if tag:
            raw_price = tag.get("content") or tag.text
            if raw_price and "menu" not in raw_price.lower():
                return format_price(raw_price)

    return None  # ✅ No valid price found

# ✅ Try to grab a favicon or og:icon/logo
def extract_site_icon(soup, base_url):
    icon = soup.find("link", rel=lambda value: value and "icon" in value.lower())
    if icon and icon.get("href"):
        href = icon["href"]
        if href.startswith("http"):
            return href
        else:
            return base_url + href if href.startswith("/") else base_url + "/" + href

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        return og_image["content"]

    return None

@router.post("/save-item/")
async def save_item(item: ItemRequest):
    if not item.users_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    url = item.url.strip()
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("title").text.strip() if soup.find("title") else "Unknown Product"
        price = extract_price(soup)
        image = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else ""
        
        # ✅ Site base URL and icon
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
            "site_icon_url": site_icon or ""
            "created_at": datetime.utcnow()
        }

        saved_item = await items_collection.insert_one(item_data)
        item_data["id"] = str(saved_item.inserted_id)

        return item_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/{users_id}")
async def get_items(users_id: str):
    items = await items_collection.find({"users_id": users_id}).to_list(100)
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

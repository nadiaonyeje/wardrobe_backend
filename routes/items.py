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

def format_price(raw_price: str) -> str:
    price = raw_price.replace("£", "").replace("$", "").replace("€", "").strip()
    if "£" in raw_price:
        return f"£{price}"
    elif "$" in raw_price:
        return f"${price}"
    elif "€" in raw_price:
        return f"€{price}"
    else:
        return price

def extract_price(soup):
    selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
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
                return format_price(raw_price)
    return None

def extract_title(soup):
    raw_title = soup.find("title").text.strip() if soup.find("title") else "Unknown Product"
    clean_title = raw_title.split("|")[0].split("–")[0].strip()  # remove site name
    return clean_title if clean_title else "Unnamed Product"

def extract_site_icon(soup, base_url):
    icon = soup.find("link", rel=lambda value: value and "icon" in value.lower())
    if icon and icon.get("href"):
        href = icon["href"]
        return href if href.startswith("http") else base_url + href if href.startswith("/") else base_url + "/" + href

    og_image = soup.find("meta", property="og:image")
    return og_image["content"] if og_image and og_image.get("content") else None

@router.post("/save-item/")
async def save_item(item: ItemRequest):
    if not item.users_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    url = item.url.strip()

    # Check if item already exists
    existing = await items_collection.find_one({"users_id": item.users_id, "source": url})
    if existing:
        raise HTTPException(status_code=409, detail="Item already saved.")

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("title").text.strip() if soup.find("title") else "Unknown Product"
        price = extract_price(soup)
        image = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else ""

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
        raise HTTPException(status_code=500, detail=str(e))

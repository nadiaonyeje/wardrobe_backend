from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from database import items_collection

router = APIRouter()

class ItemRequest(BaseModel):
    url: str
    users_id: str  # ✅ Ensure items are saved per user

# ✅ Extract price from common tag types
def extract_price(soup):
    possible_price_selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
    ]

    for selector in possible_price_selectors:
        if "attrs" in selector:
            tag = soup.find(selector["name"], attrs=selector["attrs"])
        elif "class_" in selector:
            tag = soup.find(selector["name"], class_=selector["class_"])
        else:
            continue

        # ✅ Handle <meta content="">
        if tag and tag.get("content"):
            price = tag["content"].strip()
        elif tag and tag.text:
            price = tag.text.strip()
        else:
            continue

        # ✅ Skip garbage or menu text
        if price and "menu" not in price.lower():
            return price

    return None  # ❌ No valid price found

# ✅ Save item with price/image/title
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
        price = extract_price(soup) or "Unknown Price"
        image = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else ""

        item_data = {
            "users_id": item.users_id,
            "title": title,
            "price": price,
            "image_url": image,
            "source": url
        }

        saved_item = await items_collection.insert_one(item_data)
        item_data["id"] = str(saved_item.inserted_id)

        return item_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Fetch saved items by user
@router.get("/items/{users_id}")
async def get_items(users_id: str):
    items = await items_collection.find({"users_id": users_id}).to_list(100)
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from database import items_collection

router = APIRouter()

# ✅ Model for receiving pasted link
class ItemRequest(BaseModel):
    url: str
    user_id: str  # ✅ Ensure the item is saved per user

# ✅ Extract Price Function (More Reliable)
def extract_price(soup):
    price_selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
    ]

    for selector in price_selectors:
        tag = soup.find(selector["name"], selector.get("attrs", {}))
        if tag and tag.get("content"):  # Check meta tags
            return tag["content"]
        elif tag and tag.text.strip():  # Check normal HTML elements
            return tag.text.strip()

    return "Unknown Price"

# ✅ Save item from a pasted link
@router.post("/save-item/")
async def save_item(item: ItemRequest):
    url = item.url

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ Extract product details
        title = soup.find("title").text if soup.find("title") else "Unknown Product"
        price = extract_price(soup)
        image = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else ""

        # ✅ Check if the item is already saved for this user
        existing_item = await items_collection.find_one({"source": url, "user_id": item.user_id})
        if existing_item:
            raise HTTPException(status_code=400, detail="Item already saved.")

        # ✅ Save item to database with user_id
        item_data = {
            "user_id": item.user_id,
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

# ✅ Get saved items for a user
@router.get("/items/{user_id}")
async def get_items(user_id: str):
    items = await items_collection.find({"user_id": user_id}).to_list(100)
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

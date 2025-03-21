from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from database import items_collection  # ✅ Using your existing collection

router = APIRouter()

# ✅ Model for receiving the pasted link
class ItemRequest(BaseModel):
    url: str
    user_id: str  # ✅ Ensure the item is saved per user

# ✅ Function to extract price more reliably
def extract_price(soup):
    possible_price_selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
    ]

    for selector in possible_price_selectors:
        tag = soup.find(selector["name"], selector.get("attrs", {}))
        if tag and tag.get("content"):
            return tag["content"]
        elif tag and tag.text.strip():
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
        price = extract_price(soup)  # ✅ More reliable price extraction
        image = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else ""

        item_data = {
            "user_id": item.user_id,  # ✅ Store user_id
            "title": title,
            "price": price,
            "image_url": image,
            "source": url
        }

        print("✅ Saving item to DB:", item_data)  # DEBUGGING
        saved_item = await items_collection.insert_one(item_data)
        print("✅ Inserted ID:", saved_item.inserted_id)  # DEBUGGING

        item_data["id"] = str(saved_item.inserted_id)
        return item_data
    except Exception as e:
        print("❌ Error saving item:", str(e))  # DEBUGGING
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Get items filtered by user_id
@router.get("/items/{user_id}")
async def get_items(user_id: str):
    print(f"🔎 Fetching items for user: {user_id}")  # DEBUGGING
    items = await items_collection.find({"user_id": user_id}).to_list(100)
    print("📦 Retrieved items:", items)  # DEBUGGING
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from database import items_collection  # ✅ Using your existing collection

router = APIRouter()

# ✅ Model for receiving the pasted link
class ItemRequest(BaseModel):
    url: str
    "users_id" = item.users_id  # ✅ Ensure it matches what’s returned in login

# ✅ Function to extract price more reliably
def extract_price(soup):
    """Extracts price by checking multiple possible selectors."""
    possible_price_selectors = [
        {"name": "meta", "attrs": {"property": "product:price:amount"}},
        {"name": "meta", "attrs": {"property": "og:price:amount"}},
        {"name": "span", "class_": "price"},
        {"name": "div", "class_": "price"},
    ]

    for selector in possible_price_selectors:
        tag = soup.find(selector["name"], selector.get("attrs", {}))
        if tag and tag.get("content"):  # Check meta tags
            return tag["content"]
        elif tag and tag.text.strip():  # Check regular tags
            return tag.text.strip()

    return "Unknown Price"

# ✅ Save item from a pasted link
@router.post("/save-item/")
async def save_item(item: ItemRequest):
    if not item.users_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    url = item.url.strip()
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ Extract product details
        title = soup.find("title").text.strip() if soup.find("title") else "Unknown Product"
        price = extract_price(soup)  # ✅ More reliable price extraction
        image = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else ""

        # ✅ Save item to database with user_id
        item_data = {
            "users_id": item.users_id,  # ✅ Store user_id for per-user items
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

# ✅ Get items filtered by user_id
@router.get("/items/{users_id}")
async def get_items(users_id: str):
    items = await items_collection.find({"users_id": users_id}).to_list(100)
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

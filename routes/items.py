from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from database import items_collection  # ✅ Using your existing collection

router = APIRouter()

# ✅ Model for receiving the pasted link
class ItemRequest(BaseModel):
    url: str

# ✅ Save item from a pasted link
@router.post("/save-item/")
async def save_item(item: ItemRequest):
    url = item.url

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ Extract product details (Modify based on the website's structure)
        title = soup.find("title").text if soup.find("title") else "Unknown Product"
        price = soup.find(class_="price").text if soup.find(class_="price") else "Unknown Price"
        image = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else ""

        # ✅ Save item to database
        item_data = {
            "title": title,
            "price": price,
            "image_url": image,
            "source": url  # Storing the original source link
        }
        saved_item = await items_collection.insert_one(item_data)
        item_data["id"] = str(saved_item.inserted_id)

        return item_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Get all saved items
@router.get("/items/")
async def get_items():
    items = await items_collection.find().to_list(100)
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from database import items_collection
from utils import get_current_user

router = APIRouter()

class ItemRequest(BaseModel):
    url: str

@router.post("/save-item/")
async def save_item(item: ItemRequest, user: dict = Depends(get_current_user)):
    url = item.url
    user_id = user["id"]

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("title").text if soup.find("title") else "Unknown Product"
        price = soup.find(class_="price").text if soup.find(class_="price") else "Unknown Price"
        image = soup.find("meta", property="og:image")["content"] if soup.find("meta", property="og:image") else ""

        # Prevent duplicate entries for the same user
        existing_item = await items_collection.find_one({"source": url, "user_id": user_id})
        if existing_item:
            return {**existing_item, "id": str(existing_item["_id"])}

        item_data = {
            "title": title,
            "price": price,
            "image_url": image,
            "source": url,
            "user_id": user_id,  # Associate with user
        }

        saved_item = await items_collection.insert_one(item_data)
        item_data["id"] = str(saved_item.inserted_id)

        return item_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/items/")
async def get_items(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    items = await items_collection.find({"user_id": user_id}).to_list(100)
    
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    
    return items

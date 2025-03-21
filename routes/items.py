from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from database import items_collection  # ✅ Using your existing collection
from datetime import datetime
from fastapi.responses import JSONResponse

router = APIRouter()

# ✅ Model for receiving the pasted link
class ItemRequest(BaseModel):
    url: str

# ✅ Save item from a pasted link
@router.post("/save-item/")
async def save_item(item: ItemRequest):
    url = item.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")

    try:
        # ✅ Check if item already exists in the database
        existing_item = await items_collection.find_one({"source": url})
        if existing_item:
            return JSONResponse(status_code=200, content={"message": "Item already exists.", "item": existing_item})

        # ✅ Fetch webpage data
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch URL")

        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ Extract product details (Modify based on the website's structure)
        title = soup.find("title").text.strip() if soup.find("title") else "Unknown Product"
        price = soup.find(class_="price").text.strip() if soup.find(class_="price") else "Unknown Price"
        image = soup.find("meta", property="og:image")
        image_url = image["content"] if image and "content" in image.attrs else ""

        # ✅ Prepare item data
        item_data = {
            "title": title,
            "price": price,
            "image_url": image_url,
            "source": url,  # Storing the original source link
            "created_at": datetime.utcnow()
        }

        # ✅ Save item to the database
        saved_item = await items_collection.insert_one(item_data)
        item_data["_id"] = str(saved_item.inserted_id)  # Convert ObjectId to string

        return JSONResponse(status_code=201, content=item_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving item: {str(e)}")


# ✅ Get all saved items
@router.get("/items/")
async def get_items():
    try:
        items = await items_collection.find().to_list(100)
        for item in items:
            item["_id"] = str(item["_id"])  # Convert ObjectId to string
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching items: {str(e)}")

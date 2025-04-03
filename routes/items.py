from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import items_collection
from datetime import datetime
from bson import ObjectId
from utils.scraper_pipeline import scrape_product_data  # <- Final scraper pipeline

router = APIRouter()

class ItemRequest(BaseModel):
    url: str
    users_id: str

@router.post("/save-item/")
async def save_item(item: ItemRequest):
    if not item.users_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    url = item.url.strip()
    existing = await items_collection.find_one({
        "users_id": item.users_id,
        "source": url
    })
    if existing:
        raise HTTPException(status_code=409, detail="Item already saved.")

    try:
        # Scrape using final scraper pipeline
        scraped = await scrape_product_data(url)

        item_data = {
            "users_id": item.users_id,
            "source": url,
            "created_at": datetime.utcnow(),
            **scraped  # Includes: title, price, image_url(s), icon, site_name
        }

        saved_item = await items_collection.insert_one(item_data)
        item_data["id"] = str(saved_item.inserted_id)
        item_data.pop("_id", None)  # Remove MongoDB's ObjectId if it gets included

        return item_data

    except Exception as e:
        print(f"Error during item save: {e}")
        raise HTTPException(status_code=500, detail=f"Error scraping item: {e}")

@router.get("/items/{users_id}")
async def get_items(users_id: str):
    cursor = items_collection.find({"users_id": users_id}).sort("created_at", -1)
    items = await cursor.to_list(length=100)
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

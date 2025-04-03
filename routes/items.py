from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import items_collection
from datetime import datetime
from bson import ObjectId
from utils.scraper_pipeline import scrape_product_data  # Final scraper

router = APIRouter()

# Request models
class ItemRequest(BaseModel):
    url: str
    users_id: str

class MetadataRequest(BaseModel):
    item_id: str
    ownership: str
    category: str
    subcategory: str

# Save item without ownership info
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
        scraped = await scrape_product_data(url)
        item_data = {
            "users_id": item.users_id,
            "source": url,
            "created_at": datetime.utcnow(),
            **scraped
        }
        saved_item = await items_collection.insert_one(item_data)
        item_data["id"] = str(saved_item.inserted_id)
        item_data.pop("_id", None)
        return item_data

    except Exception as e:
        print(f"[Save Error] {e}")
        raise HTTPException(status_code=500, detail=f"Error scraping item: {e}")

# Assign ownership/category/subcategory metadata after saving item
@router.post("/items/assign-metadata")
async def assign_metadata(meta: MetadataRequest):
    try:
        result = await items_collection.update_one(
            {"_id": ObjectId(meta.item_id)},
            {
                "$set": {
                    "ownership": meta.ownership,
                    "category": meta.category,
                    "subcategory": meta.subcategory
                }
            }
        )
        if result.modified_count == 1:
            return {"message": "Metadata saved"}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        print(f"[Metadata Error] {e}")
        raise HTTPException(status_code=500, detail="Failed to assign metadata")

# Get items by ownership
@router.get("/items/{users_id}/ownership/{ownership}")
async def get_items_by_ownership(users_id: str, ownership: str):
    cursor = items_collection.find({
        "users_id": users_id,
        "ownership": ownership.lower()
    }).sort("created_at", -1)
    
    items = await cursor.to_list(length=100)
    for item in items:
        item["id"] = str(item["_id"])
        del item["_id"]
    return items

# Delete item
@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    result = await items_collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 1:
        return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")

from fastapi import APIRouter, HTTPException
from database import items_collection

router = APIRouter()

@router.post("/items/")
async def add_item(name: str, image_url: str, price: str, link: str):
    new_item = {"name": name, "image_url": image_url, "price": price, "link": link}
    result = await items_collection.insert_one(new_item)
    return {"message": "Item added", "id": str(result.inserted_id)}

@router.get("/items/")
async def get_items():
    items = await items_collection.find().to_list(length=100)
    return items

from fastapi import APIRouter, HTTPException
from database import items_collection
from models import WardrobeItemSchema

router = APIRouter()

@router.post("/items/")
async def add_item(item: WardrobeItemSchema):
    result = await items_collection.insert_one(item.dict())
    return {"message": "Item added", "id": str(result.inserted_id)}

@router.get("/items/")
async def get_items():
    items = await items_collection.find().to_list(length=100)
    return items

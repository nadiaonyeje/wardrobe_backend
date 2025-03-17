from fastapi import APIRouter, HTTPException
from database import outfits_collection
from models import OutfitSchema

router = APIRouter()

@router.post("/outfits/")
async def create_outfit(outfit: OutfitSchema):
    result = await outfits_collection.insert_one(outfit.dict())
    return {"message": "Outfit created", "id": str(result.inserted_id)}

@router.get("/outfits/")
async def get_outfits():
    outfits = await outfits_collection.find().to_list(length=100)
    return outfits

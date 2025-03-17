from fastapi import APIRouter, HTTPException
from database import categories_collection, subcategories_collection
from models import CategorySchema, SubcategorySchema

router = APIRouter()

@router.post("/categories/")
async def create_category(category: CategorySchema):
    result = await categories_collection.insert_one(category.dict())
    return {"message": "Category created", "id": str(result.inserted_id)}

@router.post("/subcategories/")
async def create_subcategory(subcategory: SubcategorySchema):
    result = await subcategories_collection.insert_one(subcategory.dict())
    return {"message": "Subcategory created", "id": str(result.inserted_id)}

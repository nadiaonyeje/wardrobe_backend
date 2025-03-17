from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import Category, Subcategory
from database import get_db

router = APIRouter()

@router.post("/categories/")
def create_category(name: str, db: Session = Depends(get_db)):
    category = Category(name=name)
    db.add(category)
    db.commit()
    return {"message": "Category created"}

@router.post("/subcategories/")
def create_subcategory(name: str, category_id: int, db: Session = Depends(get_db)):
    subcategory = Subcategory(name=name, category_id=category_id)
    db.add(subcategory)
    db.commit()
    return {"message": "Subcategory created"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import WardrobeItem
from database import get_db

router = APIRouter()

@router.post("/items/")
def add_item(name: str, image_url: str, price: str, link: str, db: Session = Depends(get_db)):
    item = WardrobeItem(name=name, image_url=image_url, price=price, link=link)
    db.add(item)
    db.commit()
    return {"message": "Item added successfully"}

@router.get("/items/")
def get_items(db: Session = Depends(get_db)):
    return db.query(WardrobeItem).all()

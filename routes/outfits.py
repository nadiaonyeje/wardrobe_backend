from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from models import Outfit
from database import get_db
import json

router = APIRouter()

@router.post("/outfits/")
def create_outfit(name: str, items: list, db: Session = Depends(get_db)):
    outfit = Outfit(name=name, items=json.dumps(items))
    db.add(outfit)
    db.commit()
    return {"message": "Outfit created"}

@router.get("/outfits/")
def get_outfits(db: Session = Depends(get_db)):
    return db.query(Outfit).all()

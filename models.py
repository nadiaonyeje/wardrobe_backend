# models.py - MongoDB Collections (No SQLAlchemy Needed)

# Since MongoDB is schema-less, we do not need SQLAlchemy models.
# Instead, collections are managed in database.py using Motor (MongoDB async driver).

# Example: Defining JSON schemas for data validation (optional)
from pydantic import BaseModel
from typing import List

class UserSchema(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

class WardrobeItemSchema(BaseModel):
    name: str
    image_url: str
    price: str
    link: str

class CategorySchema(BaseModel):
    name: str

class SubcategorySchema(BaseModel):
    name: str
    category_id: str  # Store category ID as string

class OutfitSchema(BaseModel):
    name: str
    items: List[str]  # List of item IDs

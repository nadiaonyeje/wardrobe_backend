# models.py - Database Models
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    image_url = Column(String)
    price = Column(String)
    link = Column(String)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)

class Subcategory(Base):
    __tablename__ = "subcategories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category")

class Outfit(Base):
    __tablename__ = "outfits"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    items = Column(String)  # Stores item IDs as a JSON string

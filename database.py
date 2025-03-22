from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from database import items_collection

load_dotenv()

DATABASE_URL = os.getenv("MONGO_URI")  # Make sure this is set in your .env file

client = AsyncIOMotorClient(DATABASE_URL)
db = client.wardrobe_db  # Change "wardrobe_db" to whatever your database name is

# Collections
users_collection = db["users"]
items_collection = db["wardrobe_items"]
categories_collection = db["categories"]
subcategories_collection = db["subcategories"]  
outfits_collection = db["outfits"]

# Create a compound index on (users_id, source) to enforce uniqueness
items_collection.create_index(
    [("users_id", 1), ("source", 1)],
    unique=True
)

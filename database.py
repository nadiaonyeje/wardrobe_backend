from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
DATABASE_URL = os.getenv("MONGO_URI")  # Make sure MONGO_URI is set in your .env

client = AsyncIOMotorClient(DATABASE_URL)
db = client.wardrobe_db  # Change this if your DB has a different name

# Collections
users_collection = db["users"]
items_collection = db["wardrobe_items"]
categories_collection = db["categories"]
subcategories_collection = db["subcategories"]
outfits_collection = db["outfits"]

# Compound index for preventing duplicate item saves
# This will only run if the index doesn't already exist
async def create_indexes():
    await items_collection.create_index(
        [("users_id", 1), ("source", 1)],
        unique=True
    )

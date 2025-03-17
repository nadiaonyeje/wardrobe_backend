from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("MONGODB_URL")  # Make sure this is set in your .env file

client = AsyncIOMotorClient(DATABASE_URL)
db = client.wardrobe_db  # Change "wardrobe_db" to whatever your database name is

# Collections
users_collection = db["users"]
items_collection = db["wardrobe_items"]
categories_collection = db["categories"]
outfits_collection = db["outfits"]

from fastapi import APIRouter, HTTPException
from models import User
from database import users_collection
from bson import ObjectId

router = APIRouter()

@router.post("/social-login")
async def social_login(data: dict):
    email = data.get("email")
    username = data.get("username")
    first_name = data.get("first_name", "User")
    last_name = data.get("last_name", "")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required for social login")

    existing_user = await users_collection.find_one({"email": email})

    if existing_user:
        user_id = str(existing_user["_id"])
        print("✅ Found existing user:", user_id)
    else:
        new_user = {
            "email": email,
            "username": username or email,
            "first_name": first_name,
            "last_name": last_name,
            "password": "",  # no password for social login
        }
        result = await users_collection.insert_one(new_user)
        user_id = str(result.inserted_id)
        print("✅ Created new social user:", user_id)

    return {
        "user_id": user_id,
        "username": username or email,
        "first_name": first_name,
        "last_name": last_name,
    }

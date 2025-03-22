from fastapi import APIRouter, HTTPException
from database import users_collection
from bson import ObjectId

router = APIRouter()

# ✅ EMAIL/PASSWORD LOGIN
@router.post("/token/")
async def token_login(data: dict):
    email_or_username = data.get("email_or_username")
    password = data.get("password")

    if not email_or_username or not password:
        raise HTTPException(status_code=400, detail="Missing credentials")

    query = {
        "$or": [
            {"email": email_or_username},
            {"username": email_or_username}
        ]
    }

    user = await users_collection.find_one(query)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["password"] != password:
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {
        "message": "Login successful",
        "user_id": str(user["_id"]),
        "email": user.get("email"),
        "username": user.get("username"),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", "")
    }

# ✅ SOCIAL LOGIN (GOOGLE / APPLE)
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
        print("✅ Found existing social user:", user_id)
    else:
        new_user = {
            "email": email,
            "username": username or email,
            "first_name": first_name,
            "last_name": last_name,
            "password": "",  # No password required for social login
        }
        result = await users_collection.insert_one(new_user)
        user_id = str(result.inserted_id)
        print("✅ Created new social user:", user_id)

    return {
        "user_id": user_id,
        "username": username or email,
        "first_name": first_name,
        "last_name": last_name
    }

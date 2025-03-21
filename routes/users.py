from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import os
from pydantic import BaseModel, EmailStr
from utils import create_access_token

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ MongoDB Setup
client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client.wardrobe_db
users_collection = db.users

# ✅ Request model for login/register
class UserLoginRequest(BaseModel):
    email_or_username: str
    password: str
    first_name: str = "New"
    last_name: str = "User"
    username: str = None

# ✅ Login/Register in one endpoint (Fixed Case Sensitivity)
@router.post("/token/")
async def login_or_register(user_data: UserLoginRequest):
    email_or_username_lower = user_data.email_or_username.lower()

    # ✅ Check if user exists (Case-insensitive)
    existing_user = await users_collection.find_one({
        "$or": [
            {"email": email_or_username_lower},
            {"username": email_or_username_lower}
        ]
    })

    if existing_user:
        # ✅ Verify password
        if not pwd_context.verify(user_data.password, existing_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # ✅ Generate JWT token
        access_token = create_access_token(data={"sub": existing_user["email"], "users_id": str(existing_user["_id"])})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "users_id": str(existing_user["_id"]),
            "first_name": existing_user.get("first_name", ""),
            "last_name": existing_user.get("last_name", ""),
            "username": existing_user.get("username", ""),
            "message": "Login successful"
        }
    
    # ✅ Ensure username & email are unique (case-insensitive)
    if user_data.username:
        username_lower = user_data.username.lower()
        existing_username = await users_collection.find_one({"username": username_lower})
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken.")

    existing_email = await users_collection.find_one({"email": email_or_username_lower})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already in use.")

    # ✅ Register New User
    hashed_password = pwd_context.hash(user_data.password)
    new_user = {
        "email": email_or_username_lower,
        "username": (user_data.username or email_or_username_lower.split("@")[0]).lower(),
        "password": hashed_password,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "created_at": datetime.utcnow()
    }
    inserted_user = await users_collection.insert_one(new_user)

    # ✅ Generate JWT token
    access_token = create_access_token(data={"sub": email_or_username_lower, "users_id": str(inserted_user.inserted_id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "users_id": str(inserted_user.inserted_id),
        "first_name": new_user["first_name"],
        "last_name": new_user["last_name"],
        "username": new_user["username"],
        "message": "User registered successfully"
    }

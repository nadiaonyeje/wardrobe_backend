from fastapi import APIRouter, Depends, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
from pydantic import BaseModel
from typing import Optional
from utils import create_access_token

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client.wardrobe_db
users_collection = db.users

class UserLoginRequest(BaseModel):
    email_or_username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None

@router.post("/token/")
async def login_or_register(user_data: UserLoginRequest):
    email_or_username_lower = user_data.email_or_username.lower()

    existing_user = await users_collection.find_one({
        "$or": [{"email": email_or_username_lower}, {"username": email_or_username_lower}]
    })

    if existing_user:
        if not pwd_context.verify(user_data.password, existing_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(data={"sub": existing_user["email"]})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "users_id": str(existing_user["_id"]),  # ✅ Returning users_id
            "first_name": existing_user.get("first_name", ""),
            "last_name": existing_user.get("last_name", ""),
            "username": existing_user.get("username", ""),
            "message": "Login successful"
        }

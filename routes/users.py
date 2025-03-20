from fastapi import APIRouter, Depends, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from pydantic import BaseModel
from typing import Optional
from utils import create_access_token  # Ensure you have a JWT token generator

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ✅ MongoDB Setup
client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = client.wardrobe_db
users_collection = db.users

# ✅ Request model for login/register
class UserLoginRequest(BaseModel):
    email_or_username: str
    password: str
    first_name: Optional[str] = None  # Optional for login
    last_name: Optional[str] = None   # Optional for login
    username: Optional[str] = None    # Optional for login

# ✅ Login/Register in one endpoint
@router.post("/token/")
async def login_or_register(user_data: UserLoginRequest):
    # ✅ Check if input is an email or username
    query = {"$or": [{"email": user_data.email_or_username}, {"username": user_data.email_or_username}]}
    existing_user = await users_collection.find_one(query)

    if existing_user:
        # ✅ User exists, verify password
        if not pwd_context.verify(user_data.password, existing_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # ✅ Generate JWT token
        access_token = create_access_token(data={"sub": existing_user["email"]})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "first_name": existing_user.get("first_name", ""),
            "last_name": existing_user.get("last_name", ""),
            "username": existing_user.get("username", ""),
            "message": "Login successful"
        }
    else:
        # ✅ Ensure username is unique (only check if username is provided)
        if user_data.username:
            existing_username = await users_collection.find_one({"username": user_data.username})
            if existing_username:
                raise HTTPException(status_code=400, detail="Username already taken. Please choose another.")

        # ✅ New user, register them
        hashed_password = pwd_context.hash(user_data.password)
        new_user = {
            "email": user_data.email_or_username,  # Treat as email for new users
            "username": user_data.username or user_data.email_or_username.split("@")[0],  # Default to email prefix
            "password": hashed_password,
            "first_name": user_data.first_name or "New",
            "last_name": user_data.last_name or "User",
            "created_at": datetime.utcnow()
        }
        await users_collection.insert_one(new_user)

        # ✅ Generate JWT token
        access_token = create_access_token(data={"sub": user_data.email_or_username})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "first_name": new_user["first_name"],
            "last_name": new_user["last_name"],
            "username": new_user["username"],
            "message": "User registered successfully"
        }

# ✅ Google OAuth Login
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/auth/google")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, "https://wardrobe-backend-o0fr.onrender.com/auth/google/callback")

@router.get("/auth/google/callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo", {})

    if not user_info.get("email"):
        raise HTTPException(status_code=400, detail="Google authentication failed")

    user = await users_collection.find_one({"email": user_info["email"]})
    
    if not user:
        user = {
            "email": user_info["email"],
            "username": user_info["email"].split("@")[0],  # Default username
            "first_name": user_info.get("given_name", "New"),
            "last_name": user_info.get("family_name", "User"),
            "created_at": datetime.utcnow()
        }
        await users_collection.insert_one(user)

    access_token = create_access_token(data={"sub": user["email"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "username": user["username"],
    }

# ✅ Apple Login
@router.post("/auth/apple")
async def apple_login(identity_token: str):
    try:
        decoded_token = jwt.decode(identity_token, "YOUR_APPLE_PRIVATE_KEY", algorithms=["RS256"])
        email = decoded_token.get("email")
        first_name = decoded_token.get("given_name", "New")  # Apple sometimes includes this
        last_name = decoded_token.get("family_name", "User")

        if not email:
            raise HTTPException(status_code=400, detail="Apple authentication failed")

        user = await users_collection.find_one({"email": email})
        if not user:
            user = {
                "email": email,
                "username": email.split("@")[0],  # Default username
                "first_name": first_name,
                "last_name": last_name,
                "created_at": datetime.utcnow()
            }
            await users_collection.insert_one(user)

        access_token = create_access_token(data={"sub": email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "first_name": first_name,
            "last_name": last_name,
            "username": user["username"],
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

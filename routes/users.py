from fastapi import APIRouter, Depends, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from database import users_collection
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ Register a New User (Signup)
@router.post("/register/")
async def register(email: str, password: str, first_name: str, last_name: str):
    existing_user = await users_collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(password)
    new_user = {
        "email": email,
        "password": hashed_password,
        "first_name": first_name,
        "last_name": last_name,
    }
    await users_collection.insert_one(new_user)
    return {"message": "User registered successfully"}

# ✅ Login User with Email & Password
@router.post("/token/")
async def login(email: str, password: str):
    user = await users_collection.find_one({"email": email})
    if not user or not pwd_context.verify(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user["email"]})
    
    # ✅ Include first_name and last_name if available
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
    }

# ✅ Google OAuth Login
oauth = OAuth()
oauth.register(
    name='google',
    client_id="GOOGLE_CLIENT_ID",
    client_secret="GOOGLE_CLIENT_SECRET",
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
    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(status_code=400, detail="Google authentication failed")

    user = await users_collection.find_one({"email": user_info["email"]})
    
    if not user:
        user = {
            "email": user_info["email"],
            "first_name": user_info.get("given_name", ""),
            "last_name": user_info.get("family_name", ""),
        }
        await users_collection.insert_one(user)

    access_token = create_access_token(data={"sub": user["email"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "first_name": user["first_name"],
        "last_name": user["last_name"],
    }

# ✅ Apple Login
@router.post("/auth/apple")
async def apple_login(identity_token: str):
    try:
        decoded_token = jwt.decode(identity_token, "YOUR_APPLE_PRIVATE_KEY", algorithms=["RS256"])
        email = decoded_token.get("email")
        first_name = decoded_token.get("given_name", "")  # Apple sometimes includes this
        last_name = decoded_token.get("family_name", "")

        if not email:
            raise HTTPException(status_code=400, detail="Apple authentication failed")

        user = await users_collection.find_one({"email": email})
        if not user:
            user = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            }
            await users_collection.insert_one(user)

        access_token = create_access_token(data={"sub": email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "first_name": first_name,
            "last_name": last_name,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

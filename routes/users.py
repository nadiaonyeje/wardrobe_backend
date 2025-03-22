from fastapi import APIRouter, HTTPException
from database import users_collection
from bson import ObjectId
import bcrypt

router = APIRouter()

# Hash & Verify Helpers
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

# ✅ REGISTER USER
@router.post("/register/")
async def register_user(data: dict):
    email = data.get("email", "").lower().strip()
    username = data.get("username", "").lower().strip()
    password = data.get("password", "")
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")

    if not email or not username or not password:
        raise HTTPException(status_code=400, detail="Email, username, and password are required.")

    # Check for duplicates
    if await users_collection.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}}):
        raise HTTPException(status_code=409, detail="Email already in use.")

    if await users_collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}}):
        raise HTTPException(status_code=409, detail="Username already in use.")

    hashed_pw = hash_password(password)

    new_user = {
        "email": email,
        "username": username,
        "password": hashed_pw,
        "first_name": first_name,
        "last_name": last_name,
    }

    result = await users_collection.insert_one(new_user)
    user_id = str(result.inserted_id)

    return {
        "message": "Registration successful",
        "user_id": user_id,
        "email": email,
        "username": username,
        "first_name": first_name,
        "last_name": last_name
    }

# ✅ LOGIN
@router.post("/token/")
async def token_login(data: dict):
    email_or_username = data.get("email_or_username")
    password = data.get("password")

    if not email_or_username or not password:
        raise HTTPException(status_code=400, detail="Missing credentials")

    query = {
        "$or": [
            {"email": {"$regex": f"^{email_or_username}$", "$options": "i"}},
            {"username": {"$regex": f"^{email_or_username}$", "$options": "i"}}
        ]
    }

    user = await users_collection.find_one(query)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {
        "message": "Login successful",
        "user_id": str(user["_id"]),
        "email": user.get("email"),
        "username": user.get("username"),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", "")
    }

# ✅ SOCIAL LOGIN
@router.post("/social-login")
async def social_login(data: dict):
    email = data.get("email")
    username = data.get("username")
    first_name = data.get("first_name", "User")
    last_name = data.get("last_name", "")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required for social login")

    email = email.lower()
    username = (username or email).lower()

    existing_user = await users_collection.find_one({"email": email})

    if existing_user:
        user_id = str(existing_user["_id"])
    else:
        # Ensure username is unique
        if await users_collection.find_one({"username": username}):
            username += "_" + str(ObjectId())[-4:]

        new_user = {
            "email": email,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "password": "",  # No password for social login
        }
        result = await users_collection.insert_one(new_user)
        user_id = str(result.inserted_id)

    return {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name
    }

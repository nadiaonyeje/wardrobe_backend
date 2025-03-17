from fastapi import APIRouter, HTTPException
from database import users_collection
from models import UserSchema
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register/")
async def register(user: UserSchema):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = {"email": user.email, "password": hashed_password}
    result = await users_collection.insert_one(new_user)
    return {"message": "User registered", "id": str(result.inserted_id)}

@router.post("/login/")
async def login(user: UserSchema):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful"}

# main.py - FastAPI Backend
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Database Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI App
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

# API Routes
@app.get("/")
def read_root():
    return {"message": "Wardrobe API is running"}

@app.post("/upload/")
def upload_image(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(file.file.read())
    return {"info": f"file '{file.filename}' saved at '{file_location}'"}

@app.post("/users/")
def create_user(email: str, password: str, db: Session = Depends(get_db)):
    user = User(email=email, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email}

# main.py - FastAPI Backend
from fastapi import FastAPI
from routes import items, users, categories, outfits
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
import uvicorn


# Load environment variables
load_dotenv()

app = FastAPI()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Use PORT from env, default to 8000
    uvicorn.run(app, host="0.0.0.0", port=port)

app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific frontend domains in production
    allow_credentials=True,
    allow_methods=["*"]
)

# Include API routes
app.include_router(items.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(outfits.router)

@app.get("/")
def home():
    return {"message": "Wardrobe API is running"}

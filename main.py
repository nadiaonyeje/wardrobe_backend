# main.py - FastAPI Backend
from fastapi import FastAPI
from routes import items, users, categories, outfits
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from database import create_indexes  # ✅ import this
import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

# Run server if script is executed directly
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Session and CORS Middleware
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include Routes
app.include_router(items.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(outfits.router)

# ✅ On startup, create DB indexes
@app.on_event("startup")
async def startup_event():
    await create_indexes()

@app.get("/")
def home():
    return {"message": "Wardrobe API is running"}

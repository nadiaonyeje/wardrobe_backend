from fastapi import APIRouter, HTTPException
from database import items_collection
from models import WardrobeItemSchema
import requests
from bs4 import BeautifulSoup

router = APIRouter()

# Extract product details from a shopping website
@router.post("/extract-item/")
async def extract_item(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Attempt to extract name, price, and image (varies by site)
        name = soup.find("h1").text if soup.find("h1") else "Unknown Product"
        price = soup.find(class_="price").text if soup.find(class_="price") else "Price Not Found"
        image_tag = soup.find("img")
        image_url = image_tag["src"] if image_tag and "src" in image_tag.attrs else None

        if not image_url:
            raise HTTPException(status_code=400, detail="Could not extract image")

        new_item = {
            "name": name,
            "image_url": image_url,
            "price": price,
            "link": url,
        }

        result = await items_collection.insert_one(new_item)
        return {"message": "Item added", "id": str(result.inserted_id), **new_item}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to access URL")

        soup = BeautifulSoup(response.text, "html.parser")

        # Attempt to extract name, price, and image (Handle different site structures)
        name = (
            soup.find("h1").text.strip()
            if soup.find("h1")
            else soup.find("title").text.strip()
            if soup.find("title")
            else "Unknown Product"
        )

        # Look for price in common classes
        price_classes = ["price", "product-price", "current-price", "sale-price"]
        price = "Price Not Found"
        for cls in price_classes:
            price_tag = soup.find(class_=cls)
            if price_tag:
                price = price_tag.text.strip()
                break

        # Extract image
        image_tag = soup.find("img")
        image_url = (
            image_tag["src"]
            if image_tag and "src" in image_tag.attrs
            else "No image found"
        )

        if not image_url.startswith("http"):
            image_url = url + image_url  # Fix relative URLs

        # Save to MongoDB
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

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
import os

from pdf_generator import generate_itinerary
from image_search import search_images
from ai_processor import parse_raw_itinerary

app = FastAPI(title="Travel Itinerary Generator")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC SCHEMAS ---

class DayPayload(BaseModel):
    day_number: int
    title: str
    date: str
    destination: str
    description: str
    image_urls: List[str]

class HotelSummary(BaseModel):
    destination: str
    hotel_name: str
    details: str

class ItineraryPayload(BaseModel):
    guest_name: str
    duration: str
    arrival: str
    departure: str
    days: List[DayPayload]
    hotels: List[HotelSummary]
    accommodation_price: str
    transport_price: str

class RawItineraryRequest(BaseModel):
    raw_text: str

class DayPayloadWithKeywords(BaseModel):
    day_number: int
    title: str
    date: str
    destination: str
    description: str
    image_keywords: List[str]

class ItineraryPayloadWithKeywords(BaseModel):
    guest_name: str
    duration: str
    arrival: str
    departure: str
    days: List[DayPayloadWithKeywords]
    hotels: List[HotelSummary]
    accommodation_price: str
    transport_price: str

# --- ENDPOINTS ---

@app.post("/generate")
async def generate_pdf(payload: ItineraryPayload):
    """Generates the PDF directly from pre-defined image URLs and texts."""
    try:
        output_path = await generate_itinerary(payload.model_dump())
        return FileResponse(output_path, media_type="application/pdf", filename="Itinerary.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-with-keywords")
async def generate_with_keywords(payload: ItineraryPayloadWithKeywords):
    """Searches DuckDuckGo for keywords, then generates the PDF."""
    try:
        data = payload.model_dump()
        
        # Resolve image search keywords sequentially to avoid rate limits
        for day in data.get("days", []):
            keywords = day.get("image_keywords", [])
            urls = []
            for kw in keywords:
                # search_images returns a list of fallback urls
                res_urls = search_images(kw)
                if res_urls:
                    urls.extend(res_urls)
            day["image_urls"] = urls
            
        output_path = await generate_itinerary(data)
        return FileResponse(output_path, media_type="application/pdf", filename="Itinerary_With_Images.pdf")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-from-raw")
async def generate_pdf_from_raw(payload: RawItineraryRequest, request: Request):
    """Full Pipeline: Gemini -> Pexels -> PDF Generator."""
    try:
        # Extract API keys from headers
        gemini_key = request.headers.get("x-gemini-key")
        pexels_key = request.headers.get("x-pexels-key")

        # 1. Parse raw text into structured format using Gemini
        parsed_data = parse_raw_itinerary(payload.raw_text, api_key=gemini_key)
        
        # 2. Resolve image search keywords in parallel for massive speedup
        async def resolve_day_images(day):
            keywords = day.get("image_keywords", [])
            hotel_kw = day.get("hotel_image_keyword", "luxury Sri Lanka resort infinity pool")

            # Search all attraction keywords in parallel
            tasks = [asyncio.to_thread(search_images, kw, pexels_key) for kw in keywords]
            results = await asyncio.gather(*tasks)
            
            # Flatten attraction image results (1 url per keyword)
            urls = []
            for res_urls in results:
                if res_urls:
                    urls.append(res_urls[0])  # Take only the FIRST url per keyword for variety

            # Search hotel image (last slot)
            hotel_urls = await asyncio.to_thread(search_images, hotel_kw, pexels_key)
            if hotel_urls:
                urls.append(hotel_urls[0])
            else:
                # fallback hotel image
                fallback = await asyncio.to_thread(search_images, "luxury Sri Lanka resort infinity pool", pexels_key)
                if fallback:
                    urls.append(fallback[0])

            day["image_urls"] = urls

        # Run all days concurrently
        day_tasks = [resolve_day_images(day) for day in parsed_data.get("days", [])]
        await asyncio.gather(*day_tasks)
        
        # 3. Generate the PDF
        output_path = await generate_itinerary(parsed_data)
        
        filename_out = os.path.basename(output_path)
        return FileResponse(output_path, media_type="application/pdf", filename=filename_out)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

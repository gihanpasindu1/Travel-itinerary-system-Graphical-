import httpx
import os
import random
from dotenv import load_dotenv

load_dotenv()

FALLBACK_PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")


def search_images(keyword: str, pexels_key: str = None) -> list:
    """
    Searches Pexels for professional, curated travel photos matching the keyword.
    Uses intelligent fallback: tries progressively simpler terms if no results found.
    Falls back to LoremFlickr if Pexels key is not configured.
    """
    final_key = pexels_key or FALLBACK_PEXELS_KEY
    if final_key and final_key != "your_pexels_key_here":
        return _search_pexels_with_fallback(keyword, final_key)
    else:
        print(f"[WARNING] PEXELS_API_KEY not set. Using LoremFlickr for '{keyword}'")
        return _search_loremflickr(keyword)


def _search_pexels_with_fallback(keyword: str, pexels_key: str) -> list:
    """
    Tries increasingly simpler keyword variations until we get results.
    This ensures every image slot gets filled with a relevant professional photo.
    """
    words = keyword.strip().split()

    # Build a cascade of fallback queries from most specific to most general
    # e.g. "Temple of the Tooth Relic Kandy" ->
    #      "Temple Tooth Kandy" ->
    #      "Kandy temple" ->
    #      "Kandy Sri Lanka" ->
    #      "Sri Lanka"
    
    queries_to_try = [keyword]
    
    # Fallback 1: keep first location word + last 2 meaningful words
    if len(words) > 3:
        queries_to_try.append(f"{words[0]} {words[-2]} {words[-1]}")
    
    # Fallback 2: just first 2 words (location + key subject)
    if len(words) >= 2:
        queries_to_try.append(f"{words[0]} {words[1]}")
    
    # Fallback 3: just the first word (the location name itself)
    queries_to_try.append(words[0])
    
    # Fallback 4: add "Sri Lanka" to the first word for geo-context
    queries_to_try.append(f"{words[0]} Sri Lanka")
    
    for query in queries_to_try:
        urls = _fetch_pexels(query, pexels_key)
        if urls:
            if query != keyword:
                print(f"[INFO] Pexels fallback used: '{keyword}' -> '{query}' ({len(urls)} photos)")
            return urls
    
    # If all Pexels fallbacks fail, use LoremFlickr
    print(f"[WARN] All Pexels queries failed for '{keyword}', using LoremFlickr")
    return _search_loremflickr(keyword)


def _fetch_pexels(query: str, pexels_key: str, count: int = 1) -> list:
    """Makes a single Pexels API request and returns image URLs.
    Fetches only 1 image per keyword call to ensure maximum variety across all slots.
    Uses a random page offset so repeat calls for the same keyword get different photos.
    """
    try:
        headers = {"Authorization": pexels_key}
        # Random page within a small range keeps results relevant but avoids duplicates
        page = random.randint(1, 3)
        params = {
            "query": query,
            "per_page": count,
            "page": page,
            "orientation": "landscape",  # Always landscape for travel brochures
            "size": "large"  # Only high-res professional photos
        }
        
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                "https://api.pexels.com/v1/search",
                headers=headers,
                params=params
            )
            resp.raise_for_status()
            data = resp.json()
        
        photos = data.get("photos", [])
        urls = []
        for photo in photos:
            src = photo.get("src", {})
            # Prefer large2x (high quality) then large then original
            url = src.get("large2x") or src.get("large") or src.get("original")
            if url:
                urls.append(url)
        
        return urls
        
    except Exception as e:
        print(f"Pexels error for '{query}': {e}")
        return []


def _search_loremflickr(keyword: str) -> list:
    """Fallback: get random Flickr CC images (lower quality but always works)."""
    try:
        tags = ",".join(keyword.strip().split()[:4])  # Take max 4 words as tags
        urls = []
        for _ in range(5):
            url = f"https://loremflickr.com/800/600/{tags}?random={random.randint(1, 99999)}"
            urls.append(url)
        return urls
    except Exception as e:
        print(f"LoremFlickr error for '{keyword}': {e}")
        return []

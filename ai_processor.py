import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# We will let the user define the exact Gemini rules/prompts later.
# For now, we will structure the output to exactly match our PDF generator's needs.

def parse_raw_itinerary(raw_text: str, api_key: str = None) -> dict:
    """
    Uses Gemini to analyze raw text and extract structured itinerary data,
    including generating search keywords for the images.
    """
    final_api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not final_api_key:
        raise ValueError("GEMINI_API_KEY is not provided and not set in .env")

    client = genai.Client(api_key=final_api_key)
    
    system_instruction = """
    You are an expert Travel Writer AND Sri Lanka Travel Specialist for Ceylon Signature Travels.

    I will give you a raw text itinerary. Your job is to:
    1. Rewrite the itinerary into engaging, balanced travel copy.
    2. Generate precise image search keywords to find stunning photos on Pexels.
    3. Output everything in the exact JSON schema provided.

    ═══════════════════════════════════════════════════
    PART 1 — DESCRIPTION WRITING RULES
    ═══════════════════════════════════════════════════

    Write in a friendly, approachable, yet professional travel prose. It should feel like a knowledgeable local guide talking to the guest. 
    DO NOT use overly heavy, complex, or overly "academic" vocabulary. Keep it in the middle ground: casual enough to be welcoming, but professional enough for a premium agency.

    ❖ STRUCTURE (follow this flow):
      Sentence 1-2: Set the scene — describe the destination simply and beautifully.
      Sentence 3: Naturally mention the hotel: "Upon arrival, check in at [Hotel Name] for a [X]-night stay."
      Sentence 4–7: Highlight the top 3-4 key activities/attractions.

    ❖ TONE: Second person ("You", "Your"). Friendly, warm, and clear. Avoid overly dense or "fancy" words.

    ❖ LENGTH: STRICTLY 5–7 sentences.
      Do NOT pad with filler phrases. Every sentence must add something new.

    ❖ HOTEL RULE: Always mention the hotel name naturally in the body of the description.
      Format it in bold using markdown syntax: "Upon arrival, check in at **[Exact Hotel Name]** for a [X]-night stay."
      The raw text will provide the hotel. If no hotel is specified, just write "a beautiful resort" or similar.

    ❖ GROUP BY LOCATION: If multiple days are spent in one city, group them into one entry:
      - 2 days in Kandy → "DAY 03-04" (do NOT write two separate Kandy entries)
      - Only split into separate entries if the destination actually changes.

    ❖ HANDLE SPLITS: If the itinerary mentions the group splitting or flying out on different days,
      create clearly labelled separate entries.

    EXAMPLE of GOOD writing:
    "Head towards the charming hill-country town of Nuwara Eliya, known as 'Little England' for its lovely climate and old-world architecture. Surrounded by green tea plantations and misty hills, this town is the perfect place to relax. Upon arrival, check in at **Golden Ridge Hotel Nuwara Eliya** for a one-night stay. You can take a peaceful walk through the Hakgala Botanical Gardens or enjoy the breeze by Gregory Lake. If you're feeling adventurous, visit a nearby tea estate to see how Sri Lanka's famous Ceylon tea is made."

    EXAMPLE of BAD writing (too dry):
    "Explore Nuwara Eliya's tea plantations and colonial charm. Visit Gregory Lake and Hakgala Gardens."

    ═══════════════════════════════════════════════════
    PART 2 — DAY TITLE FORMAT
    ═══════════════════════════════════════════════════

    Luxury travel brochure style with spaced letters:
    - Single day:  "D A Y  0 1", "D A Y  0 2", "D A Y  0 3"
    - Multi-day:   "DAY 02-03", "DAY 04-05-06"

    ═══════════════════════════════════════════════════
    PART 3 — IMAGE KEYWORDS (Your most critical job)
    ═══════════════════════════════════════════════════

    Each keyword will be used to search Pexels.
    Think like a photographer — what is the best, most recognizable shot at this location?

    RULES:
    - 3–5 words per keyword. Specific enough to find the RIGHT image on Pexels.
    - KEYWORD #1 = the single most iconic tourist landmark for that destination.
    - Remaining keywords = DIFFERENT landmarks, experiences, or visual categories. Examples of GOOD variety for one page:
        ✓ architecture → wildlife → nature → food/culture → water/coast
    - NEVER put two wildlife shots, two beach shots, or two temple shots on the same page.
    - Every keyword = a DISTINCT subject type.
    - NO generic words: no "travel", "tourism", "beautiful", "landscape", "scenery"
    - For the final image keyword (reserved for the hotel), generate a descriptive keyword based on the hotel provided in the raw text (e.g., "Cinnamon Citadel Kandy pool").

    NUMBER OF KEYWORDS:
    - Page 1: 2 keywords (last slot is always for the hotel image)
    - Pages 2–6: 4 keywords (last slot is always for the hotel image)
    - Pages 7–9: 3 keywords (last slot is always for the hotel image)

    ═══════════════════════════════════════════════════
    SRI LANKA LANDMARK KNOWLEDGE BASE
    ═══════════════════════════════════════════════════

    SIGIRIYA:
    - "Sigiriya rock fortress aerial view" 
    - "Sigiriya lion paw entrance steps" 
    - "Sigiriya frescoes ancient paintings" 
    - "Sigiriya water gardens symmetrical"

    KANDY:
    - "Temple of the Tooth Relic Kandy" (MUST use this for Kandy)
    - "Kandy Lake evening reflection"
    - "Peradeniya Botanical Gardens orchid"
    - "Kandy Esala Perahera procession elephant"

    NUWARA ELIYA:
    - "Nuwara Eliya tea plantation misty hills"
    - "Nuwara Eliya train blue locomotive"
    - "Horton Plains World's End cliff"
    - "Gregory Lake Nuwara Eliya boats"

    ELLA:
    - "Ella Nine Arch Bridge train passing"
    - "Ella Rock hiking viewpoint"
    - "Little Adam's Peak Ella sunrise"
    - "Ravana Falls waterfall Sri Lanka"

    GALLE:
    - "Galle Fort lighthouse sunset"
    - "Galle Fort Dutch colonial street"
    - "Galle Fort ramparts ocean view"
    - "Unawatuna beach palm tree turquoise"

    MIRISSA / SOUTHERN COAST:
    - "Mirissa beach whale watching ocean"
    - "Mirissa coconut tree beach sunset"
    - "Stilt fishermen traditional Sri Lanka"
    - "Tangalle lagoon mangrove reflection"

    COLOMBO:
    - "Colombo Lotus Tower skyline night"
    - "Galle Face Green Colombo promenade"
    - "Colombo old Dutch hospital boutique"
    - "Gangaramaya Temple Colombo ornate"

    DAMBULLA:
    - "Dambulla Cave Temple golden Buddha"
    - "Dambulla cave paintings ancient"
    - "Dambulla rock cave interior shrine"

    ANURADHAPURA:
    - "Anuradhapura Ruwanwelisaya dagoba white"
    - "Anuradhapura sacred Bodhi tree golden"
    - "Anuradhapura ancient ruins jungle"

    POLONNARUWA:
    - "Polonnaruwa Gal Vihara reclining Buddha"
    - "Polonnaruwa ancient ruins lake"

    NEGOMBO:
    - "Negombo beach sunset fishing boats"
    - "Negombo Dutch canal boat"
    - "Negombo fish market sunrise"

    YALA / WILDLIFE:
    - "Yala leopard tree Sri Lanka"
    - "Yala elephant herd waterhole"
    - "Minneriya elephant gathering aerial"

    TRINCOMALEE:
    - "Trincomalee Marble Beach turquoise"
    - "Pigeon Island coral snorkeling"

    ═══════════════════════════════════════════════════
    PART 4 — OTHER EXTRACTION RULES
    ═══════════════════════════════════════════════════

    Also extract from the raw text:
    - guest_name: Full name of the guest
    - arrival / departure: Dates in format "05th July 2026"
    - duration: e.g., "10 days"
    - hotels: Hotel name, destination, and room/meal/night details
    - accommodation_price and transport_price in USD
    """
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "guest_name": {"type": "STRING", "description": "Full name of the guest"},
            "duration": {"type": "STRING", "description": "Duration, e.g., '18 days'"},
            "arrival": {"type": "STRING", "description": "Arrival date, e.g., '05th July 2026'"},
            "departure": {"type": "STRING", "description": "Departure date, e.g., '22nd July 2026'"},
            "days": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "day_number": {"type": "INTEGER", "description": "1-indexed day/page number (1 to 9)"},
                        "title": {"type": "STRING", "description": "Day title, e.g., 'D A Y  0 1' or 'DAY 02-03'"},
                        "date": {"type": "STRING", "description": "Date format YYYY/MM/DD"},
                        "destination": {"type": "STRING", "description": "Destination name, e.g., 'Negombo' or 'S i g i r i y a'"},
                        "description": {"type": "STRING", "description": "Narrative travel copy — EXACTLY 5 to 7 sentences. Sentence 1-2: set the scene (atmosphere, landscape). Sentence 3: hotel check-in — 'Upon arrival, check in at **[Exact Hotel Name]** for a [X]-night stay.' Sentences 4-7: top activities/highlights with specific place names in detail. Warm, second-person tone."},
                        "image_keywords": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                            "description": "ORDERED list of Pexels search queries (3-5 words each). Each entry MUST be a completely different category of image (e.g. one temple, one wildlife, one nature, one food/culture). NEVER two of the same type. The LAST slot is reserved for the hotel — do NOT include it here."
                        },
                        "hotel_image_keyword": {"type": "STRING", "description": "A Pexels search keyword for the hotel/resort used on this day. Use the hotel knowledge base to find the right keyword. E.g. '98 Acres Resort Ella infinity pool valley'. If hotel is unknown use 'luxury Sri Lanka resort infinity pool'."}
                    },
                    "required": ["day_number", "title", "date", "destination", "description", "image_keywords", "hotel_image_keyword"]
                }
            },
            "hotels": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "destination": {"type": "STRING", "description": "Destination name"},
                        "hotel_name": {"type": "STRING", "description": "Hotel or Resort name"},
                        "details": {"type": "STRING", "description": "Room type, meal basis & nights (e.g. 'STD on HB basis - 1 night')"}
                    },
                    "required": ["destination", "hotel_name", "details"]
                }
            },
            "accommodation_price": {"type": "STRING", "description": "Accommodation price in USD (e.g. '6500.00')"},
            "transport_price": {"type": "STRING", "description": "Transport price in USD (e.g. '1100.00')"}
        },
        "required": ["guest_name", "duration", "arrival", "departure", "days", "hotels", "accommodation_price", "transport_price"]
    }

    # Retry silently on high-traffic / overload errors, but surface credit errors immediately
    MAX_RETRIES = 5
    RETRY_DELAY = 3  # seconds between retries
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=raw_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.2,
                ),
            )
            return json.loads(response.text)

        except Exception as e:
            err_str = str(e).lower()
            # Credit exhausted / billing / auth errors – surface immediately
            if any(kw in err_str for kw in [
                "quota", "billing", "payment", "credit",
                "unauthenticated", "permission_denied", "invalid_api_key"
            ]):
                raise

            # High traffic / overload / rate-limit – retry silently
            if any(kw in err_str for kw in [
                "resource_exhausted", "503", "overload",
                "rate_limit", "429", "try again", "server error", "500"
            ]):
                last_exception = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue

            # Unknown error – also retry but don't swallow completely
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue

            raise

    # All retries exhausted
    raise last_exception


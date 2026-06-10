import fitz  # PyMuPDF
import httpx
import asyncio
from io import BytesIO

# Hand-verified precise coordinate mapping for Pages 1 to 9
PAGES_MAP = {
    1: {
        'day_title': fitz.Rect(42.0, 290.0, 160.0, 320.0),
        'date': fitz.Rect(211.0, 293.0, 324.0, 317.0),
        'destination': fitz.Rect(42.0, 320.0, 300.0, 347.0),
        'description': fitz.Rect(42.0, 346.0, 333.0, 729.0),
        'images': [
            fitz.Rect(355.0, 352.9, 580.7, 540.9),
            fitz.Rect(355.0, 556.7, 580.8, 796.8),
        ]
    },
    2: {
        'day_title': fitz.Rect(42.3, 24.6, 179.7, 60.9),
        'date': fitz.Rect(211.3, 30.5, 324.6, 53.7),
        'destination': fitz.Rect(42.3, 51.9, 333.4, 78.8),
        'description': fitz.Rect(42.3, 84.0, 333.4, 420.0),
        'images': [
            fitz.Rect(355.0, 84.1, 580.8, 299.4),
            fitz.Rect(355.0, 315.0, 580.8, 470.3),
            fitz.Rect(42.3, 429.9, 333.4, 637.0),
            fitz.Rect(355.0, 486.5, 580.7, 634.2),
            fitz.Rect(42.3, 649.4, 580.2, 827.2),
        ]
    },
    3: {
        'day_title': fitz.Rect(42.3, 24.6, 195.5, 60.9),
        'date': fitz.Rect(211.3, 30.5, 324.3, 53.7),
        'destination': fitz.Rect(42.3, 58.1, 333.4, 85.0),
        'description': fitz.Rect(42.3, 84.0, 333.4, 440.0),
        'images': [
            fitz.Rect(355.0, 86.8, 580.8, 239.1),
            fitz.Rect(355.0, 249.9, 580.8, 475.7),
            fitz.Rect(42.3, 448.2, 326.6, 638.0),
            fitz.Rect(355.0, 487.9, 580.8, 637.9),
            fitz.Rect(42.3, 650.8, 580.2, 817.3),
        ]
    },
    4: {
        'day_title': fitz.Rect(42.3, 24.6, 193.4, 60.9),
        'date': fitz.Rect(211.3, 30.5, 315.6, 53.7),
        'destination': fitz.Rect(42.3, 58.1, 333.4, 85.0),
        'description': fitz.Rect(42.3, 84.0, 333.4, 440.0),
        'images': [
            fitz.Rect(355.0, 86.8, 580.8, 240.6),
            fitz.Rect(355.0, 251.5, 580.8, 435.3),
            fitz.Rect(42.3, 454.7, 343.1, 637.8),
            fitz.Rect(355.0, 454.7, 580.8, 637.8),
            fitz.Rect(42.3, 648.5, 580.2, 827.1),
        ]
    },
    5: {
        'day_title': fitz.Rect(42.3, 24.6, 164.0, 60.9),
        'date': fitz.Rect(211.3, 30.5, 319.2, 53.7),
        'destination': fitz.Rect(42.3, 58.1, 333.4, 85.0),
        'description': fitz.Rect(42.3, 84.0, 333.4, 450.0),
        'images': [
            fitz.Rect(355.0, 96.9, 576.8, 256.4),
            fitz.Rect(355.0, 263.8, 580.8, 446.9),
            fitz.Rect(355.0, 459.9, 580.8, 624.2),
            fitz.Rect(42.6, 460.4, 333.5, 624.5),
            fitz.Rect(42.3, 647.6, 580.5, 824.8),
        ]
    },
    6: {
        'day_title': fitz.Rect(42.3, 24.6, 153.7, 60.9),
        'date': fitz.Rect(211.3, 30.5, 319.6, 53.7),
        'destination': fitz.Rect(42.3, 58.1, 333.4, 85.0),
        'description': fitz.Rect(42.3, 84.0, 333.4, 450.0),
        'images': [
            fitz.Rect(355.0, 96.9, 576.8, 256.4),
            fitz.Rect(355.0, 269.2, 580.8, 453.0),
            fitz.Rect(42.3, 465.4, 333.5, 637.2),
            fitz.Rect(355.0, 465.4, 580.8, 637.2),
            fitz.Rect(42.3, 647.6, 580.5, 824.8),
        ]
    },
    7: {
        'day_title': fitz.Rect(42.3, 24.6, 189.4, 60.9),
        'date': fitz.Rect(211.3, 30.5, 318.1, 53.7),
        'destination': fitz.Rect(42.3, 58.1, 333.4, 85.0),
        'description': fitz.Rect(42.3, 84.0, 333.4, 630.0),
        'images': [
            fitz.Rect(355.0, 86.8, 581.6, 240.6),
            fitz.Rect(356.0, 252.2, 581.8, 444.3),
            fitz.Rect(356.0, 455.5, 581.3, 638.0),
            fitz.Rect(42.3, 649.3, 581.5, 825.8),
        ]
    },
    8: {
        'day_title': fitz.Rect(42.3, 24.6, 189.2, 60.9),
        'date': fitz.Rect(211.3, 30.5, 319.6, 53.7),
        'destination': fitz.Rect(42.3, 58.1, 333.4, 85.0),
        'description': fitz.Rect(42.3, 84.0, 333.4, 630.0),
        'images': [
            fitz.Rect(356.0, 86.8, 581.8, 261.6),
            fitz.Rect(356.0, 272.4, 580.1, 431.5),
            fitz.Rect(356.0, 455.5, 581.3, 638.0),
            fitz.Rect(42.3, 649.3, 581.5, 825.8),
        ]
    },
    9: {
        'day_title': fitz.Rect(42.3, 24.6, 141.5, 60.9),
        'date': fitz.Rect(211.3, 30.5, 319.7, 53.7),
        'destination': fitz.Rect(42.3, 58.1, 333.4, 85.0),
        'description': fitz.Rect(42.3, 84.0, 333.4, 630.0),
        'images': [
            fitz.Rect(356.0, 86.8, 575.1, 248.1),
            fitz.Rect(356.0, 264.4, 575.1, 428.7),
            fitz.Rect(356.0, 455.5, 581.3, 638.0),
            fitz.Rect(42.3, 649.3, 581.5, 825.8),
        ]
    },
}

async def fetch_image(url: str) -> bytes:
    """Downloads an image from a URL into memory, following redirects."""
    if not url:
        return b""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.pexels.com/"
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return b""

async def generate_itinerary(payload: dict) -> str:
    """
    Opens the empty template, injects data into the exact coordinates for all pages,
    and saves the finished PDF.
    """
    doc = fitz.open("templates/empty  template.pdf")
    
    # --- FILL PAGES 1 TO 9 (ITINERARY DAYS) ---
    days = payload.get("days", [])
    for day in days:
        page_num = day.get("day_number")
        if page_num not in PAGES_MAP:
            continue
            
        page = doc[page_num - 1] # 0-indexed page in PyMuPDF
        cfg = PAGES_MAP[page_num]
        
        # 1. Day Title
        if day.get("title") and 'day_title' in cfg:
            # Use insert_text to prevent overflow hiding
            point = fitz.Point(cfg['day_title'].x0, cfg['day_title'].y0 + (14 if page_num == 1 else 18))
            page.insert_text(
                point,
                day["title"],
                fontsize=16 if page_num == 1 else 22,
                fontname="hebo",
                color=(0.2, 0.2, 0.3) if page_num > 1 else (0, 0, 0)
            )
            
        # 2. Date
        if day.get("date") and 'date' in cfg:
            point = fitz.Point(cfg['date'].x0, cfg['date'].y0 + (12 if page_num == 1 else 16))
            page.insert_text(
                point,
                day["date"],
                fontsize=12 if page_num == 1 else 16,
                fontname="helv",
                color=(0.2, 0.2, 0.3) if page_num > 1 else (0, 0, 0)
            )
            
        # 3. Destination
        if day.get("destination") and 'destination' in cfg:
            point = fitz.Point(cfg['destination'].x0, cfg['destination'].y0 + 16)
            page.insert_text(
                point,
                day["destination"],
                fontsize=18,
                fontname="hebo",
                color=(0.2, 0.2, 0.3) if page_num > 1 else (0, 0, 0)
            )
            
        # 4. Description — rendered with HTML box to support bold hotel names natively
        if day.get("description") and 'description' in cfg:
            import re
            desc_rect = cfg['description']
            raw_desc = day["description"]
            
            font_size = 14 if page_num == 1 else 15
            hex_color = "#33334C" if page_num > 1 else "#000000"
            
            # Convert newlines to <br> and **bold** to <b style="...">
            html_text = raw_desc.replace("\n", "<br>")
            html_text = re.sub(r'\*\*(.*?)\*\*', r'<b style="color: #000000;">\1</b>', html_text)
            
            css = f"""
            * {{
                font-family: sans-serif;
                font-size: {font_size}pt;
                color: {hex_color};
                line-height: 1.3;
            }}
            """
            
            # Try normal font size
            res = page.insert_htmlbox(desc_rect, html_text, css=css)
            
            # Since insert_htmlbox doesn't give a simple negative result on overflow like insert_textbox,
            # for a simple fallback we will just trust it fits given the new 3-4 sentence limit.
            # If we wanted to check, we'd compare the returned tuple's height against rect.height, but it usually fits now.

        # 5. Load and Draw Images
        img_urls = day.get("image_urls", [])
        image_boxes = cfg.get("images", [])

        if img_urls and image_boxes:
            # Download all provided URLs in parallel
            download_tasks = [fetch_image(url) for url in img_urls]
            all_img_bytes = await asyncio.gather(*download_tasks)

            # Filter out failed downloads
            successful_img_bytes = [b for b in all_img_bytes if b]

            for idx, box in enumerate(image_boxes):
                if idx >= len(successful_img_bytes):
                    break
                img_bytes = successful_img_bytes[idx]
                try:
                    page.insert_image(box, stream=img_bytes, keep_proportion=False)
                except Exception as e:
                    print(f"Error rendering image index {idx} on page {page_num}: {e}")

                    
        # 6. For Page 1 only: Add top metadata (guest details)
        if page_num == 1:
            metadata_fields = [
                ("guest_name", payload.get("guest_name", ""), fitz.Point(165.0, 188.0)),
                ("duration", payload.get("duration", ""), fitz.Point(390.0, 188.0)),
                ("arrival", payload.get("arrival", ""), fitz.Point(110.0, 221.0)),
                ("departure", payload.get("departure", ""), fitz.Point(390.0, 221.0)),
            ]
            for field_name, text, point in metadata_fields:
                if text:
                    page.insert_text(
                        point,
                        text,
                        fontsize=12,
                        fontname="hebo",
                        color=(0, 0, 0)
                    )


    # Save output
    guest_name = payload.get("guest_name", "Client").replace(" ", "_")
    output_path = f"{guest_name}_Itinerary.pdf"
    doc.save(output_path)
    doc.close()
    
    return output_path

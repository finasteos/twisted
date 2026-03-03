"""
Image Parser - OCR via Apple Vision/Pytesseract
"""

from pathlib import Path
import asyncio


async def extract_image(path: Path) -> str:
    """Extract text from image using OCR."""
    await asyncio.sleep(0.2)

    try:
        import pytesseract
        from PIL import Image

        img = Image.open(str(path))
        text = pytesseract.image_to_string(img)

        if text.strip():
            return text
        else:
            return "[No text detected in image]"
    except Exception as e:
        return f"[Image OCR failed: {e}]"

"""
Text Parser - Handles .txt, .pdf, .docx files
"""

from pathlib import Path
import asyncio


async def extract_text(path: Path) -> str:
    """Extract plain text from file."""
    await asyncio.sleep(0.01)
    return path.read_text(encoding="utf-8")


async def extract_pdf(path: Path) -> str:
    """Extract text from PDF."""
    await asyncio.sleep(0.1)

    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        text = "\n".join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


async def extract_docx(path: Path) -> str:
    """Extract text from DOCX."""
    await asyncio.sleep(0.1)

    try:
        from docx import Document

        doc = Document(str(path))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"[DOCX extraction failed: {e}]"

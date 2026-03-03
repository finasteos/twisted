"""
Email Parser - Handles .eml, .msg files
"""

from pathlib import Path
import asyncio
import email
from email import policy
from email.parser import BytesParser


async def extract_email(path: Path) -> str:
    """Extract content from email file."""
    await asyncio.sleep(0.1)

    try:
        with open(path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)

        parts = []
        parts.append(f"From: {msg.get('From', 'Unknown')}")
        parts.append(f"To: {msg.get('To', 'Unknown')}")
        parts.append(f"Subject: {msg.get('Subject', 'No Subject')}")
        parts.append(f"Date: {msg.get('Date', 'Unknown')}")
        parts.append("")

        body = msg.get_body(preferencelist=("plain", "html"))
        if body:
            parts.append(body.get_content())

        return "\n".join(parts)
    except Exception as e:
        return f"[Email extraction failed: {e}]"

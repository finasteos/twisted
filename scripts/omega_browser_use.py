#!/usr/bin/env python3
"""
Omega - The Caretaker's Night Shift (using browser-use)
Tests TWISTED using browser-use with local Chrome profile!
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set API keys
BROWSER_KEY = "bu_tGoTZEli69AWqEjxJFjDlF1eCiuEtXD0P1Gox9dsOFA"
GEMINI_KEY = "AIzaSyBv1PeBnd6q8MhmfjZbiyzVqatwgDF5_F8"

os.environ["BROWSER_USE_API_KEY"] = BROWSER_KEY
os.environ["GEMINI_API_KEY"] = GEMINI_KEY

from browser_use import Agent, Browser, ChatGoogle


async def run_omega_test():
    """Run Omega test using browser-use."""
    print("🌊 Omega initializing browser-use...")

    # Use local Chrome with extensions
    browser = Browser(
        is_local=True,
        headless=False,
    )

    # Use Gemini 3.0 Flash Preview
    llm = ChatGoogle(model="gemini-3.0-flash-preview")

    try:
        # Test 1: Frontend
        print("📱 Test 1: Loading TWISTED frontend...")
        agent1 = Agent(
            task="Navigate to http://localhost:3000. Wait for page to load. Tell me the page title and what you see on the screen.",
            llm=llm,
            browser=browser,
        )
        result1 = await agent1.run()
        print(f"   Result: {result1}")

        # Test 2: API
        print("🔎 Test 2: Checking API...")
        agent2 = Agent(
            task="Go to http://localhost:8000/api/health. Tell me what the API returns.",
            llm=llm,
            browser=browser,
        )
        result2 = await agent2.run()
        print(f"   Result: {result2}")

        print("\n" + "=" * 50)
        print(f"📊 OMEGA TEST - {datetime.now().isoformat()}")
        print("=" * 50)
        print("✅ Tests complete!")
        print("=" * 50)

        # Clean up
        try:
            await browser.close()
        except:
            pass

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_omega_test())

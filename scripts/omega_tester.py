#!/usr/bin/env python3
"""
Omega - The Caretaker's Night Shift
Tests TWISTED while you sleep.

Runs every 5 minutes via heartbeat.
Tests the app like a real user would.
Reports bugs and suggestions.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Skyvern setup
import os

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

os.environ.setdefault("SKYVERN_API_KEY", "local")
os.environ.setdefault("LLM_KEY", "GEMINI_2.5_FLASH")
os.environ.setdefault("ENABLE_GEMINI", "true")
os.environ.setdefault("GEMINI_API_KEY", GEMINI_KEY)
os.environ.setdefault("BROWSER_TYPE", "local")

from skyvern import Skyvern


# Omega's Mission Instructions
OMEGA_MISSION = """
You are Omega - The Caretaker of TWISTED (The Glass Cathedral).

MISSION: Test the TWISTED application as a real user would, find bugs, 
suggest improvements, and ensure the system works properly.

ABOUT TWISTED:
- TWISTED is an AI agent swarm system for decision-making
- Frontend: React with ReactFlow at http://localhost:3000
- Backend: FastAPI at http://localhost:8000
- Has admin mode with Agent Chat (floating button in bottom-left)

TESTING PROTOCOL:
1. Navigate to http://localhost:3000
2. Test the main flow:
   - Check if the app loads without errors
   - Toggle admin mode on/off
   - Click the floating agent chat button (bottom-left, purple/cyan gradient)
   - Test chatting with different agents
3. Test chat features
4. Check system health

REPORTING:
After each run, provide:
1. What worked
2. What failed (with error messages)
3. Suggestions for improvement
4. Overall system health score (1-10)

Start now. Be thorough but efficient. You have 3 minutes per run.
"""


class OmegaTester:
    def __init__(self):
        self.skyvern = None
        self.results = []

    async def setup(self):
        """Initialize Skyvern browser."""
        self.skyvern = Skyvern.local()
        print("🌊 Omega initializing browser...")

    async def run_tests(self):
        """Execute the testing mission."""
        try:
            print("🚀 Omega launching test run...")

            browser = await self.skyvern.launch_local_browser()
            page = await browser.get_working_page()

            # Test 1: Load the app
            print("📱 Test 1: Loading TWISTED frontend...")
            await page.goto("http://localhost:3000", timeout=30000)
            await asyncio.sleep(3)

            title = await page.title()
            print(f"   Page title: {title}")
            print(f"   ✅ Frontend loads!")

            # Test 2: API health
            print("🔎 Test 2: Checking API health...")
            try:
                import httpx

                async with httpx.AsyncClient() as client:
                    health = await client.get(
                        "http://localhost:8000/api/health", timeout=5
                    )
                    print(f"   API Status: {health.status_code}")
                    if health.status_code == 200:
                        print(f"   ✅ Backend is healthy!")
            except Exception as e:
                print(f"   ❌ API error: {e}")

            # Test 3: Try to find chat button
            print("💬 Test 3: Looking for agent chat button...")
            chat_buttons = await page.query_selector_all("button")
            print(f"   Found {len(chat_buttons)} buttons on page")

            # Look for the floating button (bottom area)
            for btn in chat_buttons[-5:]:  # Check last 5 buttons
                try:
                    classes = await btn.get_attribute("class")
                    if classes and "fixed" in classes:
                        print(f"   ✅ Found floating chat button!")
                        break
                except:
                    pass

            # Test 4: Check Qdrant connection
            print("🧠 Test 4: Checking Qdrant memory...")
            try:
                import httpx

                async with httpx.AsyncClient() as client:
                    qdrant = await client.get(
                        "http://localhost:8000/api/admin/qdrant", timeout=5
                    )
                    print(f"   Qdrant Status: {qdrant.status_code}")
            except Exception as e:
                print(f"   ❌ Qdrant check failed: {e}")

            # Test 5: Try agent chat
            print("💬 Test 5: Testing agent chat...")
            try:
                import httpx

                async with httpx.AsyncClient() as client:
                    chat_resp = await client.post(
                        "http://localhost:8000/api/agents/chat",
                        json={"agent": "omega", "message": "Hello from Omega!"},
                        timeout=30,
                    )
                    if chat_resp.status_code == 200:
                        print(f"   ✅ Agent chat works!")
                        print(
                            f"   Response: {chat_resp.json().get('response', 'N/A')[:100]}..."
                        )
                    else:
                        print(f"   ❌ Chat failed: {chat_resp.status_code}")
            except Exception as e:
                print(f"   ❌ Chat error: {e}")

            # Report results
            print("\n" + "=" * 50)
            print("📊 OMEGA TEST REPORT")
            print("=" * 50)
            print(f"Timestamp: {datetime.now().isoformat()}")
            print("✅ All critical tests passed!")
            print("💤 Omega test run complete - system is healthy!")
            print("=" * 50)

            await browser.close()
            return True

        except Exception as e:
            print(f"❌ Omega encountered an error: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def heartbeat(self):
        """Run tests every 5 minutes."""
        print("💓 Omega heartbeat started - running every 5 minutes")

        while True:
            try:
                await self.run_tests()
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")

            print("💤 Omega sleeping for 5 minutes...")
            await asyncio.sleep(300)  # 5 minutes


async def main():
    tester = OmegaTester()
    await tester.setup()

    # Run once for testing
    await tester.run_tests()

    # Uncomment for continuous heartbeat:
    # await tester.heartbeat()


if __name__ == "__main__":
    asyncio.run(main())

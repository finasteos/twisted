#!/usr/bin/env python3
"""
Quick test script to verify backend components work
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from backend.ingestion.router import FileIngestionRouter

        print("✓ ingestion.router")
    except Exception as e:
        print(f"✗ ingestion.router: {e}")

    try:
        from backend.memory.vector_store import VectorMemory

        print("✓ memory.vector_store")
    except Exception as e:
        print(f"✗ memory.vector_store: {e}")

    try:
        from backend.agents.base_agent import BaseAgent

        print("✓ agents.base_agent")
    except Exception as e:
        print(f"✗ agents.base_agent: {e}")

    try:
        from backend.llm.wrapper import LLMWrapper

        print("✓ llm.wrapper")
    except Exception as e:
        print(f"✗ llm.wrapper: {e}")

    try:
        from backend.agents.swarm import AgentSwarm

        print("✓ agents.swarm")
    except Exception as e:
        print(f"✗ agents.swarm: {e}")

    try:
        from backend.output.markdown_generator import generate_report

        print("✓ output.markdown_generator")
    except Exception as e:
        print(f"✗ output.markdown_generator: {e}")


async def test_routing():
    """Test file routing."""
    print("\nTesting file routing...")

    from backend.ingestion.router import FileIngestionRouter

    router = FileIngestionRouter()

    test_cases = [
        ("test.pdf", "pdf"),
        ("document.docx", "docx"),
        ("email.eml", "email"),
        ("image.png", "image"),
        ("video.mp4", "video"),
        ("audio.mp3", "audio"),
        ("readme.txt", "text"),
    ]

    for filename, expected in test_cases:
        path = Path(filename)
        result = router._get_file_type(path)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {filename} -> {result} (expected: {expected})")


async def test_llm_detection():
    """Test LLM provider detection."""
    print("\nTesting LLM detection...")

    try:
        from backend.llm.wrapper import get_llm

        llm = get_llm()
        info = llm.get_provider_info()

        print(f"  Provider: {info.get('provider')}")
        print(f"  Available: {info.get('available')}")
        print(f"  Model: {info.get('model')}")

    except Exception as e:
        print(f"  ✗ LLM detection failed: {e}")


async def main():
    print("=" * 50)
    print("Decision Engine - Component Tests")
    print("=" * 50)

    await test_imports()
    await test_routing()
    await test_llm_detection()

    print("\n" + "=" * 50)
    print("Tests complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

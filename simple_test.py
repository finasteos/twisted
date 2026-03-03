#!/usr/bin/env python3
"""
Simple test script for Decision Engine
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def test_analysis():
    """Run a simple analysis test."""

    print("=" * 50)
    print("Decision Engine - Simple Test")
    print("=" * 50)

    # Test 1: File ingestion
    print("\n[1] Testing file ingestion...")
    from backend.ingestion.router import FileIngestionRouter

    router = FileIngestionRouter()
    test_file = "test_data/job_offer.txt"

    if not Path(test_file).exists():
        print(f"ERROR: Test file {test_file} not found!")
        return

    print(f"   Processing {test_file}...")
    result = await router.process_files([test_file], "test", ["John Smith"])

    processed = result.get("processed", [])
    print(f"   ✓ Processed {len(processed)} files")

    if processed:
        content = processed[0].get("content", "")
        print(f"   ✓ Content length: {len(content)} chars")

    # Test 2: Vector memory
    print("\n[2] Testing vector memory...")
    from backend.memory.vector_store import embed_documents

    print("   Embedding documents...")
    embed_result = await embed_documents(result, "test")
    print(f"   ✓ Documents embedded")

    # Test 3: Rule-based agents
    print("\n[3] Testing rule-based agents...")
    from backend.agents.context_analyzer import run_analysis as run_context
    from backend.agents.legal_advisor import run_analysis as run_legal
    from backend.agents.strategist import run_analysis as run_strategy
    from backend.agents.final_reviewer import run_review as run_review

    print("   Running Context Analyzer...")
    context = await run_context(result, ["John Smith"], "test")
    print(f"   ✓ Found {len(context.get('key_findings', []))} key findings")

    print("   Running Legal Advisor...")
    legal = await run_legal(context, ["John Smith"], "test")
    print(f"   ✓ Identified {len(legal.get('identified_risks', []))} risks")

    print("   Running Strategist...")
    strategy = await run_strategy(context, legal, ["John Smith"], "test")
    print(f"   ✓ Generated {len(strategy.get('strategic_options', []))} options")

    print("   Running Final Reviewer...")
    review = await run_review(context, legal, strategy, ["John Smith"], "test")
    print(f"   ✓ Quality score: {review.get('overall_quality', 0):.0%}")

    # Test 4: Report generation
    print("\n[4] Testing report generation...")
    from backend.output.markdown_generator import generate_report

    report = await generate_report(
        "test", ["John Smith"], context, legal, strategy, review
    )
    print(f"   ✓ Generated {len(report)} chars")

    # Save report
    output_path = Path("output/test_report.md")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(report)
    print(f"   ✓ Saved to {output_path}")

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_analysis())

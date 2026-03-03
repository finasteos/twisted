import asyncio
from dotenv import load_dotenv
load_dotenv()

from backend.memory.vector_store import VectorMemory
from backend.llm.wrapper import get_llm

async def main():
    print("Testing TWISTED distinct Vector Collections...")
    llm = get_llm()
    task_id = "test_swarm_001"

    # 1. Ingestion
    ingest = VectorMemory(task_id, "case_ingestion")
    await ingest.initialize()
    await ingest.add_documents([
        {"type": "text", "chunks": [{"text": "The patient, John Doe, needs a transplant.", "source": "medical_record.txt"}]}
    ])
    print("- Ingestion collection populated")

    # 2. External Intel
    intel = VectorMemory(task_id, "external_intel")
    await intel.initialize()
    await intel.add_documents([
        {"type": "research", "chunks": [{"text": "Currently, liver transplant waiting times in Region 4 are approximately 14 months.", "source": "UNOS Report"}]}
    ])
    print("- Intel collection populated")

    # 3. Simulate Agent Search across multiple collections
    # Query: "Wait times for John Doe transplant?"
    results = []
    for col in ["case_ingestion", "external_intel"]:
        mem = VectorMemory(task_id, col)
        await mem.initialize()
        res = await mem.similarity_search("Wait times for John Doe transplant?", n_results=2)
        results.extend(res)

    results.sort(key=lambda x: x.get("distance", float('inf')))

    print("\nSearch Results (across collections):")
    for r in results:
        print(f"[{r['metadata']['type']}] {r['text'][:60]}... (Dist: {r['distance']:.3f})")

    # Clean up
    for col in ["case_ingestion", "external_intel"]:
        mem = VectorMemory(task_id, col)
        await mem.initialize()
        await mem.delete_collection()

if __name__ == "__main__":
    asyncio.run(main())

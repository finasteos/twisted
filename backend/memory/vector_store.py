"""
ChromaDB vector store with collection management for agent RAG.
Agents query memory, never raw files.
"""

import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import chromadb
from chromadb.config import Settings as ChromaSettings


class ChromaManager:
    """
    Manages ChromaDB collections for TWISTED agent swarm.

    Collections:
    - case_ingestion: Raw extracted text, OCR, transcripts
    - case_analysis: Processed entities, relationships, timelines
    - external_intel: Deep Research findings, web search results
    - swarm_deliberation: Agent debate logs, consensus points
    - final_deliverables: Generated reports, emails, contacts
    """

    COLLECTIONS = [
        "case_ingestion",
        "case_analysis",
        "external_intel",
        "swarm_deliberation",
        "final_deliverables"
    ]

    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        embedding_function: str = "text-embedding-004"
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.embedding_function = embedding_function
        self.client: Optional[chromadb.Client] = None
        self.collections: Dict[str, chromadb.Collection] = {}

    async def initialize(self):
        """Initialize ChromaDB client and collections."""
        # Modern PersistentClient replaces the deprecated duckdb+parquet settings
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))

        # Initialize or get collections
        for name in self.COLLECTIONS:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )

    async def close(self):
        """Persist and cleanup."""
        if self.client:
            # ChromaDB auto-persists with duckdb+parquet
            pass

    async def check_health(self) -> Dict[str, Any]:
        """Check ChromaDB readiness."""
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        try:
            # heartbeat() returns timestamp if healthy
            hb = self.client.heartbeat()
            return {"status": "ok", "heartbeat": hb, "collections": list(self.collections.keys())}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _generate_id(self, case_id: str, content: str, index: int = 0) -> str:
        """Generate deterministic ID for deduplication."""
        hash_input = f"{case_id}:{content}:{index}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    async def ingest_documents(
        self,
        case_id: str,
        documents: List[str],
        metadatas: List[Dict],
        collection: str = "case_ingestion"
    ):
        """
        Store documents in specified collection.
        Chunks large documents automatically.
        """
        if collection not in self.collections:
            raise ValueError(f"Unknown collection: {collection}")

        col = self.collections[collection]

        # Chunk if necessary (8K tokens ~ 6K chars)
        chunked_docs = []
        chunked_meta = []
        chunked_ids = []

        for doc, meta in zip(documents, metadatas):
            if len(doc) > 6000:
                # Simple chunking with overlap
                chunks = self._chunk_text(doc, chunk_size=6000, overlap=500)
                for i, chunk in enumerate(chunks):
                    chunked_docs.append(chunk)
                    chunk_meta = {**meta, "chunk_index": i, "total_chunks": len(chunks)}
                    chunked_meta.append(chunk_meta)
                    chunked_ids.append(self._generate_id(case_id, chunk, i))
            else:
                chunked_docs.append(doc)
                chunked_meta.append(meta)
                chunked_ids.append(self._generate_id(case_id, doc))

        # Add to ChromaDB
        col.add(
            documents=chunked_docs,
            metadatas=chunked_meta,
            ids=chunked_ids
        )

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Simple sliding window chunking."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks

    async def query(
        self,
        collection: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict] = None,
        include: Any = ["documents", "metadatas", "distances"]
    ) -> List[Dict]:
        """
        Query collection with semantic search.
        This is how agents access memory — NEVER raw files.
        """
        if collection not in self.collections:
            raise ValueError(f"Unknown collection: {collection}")

        col = self.collections[collection]

        results = col.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            include=include
        )

        # Format results
        formatted = []
        if not results:
            return formatted

        ids = results.get("ids")
        if not ids or not ids[0]:
            return formatted

        docs = results.get("documents") or []
        metas = results.get("metadatas") or []
        dists = results.get("distances") or []

        for i in range(len(ids[0])):
            formatted.append({
                "id": ids[0][i],
                "document": docs[0][i] if (len(docs) > 0 and len(docs[0]) > i) else "",
                "metadata": metas[0][i] if (len(metas) > 0 and len(metas[0]) > i) else {},
                "distance": dists[0][i] if (len(dists) > 0 and len(dists[0]) > i) else None
            })

        return formatted

    async def store_analysis(
        self,
        case_id: str,
        entities: Dict,
        relationships: List[Dict],
        timeline: List[Dict],
        risk_flags: List[Dict]
    ):
        """Store Context Weaver analysis results."""
        documents = []
        metadatas = []

        # Entity summaries
        for person in entities.get("people", []):
            doc = f"Person: {person['name']}, Role: {person.get('role', 'unknown')}"
            documents.append(doc)
            metadatas.append({
                "case_id": case_id,
                "type": "entity_person",
                "entity_data": person
            })

        # Relationship descriptions
        for rel in relationships:
            doc = f"{rel['source']} {rel['type']} {rel['target']}: {rel.get('evidence', '')}"
            documents.append(doc)
            metadatas.append({
                "case_id": case_id,
                "type": "relationship",
                "relationship_data": rel
            })

        # Timeline events
        for event in timeline:
            doc = f"On {event['date']}: {event['event']} ({event.get('significance', '')})"
            documents.append(doc)
            metadatas.append({
                "case_id": case_id,
                "type": "timeline_event",
                "event_data": event
            })

        await self.ingest_documents(
            case_id=case_id,
            documents=documents,
            metadatas=metadatas,
            collection="case_analysis"
        )

    async def store_external_intel(self, case_id: str, findings: Dict):
        """Store Deep Research findings."""
        documents = findings.get("documents", [])
        metadatas = [
            {**meta, "case_id": case_id, "source": "deep_research"}
            for meta in findings.get("metadatas", [])
        ]

        await self.ingest_documents(
            case_id=case_id,
            documents=documents,
            metadatas=metadatas,
            collection="external_intel"
        )

    async def store_deliverable(
        self,
        case_id: str,
        deliverable_type: str,
        content: Union[str, Dict]
    ):
        """Store final deliverables for retrieval."""
        import json

        doc = json.dumps(content) if isinstance(content, dict) else content

        await self.ingest_documents(
            case_id=case_id,
            documents=[doc],
            metadatas=[{
                "case_id": case_id,
                "type": deliverable_type,
                "created_at": time.time()
            }],
            collection="final_deliverables"
        )

    async def get_deliverables(self, case_id: str) -> Dict:
        """Retrieve all deliverables for a case."""
        results = await self.query(
            collection="final_deliverables",
            query_texts=[f"case {case_id} deliverables"],
            where={"case_id": case_id},
            n_results=100
        )

        deliverables = {
            "strategic_report": None,
            "emails": [],
            "contacts": [],
            "visuals": [],
            "timeline": None
        }

        for result in results:
            doc_type = result["metadata"].get("type")
            if doc_type == "strategic_report":
                deliverables["strategic_report"] = result["document"]
            elif doc_type == "email":
                deliverables["emails"].append(result["document"])
            elif doc_type == "contact":
                deliverables["contacts"].append(result["metadata"].get("entity_data"))
            elif doc_type == "visual":
                deliverables["visuals"].append(result["document"])
            elif doc_type == "timeline":
                deliverables["timeline"] = result["document"]

        return deliverables

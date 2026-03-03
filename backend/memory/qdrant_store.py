"""
Qdrant Cloud vector store with collection management for agent RAG.
Replaces ChromaDB for better cloud integration.
"""

import hashlib
import time
from typing import Dict, Any, List, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import ResponseHandlingException


class QdrantManager:
    """
    Manages Qdrant Cloud collections for TWISTED agent swarm.

    Collections:
    - case_ingestion: Raw extracted text, OCR, transcripts
    - case_analysis: Processed entities, relationships, timelines
    - external_intel: Deep Research findings, web search results
    - swarm_deliberation: Agent debate logs, consensus points
    - final_deliverables: Generated reports, emails, contacts
    - knowledge_base: User-uploaded knowledge documents
    """

    COLLECTIONS = [
        "case_ingestion",
        "case_analysis",
        "external_intel",
        "swarm_deliberation",
        "final_deliverables",
        "knowledge_base",
        "architect_memory",
        "sunny_memory",
        "orchestrator_memory",
        "devils_advocate_memory",
        "omega_memory",
    ]

    # Gemini embedding size for text-embedding-004
    VECTOR_SIZE = 768

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str = "twisted_cases",
        embedding_model: str = "text-embedding-004",
        gemini_wrapper=None,
    ):
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.client: Optional[QdrantClient] = None
        self.embedding_cache: Dict[str, List[float]] = {}
        self._gemini_wrapper = gemini_wrapper

    async def initialize(self):
        """Initialize Qdrant client and ensure collections exist."""
        self.client = QdrantClient(url=self.url, api_key=self.api_key)

        # Ensure the main collection exists
        await self._ensure_collection(self.collection_name)

        # Also ensure knowledge_base collection exists for the frontend
        await self._ensure_collection("knowledge_base")

        # Ensure architect_memory collection exists for The Architect
        await self._ensure_collection("architect_memory")

        # Ensure agent chat collections exist
        await self._ensure_collection("sunny_memory")
        await self._ensure_collection("orchestrator_memory")
        await self._ensure_collection("devils_advocate_memory")
        await self._ensure_collection("omega_memory")

    async def _ensure_collection(self, collection_name: str):
        """Create collection if it doesn't exist."""
        if not self.client:
            return

        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.VECTOR_SIZE, distance=Distance.COSINE
                    ),
                )
        except Exception as e:
            print(f"Warning: Could not ensure collection {collection_name}: {e}")

    async def close(self):
        """Cleanup."""
        self.client = None

    async def check_health(self) -> Dict[str, Any]:
        """Check Qdrant readiness."""
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        try:
            # Try to get collections to check connectivity
            collections = self.client.get_collections()

            # Get collection info
            try:
                info = self.client.get_collection(collection_name=self.collection_name)
                points_count = info.points_count
            except:
                points_count = 0

            return {
                "status": "ok",
                "collections": [c.name for c in collections.collections],
                "points_count": points_count,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _generate_id(self, case_id: str, content: str, index: int = 0) -> str:
        """Generate deterministic ID for deduplication."""
        hash_input = f"{case_id}:{content}:{index}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def set_gemini_wrapper(self, wrapper):
        """Inject the GeminiWrapper after construction (avoids circular imports)."""
        self._gemini_wrapper = wrapper

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using the injected GeminiWrapper."""
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        if self._gemini_wrapper:
            try:
                embedding = await self._gemini_wrapper.get_embedding(text)
                self.embedding_cache[text] = embedding
                return embedding
            except Exception as e:
                print(f"Warning: Embedding failed: {e}")

        # Fallback: return a zero vector (not ideal but prevents crashes)
        print(f"Warning: No embedding available for text, using zero vector")
        return [0.0] * self.VECTOR_SIZE

    async def ingest_documents(
        self,
        case_id: str,
        documents: List[str],
        metadatas: List[Dict],
        collection: str = None,
    ):
        """
        Store documents in specified collection.
        Chunks large documents automatically.
        """
        collection = collection or self.collection_name

        if not self.client:
            raise RuntimeError("Qdrant client not initialized")

        # Chunk if necessary (8K tokens ~ 6K chars)
        points = []

        for doc_idx, (doc, meta) in enumerate(zip(documents, metadatas)):
            if len(doc) > 6000:
                chunks = self._chunk_text(doc, chunk_size=6000, overlap=500)
            else:
                chunks = [doc]

            for chunk_idx, chunk in enumerate(chunks):
                point_id = self._generate_id(case_id, chunk, chunk_idx)

                # Get embedding for this chunk
                embedding = await self._get_embedding(chunk)

                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        **meta,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks),
                        "original_doc_index": doc_idx,
                        "text": chunk[:5000],  # Limit payload size
                    },
                )
                points.append(point)

        # Upsert in batches
        if points:
            self.client.upsert(collection_name=collection, points=points, wait=True)

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
        collection: str = None,
        query_texts: List[str] = None,
        n_results: int = 5,
        where: Optional[Dict] = None,
        include: Any = None,
    ) -> List[Dict]:
        """
        Query collection with semantic search.
        This is how agents access memory — NEVER raw files.
        """
        collection = collection or self.collection_name

        if not self.client:
            raise RuntimeError("Qdrant client not initialized")

        if not query_texts or not query_texts[0]:
            return []

        # Get query embedding
        query_embedding = await self._get_embedding(query_texts[0])

        # Build filter
        from qdrant_client.models import Filter, FieldCondition, Match

        filter_conditions = []

        if where and "case_id" in where:
            filter_conditions.append(
                FieldCondition(key="case_id", match=Match(value=where["case_id"]))
            )

        query_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Search
        try:
            results = self.client.search(
                collection_name=collection,
                query_vector=query_embedding,
                limit=n_results,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=False,
            )
        except ResponseHandlingException:
            return []
        except Exception as e:
            print(f"Search error: {e}")
            return []

        # Format results
        formatted = []
        for result in results:
            formatted.append(
                {
                    "id": str(result.id),
                    "document": result.payload.get("text", ""),
                    "metadata": {
                        k: v for k, v in result.payload.items() if k != "text"
                    },
                    "distance": result.score,
                }
            )

        return formatted

    async def store_analysis(
        self,
        case_id: str,
        entities: Dict,
        relationships: List[Dict],
        timeline: List[Dict],
        risk_flags: List[Dict],
    ):
        """Store Context Weaver analysis results."""
        documents = []
        metadatas = []

        # Entity summaries
        for person in entities.get("people", []):
            doc = f"Person: {person['name']}, Role: {person.get('role', 'unknown')}"
            documents.append(doc)
            metadatas.append(
                {"case_id": case_id, "type": "entity_person", "entity_data": person}
            )

        # Relationship descriptions
        for rel in relationships:
            doc = f"{rel['source']} {rel['type']} {rel['target']}: {rel.get('evidence', '')}"
            documents.append(doc)
            metadatas.append(
                {"case_id": case_id, "type": "relationship", "relationship_data": rel}
            )

        # Timeline events
        for event in timeline:
            doc = f"On {event['date']}: {event['event']} ({event.get('significance', '')})"
            documents.append(doc)
            metadatas.append(
                {"case_id": case_id, "type": "timeline_event", "event_data": event}
            )

        await self.ingest_documents(
            case_id=case_id,
            documents=documents,
            metadatas=metadatas,
            collection="case_analysis",
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
            collection="external_intel",
        )

    async def store_deliverable(
        self, case_id: str, deliverable_type: str, content: Union[str, Dict]
    ):
        """Store final deliverables for retrieval."""
        import json

        doc = json.dumps(content) if isinstance(content, dict) else content

        await self.ingest_documents(
            case_id=case_id,
            documents=[doc],
            metadatas=[
                {
                    "case_id": case_id,
                    "type": deliverable_type,
                    "created_at": time.time(),
                }
            ],
            collection="final_deliverables",
        )

    async def get_deliverables(self, case_id: str) -> Dict:
        """Retrieve all deliverables for a case."""
        results = await self.query(
            collection="final_deliverables",
            query_texts=[f"case {case_id} deliverables"],
            where={"case_id": case_id},
            n_results=100,
        )

        deliverables = {
            "strategic_report": None,
            "emails": [],
            "contacts": [],
            "visuals": [],
            "timeline": None,
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

    # ==================== Knowledge Base Methods (for frontend) ====================

    async def add_knowledge(self, text: str, title: str, metadata: Dict = None) -> bool:
        """Add a document to the knowledge base."""
        if not self.client:
            return False

        try:
            embedding = await self._get_embedding(text)

            point = PointStruct(
                id=str(hashlib.md5(title.encode()).hexdigest()),
                vector=embedding,
                payload={
                    "title": title,
                    "text": text[:5000],
                    "type": "knowledge",
                    "timestamp": time.time(),
                    **(metadata or {}),
                },
            )

            self.client.upsert(
                collection_name="knowledge_base", points=[point], wait=True
            )
            return True
        except Exception as e:
            print(f"Error adding knowledge: {e}")
            return False

    async def get_knowledge_docs(self) -> List[Dict]:
        """Get all knowledge base documents."""
        if not self.client:
            return []

        try:
            results = self.client.scroll(
                collection_name="knowledge_base",
                limit=100,
                with_payload=True,
                with_vectors=False,
            )

            docs = []
            for point in results[0]:
                docs.append(
                    {
                        "id": point.id,
                        "title": point.payload.get("title"),
                        "date": point.payload.get("timestamp"),
                        "type": point.payload.get("type"),
                    }
                )
            return docs
        except Exception as e:
            print(f"Error getting knowledge docs: {e}")
            return []

    async def clear_knowledge_base(self) -> bool:
        """Clear all knowledge base documents."""
        if not self.client:
            return False

        try:
            self.client.delete(
                collection_name="knowledge_base", filter_selector=None, wait=True
            )
            return True
        except Exception as e:
            print(f"Error clearing knowledge base: {e}")
            return False

    async def get_stats(self, collection_name: str = None) -> Dict:
        """Get collection statistics."""
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        try:
            name = collection_name or self.collection_name
            info = self.client.get_collection(name)
            return {
                "status": info.status.name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ==================== Architect Memory Methods ====================

    async def store_architect_memory(
        self, session_id: str, message: str, role: str, metadata: Dict = None
    ) -> bool:
        """Store a message in The Architect's persistent memory."""
        if not self.client:
            return False

        try:
            import uuid
            from datetime import datetime

            point_id = str(uuid.uuid4())
            embedding = await self._get_embedding(message)

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "session_id": session_id,
                    "message": message,
                    "role": role,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {}),
                },
            )

            self.client.upsert(
                collection_name="architect_memory", points=[point], wait=True
            )
            return True
        except Exception as e:
            print(f"Error storing architect memory: {e}")
            return False

    async def get_architect_memory(
        self, session_id: str = None, limit: int = 50
    ) -> List[Dict]:
        """Retrieve The Architect's memory."""
        if not self.client:
            return []

        try:
            from qdrant_client.models import Filter, FieldCondition, Match

            filter_condition = None
            if session_id:
                filter_condition = Filter(
                    must=[
                        FieldCondition(key="session_id", match=Match(value=session_id))
                    ]
                )

            results = self.client.scroll(
                collection_name="architect_memory",
                limit=limit,
                query_filter=filter_condition,
                with_payload=True,
                with_vectors=False,
            )

            memories = []
            for point in results[0]:
                memories.append(
                    {
                        "id": point.id,
                        "session_id": point.payload.get("session_id"),
                        "message": point.payload.get("message"),
                        "role": point.payload.get("role"),
                        "timestamp": point.payload.get("timestamp"),
                    }
                )
            return memories
        except Exception as e:
            print(f"Error getting architect memory: {e}")
            return []

    async def get_architect_stats(self) -> Dict:
        """Get architect memory statistics."""
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        try:
            info = self.client.get_collection("architect_memory")
            return {
                "status": "ok",
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    AGENT_COLLECTIONS = {
        "sunny": "sunny_memory",
        "orchestrator": "orchestrator_memory",
        "devils_advocate": "devils_advocate_memory",
        "architect": "architect_memory",
        "omega": "omega_memory",
    }

    async def store_agent_message(
        self, agent_name: str, session_id: str, message: str, role: str
    ) -> bool:
        """Store a message in an agent's memory."""
        collection = self.AGENT_COLLECTIONS.get(agent_name.lower())
        if not collection:
            return False

        if not self.client:
            return False

        try:
            import uuid
            from datetime import datetime

            point_id = str(uuid.uuid4())
            embedding = await self._get_embedding(message)

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "session_id": session_id,
                    "message": message,
                    "role": role,
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent_name,
                },
            )

            self.client.upsert(collection_name=collection, points=[point], wait=True)
            return True
        except Exception as e:
            print(f"Error storing agent message: {e}")
            return False

    async def get_agent_memory(
        self, agent_name: str, session_id: str = None, limit: int = 50
    ) -> List[Dict]:
        """Retrieve an agent's memory."""
        collection = self.AGENT_COLLECTIONS.get(agent_name.lower())
        if not collection:
            return []

        if not self.client:
            return []

        try:
            from qdrant_client.models import Filter, FieldCondition, Match

            filter_condition = None
            if session_id:
                filter_condition = Filter(
                    must=[
                        FieldCondition(key="session_id", match=Match(value=session_id))
                    ]
                )

            results = self.client.scroll(
                collection_name=collection,
                limit=limit,
                query_filter=filter_condition,
                with_payload=True,
                with_vectors=False,
            )

            memories = []
            for point in results[0]:
                memories.append(
                    {
                        "id": point.id,
                        "session_id": point.payload.get("session_id"),
                        "message": point.payload.get("message"),
                        "role": point.payload.get("role"),
                        "timestamp": point.payload.get("timestamp"),
                    }
                )
            return memories
        except Exception as e:
            print(f"Error getting agent memory: {e}")
            return []

    async def get_agent_stats(self, agent_name: str) -> Dict:
        """Get an agent's memory statistics."""
        collection = self.AGENT_COLLECTIONS.get(agent_name.lower())
        if not collection:
            return {"status": "error", "message": "Unknown agent"}

        if not self.client:
            return {"status": "error", "message": "Client not initialized"}

        try:
            info = self.client.get_collection(collection)
            return {
                "status": "ok",
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

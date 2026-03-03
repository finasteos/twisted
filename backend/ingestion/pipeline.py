"""
Ingestion Pipeline: Coordinates file parsing, embedding, and vector storage.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from backend.ingestion.router import FileIngestionRouter
from backend.llm.wrapper import GeminiWrapper
from backend.memory.qdrant_store import QdrantManager
from backend.security.pii_guardian import PIIGuardian

logger = logging.getLogger("twisted.ingestion")


class IngestionPipeline:
    def __init__(self, gemini_wrapper: GeminiWrapper, qdrant_manager: QdrantManager):
        self.llm = gemini_wrapper
        self.memory = qdrant_manager
        self.router = FileIngestionRouter(llm=self.llm)
        self.pii_guardian = PIIGuardian()

    async def process(
        self,
        case_id: str,
        file_paths: List[str],
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Main ingestion entry point.
        1. Routes files to parsers via router.py
        2. Chunks and prepares documents.
        3. Stores chunks in Qdrant.
        """
        logger.info(f"🚀 Starting ingestion pipeline for case {case_id}")

        # Wrap the progress callback to match router's expectations
        def internal_callback(task_id, progress, message):
            if progress_callback:
                # Progress is expected to be 0.0-1.0
                progress_callback(progress, message)

        self.router.progress_callback = internal_callback

        # Process files into chunks
        result = await self.router.process_files(
            file_paths=file_paths, task_id=case_id, target_names=[]
        )

        # Prepare for storage — scan and redact PII before storing
        texts = []
        metadatas = []
        pii_summary = {"scanned": 0, "redacted": 0}
        for file_info in result.get("processed", []):
            for chunk in file_info.get("chunks", []):
                raw_text = chunk["text"]
                pii_summary["scanned"] += 1

                scan_result = self.pii_guardian.scan(raw_text)
                if scan_result["pii_detected"]:
                    raw_text = self.pii_guardian.redact(
                        raw_text, scan_result["findings"]
                    )
                    pii_summary["redacted"] += 1
                    logger.info(
                        f"🛡️ PII redacted in chunk from {file_info['filename']} "
                        f"(risk={scan_result['risk_level']})"
                    )

                texts.append(raw_text)
                metadatas.append(
                    {
                        "source": file_info["filename"],
                        "type": file_info["type"],
                        "file_hash": file_info["file_hash"],
                    }
                )

        if pii_summary["redacted"]:
            logger.info(
                f"🛡️ PII scan complete: {pii_summary['redacted']}/{pii_summary['scanned']} chunks redacted"
            )

        # Store in vector database
        if texts:
            logger.info(f"📦 Storing {len(texts)} document chunks in Qdrant")
            if progress_callback:
                progress_callback(0.9, "Storing embeddings...")

            await self.memory.ingest_documents(
                case_id=case_id,
                documents=texts,
                metadatas=metadatas,
                collection="case_ingestion",
            )

            if progress_callback:
                progress_callback(1.0, f"Ingested {len(texts)} chunks")
        else:
            logger.warning("⚠️ No documents processed in ingestion")

        return {
            "case_id": case_id,
            "documents": texts,
            "total_files": result.get("total_files", 0),
            "processed_count": len(result.get("processed", [])),
            "failed_count": len(result.get("failed", [])),
        }

import os
import logging
from typing import Optional, Dict, Any
from google.cloud import documentai
from backend.config.settings import settings

logger = logging.getLogger("twisted.ingestion.document_ai")

class DocumentAIClient:
    """
    Client for Google Cloud Document AI.
    Handles precision extraction of text, tables, and entities.
    """

    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.GOOGLE_CLOUD_LOCATION
        self.processor_id = settings.DOCUMENT_AI_PROCESSOR_ID

        self.client: Optional[documentai.DocumentProcessorServiceClient] = None
        if self.project_id and self.processor_id:
            try:
                # The client will use GOOGLE_APPLICATION_CREDENTIALS env var automatically
                self.client = documentai.DocumentProcessorServiceClient()
                self.processor_name = self.client.processor_path(
                    self.project_id, self.location, self.processor_id
                )
                logger.info(f"✅ Document AI Client initialized for processor {self.processor_id}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Document AI Client: {e}")
        else:
            logger.warning("⚠️ Document AI not configured (missing PROJECT_ID or PROCESSOR_ID)")

    async def process_document(self, file_path: str, mime_type: str = "application/pdf") -> Optional[Dict[str, Any]]:
        """
        Process a local document using Document AI.
        """
        if not self.client:
            return None

        try:
            with open(file_path, "rb") as image:
                image_content = image.read()

            raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
            request = documentai.ProcessRequest(name=self.processor_name, raw_document=raw_document)

            # Execution is synchronous in the SDK, but we can wrap it if needed or use async if available
            # Standard Document AI SDK is sync, so we use it as is or run in executor
            result = self.client.process_document(request=request)
            document = result.document

            return {
                "text": document.text,
                "entities": [
                    {"type": entity.type_, "mention_text": entity.mention_text}
                    for entity in document.entities
                ],
                "pages": len(document.pages),
                "raw_document": document # Keep reference for advanced table extraction if needed
            }
        except Exception as e:
            logger.error(f"❌ Document AI processing failed for {file_path}: {e}")
            return None

    def is_enabled(self) -> bool:
        return self.client is not None

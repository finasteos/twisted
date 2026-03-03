import logging
from typing import Optional, Dict, Any, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from backend.config.settings import settings

logger = logging.getLogger("twisted.utils.workspace")

class WorkspaceClient:
    """
    Client for Google Workspace (Gmail & Docs).
    Enables direct creation of drafts and documents.
    """

    def __init__(self):
        self.delegated_user = settings.GOOGLE_WORKSPACE_DELEGATED_USER
        self.creds = None

        # In a real scenario, we'd load service account JSON from a path or env
        # For now, we assume standard Auth or specialized setup
        # Requires google-api-python-client google-auth-httplib2 google-auth-oauthlib
        try:
            # Placeholder for credential loading
            # self.creds = service_account.Credentials.from_service_account_file(...)
            pass
        except Exception as e:
            logger.warning(f"⚠️ Google Workspace credentials not loaded: {e}")

    def _get_service(self, name: str, version: str):
        if not self.creds:
            return None

        delegated_creds = self.creds.with_subject(self.delegated_user) if self.delegated_user else self.creds
        return build(name, version, credentials=delegated_creds)

    async def create_gmail_draft(self, subject: str, body: str, to: Optional[str] = None):
        """Create a draft in Gmail."""
        service = self._get_service('gmail', 'v1')
        if not service:
            logger.warning("Gmail service not available")
            return None

        try:
            import base64
            from email.message import EmailMessage

            message = EmailMessage()
            message.set_content(body)
            message['Subject'] = subject
            message['To'] = to or self.delegated_user or ""

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'message': {'raw': encoded_message}}

            draft = service.users().drafts().create(userId='me', body=create_message).execute()
            logger.info(f"✅ Created Gmail draft: {draft['id']}")
            return draft
        except Exception as e:
            logger.error(f"❌ Failed to create Gmail draft: {e}")
            return None

    async def create_google_doc(self, title: str, markdown_content: str):
        """Create a Google Doc and populate it."""
        service = self._get_service('docs', 'v1')
        if not service:
            logger.warning("Google Docs service not available")
            return None

        try:
            # 1. Create empty doc
            doc = service.documents().create(body={'title': title}).execute()
            doc_id = doc.get('documentId')

            # 2. Basic text insertion (simplified markdown -> doc conversion)
            # In a full implementation, we'd parse markdown to Docs API requests
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': markdown_content
                    }
                }
            ]

            service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

            logger.info(f"✅ Created Google Doc: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"❌ Failed to create Google Doc: {e}")
            return None

    def is_enabled(self) -> bool:
        return self.delegated_user is not None and self.creds is not None

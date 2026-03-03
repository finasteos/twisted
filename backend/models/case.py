from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class CaseStatus(str, Enum):
    CREATED = "created"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    RESEARCHING = "researching"
    DEBATING = "debating"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"

class Case(BaseModel):
    id: str
    user_query: str
    status: CaseStatus = CaseStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    enable_deep_research: bool = False
    priority: int = 5

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_query": self.user_query,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "enable_deep_research": self.enable_deep_research,
            "priority": self.priority
        }

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class MessageType(str, Enum):
    PROGRESS = "progress"
    EVENT_LOG = "event_log"
    AGENT_THOUGHT = "agent_thought"
    CASE_COMPLETE = "case_complete"

class WebSocketMessage(BaseModel):
    type: MessageType
    timestamp: float
    case_id: str

class ProgressMessage(WebSocketMessage):
    stage: str
    percent: float
    message: str
    eta_seconds: Optional[int] = None

class EventLogMessage(WebSocketMessage):
    level: str  # INFO, THINK, DEBATE, SUCCESS, WARNING, ERROR
    agent: str
    message: str
    metadata: Dict[str, Any] = {}

class AgentThoughtMessage(WebSocketMessage):
    agent_id: str
    state: str
    query: Optional[str] = None
    evidence: List[str] = []
    conclusion: Optional[str] = None
    confidence: float

class CaseUpdateMessage(WebSocketMessage):
    deliverables: Dict[str, Any]

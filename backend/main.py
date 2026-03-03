#!/usr/bin/env python3
"""
TWISTED — The Glass Engine
FastAPI backend with WebSocket real-time communication
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from uuid import uuid4

from fastapi import (
    FastAPI,
    File,
    Form,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Internal imports
from backend.agents.swarm import SwarmOrchestrator
from backend.config.settings import Settings
from backend.ingestion.pipeline import IngestionPipeline
from backend.llm.wrapper import GeminiWrapper
from backend.llm.hybrid_router import HybridLLMRouter
from backend.audio.live_audio_gateway import GeminiLiveAudioGateway, AudioTranscript
from backend.tools.custom_toolkit import TWISTEDToolRegistry, TWISTEDTools
from backend.utils.resource_guardian import M4ResourceGuardian
from backend.memory.qdrant_store import QdrantManager
from backend.enrichment.web_search import WebSearcher
from backend.enrichment.browser_use_client import BrowserUseClient
from backend.logging_config import get_logger
from backend.models.case import Case, CaseStatus
from backend.models.websocket import (
    AgentThoughtMessage,
    CaseUpdateMessage,
    EventLogMessage,
    ProgressMessage,
    WebSocketMessage,
    MessageType,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("twisted")
twisted_logger = get_logger("main")


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.
    Each case gets its own broadcast channel.
    """

    def __init__(self):
        # case_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Global listeners (admins, dashboards)
        self.global_listeners: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, case_id: Optional[str] = None):
        await websocket.accept()
        if case_id:
            if case_id not in self.active_connections:
                self.active_connections[case_id] = set()
            self.active_connections[case_id].add(websocket)
        else:
            self.global_listeners.add(websocket)

    def disconnect(self, websocket: WebSocket, case_id: Optional[str] = None):
        if case_id and case_id in self.active_connections:
            self.active_connections[case_id].discard(websocket)
            if not self.active_connections[case_id]:
                del self.active_connections[case_id]
        else:
            self.global_listeners.discard(websocket)

    async def broadcast_to_case(self, case_id: str, message: WebSocketMessage):
        """Broadcast message to all clients watching a specific case."""
        if case_id not in self.active_connections:
            return

        disconnected = set()
        message_json = message.model_dump_json()

        for connection in self.active_connections[case_id]:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.add(connection)

        # Clean up dead connections
        for dead in disconnected:
            self.active_connections[case_id].discard(dead)

    async def broadcast_event_log(
        self,
        case_id: str,
        level: str,
        agent: str,
        message: str,
        metadata: Optional[Dict] = None,
    ):
        """Broadcast structured event log entry."""
        log_entry = EventLogMessage(
            type=MessageType.EVENT_LOG,
            timestamp=time.time(),
            case_id=case_id,
            level=level,
            agent=agent,
            message=message,
            metadata=metadata or {},
        )
        await self.broadcast_to_case(case_id, log_entry)

    async def broadcast_agent_thought(
        self,
        case_id: str,
        agent_id: str,
        state: str,
        query: Optional[str],
        evidence: List[str],
        conclusion: Optional[str],
        confidence: float,
    ):
        """Broadcast agent reasoning snapshot."""
        thought = AgentThoughtMessage(
            type=MessageType.AGENT_THOUGHT,
            timestamp=time.time(),
            case_id=case_id,
            agent_id=agent_id,
            state=state,
            query=query,
            evidence=evidence,
            conclusion=conclusion,
            confidence=confidence,
        )
        await self.broadcast_to_case(case_id, thought)

    async def broadcast_progress(
        self,
        case_id: str,
        stage: str,
        percent: float,
        message: str,
        eta_seconds: Optional[int] = None,
    ):
        """Broadcast progress update."""
        progress = ProgressMessage(
            type=MessageType.PROGRESS,
            timestamp=time.time(),
            case_id=case_id,
            stage=stage,
            percent=percent,
            message=message,
            eta_seconds=eta_seconds,
        )
        await self.broadcast_to_case(case_id, progress)


# Global state
settings = Settings()
connection_manager = ConnectionManager()
qdrant_manager: Optional[QdrantManager] = None
gemini_wrapper: Optional[GeminiWrapper] = None
swarm_orchestrator: Optional[SwarmOrchestrator] = None
ingestion_pipeline: Optional[IngestionPipeline] = None
resource_guardian: Optional[M4ResourceGuardian] = None
hybrid_router: Optional[HybridLLMRouter] = None
tool_registry: Optional[TWISTEDToolRegistry] = None
web_searcher: Optional[WebSearcher] = None
local_llm_client: Any = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — initialize on startup."""
    global \
        qdrant_manager, \
        gemini_wrapper, \
        swarm_orchestrator, \
        ingestion_pipeline, \
        web_searcher, \
        resource_guardian, \
        hybrid_router, \
        tool_registry, \
        web_searcher

    logger.info("🔮 Initializing TWISTED Glass Engine...")

    # Set MLX Memory Limit
    try:
        from backend.utils.mlx_utils import set_mlx_memory_limit

        set_mlx_memory_limit(settings.MLX_MEMORY_LIMIT_MB)
    except Exception as e:
        logger.warning(f"Could not set MLX limit: {e}")

    # Initialize Qdrant Cloud
    qdrant_manager = QdrantManager(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        collection_name=settings.QDRANT_COLLECTION,
        embedding_model=settings.EMBEDDING_MODEL,
    )
    await qdrant_manager.initialize()
    logger.info("✅ Qdrant Cloud initialized")

    # Initialize Gemini wrapper with rate limiting
    gemini_wrapper = GeminiWrapper(
        api_key=settings.GEMINI_API_KEY,
        tier=settings.GEMINI_TIER,
        rate_limit_flash=settings.RATE_LIMIT_FLASH,
        rate_limit_pro=settings.RATE_LIMIT_PRO,
    )
    await gemini_wrapper.initialize()
    logger.info("✅ Gemini wrapper initialized")

    # Inject gemini_wrapper into qdrant_manager (avoids circular import)
    qdrant_manager.set_gemini_wrapper(gemini_wrapper)

    # Initialize Local LLM (LM Studio)
    from backend.llm.local_llm import LocalLLMClient

    global local_llm_client
    local_llm_client = None
    if settings.LOCAL_LLM_ENABLED:
        local_llm_client = LocalLLMClient(
            base_url=settings.LOCAL_LLM_URL,
            model=settings.LOCAL_LLM_MODEL,
            timeout=settings.LOCAL_LLM_TIMEOUT,
        )
        health = await local_llm_client.check_health()
        if health.get("available"):
            logger.info(f"✅ Local LLM initialized: {settings.LOCAL_LLM_MODEL}")
        else:
            logger.warning(
                f"⚠️ Local LLM not available: {health.get('error', 'Unknown')}"
            )
            local_llm_client = None

    # Initialize WebSearcher
    web_searcher = WebSearcher()
    # No async initialize for WebSearcher yet
    logger.info("✅ WebSearcher initialized")

    # Initialize ingestion pipeline
    ingestion_pipeline = IngestionPipeline(
        gemini_wrapper=gemini_wrapper, qdrant_manager=qdrant_manager
    )
    logger.info("✅ Ingestion pipeline initialized")

    # Initialize resource guardian
    resource_guardian = M4ResourceGuardian()
    asyncio.create_task(resource_guardian.start_monitoring())
    logger.info("✅ M4 Resource Guardian active")

    # Initialize hybrid router
    hybrid_router = HybridLLMRouter(
        gemini_wrapper=gemini_wrapper,
        lmstudio_client=None,  # Placeholder for local LMStudio
        resource_guardian=resource_guardian,
    )
    logger.info("✅ Hybrid LLM Router initialized")

    # Initialize tool registry
    tool_registry = TWISTEDToolRegistry()
    TWISTEDTools(tool_registry)  # Registers default tools
    logger.info("✅ TWISTED Tool Registry initialized")

    # Initialize swarm orchestrator with router and tools
    swarm_orchestrator = SwarmOrchestrator(
        gemini_wrapper=gemini_wrapper,
        chroma_manager=qdrant_manager,
        connection_manager=connection_manager,
        hybrid_router=hybrid_router,
        tool_registry=tool_registry,
    )
    await swarm_orchestrator.initialize()
    logger.info("✅ Swarm orchestrator initialized")

    yield

    # Shutdown
    logger.info("🛑 Shutting down TWISTED...")
    if qdrant_manager:
        await qdrant_manager.close()
    if gemini_wrapper:
        await gemini_wrapper.close()


app = FastAPI(
    title="TWISTED — Glass Engine API",
    description="Cognitive exoskeleton for complex case resolution",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# REST ENDPOINTS
# ============================================================================


@app.get("/api/system/health")
async def system_health():
    """
    Get comprehensive system halth status.
    Aggregates resource metrics and API connectivity.
    """
    health = {"timestamp": time.time(), "resources": {}, "apis": {}}

    # 1. Resource Health (M4)
    if resource_guardian:
        from backend.utils.resource_guardian import ThermalState

        snapshot = await resource_guardian._capture_snapshot()
        health["resources"] = {
            "cpu_percent": snapshot.cpu_percent,
            "memory_pressure": snapshot.memory_pressure,
            "thermal_state": snapshot.thermal_state.value,
            "unified_memory_gb": {
                "used": round(snapshot.unified_memory_used, 2),
                "total": round(snapshot.unified_memory_total, 2),
            },
            "recommended_action": snapshot.recommended_action,
        }

    # 2. Gemini API Health
    if gemini_wrapper:
        health["apis"]["gemini"] = await gemini_wrapper.check_health()
    else:
        health["apis"]["gemini"] = {"status": "error", "message": "Not initialized"}

    # 3. Web Search API Health (SerpAPI / Tavily)
    if web_searcher:
        health["apis"]["search"] = await web_searcher.check_health()
    else:
        health["apis"]["search"] = {"status": "error", "message": "Not initialized"}

    # 4. Vector Store Health (Qdrant)
    if qdrant_manager:
        health["apis"]["qdrant"] = await qdrant_manager.check_health()
    else:
        health["apis"]["qdrant"] = {"status": "error", "message": "Not initialized"}

    return health


@app.get("/api/gemini/usage")
async def get_gemini_usage():
    """
    Get Gemini API usage statistics and quota status.
    Shows current usage vs tier 1 limits.
    """
    if not gemini_wrapper:
        return {"error": "Gemini wrapper not initialized"}

    from backend.llm.model_config import get_model_info, get_all_models

    usage = gemini_wrapper.get_usage_stats()
    models = get_all_models()

    return {
        "current_usage": {
            "total_requests": usage["total_requests"],
            "total_prompt_tokens": usage["total_prompt_tokens"],
            "total_completion_tokens": usage["total_completion_tokens"],
            "total_errors": usage["total_errors"],
            "rate_limit_hits": usage["rate_limit_hits"],
            "estimated_rpm": usage.get("estimated_rpm", 0),
            "rpm_percentage": usage.get("rpm_percentage", 0),
            "requests_by_model": usage["requests_by_model"],
            "session_duration_minutes": (time.time() - usage["last_reset"]) / 60,
        },
        "tier_1_limits": {
            "max_rpm": 300,
            "max_tpm": 1_000_000,
            "max_rpd": 1_500,
        },
        "available_models": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "input_token_limit": m.input_token_limit,
                "output_token_limit": m.output_token_limit,
                "tier_1_rpm": m.tier_1_rpm,
                "is_deprecated": m.is_deprecated,
            }
            for m in models
        ],
    }


@app.post("/api/gemini/usage/reset")
async def reset_gemini_usage():
    """Reset usage statistics"""
    if not gemini_wrapper:
        return {"error": "Gemini wrapper not initialized"}

    gemini_wrapper.reset_usage_stats()
    return {"status": "ok", "message": "Usage statistics reset"}


@app.get("/api/gemini/models")
async def get_available_models():
    """Get all available Gemini models with their capabilities"""
    from backend.llm.model_config import get_all_models, get_preferred_models

    all_models = get_all_models()
    preferred = get_preferred_models()

    return {
        "all_models": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "input_token_limit": m.input_token_limit,
                "output_token_limit": m.output_token_limit,
                "supports_thinking": m.supports_thinking,
                "supports_vision": m.supports_vision,
                "supports_caching": m.supports_caching,
                "tier_1_rpm": m.tier_1_rpm,
                "tier_1_tpm": m.tier_1_tpm,
                "tier_1_rpd": m.tier_1_rpd,
                "is_deprecated": m.is_deprecated,
            }
            for m in all_models
        ],
        "preferred": [m.name for m in preferred],
    }


@app.get("/api/gemini/test")
async def test_gemini():
    """Test Gemini connectivity via the shared GeminiWrapper."""

    if not gemini_wrapper:
        return {"error": "Gemini wrapper not initialized", "status": "error"}

    try:
        resp = await gemini_wrapper.generate(
            prompt="Say hi in 3 words",
            model="gemini-3.1-pro-preview",
            temperature=0.7,
            task_complexity="analysis",
        )
        text = getattr(resp, "text", None) or getattr(resp, "content", None) or ""
        return {"response": text, "status": "ok"}
    except Exception as e:
        return {"error": str(e), "status": "error"}


@app.post("/api/quick/chat")
async def quick_chat(request: Dict):
    """Quick chat using the shared GeminiWrapper (with model fallback)."""

    message = request.get("message", "")

    if not gemini_wrapper:
        return {"error": "Gemini wrapper not initialized", "source": "failed"}

    # Model fallback chain
    model_chain = [
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]

    for model in model_chain:
        try:
            resp = await gemini_wrapper.generate(
                prompt=message,
                model=model,
                task_complexity="analysis",
                temperature=0.7,
            )
            text = getattr(resp, "text", None) or getattr(resp, "content", None) or ""
            if text:
                return {"response": text, "source": f"gemini-{model}"}
        except Exception as e:
            logger.warning(f"Quick chat {model} failed: {e}")
            continue

    # All Gemini failed, try local LLM
    if local_llm_client:
        try:
            resp = await local_llm_client.generate(message)
            return {"response": resp, "source": "local_llm"}
        except Exception as llm_err:
            return {
                "error": f"All Gemini models and local LLM failed: {llm_err}",
                "source": "failed",
            }

    return {
        "error": "All Gemini models failed and local LLM unavailable",
        "source": "failed",
    }


@app.get("/api/local-llm/status")
async def get_local_llm_status():
    """Get local LLM status"""
    global local_llm_client
    if not local_llm_client:
        return {"available": False, "message": "Local LLM not enabled or not available"}

    health = await local_llm_client.check_health()
    return health


@app.post("/api/local-llm/chat")
async def chat_with_local_llm(request: Dict):
    """Chat with local LLM"""
    global local_llm_client
    if not local_llm_client:
        return {"error": "Local LLM not available"}

    try:
        response = await local_llm_client.generate(
            prompt=request.get("message", ""),
            system_prompt=request.get("system_prompt"),
            temperature=request.get("temperature", 0.7),
        )
        return {"response": response, "model": local_llm_client.model}
    except Exception as e:
        return {"error": str(e)}


class CreateCaseRequest(BaseModel):
    user_query: str = Field(
        ...,
        description="Who should we help? E.g., 'Help Sarah with her insurance claim'",
    )
    enable_deep_research: bool = Field(
        False, description="Enable exhaustive background research"
    )
    priority: int = Field(5, ge=1, le=10, description="Case priority 1-10")


@app.post("/api/cases", response_model=Dict)
async def create_case(request: CreateCaseRequest):
    """
    Initialize a new case. Returns case_id for tracking.
    """
    case_id = str(uuid4())

    case = Case(
        id=case_id,
        user_query=request.user_query,
        status=CaseStatus.CREATED,
        created_at=datetime.utcnow(),
        enable_deep_research=request.enable_deep_research,
        priority=request.priority,
    )

    # Persist case metadata (in production, use proper database)
    # For now, store in Qdrant metadata collection

    logger.info(f"📁 Created case {case_id}: {request.user_query}")

    return {
        "case_id": case_id,
        "status": "created",
        "message": "Drop files via WebSocket or POST to /api/cases/{case_id}/files",
    }


@app.post("/api/cases/{case_id}/files")
async def upload_files(
    case_id: str,
    files: List[UploadFile] = File(...),
    deep_research_override: Optional[bool] = Form(None),
):
    """
    Upload files for case analysis. Triggers ingestion pipeline.
    """
    # Validate case exists
    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Save uploaded files
    upload_dir = Path(settings.UPLOAD_DIR) / case_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for file in files:
        file_path = upload_dir / file.filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        saved_paths.append(str(file_path))

    logger.info(f"📤 Received {len(saved_paths)} files for case {case_id}")

    # Trigger async ingestion and analysis
    asyncio.create_task(
        process_case_pipeline(case_id, saved_paths, deep_research_override)
    )

    return {
        "case_id": case_id,
        "files_received": len(saved_paths),
        "status": "processing",
        "websocket_url": f"ws://localhost:8000/ws/cases/{case_id}",
    }


@app.get("/api/cases/{case_id}")
async def get_case_status(case_id: str):
    """Get current case status and deliverables if complete."""
    case = await get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return case.to_dict()


@app.get("/api/cases/{case_id}/deliverables")
async def get_deliverables(case_id: str):
    """Get generated reports, emails, contacts for case."""
    case = await get_case(case_id)
    if not case or case.status != CaseStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Case not complete")

    # Retrieve from Qdrant final_deliverables collection
    deliverables = await qdrant_manager.get_deliverables(case_id)
    return deliverables


# ============================================================================
# NOTEBOOKLM MCP INTEGRATION
# ============================================================================

from backend.enrichment.notebooklm_client import get_notebooklm_client


@app.get("/api/notebooklm/health")
async def notebooklm_health():
    """Check NotebookLM MCP connection status."""
    client = await get_notebooklm_client()
    return {"connected": client.is_connected}


@app.get("/api/notebooklm/notebooks")
async def list_notebooks():
    """List all NotebookLM notebooks."""
    client = await get_notebooklm_client()
    if not client.is_connected:
        await client.connect()

    notebooks = await client.list_notebooks()
    return {"notebooks": notebooks}


@app.get("/api/notebooklm/notebooks/{notebook_id}/sources")
async def get_notebook_sources(notebook_id: str):
    """Get sources for a specific notebook."""
    client = await get_notebooklm_client()
    if not client.is_connected:
        await client.connect()

    sources = await client.get_notebook_sources(notebook_id)
    return {"sources": sources}


@app.post("/api/notebooklm/search")
async def search_notebooks(query: str):
    """Search across all notebooks."""
    client = await get_notebooklm_client()
    if not client.is_connected:
        await client.connect()

    results = await client.search_notebooks(query)
    return {"results": results}


# ============================================================================
# ADMIN API ENDPOINTS (for new frontend)
# ============================================================================


@app.get("/api/admin/qdrant")
async def get_qdrant_stats():
    """Get Qdrant collection stats."""
    if qdrant_manager:
        return await qdrant_manager.check_health()
    return {"status": "error", "message": "Qdrant not initialized", "points_count": 0}


@app.delete("/api/admin/qdrant")
async def clear_qdrant_memory():
    """Clear Qdrant knowledge base."""
    if qdrant_manager:
        success = await qdrant_manager.clear_knowledge_base()
        return {"success": success}
    return {"success": False, "error": "Qdrant not initialized"}


@app.get("/api/admin/agents")
async def get_agent_configs():
    """Get all agent configurations."""
    from pathlib import Path

    # Get agent profiles from the profiles directory
    profiles_root = Path(__file__).parent.parent / "agents" / "profiles"

    agents = []
    if profiles_root.exists():
        for agent_dir in profiles_root.iterdir():
            if agent_dir.is_dir():
                agent_id = agent_dir.name

                # Load profile files
                system_prompt = ""
                if (agent_dir / "SystemAgent.md").exists():
                    system_prompt = (agent_dir / "SystemAgent.md").read_text()[:500]

                agents.append(
                    {
                        "id": agent_id,
                        "name": agent_id.replace("_", " ").title(),
                        "model": "gemini-3-flash-preview",
                        "prompt": system_prompt or "No system prompt defined.",
                        "temperature": 0.7,
                    }
                )

    # Fallback defaults if no profiles loaded
    if not agents:
        agents = [
            {
                "id": "coordinator",
                "name": "Coordinator Alpha",
                "model": "gemini-3-flash-preview",
                "prompt": "You orchestrate the swarm...",
                "temperature": 0.7,
            },
            {
                "id": "context_weaver",
                "name": "Context Weaver",
                "model": "gemini-3.1-pro-preview",
                "prompt": "Extract key entities from the query...",
                "temperature": 0.7,
            },
            {
                "id": "echo_vault",
                "name": "Echo Vault",
                "model": "gemini-3.1-pro-preview",
                "prompt": "Recall past cases and search the web...",
                "temperature": 0.7,
            },
            {
                "id": "outcome_architect",
                "name": "Outcome Architect",
                "model": "gemini-3.1-pro-preview",
                "prompt": "Devise a strategic plan...",
                "temperature": 0.7,
            },
            {
                "id": "chronicle_scribe",
                "name": "Chronicle Scribe",
                "model": "gemini-3.1-pro-preview",
                "prompt": "Create a final report...",
                "temperature": 0.7,
            },
        ]

    return agents


@app.post("/api/admin/agents")
async def save_agent_configs(agents: List[Dict]):
    """Save agent configurations."""
    # In a full implementation, you'd save these to a config file or database
    logger.info(f"Saving {len(agents)} agent configurations")
    return {"status": "ok", "message": f"Saved {len(agents)} agent configurations"}


@app.post("/api/admin/chat")
async def admin_chat(request: Dict):
    """Chat with The Architect (Admin Agent)."""
    message = request.get("message", "")
    session_id = request.get("session_id", "default")

    if not gemini_wrapper:
        return {"response": "Backend not ready. Please restart."}

    try:
        from pathlib import Path

        admin_dir = Path(__file__).parent / "agents" / "profiles" / "admin_agent"

        system_prompt = ""
        if (admin_dir / "SystemAgent.md").exists():
            system_prompt = (admin_dir / "SystemAgent.md").read_text()

        arch_path = Path(__file__).parent / "agents" / "profiles" / "ARCHITECTURE.md"
        arch_info = ""
        if arch_path.exists():
            arch_info = arch_path.read_text()

        agents_dir = Path(__file__).parent / "agents" / "profiles"
        available_agents = []
        for d in agents_dir.iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                agent_info = {"name": d.name, "files": []}
                for f in d.iterdir():
                    if f.is_file():
                        agent_info["files"].append(f.name)
                available_agents.append(agent_info)

        conversation_history = ""
        if qdrant_manager:
            memories = await qdrant_manager.get_architect_memory(
                session_id=session_id, limit=20
            )
            if memories:
                conversation_history = "## Previous Conversation\n"
                for mem in memories:
                    role_label = "User" if mem.get("role") == "user" else "Architect"
                    conversation_history += f"{role_label}: {mem.get('message', '')}\n"

        full_prompt = f"""{system_prompt}

## System Architecture
{arch_info}

## Available Agents
{chr(10).join([f"- {a['name']}: {', '.join(a['files'])}" for a in available_agents])}

{conversation_history}

## Current Message
User: {message}

Remember: You can read agent profile files, analyze logs, and with approval - create/modify files. Be helpful and analytical."""

        response = await gemini_wrapper.generate(
            prompt=full_prompt, model="gemini-3.1-pro-preview", temperature=0.7
        )

        response_text = response.text or "I'm thinking... (no response)"

        if qdrant_manager:
            await qdrant_manager.store_architect_memory(
                session_id=session_id, message=message, role="user"
            )
            await qdrant_manager.store_architect_memory(
                session_id=session_id, message=response_text, role="architect"
            )

        return {"response": response_text, "session_id": session_id}
    except Exception as e:
        logger.error(f"Admin chat error: {e}")
        return {"response": f"I encountered an error: {str(e)}"}


@app.get("/api/admin/architect/stats")
async def get_architect_stats():
    """Get The Architect's memory statistics."""
    if qdrant_manager:
        stats = await qdrant_manager.get_architect_stats()
        return stats
    return {"status": "error", "message": "Qdrant not initialized"}


@app.post("/api/admin/architect/read")
async def architect_read_file(request: Dict):
    """Allow The Architect to read files for analysis."""
    file_path = request.get("path", "")

    from pathlib import Path

    base_path = Path(__file__).parent.parent.resolve()
    full_path = (base_path / file_path).resolve()

    if not full_path.is_relative_to(base_path):
        return {"error": "Access denied: Path outside project"}

    try:
        if full_path.exists() and full_path.is_file():
            content = full_path.read_text(encoding="utf-8", errors="ignore")
            return {"content": content[:50000], "path": str(full_path)}
        else:
            return {"error": "File not found"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/admin/architect/list-dir")
async def architect_list_dir(request: Dict):
    """Allow The Architect to list directory contents."""
    dir_path = request.get("path", "")

    from pathlib import Path

    base_path = Path(__file__).parent.parent.resolve()
    full_path = (base_path / dir_path).resolve()

    if not full_path.is_relative_to(base_path):
        return {"error": "Access denied: Path outside project"}

    try:
        if full_path.exists() and full_path.is_dir():
            items = []
            for item in full_path.iterdir():
                items.append(
                    {"name": item.name, "type": "dir" if item.is_dir() else "file"}
                )
            return {"items": items, "path": str(full_path)}
        else:
            return {"error": "Directory not found"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# AGENT CHAT ENDPOINTS
# ============================================================================

AGENT_PROFILES = {
    "sunny": "sunny_agent",
    "orchestrator": "orchestrator_agent",
    "devils_advocate": "devils_advocate",
    "architect": "admin_agent",
    "omega": "omega_agent",
}


@app.post("/api/agents/chat")
async def agent_chat(request: Dict):
    """Chat with any agent (sunny, orchestrator, devils_advocate, architect)."""
    agent_name = request.get("agent", "orchestrator").lower()
    message = request.get("message", "")
    session_id = request.get("session_id", "default")

    logger.info(
        f"🔵 AGENT CHAT START | agent={agent_name} | session={session_id} | message='{message[:50]}...'"
    )

    if agent_name not in AGENT_PROFILES:
        logger.error(f"❌ Unknown agent: {agent_name}")
        return {"error": f"Unknown agent. Available: {list(AGENT_PROFILES.keys())}"}

    if not gemini_wrapper:
        logger.error("❌ Gemini wrapper not initialized")
        return {"response": "Backend not ready. Please restart."}

    try:
        from pathlib import Path

        agent_dir = (
            Path(__file__).parent / "agents" / "profiles" / AGENT_PROFILES[agent_name]
        )
        logger.info(f"📁 Loading agent profile from: {agent_dir}")

        system_prompt = ""
        if (agent_dir / "SystemAgent.md").exists():
            system_prompt = (agent_dir / "SystemAgent.md").read_text()
            logger.info(f"✅ Loaded system prompt ({len(system_prompt)} chars)")
        else:
            logger.warning(f"⚠️ No SystemAgent.md found for {agent_name}")

        # Memory lookup
        logger.info(f"🔍 Checking Qdrant memory for {agent_name}...")
        conversation_history = ""
        if qdrant_manager:
            try:
                memories = await qdrant_manager.get_agent_memory(
                    agent_name, session_id=session_id, limit=20
                )
                logger.info(f"📚 Found {len(memories) if memories else 0} memories")
                if memories:
                    conversation_history = "## Previous Conversation\n"
                    for mem in memories:
                        role_label = (
                            "User" if mem.get("role") == "user" else agent_name.title()
                        )
                        conversation_history += (
                            f"{role_label}: {mem.get('message', '')}\n"
                        )
            except Exception as mem_err:
                logger.error(f"❌ Memory lookup failed: {mem_err}")
                conversation_history = ""
        else:
            logger.warning("⚠️ Qdrant manager not available")

        full_prompt = f"""{system_prompt}

{conversation_history}

## Current Message
User: {message}

Respond in character as {agent_name.title()}."""

        logger.info(
            f"📤 Sending to Gemini (model=gemini-3.1-pro-preview, prompt_len={len(full_prompt)})"
        )

        # Model fallback chain: 3.1-pro → 3-flash → 2.5-flash → 2.0-flash
        model_chain = [
            "gemini-3.1-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
        ]

        response_text = None
        last_error = None

        for model in model_chain:
            try:
                logger.info(f"🔄 Trying model: {model}")
                resp = await gemini_wrapper.generate(
                    prompt=full_prompt,
                    model=model,
                    temperature=0.7,
                    task_complexity="analysis",
                )
                response_text = (
                    getattr(resp, "text", None)
                    or getattr(resp, "content", None)
                    or "I'm thinking... (no response)"
                )
                logger.info(f"✅ Success with model: {model}")
                break
            except Exception as api_error:
                logger.warning(f"❌ {model} failed: {api_error}")
                last_error = api_error
                if "503" in str(api_error) or "429" in str(api_error):
                    continue  # Try next model
                else:
                    break  # Other error, don't retry

        # If all Gemini models failed, try local LLM
        if not response_text and last_error:
            logger.warning("🔄 All Gemini models failed, trying local LLM...")
            if local_llm_client:
                try:
                    response_text = await local_llm_client.generate(full_prompt)
                    logger.info(
                        f"✅ Local LLM response received ({len(response_text)} chars)"
                    )
                except Exception as llm_error:
                    logger.error(f"❌ Local LLM also failed: {llm_error}")
                    raise Exception(
                        f"All Gemini models and local LLM failed: {llm_error}"
                    )
            else:
                raise last_error

        # Store in memory
        if qdrant_manager:
            try:
                await qdrant_manager.store_agent_message(
                    agent_name, session_id, message, "user"
                )
                await qdrant_manager.store_agent_message(
                    agent_name, session_id, response_text, agent_name
                )
                logger.info(f"💾 Stored messages in Qdrant")
            except Exception as store_err:
                logger.error(f"❌ Failed to store memory: {store_err}")

        logger.info(f"🎉 AGENT CHAT COMPLETE | agent={agent_name}")

        return {
            "response": response_text,
            "session_id": session_id,
            "agent": agent_name,
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ AGENT CHAT FAILED: {error_msg}")
        return {"response": f"I encountered an error: {error_msg}"}


@app.get("/api/agents/{agent_name}/stats")
async def get_agent_stats(agent_name: str):
    """Get an agent's memory statistics."""
    if qdrant_manager:
        stats = await qdrant_manager.get_agent_stats(agent_name)
        return stats
    return {"status": "error", "message": "Qdrant not initialized"}


# ============================================================================
# DEEP RESEARCH ENDPOINT (Gemini Interactions API)
# ============================================================================


@app.post("/api/research/deep")
async def deep_research(request: Dict):
    """
    Use Gemini Deep Research model (deep-research-pro-preview-12-2025)
    for exhaustive research tasks.
    """
    query = request.get("query", "")
    session_id = request.get("session_id", f"research_{int(time.time())}")

    if not query:
        return {"error": "Query is required"}

    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        interaction = client.interactions.create(
            agent="deep-research-pro-preview-12-2025", input=query, background=True
        )

        interaction_id = interaction.id

        if qdrant_manager:
            await qdrant_manager.store_agent_message(
                "research", session_id, f"Research query: {query}", "user"
            )

        return {
            "status": "started",
            "interaction_id": interaction_id,
            "message": "Deep research started. Poll /api/research/status/{id} for results.",
        }

    except Exception as e:
        logger.error(f"Deep research error: {e}")
        return {"error": str(e)}


@app.get("/api/research/status/{interaction_id}")
async def get_research_status(interaction_id: str):
    """Poll for deep research results."""
    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        interaction = client.interactions.get(id=interaction_id)

        if interaction.status == "completed":
            return {
                "status": "completed",
                "response": interaction.response,
                "thinking": getattr(interaction, "thinking_summary", None),
            }
        elif interaction.status == "failed":
            return {
                "status": "failed",
                "error": getattr(interaction, "error", "Unknown error"),
            }
        else:
            return {"status": interaction.status, "message": "Research in progress..."}

    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# KNOWLEDGE BASE ENDPOINTS
# ============================================================================


@app.get("/api/knowledge")
async def get_knowledge_docs():
    """Get all knowledge base documents."""
    if qdrant_manager:
        docs = await qdrant_manager.get_knowledge_docs()
        return docs
    return []


@app.post("/api/knowledge")
async def add_knowledge(request: Dict):
    """Add a document to knowledge base."""
    text = request.get("text", "")
    title = request.get("title", "Untitled")

    if qdrant_manager:
        success = await qdrant_manager.add_knowledge(text, title)
        return {"success": success}
    return {"success": False, "error": "Qdrant not initialized"}


@app.post("/api/agent/witty")
async def get_witty_response(request: Dict):
    """Get a witty response for the objective."""
    objective = request.get("objective", "")

    if not gemini_wrapper:
        return {"response": "Drop your files. Let's sort this mess out."}

    try:
        response = await gemini_wrapper.generate(
            prompt=f"""The user stated their objective: "{objective}". Give a very short, witty, grayscale-themed, slightly cynical but helpful response (max 15 words) inviting them to drop their files to achieve this.""",
            model="gemini-3-flash-preview",
            temperature=0.9,
        )
        return {
            "response": response.text or "Drop your files. Let's sort this mess out."
        }
    except Exception as e:
        logger.error(f"Witty response error: {e}")
        return {"response": "Drop your files. Let's sort this mess out."}


# ============================================================================
# WEBSOCKET ENDPOINT — Real-time Glass Engine
# ============================================================================


@app.websocket("/ws/cases/{case_id}")
async def case_websocket(websocket: WebSocket, case_id: str):
    """
    Primary real-time connection for case monitoring.
    Receives: file uploads, user messages, commands
    Sends: progress updates, agent thoughts, event logs, final deliverables
    """
    await connection_manager.connect(websocket, case_id)

    try:
        # Send initial connection acknowledgment
        await websocket.send_json(
            {
                "type": "connection_established",
                "case_id": case_id,
                "timestamp": time.time(),
            }
        )

        # If case already processing/completed, send current state
        case = await get_case(case_id)
        if case and case.status in [
            CaseStatus.ANALYZING,
            CaseStatus.DEBATING,
            CaseStatus.COMPLETE,
        ]:
            await send_current_state(websocket, case)

        # Message handling loop
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            msg_type = data.get("type")

            if msg_type == "upload_files":
                # Handle base64-encoded files from browser
                await handle_websocket_upload(case_id, data["files"], websocket)

            elif msg_type == "user_message":
                # Aftermath chat message
                await handle_aftermath_chat(case_id, data["message"], websocket)

            elif msg_type == "command":
                # User commands: pause, resume, cancel, request_deep_research
                await handle_command(case_id, data["command"], data.get("args", {}))

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, case_id)
        logger.info(f"🔌 Client disconnected from case {case_id}")
    except Exception as e:
        logger.error(f"WebSocket error for case {case_id}: {e}")
        connection_manager.disconnect(websocket, case_id)


@app.websocket("/ws/audio/{case_id}")
async def audio_websocket(websocket: WebSocket, case_id: str):
    """
    WebSocket endpoint for real-time bidirectional audio.
    Bridges frontend Web Audio to Gemini Live Audio API.
    """
    await websocket.accept()
    logger.info(f"🎙️ Audio WebSocket connected for case {case_id}")

    gateway = GeminiLiveAudioGateway(gemini_api_key=settings.GEMINI_API_KEY)

    # Callback to send Gemini's audio to frontend
    async def send_to_frontend(audio_bytes: bytes):
        try:
            await websocket.send_bytes(audio_bytes)
        except Exception as e:
            logger.error(f"Error sending audio to frontend: {e}")

    # Callback to send transcripts to frontend
    async def send_transcript(transcript: AudioTranscript):
        try:
            await websocket.send_json(
                {
                    "type": "transcript",
                    "text": transcript.text,
                    "is_final": transcript.is_final,
                    "speaker": transcript.speaker,
                }
            )
        except Exception as e:
            logger.error(f"Error sending transcript: {e}")

    gateway.output_callback = send_to_frontend
    gateway.transcript_callbacks.append(send_transcript)

    try:
        await gateway.start_session()

        while True:
            # Receive PCM audio chunks from frontend
            data = await websocket.receive_bytes()
            await gateway.audio_queue.put(data)

    except WebSocketDisconnect:
        logger.info(f"🎙️ Audio WebSocket disconnected for case {case_id}")
    except Exception as e:
        logger.error(f"Audio WebSocket error: {e}")
    finally:
        await gateway.close()


# ============================================================================
# PIPELINE ORCHESTRATION
# ============================================================================


async def process_case_pipeline(
    case_id: str, file_paths: List[str], deep_research_override: Optional[bool] = None
):
    """Main processing pipeline. Triggered after file upload."""

    pipeline_start = time.time()
    twisted_logger.pipeline_stage(case_id, "pipeline", 0, "Starting pipeline")

    try:
        # STAGE 1: Ingestion (0-10%)
        twisted_logger.pipeline_stage(case_id, "ingestion", 0, "Starting file ingestion")
        ingestion_start = twisted_logger.agent_start(
            "Coordinator",
            case_id,
            "ingestion",
            {"file_count": len(file_paths)},
        )

        await connection_manager.broadcast_progress(
            case_id, "ingestion", 0, "Starting file ingestion..."
        )

        if not ingestion_pipeline:
            err = "Ingestion pipeline not initialized"
            logger.error(err)
            twisted_logger.error(err, agent="pipeline", case_id=case_id, operation="ingestion")
            await connection_manager.broadcast_progress(
                case_id, "ingestion", 0, "Error: System not ready"
            )
            return

        ingestion_result = await ingestion_pipeline.process(
            case_id=case_id,
            file_paths=file_paths,
            progress_callback=lambda p, m: connection_manager.broadcast_progress(
                case_id,
                "ingestion",
                p * 0.1,
                m,  # 0-10% of total
            ),
        )

        document_count = len(ingestion_result.get("documents", []))
        await connection_manager.broadcast_progress(
            case_id,
            "ingestion",
            10,
            f"Ingested {document_count} documents",
        )
        twisted_logger.agent_complete(
            "Coordinator",
            case_id,
            "ingestion",
            ingestion_start,
            {"document_count": document_count},
        )

        # STAGE 2: Context Analysis (10-40%)
        twisted_logger.pipeline_stage(case_id, "analysis", 10, "Starting context analysis")
        ctx_start = twisted_logger.agent_start(
            "Context Weaver",
            case_id,
            "context_analysis",
            {"summary_preview": str(ingestion_result.get("summary", ""))[:200]},
        )

        await connection_manager.broadcast_event_log(
            case_id,
            "INFO",
            "Coordinator",
            "Activating Context Weaver for situation analysis",
        )

        if swarm_orchestrator:
            await swarm_orchestrator.run_context_analysis(
                case_id=case_id,
                progress_callback=lambda p, m: connection_manager.broadcast_progress(
                    case_id,
                    "analysis",
                    10 + (p * 0.3),
                    m,  # 10-40%
                ),
                thought_callback=lambda **kwargs: (
                    connection_manager.broadcast_agent_thought(case_id, **kwargs)
                ),
            )
            twisted_logger.agent_complete(
                "Context Weaver", case_id, "context_analysis", ctx_start
            )
        else:
            err = f"Swarm orchestrator not initialized for case {case_id}. Skipping context analysis."
            logger.error(err)
            twisted_logger.agent_error(
                "Context Weaver",
                case_id,
                "context_analysis",
                Exception("swarm_orchestrator_not_initialized"),
                {"message": err},
            )
            await connection_manager.broadcast_event_log(
                case_id,
                "ERROR",
                "Coordinator",
                "Swarm orchestrator not ready. Context analysis skipped.",
                metadata={"error_type": "system_not_ready"},
            )

        # STAGE 3: Deep Research (optional, 40-50%)
        enable_deep = (
            deep_research_override
            if deep_research_override is not None
            else settings.ENABLE_DEEP_RESEARCH
        )

        if enable_deep:
            twisted_logger.pipeline_stage(case_id, "deep_research", 40, "Starting deep research")
            research_start = twisted_logger.agent_start(
                "Coordinator",
                case_id,
                "deep_research",
                {"browser_use_enabled": bool(settings.BROWSER_USE_ENABLED)},
            )

            await connection_manager.broadcast_progress(
                case_id, "research", 40, "Initiating deep research phase..."
            )

            from backend.enrichment.deep_research import DeepResearchOrchestrator

            research = DeepResearchOrchestrator(gemini_wrapper)
            findings = await research.execute(
                case_id=case_id,
                context_query=str(ingestion_result.get("summary", "")),
                progress_callback=lambda p, m: connection_manager.broadcast_progress(
                    case_id,
                    "deep_research",
                    40 + (p * 0.1),
                    m,  # 40-50%
                ),
            )

            # Optional Browser Use Cloud augmentation
            if settings.BROWSER_USE_ENABLED and settings.BROWSER_USE_API_KEY:
                try:
                    browser_client = BrowserUseClient(api_key=settings.BROWSER_USE_API_KEY)
                    browser_result = await browser_client.run_research(
                        query=str(ingestion_result.get("summary", ""))
                    )
                    await browser_client.close()

                    findings.setdefault("documents", []).append(
                        json.dumps(browser_result, default=str)
                    )
                    findings.setdefault("metadatas", []).append(
                        {"type": "browser_use", "source": "browser_use"}
                    )
                except Exception as e:
                    twisted_logger.warning(
                        f"Browser Use research failed: {e}",
                        agent="BrowserUse",
                        case_id=case_id,
                        operation="deep_research",
                    )

            if qdrant_manager:
                await qdrant_manager.store_external_intel(case_id, findings)

            await connection_manager.broadcast_progress(
                case_id, "research", 50, "Deep research complete"
            )

            twisted_logger.agent_complete(
                "Coordinator",
                case_id,
                "deep_research",
                research_start,
                {"external_doc_count": len(findings.get("documents", []))},
            )

        # STAGE 4: Swarm Debate (50-90%)
        twisted_logger.pipeline_stage(case_id, "debate", 50, "Starting swarm debate")
        debate_start = twisted_logger.agent_start(
            "Swarm", case_id, "debate", {"rounds": 3}
        )

        await connection_manager.broadcast_event_log(
            case_id,
            "INFO",
            "Coordinator",
            "Initiating multi-agent debate for outcome optimization",
        )

        if not swarm_orchestrator:
            err = f"Swarm orchestrator not initialized for case {case_id}. Skipping debate."
            logger.error(err)
            twisted_logger.agent_error(
                "Swarm",
                case_id,
                "debate",
                Exception("swarm_orchestrator_not_initialized"),
                {"message": err},
            )
            await connection_manager.broadcast_progress(
                case_id, "debate", 50, "Error: System not ready for debate"
            )
            final_outcome: Dict[str, Any] = {
                "error": "Swarm orchestrator not available for debate"
            }
        else:
            final_outcome = await swarm_orchestrator.run_debate(
                case_id=case_id,
                rounds=3,
                progress_callback=lambda p, m: connection_manager.broadcast_progress(
                    case_id,
                    "debate",
                    50 + (p * 0.4),
                    m,  # 50-90%
                ),
                thought_callback=lambda **kwargs: (
                    connection_manager.broadcast_agent_thought(case_id, **kwargs)
                ),
                log_callback=lambda **kwargs: connection_manager.broadcast_event_log(
                    case_id, **kwargs
                ),
            )

        twisted_logger.agent_complete(
            "Swarm",
            case_id,
            "debate",
            debate_start,
            {"outcome_keys": list(final_outcome.keys())},
        )

        # STAGE 5: Deliverable Generation (90-100%)
        twisted_logger.pipeline_stage(case_id, "synthesis", 90, "Generating deliverables")
        deliverables_start = twisted_logger.agent_start(
            "Chronicle Scribe", case_id, "deliverables"
        )

        await connection_manager.broadcast_progress(
            case_id, "synthesis", 90, "Generating final deliverables..."
        )

        if not swarm_orchestrator:
            err = "Swarm orchestrator not initialized"
            logger.error(err)
            twisted_logger.error(err, agent="pipeline", case_id=case_id, operation="synthesis")
            await connection_manager.broadcast_progress(
                case_id, "synthesis", 100, "Error: System not ready"
            )
            return

        deliverables = await swarm_orchestrator.generate_deliverables(
            case_id=case_id,
            outcome=final_outcome,
            progress_callback=lambda p, m: connection_manager.broadcast_progress(
                case_id,
                "synthesis",
                90 + (p * 0.1),
                m,  # 90-100%
            ),
        )

        twisted_logger.agent_complete(
            "Chronicle Scribe",
            case_id,
            "deliverables",
            deliverables_start,
            {
                "deliverable_keys": list(deliverables.keys())
                if isinstance(deliverables, dict)
                else None
            },
        )

        pipeline_duration = time.time() - pipeline_start
        twisted_logger.pipeline_stage(
            case_id,
            "pipeline",
            100,
            f"Pipeline finished in {pipeline_duration:.1f}s",
        )

        # Complete
        await connection_manager.broadcast_progress(
            case_id, "complete", 100, "Analysis complete. Review your strategy."
        )

        await update_case_status(case_id, CaseStatus.COMPLETE, deliverables)

        # Send final deliverables
        await connection_manager.broadcast_to_case(
            case_id,
            CaseUpdateMessage(
                type=MessageType.CASE_COMPLETE,
                timestamp=time.time(),
                case_id=case_id,
                deliverables=deliverables,
            ),
        )

    except Exception as e:
        logger.exception(f"Pipeline failed for case {case_id}")
        twisted_logger.error(
            f"Pipeline failed for case {case_id}: {str(e)}",
            agent="pipeline",
            case_id=case_id,
            operation="pipeline",
            step="error",
            error=str(e),
        )
        await connection_manager.broadcast_event_log(
            case_id,
            "ERROR",
            "Coordinator",
            f"Pipeline failure: {str(e)}",
            metadata={"error_type": "pipeline_failure", "recoverable": False},
        )
        await update_case_status(case_id, CaseStatus.FAILED, {"error": str(e)})


# ============================================================================
# HELPER FUNCTIONS (simplified — implement with proper DB in production)
# ============================================================================


async def get_case(case_id: str) -> Optional[Case]:
    """Retrieve case from storage."""
    # Placeholder — implement with Redis/PostgreSQL
    pass


async def update_case_status(case_id: str, status: CaseStatus, data: Dict):
    """Update case status."""
    pass


async def send_current_state(websocket: WebSocket, case: Case):
    """Send current case state to reconnecting client."""
    pass


async def handle_websocket_upload(
    case_id: str, files: List[Dict], websocket: WebSocket
):
    """Handle base64 file upload via WebSocket."""
    pass


async def handle_aftermath_chat(case_id: str, message: str, websocket: WebSocket):
    """Handle post-analysis chat messages."""
    pass


async def handle_command(case_id: str, command: str, args: Dict):
    """Handle user commands."""
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info"
    )

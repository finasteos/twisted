# orgaNICE v3 - The "Liquid Glass" Master Prompt

This document serves as a comprehensive system prompt/blueprint for rebuilding the entire orgaNICE decision engine from scratch.

## Core Philosophy

- **Helping Users in Complex Cases**: orgaNICE is an automated assistant designed to analyze complex personal, legal, or professional situations (e.g., insurance claims, legal disputes, risk assessments). It transforms fragmented data into strategic clarity.
- **Ultra-simple UI. Ultra-powerful engine.** The user should only see a drag-and-drop zone and a text prompt ("Who should I help?").
- **Liquid Glass Standard**: The UI must use a premium dark glassmorphism aesthetic (translucent cards, blurred backgrounds, smooth gradients, subtle glowing hover states, and micro-animations).
- **RAG-Powered Swarm**: The backend uses multi-agent debate architecture powered by ChromaDB vector memory. Agents NEVER read raw files; they query the vector store for semantic context.
- **Transparent Thinking (The Glass Engine)**: The visual Agent Flow diagram and the verbose real-time Event Log are NOT development tools—they are core user-facing pillars. The user must physically see the engine working, routing data, extracting context, and debating, to build maximum trust in the final outcome.

## 1. System Architecture

The application is split into a standalone Python backend (`FastAPI`) and a modern web frontend (`Vite + React + TS`).

### Tech Stack
- **Backend**: Python 3.14, FastAPI, Uvicorn, ChromaDB, `google-genai` (SDK 3.1+), Pydantic, WebSockets.
- **Frontend**: React 19, TypeScript, Vite, React Flow, Lucide-React.
- **Styling**: Vanilla CSS (no Tailwind). Dark Glassmorphism.

## 2. Backend Implementation (`/backend`)

**Directory Structure:**

```bash
/backend
├── agents/             # The swarm configuration
│   ├── base_agent.py   # Base class with memory/thought logic
│   ├── swarm.py        # Orchestrates the debate rounds
│   ├── [agent_name]/   # e.g., legal_advisor, strategist
│   │   ├── IDENTITY.md # Persona and core instructions
│   │   ├── SKILLS.md   # Domain-specific capabilities
│   │   └── SOUL.md     # Ethical/Philosophical guidance
├── enrichment/
│   ├── deep_research.py # Gemini Deep Research orchestrator
│   └── web_search.py   # SerpAPI/Tavily wrappers
├── ingestion/          # PDF, docx, txt, images, and audio parsing
├── llm/                # Universal LLM Client
│   └── wrapper.py      # Unified interface with rate limiting & routing
├── memory/
│   └── vector_store.py # ChromaDB RAG implementation
└── main.py             # FastAPI App + Analysis Pipeline
```

### Core Logic Flows

1. **Gemini 3 Integration (`wrapper.py`)**:
   - Uses `google-genai` library.
   - **gemini-3-flash-preview**: Default for speed, extraction, and context gathering.
   - **gemini-3.1-pro-preview**: Routed for heavy reasoning, legal analysis, and final synthesis.
   - **Rate Limiting**: Enforced delays to stay within Tier 1 margins (Pro: 100s, Flash: 12s safety intervals).

2. **Deep Research & SerpAPI**:
   - **Deep Research**: Utilizes `deep-research-pro-preview-12-2025` for exhaustive background checks.
   - **Web Search**: Integrates SerpAPI for real-time "deep web" intelligence.
   - Findings are injected into the Vector Store context before the Swarm begins.

3. **The Swarm Debate**:
   - Agents query the vector store, gather evidence, and debate over multiple rounds.
   - Progress is broadcast via WebSockets to the frontend.

## 3. Help Package & Deliverables

The engine produces a comprehensive "Help Package" tailored to the user's specific case:
- **Strategic Report**: Detailed analysis with "Executive Summary", "Key Findings", and "Action Plan".
- **Pre-written Emails**: Professional communications for lawyers, insurers, or counterparts.
- **Contact List**: Identification of key people, entities, and contact points from the data.
- **Possible Lawsuits**: Identification of potential legal avenues or claims.
- **Visuals**: Mermaid diagrams for timelines/relationships and AI-generated imagery for evidence visualization.

## 4. Aftermath Chat & Support

- Following the analysis, the user transitions to an interactive "Aftermath Chat".
- **Goal**: To further guide the user through the implementation of the strategy.
- **Context Awareness**: The chat agent has full context from the analysis report and the vector memory.
- **Steerability**: User can ask for specific revisions to emails, deeper dives into findings, or "What should I do next?" guidance.

## 5. Frontend Implementation (`/frontend`)

- **State Machine**: Input -> Analyzing -> Report.
- **Deep Research Toggle**: Direct user control over long-running comprehensive research.
- **Agent Flow Viz**: Real-time visualization of agent activity.
- **Settings**: Persistent storage for Gemini and SerpAPI keys.

## 6. Execution

- Backend: `uvicorn main:app --reload --port 8000`
- Frontend: `npm run dev -- --port 5173`
- Environment: Expected `.env` file with `GEMINI_API_KEY` and `SERPAPI_KEY`.

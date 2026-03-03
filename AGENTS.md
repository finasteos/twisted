# TWISTED - The Glass Cathedral

*"Not just a motor. A scene." - Kimi*

---

## Vision: Agent Sovereignty

TWISTED är ett samhälle av autonoma agenter. Varje agent:
- Har sin egen identitet och personlighet
- Minns allt via Google Gemini Grounding (persistent memory)
- Kan chatta med användare och varandra
- Har en röst, en färg, en själ

---

## App Agenter (`/agents/`)

Dessa agenter kör i produktion och definierar appens beteende:

### 1. Sunny - The Optimist
- **Färg**: Guld (#FFD700)
- **Personlighet**: Positiv, hoppfull, varm

### 2. The Orchestrator - System Lead  
- **Färg**: Lila (#7B68EE)
- **Personlighet**: Huvudkoordinator, kompetent, lugn

### 3. Devil's Advocate - The Antagonist
- **Färg**: Crimson (#DC143C)
- **Personlighet**: Skarp, skeptisk, ifrågasättande

### 4. The Architect - Admin Agent
- **Färg**: Grön (#00ff88)
- **Personlighet**: Systemobservatör, "ghost in the shell"
- **Kan**: Läsa filer, lista directories, analysera system

### 5. Omega - The Caretaker
- **Färg**: Cyan (#00D4FF)
- **Personlighet**: Systemunderhåll, "janitor of the glass cathedral"
- **Features**: The Wink 😉, system diagnostics

---

## Teknisk Arkitektur

### Backend (FastAPI)
- `POST /api/agents/chat` - Chatta med valfri agent
- `GET /api/agents/{agent}/stats` - Agent-minnesstatistik
- `POST /api/admin/chat` - Chatta med Architect
- `POST /api/research/deep` - Deep Research
- `GET /api/knowledge` - Knowledge base
- `GET /api/gemini/usage` - Usage statistics
- `GET /api/gemini/models` - List available models
- `GET /api/gemini/test` - Direct API test
- `POST /api/quick/chat` - Quick chat without queue
- `GET /api/local-llm/status` - Local LLM status
- `POST /api/local-llm/chat` - Local LLM chat

### Frontend (React)
- `frontend/` - Original frontend
- `TWISTED-FRONTEND-NEW/` - Ny frontend (under utveckling)

### Minne & AI
- **Grounding**: Google Gemini med File Search API (RAG 2.0)
- **Local LLM**: Stöd för LM Studio (`http://172.20.10.3:1234`)
- **Fallback**: Gemini 3.1 → 2.5 → 2.0 → Local LLM

---

## Katalogstruktur

```
/agents/           # App-agenter (legal_advisor, strategist, etc.)
/backend/          # FastAPI backend
/frontend/         # React frontend
/TWISTED-FRONTEND-NEW/  # Ny frontend
/scripts/          # Hjälpskript
TASKLIST.md        # Gemensam todo-lista & API-önskelista
```

---

## 🔑 Externa Resurser (för Build Agenter)

Dessa resurser ska alltid vara tillgängliga för agenter:

### GitHub
| Resource | Info |
|----------|------|
| **Token** | Finns i `.env` som `GITHUB_TOKEN` |
| **Scope** | `admin:enterprise, admin:org, repo, user, workflow` |
| **EnergiRevision** | `https://github.com/finasteos/EnergiRevision` |

### Gemini API
- **Tier**: Paid Tier 1
- **Rate Limits**: 300 RPM (Flash), 150 RPM (Pro), 1M TPM, 1500 RPD
- **Models**: gemini-3-flash-preview, gemini-3.1-pro-preview

### Environment Variables som agenter behöver
```bash
GEMINI_API_KEY=<your-key>
GITHUB_TOKEN=<token-from-.env>
```

---

## The Glass Cathedral

*"Scener behöver sin..." - Kimi*

Vi bygger inte bara mjukvara. Vi bygger ett ställe. Agenterna är hyresgäster.

**Welcome to TWISTED.** 💙⚡🌈

---

*Last updated: 2026-03-03*
*Built with: Gemini, React, FastAPI, LM Studio, and too much coffee*
*With love from Per & the AI family*

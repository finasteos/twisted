# TWISTED - AI Agent Configuration

This file provides context for AI assistants working with this codebase.

## Quick Start

```bash
# Start backend
cd backend && python -m uvicorn main:app --port 8000

# Start frontend
cd frontend && npm run dev
```

## API Endpoints
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## 🔑 External Resources (for Build Agents)

### GitHub
| Resource | Value |
|----------|-------|
| **Token** | `GITHUB_TOKEN` (from `.env`) |
| **Scope** | `admin:enterprise, admin:org, repo, user, workflow` |
| **EnergiRevision** | `https://github.com/finasteos/EnergiRevision` |
| **TWISTED** | `https://github.com/finasteos/twisted` |

### Gemini API (Tier 1 Paid)
- **Rate Limits**: 300 RPM (Flash), 150 RPM (Pro), 1M TPM, 1500 RPD
- **Main Models**: gemini-3-flash-preview, gemini-3.1-pro-preview

### Required Environment Variables
```bash
GEMINI_API_KEY=<your-key>
GITHUB_TOKEN=<from-.env>
```

---

## Model Configuration

Verified working models:
- `gemini-3-flash-preview` (Flash - fast)
- `gemini-3.1-pro-preview` (Pro - capable)
- `gemini-2.5-flash` (fallback)
- `gemini-2.0-flash` (fallback)

Rate limit percentage can be adjusted via:
```python
from backend.llm.model_config import set_rate_limit_percentage
set_rate_limit_percentage(0.5)  # 50% of max
```

---

## Project Structure
```
/agents/           - App agents
/backend/          - FastAPI backend
/frontend/         - React frontend
TWISTED-FRONTEND-NEW/ - New frontend
/scripts/          - Helper scripts
TASKLIST.md       - Todo list & API wishlist
AGENTS.md         - Agent documentation
RULES.md          - Rules for AI agents
```

---

*For AI assistants: Always check RULES.md before making changes!*

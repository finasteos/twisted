# TWISTED - Task List for Brave Builders

> "Not all those who wander are lost - but they could use a better agent orchestration system."

---

## ✅ Phase 1: Get a Successful Run Working (COMPLETED)

### What's Working Now:
- [x] Agent chat with automatic model fallback
- [x] Quick chat endpoint with retry logic
- [x] Verbose logging for debugging
- [x] Fallback: gemini-3.1 → gemini-2.5 → gemini-2.0 → local LLM
- [x] Local LLM support (LM Studio)
- [x] Usage tracking
- [x] Rate limit handling (10s for tier 1)

### Current Issues:
- ⚠️ Google Gemini 3.1-pro-preview returns 503 (high demand)
- ⚠️ Local LLM server not reachable (172.20.10.3:1234)
- ⚠️ gemini-3-flash-preview works but not yet in fallback chain

---

## 🎯 Phase 2: Immediate TODO

- [ ] Update fallback chain to include `gemini-3-flash-preview` (confirmed working!)
- [ ] Test full agent flow in frontend
- [ ] Verify LM Studio connection when on same network

---

## 💡 API Wishlist

Here are suggested APIs to add for a better engine:

### High Priority
- [ ] `POST /api/agents/{agent}/memory/search` - Search agent memory
- [ ] `DELETE /api/agents/{agent}/memory` - Clear agent memory
- [ ] `GET /api/agents/list` - List all available agents
- [ ] `POST /api/agents/{agent}/reload` - Reload agent config

### Monitoring
- [ ] `GET /api/system/health` - Full system health check
- [ ] `GET /api/system/stats` - Combined stats (memory, CPU, API usage)
- [ ] `GET /api/logs/stream` - SSE for live logs

### Agent Management
- [ ] `POST /api/agents/create` - Create new agent
- [ ] `PUT /api/agents/{agent}/config` - Update agent config
- [ ] `DELETE /api/agents/{agent}` - Delete agent
- [ ] `POST /api/agents/{agent}/clone` - Clone existing agent

### Advanced
- [ ] `POST /api/swarm/run` - Run agent swarm
- [ ] `GET /api/swarm/{run_id}/status` - Swarm execution status
- [ ] `POST /api/grounding/search` - Direct grounding search
- [ ] `GET /api/models/pricing` - Estimated costs per model

---

## 🔧 Technical Notes

### Environment
- Python 3.12+ (`.venv312`)
- Node.js 18+
- Google Gemini API (Grounding with File Search)
- LM Studio for local LLM fallback

### Key Files
- `backend/main.py` - FastAPI server, all endpoints
- `backend/llm/wrapper.py` - Gemini wrapper with rate limiting
- `backend/llm/model_config.py` - Model configuration
- `backend/llm/local_llm.py` - Local LLM client
- `backend/config/settings.py` - Settings
- `agents/` - Agent profiles (IDENTITY.md, SKILLS.md, SOUL.md)

### API Keys Needed
- Gemini API (in `.env`)
- LM Studio running at `172.20.10.3:1234`

---

## 📊 Model Fallback Chain (Current)

```
1. gemini-3.1-pro-preview     ← Often returns 503 (high demand)
2. gemini-2.5-flash           ← Works
3. gemini-2.0-flash           ← Works
4. Local LLM (LM Studio)     ← Not reachable
```

### Known Working Models
- ✅ gemini-3-flash-preview
- ✅ gemini-2.5-flash
- ✅ gemini-2.0-flash

---

*"The best way to predict the future is to invent it."* - Alan Kay

*"Or just build really good AI agents. Either works."* - TWISTED Team

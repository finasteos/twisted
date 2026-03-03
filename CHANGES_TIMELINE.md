# TWISTED System - Change Timeline

## Session: 2026-03-03 - Backend & Frontend Setup

---

### 1. FIXED: Backend Reload Issue
- **Time**: Start of session
- **Issue**: Backend had `reload=True` causing constant restarts
- **Fix**: Changed to `reload=False` in `backend/main.py:1310`
- **Result**: Backend runs stable without auto-reload

---

### 2. ADDED: Rate Limit Configuration
- **Time**: Early in session
- **File**: `backend/config/settings.py`
- **Changes**:
  - `RATE_LIMIT_FLASH`: 12.0s → 10.0s (10% of tier 1 max)
  - `RATE_LIMIT_PRO`: 100.0s → 10.0s (10% of tier 1 max)
- **File**: `backend/llm/wrapper.py`
- **Changes**:
  - Updated RATE_LIMITS dict to use 10s for both Flash and Pro

---

### 3. ADDED: Model Configuration
- **Time**: Mid session
- **File Created**: `backend/llm/model_config.py`
- **Purpose**: Central configuration for all Gemini models
- **Contains**:
  - All Gemini models (2.x, 3.x, Deep Research)
  - Model capabilities (thinking, vision, caching)
  - Tier 1 rate limits (RPM, TPM, RPD)
  - Deprecation status
  - Helper functions: `get_model_info()`, `get_all_models()`, `get_preferred_models()`

---

### 4. ADDED: Usage Tracking
- **File**: `backend/llm/wrapper.py`
- **Changes**:
  - Added `usage_stats` dict tracking:
    - `total_requests`
    - `total_prompt_tokens`
    - `total_completion_tokens`
    - `total_errors`
    - `rate_limit_hits`
    - `requests_by_model`
  - Added methods:
    - `record_usage()` - records API usage
    - `get_usage_stats()` - returns current stats with RPM estimates
    - `reset_usage_stats()` - resets counters

---

### 5. ADDED: New API Endpoints
- **File**: `backend/main.py`
- **Added**:
  - `GET /api/gemini/usage` - Usage statistics
  - `POST /api/gemini/usage/reset` - Reset stats
  - `GET /api/gemini/models` - List all available models
  - `GET /api/gemini/test` - Direct API test
  - `POST /api/quick/chat` - Quick chat without queue
  - `GET /api/local-llm/status` - Local LLM status
  - `POST /api/local-llm/chat` - Local LLM chat

---

### 6. ADDED: Local LLM Support (LM Studio)
- **File Created**: `backend/llm/local_llm.py`
- **Purpose**: Connect to local LLM via LM Studio
- **Features**:
  - Connects to `http://172.20.10.3:1234`
  - Model: `llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b`
  - Async HTTP calls
  - Usage tracking
  - Health checks
- **File Updated**: `backend/config/settings.py`
  - Added: `LOCAL_LLM_ENABLED`, `LOCAL_LLM_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_TIMEOUT`
- **File Updated**: `backend/main.py`
  - Added initialization in lifespan
  - Added global `local_llm_client` variable
  - Added endpoints for local LLM

---

### 7. ADDED: Verbose Logging for Agent Chat
- **File**: `backend/main.py` - `agent_chat` endpoint
- **Added Logs**:
  - `🔵 AGENT CHAT START` - When request arrives
  - `📁 Loading agent profile` - Profile path
  - `✅ Loaded system prompt` - Prompt loaded
  - `📚 Found X memories` - Memory lookup result
  - `📤 Sending to Gemini` - API call start
  - `✅ Gemini response received` - Success
  - `❌ Gemini API error` - Error handling
  - `🔄 Trying local LLM fallback` - Fallback attempt
  - `✅ Local LLM response received` - Fallback success
  - `💾 Stored messages in Qdrant` - Memory storage
  - `🎉 AGENT CHAT COMPLETE` - Success
  - `❌ AGENT CHAT FAILED` - Final error

---

### 8. FIXED: Gemini API Call Method
- **Issue**: Python SDK (`google.genai`) hangs on API calls
- **Solution**: Switched to direct HTTP calls using `httpx`
- **Files Updated**:
  - `backend/main.py` - `/api/gemini/test`, `/api/quick/chat`, `agent_chat`
- **Benefits**:
  - No more hanging requests
  - Proper timeout handling
  - Better error messages (503, etc.)
  - Works when Python SDK fails

---

### 9. ADDED: Fallback Logic
- **File**: `backend/main.py`
- **Implemented**:
  - If Gemini returns 503, automatically try local LLM
  - If both fail, return clear error message
  - Fallback available in:
    - `/api/quick/chat`
    - `/api/agents/chat`

---

### 10. CURRENT ISSUES IDENTIFIED
- **Google Gemini 3.1-pro-preview**: Returns 503 (high demand)
- **Local LLM**: Server `172.20.10.3:1234` not reachable
- **Python SDK**: Hangs on API calls (using httpx as workaround)

---

### Files Modified:
1. `backend/main.py` - Multiple endpoints and fixes
2. `backend/config/settings.py` - Rate limits + Local LLM settings
3. `backend/llm/wrapper.py` - Usage tracking
4. `backend/llm/model_config.py` - NEW - Model configuration
5. `backend/llm/local_llm.py` - NEW - Local LLM client

---

### Next Optimizations (TODO):
- Fix the queue-based rate limiter in wrapper
- Add retry logic with exponential backoff
- Cache model list
- Add more aggressive fallback (try gemini-2.5-flash if 3.1 fails)
- Clean up old unused code

---

## Session: 2026-03-03 (Continued) - Optimizations Applied

### 11. ADDED: Retry Logic with Exponential Backoff
- **File**: `backend/main.py`
- **Implementation**:
  - Tries `gemini-3.1-pro-preview` first
  - If 503, waits 2s, then 4s (exponential backoff)
  - Falls back to `gemini-2.5-flash`
  - Falls back to `gemini-2.0-flash`
  - All attempts use max 3 retries
- **Applied to**:
  - `/api/quick/chat`
  - `/api/agents/chat`

### 12. ADDED: Model Fallback Chain
- **Models tried in order**:
  1. `gemini-3.1-pro-preview` (preferred)
  2. `gemini-2.5-flash` (fallback 1)
  3. `gemini-2.0-flash` (fallback 2)
- **Local LLM**: Final fallback if all cloud models fail

### 13. REPLACED: Python SDK with httpx
- **Reason**: Python SDK hangs on API calls
- **Solution**: Direct HTTP calls using httpx
- **Benefits**:
  - Proper timeout handling
  - Better error messages
  - Works when SDK fails

### 14. ADDED: Verbose Logging Throughout
- **All endpoints now log**:
  - Request start
  - Model selection
  - Retry attempts
  - Success/failure
  - Fallback attempts

---

## Summary

### What's Working Now:
✅ Agent chat with automatic model fallback
✅ Quick chat endpoint with retry logic
✅ Verbose logging for debugging
✅ Fallback from gemini-3.1 → gemini-2.5 → gemini-2.0
✅ Local LLM as final fallback

### Current Issues:
⚠️ Google Gemini 3.1-pro-preview returns 503 (high demand)
⚠️ Local LLM server not reachable (172.20.10.3:1234)

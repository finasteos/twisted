# TWISTED - Rules for AI Agents

## 🚨 GOLDEN RULE: Verify Before Using

**ALWAYS verify model names against the Gemini API before using them!**
- API endpoint: `https://generativelanguage.googleapis.com/v1/models?key=YOUR_API_KEY`
- Or use the helper: `get_available_models_from_api()` in `backend/llm/model_config.py`
- Check https://ai.google.dev/models for official documentation

**NEVER invent or assume model names!**
- If a model isn't in the verified list, it doesn't exist
- "Preview" models may not be available to all users
- When in doubt, TEST first with a simple API call

---

## ✅ VERIFIED MODELS (User-Confirmed Working)

| Model | Type | Notes |
|-------|------|-------|
| `gemini-3-flash-preview` | Flash | User's main fast model |
| `gemini-3.1-pro-preview` | Pro | User's main pro model (may return 503 under high load) |
| `gemini-2.5-flash` | Flash | Stable fallback |
| `gemini-2.0-flash` | Flash | Stable fallback |

---

## ⚠️ Model Naming Convention

**Flash = 3 (not 3.1)**
- ✅ `gemini-3-flash-preview`
- ❌ `gemini-3.1-flash-preview` (DOES NOT EXIST)

**Pro = 3.1**
- ✅ `gemini-3.1-pro-preview`

---

## 📊 Rate Limits (Tier 1 Paid)

| Model | RPM | TPM | RPD |
|-------|-----|-----|-----|
| Flash | 300 | 1M | 1500 |
| Pro | 150 | 1M | 1500 |

### Configurable Percentage
The app supports setting percentage of max limits:
- **10%** = Conservative (default)
- **50%** = Aggressive
- **100%** = Max

Use `set_rate_limit_percentage(0.5)` to set to 50%.

---

## Quick Reference

```python
# ✅ CORRECT - Use verified models
from backend.llm.model_config import get_preferred_models, set_rate_limit_percentage

# Set to 50% of max
set_rate_limit_percentage(0.5)

# Get recommended models
preferred = get_preferred_models()

# ❌ WRONG - Never use unverified names
model = "gemini-3.1-flash-preview"  # DOES NOT EXIST!
```

---

## Architecture Rules

1. **All LLM calls MUST go through GeminiWrapper** - No raw httpx calls
2. **Rate limiting is enforced** - Respect the limits in model_config.py
3. **Usage tracking is mandatory** - All API calls are tracked
4. **Fallback chain**: gemini-3-flash-preview → gemini-2.5-flash → gemini-2.0-flash → Local LLM

---

*Last updated: 2026-03-03*
*Rule: Trust the API, not assumptions!*

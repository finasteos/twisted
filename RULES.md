# Claude Code Session Rules

## 🚨 IMPORTANT: Model Versions

**ALWAYS use these models:**

| Model Type | Correct Model Name |
|------------|-------------------|
| **Flash** | `gemini-3.0-flash` or `gemini-3.0-flash-001` |
| **Pro** | `gemini-3.1-pro-preview` or `gemini-3.5-pro-preview` |

**NEVER use:**
- ❌ `gemini-2.0-flash` (deprecated)
- ❌ `gemini-2.0-flash-001` (deprecated)
- ❌ `gemini-2.5-flash-*` (old version)
- ❌ `gemini-2.5-pro-*` (old version)

---

## Quick Reference

```python
# ✅ CORRECT
llm = ChatGoogle(model="gemini-3.0-flash")

# ❌ WRONG
llm = ChatGoogle(model="gemini-2.0-flash")
```

---

*Last updated: 2026-03-02*

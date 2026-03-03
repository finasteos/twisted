# Admin Mode Settings Plan for TWISTED Backend

## 🎯 EXECUTIVE SUMMARY

**Goal**: Separate sensitive configuration from standard operational settings to enhance security and usability.

**Strategy**: Split `settings.py` into two distinct modes:
- **Standard Mode** - Safe for regular users (no API keys, limited controls)
- **Admin Mode** - Full access for system administrators (all settings, API keys, security controls)

**Security Benefits**:
- No accidental exposure of API keys to non-admin users
- Reduced attack surface in standard mode
- Clear separation of duties
- Better compliance with least privilege principle

---

## 📊 SETTINGS CATEGORIZATION

### 🔒 **ADMIN-ONLY SETTINGS** (Sensitive/Critical)

#### API Keys & Authentication
```python
# API Keys (Admin only)
GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
SERPAPI_KEY: Optional[str] = Field(None, description="SerpAPI key for web search")
TAVILY_API_KEY: Optional[str] = Field(None, description="Tavily API key alternative")

# Google Cloud (Admin only)
GOOGLE_CLOUD_PROJECT: Optional[str] = Field(None, description="Google Cloud Project ID")
GOOGLE_CLOUD_LOCATION: str = Field("us", description="Google Cloud Location (e.g., us, eu)")
DOCUMENT_AI_PROCESSOR_ID: Optional[str] = Field(None, description="Document AI Processor ID")
GOOGLE_WORKSPACE_DELEGATED_USER: Optional[str] = Field(None, description="Email to delegate as for Workspace APIs")

# Security Keys (Admin only)
ENCRYPTION_KEY: Optional[str] = Field(None, description="AES-256-GCM key for data at rest")
```

#### Performance & Resource Controls (Admin only)
```python
# Resource Limits (Admin only)
MLX_MEMORY_LIMIT_MB: int = Field(4096, description="MLX memory limit in MB")
DISABLE_LOCAL_MLX: bool = Field(True, description="Disable local MLX processing for thermal relief")

# Rate Limiting (Admin only)
RATE_LIMIT_FLASH: float = Field(12.0, description="Seconds between Flash calls")
RATE_LIMIT_PRO: float = Field(100.0, description="Seconds between Pro calls")
```

#### Advanced Features (Admin only)
```python
# Deep Research (Admin only)
ENABLE_DEEP_RESEARCH: bool = Field(False, description="Enable deep research stage")

# NotebookLM MCP (Admin only)
NOTEBOOKLM_MCP_ENABLED: bool = Field(True, description="Enable NotebookLM MCP integration")
NOTEBOOKLM_MCP_COMMAND: str = Field("notebooklm-mcp", description="Path to notebooklm-mcp command")
```

### 🔧 **STANDARD SETTINGS** (Safe for Regular Users)

#### Core Configuration (Safe)
```python
# Server Configuration (Standard)
HOST: str = Field("0.0.0.0", description="Server bind address")
PORT: int = Field(8000, description="Server port")
DEBUG: bool = Field(False, description="Debug mode")

# CORS Origins (Standard)
CORS_ORIGINS: list = Field([
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000"
])
```

#### File & Data Management (Safe)
```python
# File Handling (Standard)
UPLOAD_DIR: str = Field("./uploads", description="Temporary file storage")
MAX_FILE_SIZE: int = Field(100 * 1024 * 1024, description="Max file size in bytes (100MB)")
ALLOWED_EXTENSIONS: list = Field([...])

# Vector Storage (Standard)
CHROMA_PERSIST_DIR: str = Field("./chroma_db", description="Vector store directory")
EMBEDDING_MODEL: str = Field("text-embedding-004", description="Embedding model")
```

#### Feature Toggles (Safe)
```python
# Feature Flags (Standard)
DATA_PRIVACY_STRICT: bool = Field(False, description="Force all processing to be local if True")
GEMINI_TIER: str = Field("tier_1", description="API tier for rate limiting")
```

---

## 🏗️ IMPLEMENTATION ARCHITECTURE

### 1. **Settings Class Hierarchy**

```python
class BaseSettings(BaseSettings):
    """Common settings shared by both modes"""
    HOST: str = Field("0.0.0.0", description="Server bind address")
    PORT: int = Field(8000, description="Server port")
    DEBUG: bool = Field(False, description="Debug mode")
    UPLOAD_DIR: str = Field("./uploads", description="Temporary file storage")
    MAX_FILE_SIZE: int = Field(100 * 1024 * 1024, description="Max file size in bytes (100MB)")
    ALLOWED_EXTENSIONS: list = Field([...])
    CHROMA_PERSIST_DIR: str = Field("./chroma_db", description="Vector store directory")
    EMBEDDING_MODEL: str = Field("text-embedding-004", description="Embedding model")


class AdminSettings(BaseSettings):
    """Full admin settings with all sensitive data"""
    # API Keys (Admin only)
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
    SERPAPI_KEY: Optional[str] = Field(None, description="SerpAPI key for web search")
    TAVILY_API_KEY: Optional[str] = Field(None, description="Tavily API key alternative")
    
    # Google Cloud (Admin only)
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(None, description="Google Cloud Project ID")
    GOOGLE_CLOUD_LOCATION: str = Field("us", description="Google Cloud Location (e.g., us, eu)")
    DOCUMENT_AI_PROCESSOR_ID: Optional[str] = Field(None, description="Document AI Processor ID")
    GOOGLE_WORKSPACE_DELEGATED_USER: Optional[str] = Field(None, description="Email to delegate as for Workspace APIs")
    
    # Security Keys (Admin only)
    ENCRYPTION_KEY: Optional[str] = Field(None, description="AES-256-GCM key for data at rest")
    
    # Resource Limits (Admin only)
    MLX_MEMORY_LIMIT_MB: int = Field(4096, description="MLX memory limit in MB")
    DISABLE_LOCAL_MLX: bool = Field(True, description="Disable local MLX processing for thermal relief")
    
    # Rate Limiting (Admin only)
    RATE_LIMIT_FLASH: float = Field(12.0, description="Seconds between Flash calls")
    RATE_LIMIT_PRO: float = Field(100.0, description="Seconds between Pro calls")
    
    # Advanced Features (Admin only)
    ENABLE_DEEP_RESEARCH: bool = Field(False, description="Enable deep research stage")
    NOTEBOOKLM_MCP_ENABLED: bool = Field(True, description="Enable NotebookLM MCP integration")
    NOTEBOOKLM_MCP_COMMAND: str = Field("notebooklm-mcp", description="Path to notebooklm-mcp command")

    # Inherit from BaseSettings
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class StandardSettings(BaseSettings):
    """Limited settings for standard users"""
    # Inherit all safe settings from BaseSettings
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
```

### 2. **Mode Detection**

```python
class ModeDetector:
    """Detect current mode based on environment or request context"""
    
    @staticmethod
    def detect_mode() -> str:
        """Detect mode: 'admin' or 'standard'"""
        # Check environment variable first
        mode = os.getenv("TWISTED_MODE")
        if mode in ["admin", "standard"]:
            return mode
        
        # Check if API keys are present (admin mode)
        if os.getenv("GEMINI_API_KEY"):
            return "admin"
        
        return "standard"
```

### 3. **Unified Settings Access**

```python
class SettingsManager:
    """Unified settings access with mode-aware security"""
    
    def __init__(self):
        self.mode = ModeDetector.detect_mode()
        self._settings = None
        
        if self.mode == "admin":
            self._settings = AdminSettings()
        else:
            self._settings = StandardSettings()
    
    @property
    def settings(self) -> BaseSettings:
        """Get current mode settings"""
        if self._settings is None:
            self._settings = self._create_settings()
        return self._settings
    
    def get_admin_setting(self, key: str, default=None):
        """Get admin setting if available, else default"""
        if self.mode != "admin":
            raise PermissionError(f"Admin setting '{key}' not accessible in {self.mode} mode")
        
        return getattr(self._settings, key, default)
    
    def get_all_settings(self) -> dict:
        """Get all settings (admin only)"""
        if self.mode != "admin":
            raise PermissionError("Cannot access all settings in standard mode")
        
        return self._settings.model_dump()
```

---

## 🔐 SECURITY CONTROLS

### 1. **API Access Control**

```python
class SettingsAuthMiddleware:
    """Middleware to enforce settings access based on user role"""
    
    async def __call__(self, request: Request, call_next):
        # Check if request requires admin access
        admin_required = self._requires_admin_access(request)
        
        if admin_required:
            # Verify user is admin
            if not await self._is_admin_user(request):
                raise HTTPException(status_code=403, detail="Admin access required")
        
        return await call_next(request)
    
    def _requires_admin_access(self, request) -> bool:
        """Check if endpoint requires admin access"""
        admin_endpoints = [
            "/api/settings/admin",
            "/api/settings/api-keys",
            "/api/settings/security",
            "/api/settings/performance"
        ]
        
        for endpoint in admin_endpoints:
            if request.url.path.startswith(endpoint):
                return True
        
        return False
```

### 2. **Settings API Endpoints**

```python
# Standard Mode Endpoints (Safe)
@app.get("/api/settings")
async def get_standard_settings():
    """Get standard settings (safe for all users)"""
    return {
        "mode": "standard",
        "settings": {
            "host": settings.HOST,
            "port": settings.PORT,
            "debug": settings.DEBUG,
            "upload_dir": settings.UPLOAD_DIR,
            "max_file_size": settings.MAX_FILE_SIZE,
            "allowed_extensions": settings.ALLOWED_EXTENSIONS,
            "chroma_persist_dir": settings.CHROMA_PERSIST_DIR,
            "embedding_model": settings.EMBEDDING_MODEL,
            "data_privacy_strict": settings.DATA_PRIVACY_STRICT,
            "gemini_tier": settings.GEMINI_TIER
        }
    }

# Admin Mode Endpoints (Restricted)
@app.get("/api/settings/admin")
@admin_required
async def get_admin_settings():
    """Get all admin settings (admin only)"""
    return {
        "mode": "admin",
        "settings": settings.model_dump()
    }

@app.post("/api/settings/admin")
@admin_required
async def update_admin_settings(update_data: Dict):
    """Update admin settings (admin only)"""
    # Validate and update settings
    return {"success": True, "updated": update_data}
```

---

## 🎨 UI MODE DIFFERENCES

### Standard Mode UI
```
┌─────────────────────────────────────────────────┐
│ TWISTED SETTINGS - STANDARD MODE               │
├─────────────────────────────────────────────────┤
│ Server Configuration                            │
│   Host: 0.0.0.0                                 │
│   Port: 8000                                    │
│   Debug: Off                                    │
│                                                 │
│ File Management                                 │
│   Upload Directory: ./uploads                   │
│   Max File Size: 100MB                          │
│   Allowed Types: [jpg, png, pdf, ...]           │
│                                                 │
│ Vector Storage                                  │
│   ChromaDB: ./chroma_db                         │
│   Embedding Model: text-embedding-004           │
│                                                 │
│ Privacy & Features                              │
│   Data Privacy: Off                             │
│   Gemini Tier: tier_1                           │
│                                                 │
│ [Save Settings]                                 │
└─────────────────────────────────────────────────┘
```

### Admin Mode UI
```
┌─────────────────────────────────────────────────┐
│ TWISTED SETTINGS - ADMIN MODE                   │
├─────────────────────────────────────────────────┤
│ ⚠️ ADMIN MODE - ALL SETTINGS VISIBLE            │
│                                                 │
│ ┌── API KEYS ──────────────────────────────────┐│
│ │ Gemini API Key: [hidden]                     ││
│ │ SerpAPI Key: [hidden]                        ││
│ │ Tavily API Key: [hidden]                     ││
│ │                                             ││
│ │ [Show Keys] [Edit Keys]                      ││
│ └───────────────────────────────────────────────┘│
│                                                 │
│ ┌── GOOGLE CLOUD ──────────────────────────────┐│
│ │ Project ID: [hidden]                         ││
│ │ Location: us                                 ││
│ │ Document AI Processor: [hidden]              ││
│ │                                             ││
│ │ [Configure Cloud]                            ││
│ └───────────────────────────────────────────────┘│
│                                                 │
│ ┌── PERFORMANCE & SECURITY ──────────────────┐│
│ │ Encryption Key: [hidden]                    ││
│ │ MLX Memory Limit: 4096MB                    ││
│ │ Disable MLX: True                           ││
│ │                                             ││
│ │ [Performance Settings]                      ││
│ └───────────────────────────────────────────────┘│
│                                                 │
│ ┌── ADVANCED FEATURES ────────────────────────┐│
│ │ Deep Research: Off                          ││
│ │ NotebookLM MCP: On                          ││
│ │ NotebookLM Command: notebooklm-mcp          ││
│ │                                             ││
│ │ [Advanced Settings]                         ││
│ └───────────────────────────────────────────────┘│
│                                                 │
│ ┌── STANDARD SETTINGS ────────────────────────┐│
│ │ (same as standard mode)                     ││
│ └───────────────────────────────────────────────┘│
│                                                 │
│ [Save All Settings]                            │
│ [Export Settings]                              │
│ [Reset to Defaults]                            │
└─────────────────────────────────────────────────┘
```

---

## 🚀 IMPLEMENTATION ROADMAP

### Phase 1: Architecture Setup (Week 1)
- [ ] Create `BaseSettings`, `AdminSettings`, `StandardSettings` classes
- [ ] Implement `ModeDetector` and `SettingsManager`
- [ ] Add mode detection to main app

### Phase 2: API Security (Week 2)
- [ ] Implement `SettingsAuthMiddleware`
- [ ] Create admin endpoints (`/api/settings/admin`, etc.)
- [ ] Add role-based access control

### Phase 3: UI Integration (Week 3)
- [ ] Create admin UI components
- [ ] Implement mode switching
- [ ] Add validation and error handling

### Phase 4: Testing & Deployment (Week 4)
- [ ] Security testing
- [ ] Performance testing
- [ ] Documentation

---

## 🔑 KEY BENEFITS

1. **Enhanced Security**: API keys never exposed to standard users
2. **Better UX**: Simplified interface for regular users
3. **Clear Separation**: Admin vs user responsibilities
4. **Compliance**: Least privilege principle
5. **Scalability**: Easy to add more admin controls later
6. **Auditability**: Clear mode detection and access logs

This architecture provides a solid foundation for secure, user-friendly settings management while maintaining full administrative capabilities when needed.

const API_BASE = 'http://localhost:8000';

// ─── Types ───────────────────────────

export interface AnalyzeRequest {
  target_names: string[];
  files?: string[];
  pasted_text?: string;
  use_llm?: boolean;
  debate_rounds?: number;
  custom_question?: string;
  help_package?: string[];
  deep_research?: boolean;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  progress: number;
  confidence: number;
  message: string;
  current_agent?: string;
  recent_events?: EventEntry[];
}

export interface EventEntry {
  timestamp: string;
  type: string;
  agent: string;
  message: string;
  data: Record<string, unknown>;
}

export interface Settings {
  gemini_api_key?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
  serpapi_key?: string;
  tavily_api_key?: string;
  lmstudio_url?: string;
  lmstudio_model?: string;
  default_provider?: string;
  debate_rounds?: number;
  chunk_size?: number;
  chunk_overlap?: number;
  ocr_engine?: string;
  transcription_engine?: string;
  help_package?: string[];
  mcp_servers?: Array<{ name: string; url: string; enabled: boolean }>;
}

export interface AgentProfile {
  id: string;
  name: string;
  codename?: string;
  files: {
    identity?: string;
    skills?: string;
    soul?: string;
  };
}

export interface SystemHealth {
  timestamp: number;
  resources: {
    cpu_percent: number;
    memory_pressure: number;
    thermal_state: string;
    unified_memory_gb: {
      used: number;
      total: number;
    };
    recommended_action: string;
  };
  apis: {
    gemini: { status: string; latency?: number; message?: string };
    search: {
      tavily: { status: string; code?: number; message?: string };
      serpapi: { status: string; code?: number; message?: string };
    };
    chromadb: { status: string; collections?: string[]; message?: string };
  };
}

// ─── API Functions ───────────────────

export async function getSystemHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/api/system/health`);
  return res.json();
}

export async function uploadFiles(files: File[]): Promise<string[]> {
  const formData = new FormData();
  files.forEach(f => formData.append('files', f));

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  const data = await res.json();
  return data.uploaded || [];
}

export async function startAnalysis(req: AnalyzeRequest) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  return res.json();
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const res = await fetch(`${API_BASE}/status/${taskId}`);
  return res.json();
}

export async function getResult(taskId: string) {
  const res = await fetch(`${API_BASE}/result/${taskId}`);
  return res.json();
}

export async function getEvents(taskId: string, since: number = 0) {
  const res = await fetch(`${API_BASE}/events/${taskId}?since=${since}`);
  return res.json();
}

export async function getSettings(): Promise<Settings> {
  const res = await fetch(`${API_BASE}/settings`);
  return res.json();
}

export async function updateSettings(settings: Partial<Settings>) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  return res.json();
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function getLLMStatus() {
  const res = await fetch(`${API_BASE}/llm/status`);
  return res.json();
}

// ─── Agents API ──────────────────────

export async function listAgents(): Promise<AgentProfile[]> {
  const res = await fetch(`${API_BASE}/agents`);
  return res.json();
}

export async function getAgent(agentId: string): Promise<AgentProfile> {
  const res = await fetch(`${API_BASE}/agents/${agentId}`);
  return res.json();
}

export async function updateAgent(agentId: string, update: { identity?: string; skills?: string; soul?: string }) {
  const res = await fetch(`${API_BASE}/agents/${agentId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  });
  return res.json();
}

export async function createAgent(agentId: string, update: { identity?: string; skills?: string; soul?: string }) {
  const res = await fetch(`${API_BASE}/agents?agent_id=${encodeURIComponent(agentId)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  });
  return res.json();
}

// ─── WebSocket ───────────────────────

export function createWebSocket(taskId: string): WebSocket {
  return new WebSocket(`ws://localhost:8000/ws/${taskId}`);
}

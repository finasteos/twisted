const PYTHON_BACKEND_URL = 'http://localhost:8000';

// Determine if we should use Python backend
const USE_PYTHON_BACKEND = import.meta.env.VITE_USE_PYTHON_BACKEND === 'true';

function getBaseUrl() {
  if (USE_PYTHON_BACKEND) {
    return PYTHON_BACKEND_URL;
  }
  // Use relative URLs (same server)
  return '';
}

export async function apiFetch(path: string, options?: RequestInit) {
  const baseUrl = getBaseUrl();
  const url = `${baseUrl}${path}`;
  
  console.log(`📡 API ${options?.method || 'GET'} ${url}`);
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
}

export async function getKnowledgeDocs() {
  return apiFetch('/api/knowledge');
}

export async function addKnowledge(text: string, title: string) {
  return apiFetch('/api/knowledge', {
    method: 'POST',
    body: JSON.stringify({ text, title }),
  });
}

export async function getQdrantStats() {
  return apiFetch('/api/admin/qdrant');
}

export async function clearQdrantMemory() {
  return apiFetch('/api/admin/qdrant', {
    method: 'DELETE',
  });
}

export async function getAgentConfigs() {
  return apiFetch('/api/admin/agents');
}

export async function saveAgentConfigs(agents: any[]) {
  return apiFetch('/api/admin/agents', {
    method: 'POST',
    body: JSON.stringify(agents),
  });
}

export async function getSystemHealth() {
  return apiFetch('/api/system/health');
}

export async function adminChat(message: string) {
  return apiFetch('/api/admin/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function agentChat(agent: string, message: string, sessionId?: string) {
  return apiFetch('/api/agents/chat', {
    method: 'POST',
    body: JSON.stringify({ 
      agent, 
      message,
      session_id: sessionId || `session_${agent}_${Date.now()}`
    }),
  });
}

export async function getAgentStats(agent: string) {
  return apiFetch(`/api/agents/${agent}/stats`);
}

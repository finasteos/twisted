export type ProgressUpdate = {
  stage: string;
  percent: number;
  message: string;
  etaSeconds?: number;
};

export type AgentThought = {
  agentId: string;
  state: string;
  query: string;
  evidence: string[];
  conclusion: string;
  confidence: number;
  timestamp: string;
};

export type EventLogEntry = {
  id: string;
  timestamp: string;
  level: string;
  agent: string;
  message: string;
  metadata?: Record<string, unknown>;
};

export type AgentTaskItem = {
  name: string;
  status: 'pending' | 'running' | 'done' | 'error' | 'skipped';
  duration_ms?: number;
  detail?: string;
};

export type AgentTasksUpdate = {
  agentId: string;
  agentName: string;
  tasks: AgentTaskItem[];
  overallStatus: 'idle' | 'working' | 'done' | 'error';
};

export const WS_VERSION = "1.0.0";

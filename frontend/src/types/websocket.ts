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
  metadata?: any;
};

export const WS_VERSION = "1.0.0";

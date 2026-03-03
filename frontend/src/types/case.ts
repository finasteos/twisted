export type CaseStatus =
  | 'IDLE'
  | 'UPLOADING'
  | 'ANALYZING'
  | 'DEBATING'
  | 'SYNTHESIZING'
  | 'COMPLETE'
  | 'ERROR';

export const CaseStatus = {
  IDLE: 'IDLE' as const,
  UPLOADING: 'UPLOADING' as const,
  ANALYZING: 'ANALYZING' as const,
  DEBATING: 'DEBATING' as const,
  SYNTHESIZING: 'SYNTHESIZING' as const,
  COMPLETE: 'COMPLETE' as const,
  ERROR: 'ERROR' as const
};

export interface AgentState {
  id: string;
  name: string;
  status: 'idle' | 'thinking' | 'active' | 'complete';
  state: string;
  confidence: number;
  lastThought?: string;
}

export interface CaseDeliverables {
  strategic_report?: string;
  emails?: any[];
  contacts?: any[];
  visuals?: any[];
}

export interface CaseState {
  caseId: string | null;
  status: CaseStatus;
  progress: number;
  stage: string;
  currentAgent: string | null;
  agents: AgentState[];
  connections: any[];
  eventLog: any[];
  deliverables: CaseDeliverables;
}

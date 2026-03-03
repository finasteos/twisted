export enum CaseStatus {
  IDLE = 'IDLE',
  CREATED = 'CREATED',
  UPLOADING = 'UPLOADING',
  ANALYZING = 'ANALYZING',
  DEBATING = 'DEBATING',
  SYNTHESIZING = 'SYNTHESIZING',
  COMPLETE = 'COMPLETE',
  FAILED = 'FAILED'
}

export interface CaseState {
  status: CaseStatus;
  progress: number;
  stage: string;
  agents: any[];
  connections: any[];
  currentAgent?: string;
  eventLog: any[];
  deliverables?: any;
}

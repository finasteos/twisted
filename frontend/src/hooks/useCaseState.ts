import { useCallback, useState } from 'react';
import type { CaseDeliverables, CaseState } from '../types/case';
import { CaseStatus } from '../types/case';
import type { AgentThought, EventLogEntry, ProgressUpdate } from '../types/websocket';

const INITIAL_STATE: CaseState = {
  caseId: null,
  status: CaseStatus.IDLE,
  progress: 0,
  stage: 'Idle',
  currentAgent: null,
  agents: [
    { id: 'context_weaver', name: 'Context Weaver', status: 'idle', state: 'idle', confidence: 1.0 },
    { id: 'outcome_architect', name: 'Outcome Architect', status: 'idle', state: 'idle', confidence: 1.0 },
    { id: 'chronicle_scribe', name: 'Chronicle Scribe', status: 'idle', state: 'idle', confidence: 1.0 },
    { id: 'pulse_monitor', name: 'Pulse Monitor', status: 'idle', state: 'idle', confidence: 1.0 }
  ],
  connections: [],
  eventLog: [],
  deliverables: {}
};

export function useCaseState() {
  const [caseState, setCaseState] = useState<CaseState>(INITIAL_STATE);

  const updateProgress = useCallback((update: ProgressUpdate) => {
    setCaseState(prev => ({
      ...prev,
      progress: update.percent,
      stage: update.stage,
      status: CaseStatus.ANALYZING
    }));
  }, []);

  const addAgentThought = useCallback((thought: AgentThought) => {
    setCaseState(prev => ({
      ...prev,
      currentAgent: thought.agentId,
      status: CaseStatus.DEBATING,
      agents: prev.agents.map(a =>
        a.id === thought.agentId ? {
          ...a,
          status: 'thinking',
          state: thought.state,
          confidence: thought.confidence,
          lastThought: thought.conclusion
        } : a
      ),
      eventLog: [...prev.eventLog, {
        id: thought.timestamp,
        type: 'THOUGHT',
        agent: thought.agentId,
        message: thought.conclusion,
        timestamp: thought.timestamp
      }]
    }));
  }, []);

  const addEventLog = useCallback((entry: EventLogEntry) => {
    setCaseState(prev => ({
      ...prev,
      eventLog: [...prev.eventLog, entry]
    }));
  }, []);

  const setDeliverables = useCallback((deliverables: unknown) => {
    setCaseState(prev => ({
      ...prev,
      status: CaseStatus.COMPLETE,
      progress: 100,
      stage: 'Complete',
      deliverables: deliverables as CaseDeliverables
    }));
  }, []);

  const resetCase = useCallback(() => {
    setCaseState(INITIAL_STATE);
  }, []);

  return {
    caseState,
    updateProgress,
    addAgentThought,
    addEventLog,
    setDeliverables,
    resetCase
  };
}

import {
    Background,
    BackgroundVariant,
    Controls,
    Handle,
    Position,
    ReactFlow,
    type Edge,
    type Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { listAgents, type AgentProfile, type EventEntry } from '../api';

interface FlowOverviewProps {
  onClose?: () => void;
  progress?: { status: string; progress?: number; confidence?: number; current_agent?: string };
  events?: EventEntry[];
}

// Custom Node to display active state and event logs
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function CustomFlowNode({ data }: { data: any }) {
  const isActive = data.isActive;
  const recentEvent = data.recentEvent;

  return (
    <div style={{
      background: isActive ? `rgba(255, 255, 255, 0.08)` : `rgba(255, 255, 255, 0.03)`,
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      border: `1px solid ${isActive ? data.color : 'rgba(255, 255, 255, 0.1)'}`,
      borderRadius: 16,
      padding: '16px 24px',
      color: '#ffffff',
      fontSize: 13,
      fontFamily: 'Outfit, Inter, sans-serif',
      fontWeight: 500,
      minWidth: 180,
      textAlign: 'center',
      boxShadow: isActive
        ? `0 0 30px ${data.color}30, inset 0 0 15px ${data.color}15`
        : '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      transform: isActive ? 'scale(1.05)' : 'scale(1)',
      transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
      position: 'relative',
    }}>
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        alignItems: 'center'
      }}>
        <div style={{
          fontSize: '1.2rem',
          filter: isActive ? 'drop-shadow(0 0 8px currentColor)' : 'none',
          transition: 'all 0.3s'
        }}>{data.icon}</div>
        <div style={{
          whiteSpace: 'pre-line',
          letterSpacing: '0.02em',
          opacity: isActive ? 1 : 0.8
        }}>{data.label}</div>
      </div>

      {/* Event Log Display inside Node */}
      {isActive && recentEvent && (
        <div style={{
          marginTop: 16,
          paddingTop: 12,
          borderTop: `1px solid rgba(255, 255, 255, 0.1)`,
          fontSize: 11,
          color: 'rgba(255, 255, 255, 0.6)',
          textAlign: 'left',
          animation: 'fade-in 0.5s ease-out',
        }}>
          <div style={{
            display: 'flex',
            gap: 6,
            alignItems: 'flex-start'
          }}>
            <span style={{ color: data.color, fontWeight: 800 }}>●</span>
            <span>{recentEvent.message}</span>
          </div>
        </div>
      )}

      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes = {
  customNode: CustomFlowNode,
};

export function FlowOverview({ onClose, progress, events = [] }: FlowOverviewProps) {
  const [agents, setAgents] = useState<AgentProfile[]>([]);

  useEffect(() => {
    listAgents().then(setAgents).catch(() => {});
  }, []);

  // Compute active nodes and events
  const getActiveState = useCallback((nodeId: string, nodeType: string) => {
    let isActive = false;
    let recentEvent = null;

    if (!progress) return { isActive, recentEvent };

    // Find the most recent event for this node type
    const relevantEvents = events.filter(e => {
      if (nodeType === 'ingestion' && e.type === 'ingest') return true;
      if (nodeType === 'chromadb' && e.type === 'vector') return true;
      if (nodeType === 'agent' && e.type === 'agent' && `agent-${e.agent}` === nodeId) return true;
      if (nodeType === 'llm' && e.type === 'llm_call') return true;
      if (nodeType === 'report' && e.type === 'complete') return true;
      return false;
    });

    if (relevantEvents.length > 0) {
      recentEvent = relevantEvents[relevantEvents.length - 1];
    }

    // Determine if currently active based on status
    if (progress.status === 'ingesting' && nodeType === 'ingestion') isActive = true;
    if (progress.status === 'ingesting' && (progress.progress ?? 0) >= 0.15 && nodeType === 'chromadb') isActive = true;
    if (progress.status === 'llm_analysis') {
      if (nodeType === 'agent' && `agent-${progress.current_agent}` === nodeId) isActive = true;
      if (nodeType === 'llm' && recentEvent && Date.now() - new Date(recentEvent.timestamp).getTime() < 2000) isActive = true;
    }
    if (progress.status === 'generating' && nodeType === 'report') isActive = true;

    return { isActive, recentEvent };
  }, [progress, events]);

  // Build nodes and edges from agent data
  const buildFlow = useCallback(() => {
    const nodes: Node[] = [
      // Input sources
      {
        id: 'file-drop',
        type: 'customNode',
        position: { x: 50, y: 50 },
        data: { label: 'File Drop', icon: '📂', color: '#a78bfa', ...getActiveState('file-drop', 'source') },
        sourcePosition: Position.Right,
      },
      {
        id: 'clipboard',
        type: 'customNode',
        position: { x: 50, y: 160 },
        data: { label: 'Clipboard Paste', icon: '📋', color: '#a78bfa', ...getActiveState('clipboard', 'source') },
        sourcePosition: Position.Right,
      },

      // Ingestion
      {
        id: 'ingestion',
        type: 'customNode',
        position: { x: 300, y: 105 },
        data: { label: 'Ingestion Router', icon: '🔄', color: '#34d399', ...getActiveState('ingestion', 'ingestion') },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      },

      // Vector Store
      {
        id: 'chromadb',
        type: 'customNode',
        position: { x: 550, y: 105 },
        data: { label: 'ChromaDB Memory', icon: '🧠', color: '#10b981', ...getActiveState('chromadb', 'chromadb') },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      },
    ];

    // Agent nodes
    const agentNames = agents.length > 0
      ? agents.map(a => ({ id: a.id, name: a.name, codename: a.codename }))
      : [
          { id: 'context_analyzer', name: 'Context Analyzer', codename: 'The Archivist' },
          { id: 'legal_advisor', name: 'Legal Advisor', codename: 'The Counselor' },
          { id: 'strategist', name: 'Strategist', codename: 'The Architect' },
          { id: 'final_reviewer', name: 'Final Reviewer', codename: 'The Sentinel' },
        ];

    agentNames.forEach((agent, i) => {
      nodes.push({
        id: `agent-${agent.id}`,
        type: 'customNode',
        position: { x: 820, y: 20 + i * 110 },
        data: {
          label: `${agent.name}\n${agent.codename ? `(${agent.codename})` : ''}`,
          icon: '🤖',
          color: '#60a5fa',
          ...getActiveState(`agent-${agent.id}`, 'agent')
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });
    });

    // LLM Provider
    nodes.push({
      id: 'llm',
      type: 'customNode',
      position: { x: 1100, y: 165 },
      data: { label: 'LLM Provider', icon: '⚡', color: '#fbbf24', ...getActiveState('llm', 'llm') },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    });

    // Report output
    nodes.push({
      id: 'report',
      type: 'customNode',
      position: { x: 1350, y: 165 },
      data: { label: 'Strategic Report', icon: '📊', color: '#f59e0b', ...getActiveState('report', 'report') },
      targetPosition: Position.Left,
    });

    // Edges
    const edges: Edge[] = [
      { id: 'e-file-ingest', source: 'file-drop', target: 'ingestion', animated: true, style: { stroke: '#8b5cf6' } },
      { id: 'e-clip-ingest', source: 'clipboard', target: 'ingestion', animated: true, style: { stroke: '#8b5cf6' } },
      { id: 'e-ingest-chroma', source: 'ingestion', target: 'chromadb', animated: true, style: { stroke: '#34d399' } },
    ];

    // Each agent connects to ChromaDB (RAG) and to LLM
    agentNames.forEach((agent, i) => {
      edges.push({
        id: `e-chroma-agent-${i}`,
        source: 'chromadb',
        target: `agent-${agent.id}`,
        animated: true,
        style: { stroke: '#60a5fa' },
      });
      edges.push({
        id: `e-agent-llm-${i}`,
        source: `agent-${agent.id}`,
        target: 'llm',
        animated: true,
        style: { stroke: '#f59e0b' },
      });
    });

    edges.push({
      id: 'e-llm-report',
      source: 'llm',
      target: 'report',
      animated: true,
      style: { stroke: '#fbbf24' },
    });

    return { nodes, edges };
  }, [agents, getActiveState]);

  const { nodes, edges } = buildFlow();

  return (
    <div className="flow-overlay" onClick={(e) => {
      if (e.target === e.currentTarget && onClose) onClose();
    }}>
      <div className="flow-panel" style={{
        width: '95%',
        maxWidth: 1400,
        height: '80vh',
        borderRadius: 16,
        background: '#12121a',
        border: '1px solid rgba(255,255,255,0.08)',
        overflow: 'hidden',
        position: 'relative',
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '16px 24px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          background: '#0a0a0f',
        }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, display: 'flex', gap: 8, alignItems: 'center' }}>
            🔄 Agent Flow Overview
          </h2>
          {progress && progress.status !== 'completed' && progress.status !== 'pending' && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '6px 16px',
              borderRadius: 20,
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'rgba(255, 255, 255, 0.5)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Confidence
              </span>
              <div style={{
                width: 100,
                height: 6,
                background: 'rgba(255, 255, 255, 0.1)',
                borderRadius: 3,
                overflow: 'hidden',
                position: 'relative'
              }}>
                <div style={{
                  width: `${(progress.confidence ?? 0) * 100}%`,
                  height: '100%',
                  background: `linear-gradient(90deg, #3b82f6, #60a5fa)`,
                  boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)',
                  transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)',
                }} />
              </div>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, minWidth: 40, color: '#60a5fa' }}>
                {Math.round((progress.confidence ?? 0) * 100)}%
              </span>
            </div>
          )}
          {onClose && (
            <button className="settings-btn" onClick={onClose} style={{ border: 'none' }}>
              <X size={18} />
            </button>
          )}
        </div>
        <div style={{ height: 'calc(100% - 57px)' }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            proOptions={{ hideAttribution: true }}
            style={{ background: '#0a0a0f' }}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1a1a2e" />
            <Controls
              style={{
                background: '#1a1a2e',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 8,
              }}
            />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}

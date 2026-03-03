import {
    Background,
    Controls,
    type Edge,
    type Node,
    ReactFlow,
    useEdgesState,
    useNodesState
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useEffect, useMemo } from 'react';
import { AgentNode } from './AgentNode';

interface AgentTaskItem {
  name: string;
  status: 'pending' | 'running' | 'done' | 'error' | 'skipped';
  duration_ms?: number;
  detail?: string;
}

interface AgentFlowGraphProps {
  agents: Array<{
    id: string;
    name: string;
    state: string;
    confidence: number;
    lastThought?: string;
    tasks?: AgentTaskItem[];
    overallTaskStatus?: string;
  }>;
  connections: Array<{
    from: string;
    to: string;
    active: boolean;
  }>;
  activeAgent?: string;
}

const nodeTypes = {
  agent: AgentNode
};

/**
 * Real-time Agent Swarm Visualization
 *
 * Shows:
 * - Agent nodes with live state (idle, querying, reasoning, debating)
 * - Animated edges showing data flow
 * - Confidence levels via visual indicators
 * - Active thought bubbles
 */

export function AgentFlowGraph({ agents, connections, activeAgent }: AgentFlowGraphProps) {
  const initialNodes: Node[] = useMemo(() => [
    // Coordinator at top
    {
      id: 'coordinator',
      type: 'agent',
      position: { x: 400, y: 30 },
      data: {
        name: 'Coordinator Alpha',
        role: 'orchestrator',
        state: 'active',
        confidence: 1.0,
        isActive: false
      }
    },
    // Analysis layer
    {
      id: 'context_weaver',
      type: 'agent',
      position: { x: 100, y: 200 },
      data: {
        name: 'Context Weaver',
        role: 'analysis',
        state: 'idle',
        confidence: 1.0,
        isActive: false
      }
    },
    {
      id: 'echo_vault',
      type: 'agent',
      position: { x: 400, y: 200 },
      data: {
        name: 'Echo Vault',
        role: 'memory',
        state: 'idle',
        confidence: 1.0,
        isActive: false
      }
    },
    {
      id: 'dispute_skeptic',
      type: 'agent',
      position: { x: 700, y: 200 },
      data: {
        name: 'Dispute Skeptic',
        role: 'red team',
        state: 'idle',
        confidence: 1.0,
        isActive: false
      }
    },
    // Reasoning layer
    {
      id: 'outcome_architect',
      type: 'agent',
      position: { x: 400, y: 380 },
      data: {
        name: 'Outcome Architect',
        role: 'strategy',
        state: 'idle',
        confidence: 1.0,
        isActive: false
      }
    },
    // Output layer
    {
      id: 'chronicle_scribe',
      type: 'agent',
      position: { x: 250, y: 540 },
      data: {
        name: 'Chronicle Scribe',
        role: 'documentation',
        state: 'idle',
        confidence: 1.0,
        isActive: false
      }
    },
    {
      id: 'pulse_monitor',
      type: 'agent',
      position: { x: 550, y: 540 },
      data: {
        name: 'Pulse Monitor',
        role: 'telemetry',
        state: 'idle',
        confidence: 1.0,
        isActive: false
      }
    }
  ], []);

  const initialEdges: Edge[] = useMemo(() => [
    { id: 'c-cw', source: 'coordinator', target: 'context_weaver', animated: false },
    { id: 'c-ev', source: 'coordinator', target: 'echo_vault', animated: false },
    { id: 'c-ds', source: 'coordinator', target: 'dispute_skeptic', animated: false },
    { id: 'cw-oa', source: 'context_weaver', target: 'outcome_architect', animated: false },
    { id: 'ev-oa', source: 'echo_vault', target: 'outcome_architect', animated: false },
    { id: 'ds-oa', source: 'dispute_skeptic', target: 'outcome_architect', animated: false },
    { id: 'oa-cs', source: 'outcome_architect', target: 'chronicle_scribe', animated: false },
    { id: 'oa-pm', source: 'outcome_architect', target: 'pulse_monitor', animated: false },
    { id: 'c-oa', source: 'coordinator', target: 'outcome_architect', animated: false, type: 'step' }
  ], []);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes with live agent data
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => {
        const agentData = agents.find(a => a.id === node.id);
        if (agentData) {
          return {
            ...node,
            data: {
              ...node.data,
              state: agentData.state,
              confidence: agentData.confidence,
              lastThought: agentData.lastThought,
              isActive: activeAgent === node.id,
              tasks: agentData.tasks,
              overallTaskStatus: agentData.overallTaskStatus
            }
          };
        }
        return node;
      })
    );
  }, [agents, activeAgent, setNodes]);

  // Update edge animation based on active connections
  useEffect(() => {
    setEdges((eds) =>
      eds.map((edge) => {
        const connection = connections.find(
          c => c.from === edge.source && c.to === edge.target
        );
        return {
          ...edge,
          animated: connection?.active || false,
          style: connection?.active
            ? { stroke: '#00ff88', strokeWidth: 2 }
            : { stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1 }
        };
      })
    );
  }, [connections, setEdges]);

  return (
    <div className="agent-flow-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      >
        <Background
          color="rgba(255,255,255,0.05)"
          gap={20}
          size={1}
        />
        <Controls
          style={{
            background: 'rgba(15, 15, 25, 0.8)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px'
          }}
        />
      </ReactFlow>

      {/* Legend */}
      <div className="flow-legend glass-card">
        <div className="legend-item">
          <span className="legend-dot idle" />
          <span>Idle</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot querying" />
          <span>Querying</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot reasoning" />
          <span>Reasoning</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot debating" />
          <span>Debating</span>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Node,
  Edge
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { AgentNode } from './AgentNode';

interface AgentFlowGraphProps {
  agents: Array<{
    id: string;
    name: string;
    state: string;
    confidence: number;
    lastThought?: string;
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

export function AgentFlowGraph({ agents, connections, activeAgent }: AgentFlowGraphProps) {
  const initialNodes: Node[] = useMemo(() => [
    {
      id: 'coordinator',
      type: 'agent',
      position: { x: 400, y: 50 },
      data: { name: 'Coordinator Alpha', role: 'orchestrator', state: 'active' }
    },
    {
      id: 'context_weaver',
      type: 'agent',
      position: { x: 200, y: 200 },
      data: { name: 'Context Weaver', role: 'analysis', state: 'idle' }
    },
    {
      id: 'echo_vault',
      type: 'agent',
      position: { x: 600, y: 200 },
      data: { name: 'Echo Vault', role: 'memory', state: 'idle' }
    },
    {
      id: 'outcome_architect',
      type: 'agent',
      position: { x: 400, y: 350 },
      data: { name: 'Outcome Architect', role: 'strategy', state: 'idle' }
    },
    {
      id: 'chronicle_scribe',
      type: 'agent',
      position: { x: 300, y: 500 },
      data: { name: 'Chronicle Scribe', role: 'documentation', state: 'idle' }
    },
    {
      id: 'pulse_monitor',
      type: 'agent',
      position: { x: 500, y: 500 },
      data: { name: 'Pulse Monitor', role: 'telemetry', state: 'idle' }
    }
  ], []);

  const initialEdges: Edge[] = useMemo(() => [
    { id: 'c-cw', source: 'coordinator', target: 'context_weaver', animated: true },
    { id: 'c-ev', source: 'coordinator', target: 'echo_vault', animated: false },
    { id: 'cw-oa', source: 'context_weaver', target: 'outcome_architect', animated: true },
    { id: 'ev-oa', source: 'echo_vault', target: 'outcome_architect', animated: false },
    { id: 'oa-cs', source: 'outcome_architect', target: 'chronicle_scribe', animated: false },
    { id: 'oa-pm', source: 'outcome_architect', target: 'pulse_monitor', animated: false },
    { id: 'c-oa', source: 'coordinator', target: 'outcome_architect', animated: false, type: 'step' }
  ], []);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

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
              isActive: activeAgent === node.id
            }
          };
        }
        return node;
      })
    );
  }, [agents, activeAgent, setNodes]);

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
    <div className="h-full w-full relative glass-card overflow-hidden">
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
      
      <div className="absolute bottom-4 right-4 glass-card p-4 flex space-x-4 text-xs font-medium text-[var(--text-secondary)] z-10">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-[rgba(255,255,255,0.2)]" />
          <span>Idle</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-[var(--accent-blue)]" />
          <span>Querying</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-[var(--accent-purple)]" />
          <span>Reasoning</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-[var(--accent-amber)]" />
          <span>Debating</span>
        </div>
      </div>
    </div>
  );
}

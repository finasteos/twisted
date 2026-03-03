import { Handle, Position } from '@xyflow/react';
import React from 'react';

interface AgentNodeProps {
  data: {
    name: string;
    role: string;
    state: 'idle' | 'thinking' | 'active' | 'complete' | 'error';
    confidence: number;
    lastThought?: string;
    isActive: boolean;
  };
}

export const AgentNode: React.FC<AgentNodeProps> = ({ data }) => {
  const getStatusColor = () => {
    switch (data.state) {
      case 'thinking': return 'text-blue-400';
      case 'active': return 'text-green-400';
      case 'error': return 'text-red-400';
      default: return 'text-white/50';
    }
  };

  return (
    <div className={`agent-node glass-card p-4 min-w-[180px] transition-all duration-500 ${data.isActive ? 'isActive ring-2 ring-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.3)]' : 'opacity-80'}`}>
      <Handle type="target" position={Position.Top} className="!bg-white/20 !border-white/10" />

      <div className="agent-node-header flex justify-between items-center mb-2">
        <span className="agent-name font-bold text-sm tracking-wider uppercase">{data.name}</span>
        <div className={`status-dot w-2 h-2 rounded-full ${data.state === 'active' || data.state === 'thinking' ? 'bg-green-400 animate-pulse' : 'bg-white/20'}`} />
      </div>

      <div className="agent-role text-[10px] text-white/40 uppercase mb-3 tracking-widest">{data.role}</div>

      <div className="confidence-meter w-full bg-white/5 h-1 rounded-full mb-2 overflow-hidden">
        <div
          className="confidence-level h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-1000"
          style={{ width: `${data.confidence * 100}%` }}
        />
      </div>

      {data.lastThought && (
        <div className="agent-thought text-[11px] leading-relaxed text-white/70 mt-3 border-t border-white/5 pt-2 animate-fade-in line-clamp-3">
          "{data.lastThought}"
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-white/20 !border-white/10" />

      {data.state === 'thinking' && (
        <div className="scan-line absolute inset-0 rounded-xl overflow-hidden pointer-events-none" />
      )}
    </div>
  );
};
